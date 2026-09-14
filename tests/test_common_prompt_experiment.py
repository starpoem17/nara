"""An experimental common prompt must survive splitting without changing input."""
import unittest
from nara.inference.compact_predictor import CRITERIA
from nara.inference.predictor import Limits
from nara.inference.prefix_predictor import SourceFirstPredictor, predict_notice
from experiments.legacy_prefix200.code.benchmark_prefix200 import predictor_with_common
from test_inference import Model, Retriever, TABLE, SCHEMA, final, record


class CommonPromptExperimentTests(unittest.TestCase):
    def test_override_reaches_all_phases_and_preserves_source_and_schema(self):
        model = Model(final)
        old_common = CRITERIA['common']
        limits = Limits(batch_size=11, output_tokens=512)
        base = SourceFirstPredictor(model, Retriever(), TABLE, SCHEMA, limits=limits)
        revised = predictor_with_common('replacement common prompt')(
            model, Retriever(), TABLE, SCHEMA, limits=limits)
        groups = [['v1'], ['v2'], ['v3'], ['v4']]
        result, _ = predict_notice(revised, record(), groups)
        self.assertIsNone(result.error)
        self.assertEqual([len(batch) for batch in model.calls], [1, 3])
        for turn, group in zip([t for batch in model.calls for t in batch], groups):
            self.assertEqual(turn.messages[0]['content'], 'replacement common prompt')
            self.assertEqual(turn.messages[1], base._messages(record(), group)[1])
            self.assertEqual(turn.schema, base._schema(group, True))
            self.assertEqual(turn.max_tokens, 512)
        self.assertEqual(CRITERIA['common'], old_common)

    def test_original_common_override_is_identical_to_existing_path(self):
        model = Model(final)
        base = SourceFirstPredictor(model, Retriever(), TABLE, SCHEMA)
        same = predictor_with_common(CRITERIA['common'])(model, Retriever(), TABLE, SCHEMA)
        self.assertEqual(same._messages(record(), ['v1']), base._messages(record(), ['v1']))


if __name__ == '__main__':
    unittest.main()
