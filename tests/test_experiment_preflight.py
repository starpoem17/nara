"""Fresh prefix measurements must follow current inputs and enforce context budgets."""
from types import SimpleNamespace
import unittest
from nara.inference.pipeline import measure_prefix_inputs


class PreflightTests(unittest.TestCase):
    def predictor(self, *, extra='', max_context=1000):
        model = SimpleNamespace(render_messages=lambda messages: list(messages[1]['content'].encode()),
                                max_model_len=max_context)
        return SimpleNamespace(model=model, limits=SimpleNamespace(output_tokens=16),
            _messages=lambda r, g: [{'role': 'system', 'content': ''},
                {'role': 'user', 'content': r['docs'][0]['text'] + extra + g[0]}])

    def test_current_input_changes_recompute_prefix_and_lengths(self):
        records = [{'id': 'A', 'docs': [{'text': 'source'}]}]
        before = measure_prefix_inputs(records, self.predictor(), [['a'], ['b']])
        after = measure_prefix_inputs(records, self.predictor(extra='new'), [['a'], ['b']])
        self.assertEqual(before[0]['shared_prefix_tokens'], 6)
        self.assertEqual(after[0]['shared_prefix_tokens'], 9)
        self.assertEqual(after[0]['input_tokens'], [10, 10])

    def test_context_overflow_rejected_with_output_reserve(self):
        records = [{'id': 'A', 'docs': [{'text': 'source'}]}]
        with self.assertRaisesRegex(ValueError, 'no text was truncated'):
            measure_prefix_inputs(records, self.predictor(max_context=150), [['a'], ['b']])


if __name__ == '__main__': unittest.main()
