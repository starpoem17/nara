"""Check overlap accounting and the actual short-thinking sampling override."""
from dataclasses import dataclass
from types import SimpleNamespace
import unittest
from nara.inference.hybrid_experiment import TimedLLM
from nara.evaluation.summarize_hybrid200 import interval_union_breakdown


class TimingTests(unittest.TestCase):
    def test_concurrent_intervals_are_not_double_counted(self):
        def row(a,b,c):return {'request_stats':{'scheduled_ts':a,'first_token_ts':b,'last_token_ts':c}}
        out=interval_union_breakdown([row(1,2,4),row(1.5,2.5,5)])
        self.assertEqual(out,{'prefill_only_seconds':1.,'decode_only_seconds':2.5,'overlap_seconds':.5})
        self.assertEqual(sum(out.values()),4.)

    def test_budget_override_reaches_engine_and_leaves_instant_off(self):
        @dataclass
        class Stats:
            queued_ts:float=1.
            scheduled_ts:float=1.1
            first_token_ts:float=1.2
            last_token_ts:float=1.5
        class Engine:
            def generate(self,*args,**kw):
                self.budgets=[p.thinking_token_budget for p in kw['sampling_params']]
                return [SimpleNamespace(metrics=Stats(),request_id=str(i),prompt_token_ids=[1,2,3],num_cached_tokens=2,
                          num_cache_creation_tokens=1,outputs=[SimpleNamespace(token_ids=[4,5],finish_reason='stop')]) for i in range(2)]
        engine=Engine();observer=TimedLLM(engine);observer.thinking_budget=256
        observer.generate([],sampling_params=[SimpleNamespace(thinking_token_budget=1024),SimpleNamespace(thinking_token_budget=None)])
        self.assertEqual(engine.budgets,[256,None])
        self.assertEqual(len(observer.rows),2)
        self.assertAlmostEqual(observer.rows[0]['prefill_seconds'],.1)
        self.assertAlmostEqual(observer.rows[0]['decode_seconds'],.3)

if __name__=='__main__':unittest.main()
