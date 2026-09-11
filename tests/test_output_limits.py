"""Instant caps must recover truncated JSON without reducing thinking budgets."""
from copy import deepcopy
import unittest

from nara.batch_barrier import BatchedPredictor
from nara.continuous import ContinuousPredictor
from nara.inference import Limits, Predictor, Reply, compact
from test_continuous import Engine
from test_inference import Model, TABLE, SCHEMA, record, Retriever, final


class ReplyModel(Model):
    thinking = False

    def generate(self, turns):
        self.calls.append(deepcopy(turns))
        return {t.task_id: self.behavior(t) for t in turns}


class ReplyEngine(Engine):
    def poll(self):
        return [(key, reply.text) for key, reply in super().poll()]


class OutputLimitTests(unittest.TestCase):
    def test_search_truncation_retry_and_thinking(self):
        for predictor_type in (Predictor, ContinuousPredictor, BatchedPredictor):
            for thinking in (False, True):
                with self.subTest(predictor=predictor_type.__name__, thinking=thinking):
                    seen = []

                    def behavior(turn):
                        seen.append(turn.max_tokens)
                        if len(seen) == 1:
                            return Reply(compact({'action': 'search', 'queries': ['법령']}))
                        if len(seen) == 2:
                            return Reply('{"action":"final",', finish_reason='length')
                        return Reply(final(turn, '공고 원문 근거'))

                    model = ReplyModel(behavior) if predictor_type is Predictor else ReplyEngine(behavior)
                    model.thinking = thinking
                    p = predictor_type(model, Retriever(), TABLE, SCHEMA,
                                       limits=Limits(output_tokens=2048, instant_output_tokens=512))
                    result = p.predict([record()])[0]
                    self.assertEqual(seen, [2048, 2048, 2048] if thinking else [512, 512, 512])
                    self.assertIsNone(result.error)
                    self.assertEqual(result.judgments['v1']['근거문구'], '공고 원문 근거')
                    self.assertEqual(len(p.retriever.calls), 1)
                    self.assertEqual(sum(e['event'] == 'invalid_response'
                                         for t in result.trace for e in t['events']), 1)

    def test_mixed_batch_keeps_each_modes_budget(self):
        seen = []

        def behavior(turn):
            seen.append((turn.task_id, turn.max_tokens))
            return Reply(final(turn))

        p = BatchedPredictor(ReplyEngine(behavior), Retriever(), TABLE, SCHEMA,
                             limits=Limits(output_tokens=2048, instant_output_tokens=512))
        result = p.predict([record()], item_groups=[['v1', 'v2'], ['v3', 'v4']],
                           thinking_groups=[False, True])[0]
        self.assertIsNone(result.error)
        self.assertEqual(dict(seen), {'0:0': 512, '0:1': 2048})

    def test_optional_cap_validation(self):
        self.assertIsNone(Limits().instant_output_tokens)
        for value in (0, -1, True, 1.5, 2049):
            with self.subTest(value=value), self.assertRaises(ValueError):
                Limits(output_tokens=2048, instant_output_tokens=value)


if __name__ == '__main__':
    unittest.main()
