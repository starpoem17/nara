import json
from pathlib import Path
import unittest
from nara.compact_predictor import CompactPredictor
from scripts.benchmark_compact200 import configuration
from scripts.benchmark_grouping_time import PLANS

class CompactExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.table=json.loads(Path('data/항목표.json').read_text())['항목']
        cls.schema=json.loads(Path('data/정답스키마_디코딩.json').read_text())['properties']['판정']

    def test_hypothesis_removes_only_two_targets_and_keeps_groups(self):
        for plan in PLANS:
            table,schema,groups=configuration(self.table,self.schema,plan,True)
            self.assertEqual(len(groups),len(PLANS[plan]))
            self.assertEqual(set(table),set(self.table)-{'v2','v3'})
            self.assertEqual(set(schema['required']),set(table))
            self.assertEqual(set(schema['properties']),set(table))
            self.assertEqual(len([k for g in groups for k in g]),22)
            predictor=CompactPredictor(None,None,table,schema)
            for group in groups:
                record={'id':'test','meta':{},'docs':[{'type':'공고','doc_id':'d','text':'전체 원문'}]}
                system=predictor._messages(record,group)[0]['content']
                for key in self.table:
                    self.assertEqual(f'[{key}] ' in system,key in group)
                self.assertNotIn('[v2]',system)
                self.assertNotIn('[v3]',system)

    def test_input_allowlist_and_full_source_in_every_group(self):
        record={'id':'test','meta':{'입찰추정가격':123},'docs':[
            {'type':'공고','doc_id':'a','text':'공고\n\n원문\t!'},
            {'type':'첨부','doc_id':'b','text':'첨부\n끝까지'}],
            'labels':'SENTINEL_LABEL_DO_NOT_INCLUDE'}
        p=CompactPredictor(None,None,self.table,self.schema)
        source=p._messages(record,list(self.table))[1]
        for group in PLANS['groups12']:
            messages=p._messages(record,group)
            self.assertEqual(messages[1],source)
            self.assertNotIn('SENTINEL',json.dumps(messages))
            for doc in record['docs']:self.assertIn(doc['text'],source['content'])

if __name__=='__main__':unittest.main()
