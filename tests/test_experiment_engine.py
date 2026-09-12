"""Run the default driver through failed-notice and isolated recovery accounting."""
from contextlib import ExitStack, contextmanager, redirect_stdout
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
import io
import hashlib
import json
import sys
import tempfile
import unittest

from nara.inference import Prediction
from scripts import benchmark_prefix_pipeline as runner


class ExperimentEngineTests(unittest.TestCase):
    def test_recovery_keeps_all_engine_evidence_and_explicit_failures(self):
        for isolated_needed, isolated_fails in ((False, False), (True, False), (True, True)):
            with self.subTest(isolated_needed=isolated_needed, isolated_fails=isolated_fails):
                self.run_recovery(isolated_needed, isolated_fails)

    def run_recovery(self, isolated_needed, isolated_fails):
        def judgments():
            return {f'v{i}': {'위반여부': int(i == 22), '근거문구': '사업설명회 불참 업체는 입찰 참가 불가' if i == 22 else None} for i in range(1, 25)}

        class Model:
            thinking = False
            def __init__(self):
                self.scheduler = []
                self.stages = 0
                self.serial = 0
                self.resets = 0
                self.observer_closed = False
            def engine_info(self):
                return {'max_num_seqs': 16}
            def generate(self, turns):
                return {}
            def reset_prefix_cache(self):
                self.resets += 1
                return True
            def stream(self):
                self.stages += 1
                return NS(stage={1: 'smoke', 2: 'main', 3: 'recovery'}.get(self.stages, 'isolated'),
                          rows=[], lifecycle=[])
            @contextmanager
            def observe_scheduler(self):
                try:
                    yield self.scheduler
                finally:
                    self.observer_closed = True

        model = Model()

        class Pipeline:
            def __init__(self, stream, retriever, table, schema, **kwargs):
                self.stream = stream
                self.metrics = {}
                self.admission = []
            def predict(self, selected, *, item_groups, on_record=None, **kwargs):
                results = []
                for record in selected:
                    isolated = isinstance(self, Isolated)
                    stage = 'isolated' if isolated else self.stream.stage
                    failed = record['id'] == '0' and (
                        (stage == 'main') or (stage == 'recovery' and isolated_needed)
                        or (stage == 'isolated' and isolated_fails))
                    model.serial += 1
                    rid = str(model.serial)
                    self.stream.rows.append({'request_id': rid, 'input_tokens': 1,
                                             'output_tokens': 1, 'cached_tokens': 0})
                    self.stream.lifecycle.extend([{'event': e, 'request_id': rid}
                                                  for e in ('submit', 'complete')])
                    model.scheduler.append({'attempt': stage, 'graph': {'runtime_mode': 'FULL'}})
                    events = [{'event': 'model', 'input_tokens': 1, 'output_tokens': 1, 'thinking_tokens': 0, 'response': '{}'}]
                    if not failed:
                        events.append({'event': 'final'})
                    keys = [key for group in item_groups for key in group]
                    values = {k: v for k, v in judgments().items() if k in keys}
                    result = Prediction(record['id'], None if failed else values,
                        'retry exhausted' if failed else None,
                        [{'items': keys, 'events': events, 'search_rounds': 0, 'retrieval_tokens': 0}])
                    results.append(result)
                    if on_record:
                        on_record(result)
                return results

        class Isolated(Pipeline):
            pass

        records = [{'id': str(i), 'docs': [{'doc_id': 'D0', 'type': '공고문',
                    'text': '사업설명회 불참 업체는 입찰 참가 불가'}],
                    'meta': {'낙찰방법': '협상에의한계약'}} for i in range(200)]
        counts = [{'id': r['id'], 'shared_prefix_tokens': 1, 'input_tokens': [1] * 12} for r in records]
        torch = NS(cuda=NS(synchronize=lambda: None, get_device_name=lambda _: 'test engine'))
        with tempfile.TemporaryDirectory() as temp, ExitStack() as stack:
            out = Path(temp) / 'run'
            stack.enter_context(patch.dict(sys.modules, {'torch': torch}))
            stack.enter_context(patch('nara.vllm_model.TokenCounter', return_value=NS()))
            stack.enter_context(patch('nara.vllm_model.VLLMModel', return_value=model))
            stack.enter_context(patch('nara.retrieval.BGEEncoder', return_value=None))
            stack.enter_context(patch('nara.retrieval.LegalRetriever', return_value=None))
            stack.enter_context(patch.object(runner, 'read_records', return_value=records))
            stack.enter_context(patch.object(runner, 'measure_prefix_inputs', return_value=counts))
            stack.enter_context(patch.object(runner, 'PrefixPipelinePredictor', Pipeline))
            stack.enter_context(patch.object(runner, 'ContinuousPredictor', Isolated))
            stack.enter_context(patch.object(runner, 'split_predictor', side_effect=lambda p, groups: p))
            evaluate = stack.enter_context(patch.object(runner, 'evaluate'))
            with redirect_stdout(io.StringIO()):
                runner.main(['--output-dir', str(out)], verify_reference=False)
            manifest = json.loads((out / 'manifest.json').read_text())
            self.assertEqual(manifest['groups'][10], ['v23'])
            self.assertEqual(manifest['rule_items'], ['v2', 'v3', 'v22'])
            self.assertNotIn('v22', [k for g in manifest['groups'] for k in g])
            self.assertIn('nara/briefing_rule.py', manifest['source_sha256'])
            snapshot = out / 'source/nara/conversation.py'
            self.assertEqual(snapshot.read_bytes(), Path('nara/conversation.py').read_bytes())
            self.assertEqual(manifest['source_sha256']['nara/conversation.py'],
                             hashlib.sha256(snapshot.read_bytes()).hexdigest())
            report = json.loads((out / 'report.json').read_text())
            scheduler = [json.loads(s) for s in (out / 'scheduler.jsonl').read_text().splitlines()]
            requests = [json.loads(s) for s in (out / 'request_timings.jsonl').read_text().splitlines()]
            trace = [json.loads(s) for s in (out / 'trace.jsonl').read_text().splitlines()]
            expected = 202 if isolated_needed else 201
            attempts = [json.loads(s) for s in (out / 'recovery_attempts.jsonl').read_text().splitlines()]
            self.assertEqual(len(attempts), expected - 200)
            self.assertEqual(bool(attempts[0]['trace'][0]['error']), isolated_needed)
            self.assertEqual(sum(len(a['requests']) for a in attempts), expected - 200)
            self.assertEqual(len(scheduler), expected)
            self.assertEqual(len(requests), expected)
            self.assertEqual(report['model_turns'], expected)
            self.assertEqual([s['attempt'] for s in scheduler[-(expected - 200):]],
                             ['recovery', 'isolated'] if isolated_needed else ['recovery'])
            self.assertTrue(all(s['stage'] == 'recovery' for s in scheduler[200:]))
            self.assertTrue(model.observer_closed)
            self.assertEqual(model.resets, 3)
            self.assertEqual(report['failed_ids'], ['0'] if isolated_fails else [])
            self.assertEqual((out / 'submission.csv').exists(), not isolated_fails)
            self.assertEqual(evaluate.call_count, int(not isolated_fails))
            self.assertEqual(trace[0]['judgments'] is None, isolated_fails)
            self.assertGreater(report['recovery_seconds'], 0)
            self.assertTrue(all(r['judgments'] == judgments() and not r['error'] for r in trace[1:]))


if __name__ == '__main__':
    unittest.main()
