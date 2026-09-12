"""Verify prefix reuse scheduling preserves independent complete predictions."""
import unittest
from nara.inference.compact_predictor import CompactPredictor, CRITERIA
from nara.inference.prefix_predictor import SourceFirstPredictor, predict_notice
from test_inference import TABLE, SCHEMA, Model, Retriever, final, record


class PrefixTests(unittest.TestCase):
    def predictor(self, model):
        return SourceFirstPredictor(model, Retriever(), TABLE, SCHEMA)

    def test_source_and_selected_criteria_preserved(self):
        model = Model(final)
        predictor = self.predictor(model)
        original = CompactPredictor(model, Retriever(), TABLE, SCHEMA)
        for group in [['v1', 'v4'], ['v2', 'v3']]:
            old = original._messages(record(), group)
            new = predictor._messages(record(), group)
            self.assertEqual(new[0], {'role': 'system', 'content': CRITERIA['common']})
            self.assertTrue(new[1]['content'].startswith(old[1]['content']))
            self.assertTrue(new[1]['content'].endswith(old[0]['content'][len(CRITERIA['common']):]))
            self.assertNotIn('DO NOT LEAK', str(new))

    def test_first_group_completes_before_independent_remaining_groups(self):
        model = Model(final)
        phases = []
        prediction, metrics = predict_notice(self.predictor(model), record(),
            [['v1'], ['v2'], ['v3'], ['v4']], lambda *x: phases.append(x))
        self.assertEqual([len(batch) for batch in model.calls], [1, 3])
        self.assertEqual(phases, [('A', 'first'), ('A', 'remaining')])
        self.assertIsNone(prediction.error)
        self.assertEqual(set(prediction.judgments), set(TABLE))
        self.assertEqual(len(prediction.trace), 4)
        self.assertEqual(len({t['task_id'] for t in prediction.trace}), 4)
        self.assertTrue(all(len(t.messages) == 2 for b in model.calls for t in b))
        self.assertEqual(len(metrics), 2)

    def test_failed_phase_does_not_become_partial_or_zero_prediction(self):
        model = Model(lambda turn: 'invalid' if '[v1] ' in turn.messages[-1]['content'] else final(turn))
        prediction, _ = predict_notice(self.predictor(model), record(), [['v1'], ['v2', 'v3', 'v4']])
        self.assertIsNotNone(prediction.error)
        self.assertIsNone(prediction.judgments)
        self.assertEqual(len(prediction.trace), 2)


if __name__ == '__main__':
    unittest.main()
