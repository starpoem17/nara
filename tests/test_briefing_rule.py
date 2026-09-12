"""Rule extraction and the twelve-group model/output seam; no GPU inference."""
import csv
import json
from pathlib import Path
import tempfile
import unittest

from nara.briefing_rule import judge
from nara.hypothesis6 import judge as experience_judge
from nara.hybrid_experiment import THINK
from nara.prefix_predictor import SourceFirstPredictor, predict_notice
from scripts.benchmark_compact200 import configuration
from scripts.benchmark_grouping_time import PLANS
from script import write_submission
from test_inference import Model, Retriever, final


def notice(text, negotiated=True):
    return {'id': 'test', 'meta': {'낙찰방법': '협상에의한계약' if negotiated else '적격심사제'},
            'docs': [{'doc_id': 'D0', 'type': '공고문', 'text': text}]}


class BriefingRuleTests(unittest.TestCase):
    def test_mandatory_phrasing_and_scope(self):
        for text, expected in [
            ('사업설명회 불참 업체는 입찰 참가 불가', 1),
            ('사업설명회에 참석하지 아니한 업체의 입찰 참가는 허용되지 않습니다.', 1),
            ('현장설명회 참석업체에 한하여 제안서 제출 자격을 부여합니다.', 1),
            ('설명회 미참석 업체의 제안서는 접수하지 않음', 1),
            ('입찰참가자격\n아래의 자격을 모두 갖춘 자\n○ 사업설명회에 참석한 자', 1),
            ('사업설명회 참석은 선택사항이며 불참 업체도 입찰 참가 가능', 0),
            ('사업설명회는 개최하지 않습니다.', 0),
            ('제안설명회에 참가하지 않은 업체는 입찰을 포기하는 것으로 간주하며 평가대상에서 제외합니다.', 0),
        ]:
            with self.subTest(text=text):
                r = notice(text)
                cell = judge(r)['judgments']['v22']
                self.assertEqual(cell['위반여부'], expected)
                if expected:
                    self.assertIn(cell['근거문구'], text)
                    self.assertLessEqual(len(cell['근거문구']), 500)
                else:
                    self.assertIsNone(cell['근거문구'])
        self.assertEqual(judge(notice('사업설명회 불참 업체는 입찰 참가 불가', False))['judgments']['v22']['위반여부'], 0)

    def test_migrated_rule_matches_frozen_predictions_without_labels(self):
        frozen = {r['id']: r for r in map(json.loads, Path('analysis/v22_rule200/predictions_revised.jsonl').read_text().splitlines())}
        records = [json.loads(l) for l in Path('data/dev.jsonl').read_text().splitlines()]
        self.assertEqual({r['id'] for r in records}, set(frozen))
        for r in records:
            result = judge(r)
            self.assertEqual(result['briefing'], frozen[r['id']])
            self.assertEqual({k: result['judgments'][k] for k in ('v2', 'v3')}, experience_judge(r)['judgments'])

    def test_twelve_requests_and_complete_submission(self):
        table = json.loads(Path('data/항목표.json').read_text())['항목']
        schema = json.loads(Path('data/정답스키마_디코딩.json').read_text())['properties']['판정']
        t, s, groups = configuration(table, schema, 'groups12', True, briefing_rule=True)
        self.assertEqual(len(groups), 12)
        self.assertEqual(groups[10], ['v23'])
        self.assertEqual(set(t), set(table) - {'v2', 'v3', 'v22'})
        r = notice('사업설명회 불참 업체는 입찰 참가 불가')
        model = Model(final)
        prediction, _ = predict_notice(SourceFirstPredictor(model, Retriever(), t, s), r, groups)
        self.assertIsNone(prediction.error)
        turns = [turn for batch in model.calls for turn in batch]
        self.assertEqual(len(turns), 12)
        for turn in turns:
            self.assertNotIn('[v22]', str(turn.messages))
            spec = turn.schema.get('anyOf', [turn.schema])[-1]
            self.assertNotIn('v22', spec['properties']['judgments']['properties'])
        prediction.judgments.update(judge(r)['judgments'])
        self.assertEqual(set(prediction.judgments), set(table))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'submission.csv'
            write_submission([prediction], path)
            with path.open(newline='') as stream:
                row = next(csv.DictReader(stream))
            self.assertEqual(len(row), 49)
            self.assertEqual(row['v22'], '1')
            self.assertIn(row['e22'], r['docs'][0]['text'])
        # Legacy plans (including hybrid callers reusing groups12 configuration)
        # retain their exact assignments unless explicitly opting in.
        for plan in PLANS:
            _, _, old = configuration(table, schema, plan, True)
            self.assertEqual(old, [[k for k in group if k not in ('v2', 'v3')] for group in PLANS[plan]])
            if plan != 'groups12':
                with self.assertRaises(ValueError):
                    configuration(table, schema, plan, True, briefing_rule=True)
        self.assertIn('v22', THINK)


if __name__ == '__main__':
    unittest.main()
