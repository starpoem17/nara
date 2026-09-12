"""The fallback must never admit a successor while an earlier batch is active."""
from copy import deepcopy
import unittest
from nara.inference.batch_barrier import BatchedPredictor
from nara.inference.predictor import Limits
from test_continuous import Engine
from test_inference import CELL, record, Retriever, final


class BatchBarrierTests(unittest.TestCase):
    def make(self, engine, keys=('v1',)):
        table={k:{'항목명':k,'부재탐지':False} for k in keys}
        return BatchedPredictor(engine,Retriever(),table,{'properties':{k:deepcopy(CELL) for k in keys}},limits=Limits(batch_size=2,output_tokens=512))

    def test_waits_for_slow_first_and_releases_in_submit_order(self):
        model=Engine();out=self.make(model).predict([record(str(i)) for i in range(5)])
        events=[(e,k) for e,k,_ in model.events]
        self.assertGreater(events.index(('submit','2:0')),events.index(('complete','0:0')))
        self.assertGreater(events.index(('submit','2:0')),events.index(('complete','1:0')))
        self.assertEqual(model.peak,2)
        self.assertEqual([r.record_id for r in out],list(map(str,range(5))))
        self.assertTrue(all(not r.error for r in out))

    def test_modes_cache_dependencies_and_retry_survive_barrier(self):
        def behavior(turn):
            if turn.task_id=='0:1' and '이전 출력' not in turn.messages[-1]['content']:return 'bad'
            return final(turn)
        model=Engine(behavior);out=self.make(model,('v1','v4')).predict([record('A'),record('B')],item_groups=[['v1'],['v4']],thinking_groups=[False,True],cache_seed=True)
        events=[(e,k) for e,k,_ in model.events]
        for key in ['0:1','1:1']:
            for seed in ['0:0','1:0']:
                self.assertGreater(events.index(('submit',key)),events.index(('complete',seed)))
        self.assertTrue(all(on==k.endswith(':1') for e,k,on in model.events if e=='submit'))
        self.assertTrue(all(set(r.judgments)=={'v1','v4'} and not r.error for r in out))
        self.assertEqual(sum(e['event']=='invalid_response' for t in out[0].trace for e in t['events']),1)

if __name__=='__main__':unittest.main()
