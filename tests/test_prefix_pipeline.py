"""Prove cache dependency, early next-source admission and bounded concurrency."""
from copy import deepcopy
import unittest
from test_continuous import Engine
from test_inference import CELL, Retriever, record
from nara.inference.predictor import Limits
from nara.inference.prefix_pipeline import PrefixPipelinePredictor


class PipelineTests(unittest.TestCase):
    def run_pipeline(self, *, budget=100, behavior=None):
        class SlowTail(Engine):
            def submit(self, turn):
                super().submit(turn)
                end, value = self.pending[turn.task_id]
                self.pending[turn.task_id] = (self.clock + (20 if turn.task_id == 'A:2' else 1), value)
        engine = SlowTail() if behavior is None else SlowTail(behavior)
        keys = ['v1', 'v4', 'v5']
        table = {k: {'항목명': k, '部': '', '부재탐지': False} for k in keys}
        schema = {'properties': {k: deepcopy(CELL) for k in keys}}
        predictor = PrefixPipelinePredictor(engine, Retriever(), table, schema,
                    limits=Limits(batch_size=3, output_tokens=512))
        results = predictor.predict([record(k) for k in 'ABCD'], item_groups=[[k] for k in keys],
                    source_tokens={k: 10 for k in 'ABCD'}, max_live_source_tokens=budget,
                    lookahead_groups=3)
        return engine, predictor, results

    def test_next_seed_starts_before_cached_notices_finish(self):
        engine, p, results = self.run_pipeline()
        events = [(e, k) for e, k, _ in engine.events]
        self.assertLess(events.index(('submit', 'C:0')), events.index(('complete', 'A:2')))
        self.assertLessEqual(engine.peak, 3)
        self.assertTrue(any(r['event'] == 'admit' and r['reason'] == 'lookahead' for r in p.admission))
        self.assertEqual([r.record_id for r in results], list('ABCD'))
        self.assertTrue(all(not r.error and set(r.judgments) == {'v1', 'v4', 'v5'} for r in results))
        for rid in 'ABCD':
            for gi in [1, 2]:
                self.assertLess(events.index(('complete', f'{rid}:0')), events.index(('submit', f'{rid}:{gi}')))

    def test_memory_bound_is_reported_without_deadlock(self):
        _, p, results = self.run_pipeline(budget=10)
        self.assertTrue(all(not r.error for r in results))
        self.assertTrue(any(e['event'] == 'admission_blocked' and e['reason'] == 'source_token_budget' for e in p.admission))
        self.assertTrue(all(e['live_source_tokens'] <= 10 for e in p.admission if e['event'] == 'admit'))

    def test_failed_seed_does_not_zero_fill_or_block_following_notices(self):
        _, _, results = self.run_pipeline(behavior=lambda _: 'invalid')
        self.assertEqual(len(results), 4)
        self.assertTrue(all(r.error and r.judgments is None for r in results))


if __name__ == '__main__': unittest.main()
