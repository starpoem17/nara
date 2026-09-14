"""Completion refill, per-request isolation, dependent cache seed and RAG retry."""
from copy import deepcopy
import json
import unittest
from nara.continuous import ContinuousPredictor
from nara.inference import Limits,Reply
from test_inference import CELL,record,Retriever,final

class Engine:
    max_model_len=100000
    thinking=True
    def __init__(self,behavior=final):self.pending={};self.events=[];self.clock=0;self.behavior=behavior;self.peak=0
    def count_text(self,text):return len(text)
    def count_messages(self,messages):return sum(len(m['content']) for m in messages)
    def submit(self,turn):
        # The first request spans several completions by later requests.
        delay=10 if turn.task_id=='0:0' else 1
        self.pending[turn.task_id]=(self.clock+delay,deepcopy(turn));self.events.append(('submit',turn.task_id,self.thinking))
        self.peak=max(self.peak,len(self.pending))
    def poll(self):
        key=min(self.pending,key=lambda k:self.pending[k][0]);end,turn=self.pending.pop(key);self.clock=end
        self.events.append(('complete',key,self.thinking));return [(key,Reply(self.behavior(turn)))]
    def abort(self):self.pending.clear()

class ContinuousTests(unittest.TestCase):
    def make(self,engine,keys=('v1',),**limits):
        table={k:{'항목명':k,'部':'','부재탐지':False} for k in keys}
        return ContinuousPredictor(engine,Retriever(),table,{'properties':{k:deepcopy(CELL) for k in keys}},limits=Limits(batch_size=2,output_tokens=512,**limits))
    def test_refills_before_slow_original_request_completes(self):
        model=Engine();p=self.make(model);r=p.predict([record(str(i)) for i in range(5)])
        events=[(e,k) for e,k,_ in model.events]
        self.assertLess(events.index(('submit','2:0')),events.index(('complete','0:0')))
        self.assertEqual(model.peak,2);self.assertEqual([x.record_id for x in r],list(map(str,range(5))))
        self.assertTrue(all(not x.error for x in r))
    def test_seed_dependency_and_modes_survive_other_completions(self):
        model=Engine();p=self.make(model,('v1','v4'))
        r=p.predict([record('A'),record('B')],item_groups=[['v1'],['v4']],thinking_groups=[False,True],cache_seed=True)
        events=[(e,k) for e,k,_ in model.events]
        self.assertLess(events.index(('complete','1:0')),events.index(('submit','1:1')))
        self.assertLess(events.index(('submit','1:1')),events.index(('complete','0:0')))
        self.assertTrue(all(on==(key.endswith(':1')) for e,key,on in model.events if e=='submit'))
        self.assertTrue(all(set(x.judgments)=={'v1','v4'} for x in r))
    def test_search_and_retry_keep_task_identity_and_budget(self):
        def behavior(t):
            if t.task_id=='0:0' and len(t.messages)==2:return json.dumps({'action':'search','queries':['법령']})
            if t.task_id=='1:0' and '이전 출력' not in t.messages[-1]['content']:return 'bad'
            return final(t)
        p=self.make(Engine(behavior));out=p.predict([record('A'),record('B'),record('C')])
        self.assertEqual(len(p.retriever.calls),1);self.assertTrue(all(not x.error for x in out))
        self.assertEqual(out[0].trace[0]['search_rounds'],1)
        self.assertEqual(sum(e['event']=='invalid_response' for e in out[1].trace[0]['events']),1)
    def test_context_failure_and_exhausted_retry_do_not_zero_fill(self):
        model=Engine(lambda t:'bad');p=self.make(model);out=p.predict([record('A')])
        self.assertIsNone(out[0].judgments);self.assertIsNotNone(out[0].error)
        model=Engine();model.max_model_len=10;p=self.make(model);out=p.predict([record('A')])
        self.assertFalse(model.events);self.assertIsNone(out[0].judgments)

if __name__=='__main__':unittest.main()
