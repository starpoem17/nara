"""Mixed-mode groups must stay independent and complete before merging."""
import unittest
from copy import deepcopy
from nara.hybrid_experiment import GROUPS,INSTANT,THINK,predict_hybrid
from nara.prefix_predictor import SourceFirstPredictor
from test_inference import Model,Retriever,CELL,final,record


class HybridTests(unittest.TestCase):
    def make(self,behavior):
        table={f'v{i}':{'항목명':str(i),'비고':'','부재탐지':i in [10,11,16,18,20]} for i in range(1,25) if i not in [2,3]}
        model=Model(behavior);model.thinking=False
        model.modes=[]
        original=model.generate
        def generate(turns):model.modes.append(model.thinking);return original(turns)
        model.generate=generate
        return SourceFirstPredictor(model,Retriever(),table,{'properties':{k:deepcopy(CELL) for k in table}})
    def test_partition_and_sequential_modes(self):
        self.assertEqual(sorted(k for g in GROUPS for k in g),sorted(f'v{i}' for i in range(1,25) if i not in [2,3]))
        p=self.make(final)
        class Observer:
            def set_phase(self,*args):pass
        r,m=predict_hybrid(p,record(),Observer())
        self.assertIsNone(r.error)
        self.assertEqual(set(r.judgments),set(p.items))
        self.assertEqual([len(b) for b in p.model.calls],[1,3,1])
        self.assertEqual(p.model.modes,[False,False,True])
        self.assertEqual([list(t['items']) for t in r.trace],GROUPS)
        self.assertEqual(len({t['task_id'] for t in r.trace}),5)
        self.assertTrue(all(len(t.messages)==2 for b in p.model.calls for t in b))
    def test_failed_thinking_does_not_become_zero_or_partial_result(self):
        p=self.make(lambda turn:'invalid' if '[v1] ' in turn.messages[-1]['content'] else final(turn))
        class Observer:
            def set_phase(self,*args):pass
        r,_=predict_hybrid(p,record(),Observer())
        self.assertIsNotNone(r.error);self.assertIsNone(r.judgments)

if __name__=='__main__':unittest.main()
