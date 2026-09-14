"""A failed comparison must not look like a completed sweep or use changed CSVs."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from nara.experiments.recording import Run
from nara.cli import main
from nara.evaluation.compare_dev_runs import compare


class RunCompletionTests(unittest.TestCase):
    def test_comparison_failure_retains_successful_conditions_and_failed_sweep(self):
        create = Run.create
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            def local_create(*args, **kwargs):
                return create(*args, root=root, **kwargs)
            with patch.object(Run, 'create', side_effect=local_create), patch.object(Run, 'capture'), patch.object(Run, 'reference'), \
                 patch.object(Run, 'capture_input'), patch('nara.inference.pipeline.execute', side_effect=lambda out, *a, **kw: (out / 'report.json').write_text('{"records": 200}')), patch('nara.evaluation.evaluate_dev.evaluate'), patch('nara.evaluation.compare_dev_runs.compare', side_effect=ValueError('comparison failed')):
                with self.assertRaisesRegex(ValueError, 'comparison failed'):
                    main(['--input', 'data/dev.jsonl', '--labels', 'data/dev_labels.csv', '--experiment', '--grouping', 'groups12', 'groups21'])
            record = Run(next((root / 'experiments').iterdir()))
            self.assertEqual(record.metadata['status'], 'failed')
            self.assertIn('comparison failed', record.metadata['error'])
            self.assertEqual([c['status'] for c in record.metadata['conditions'].values()], ['complete', 'complete'])
            self.assertIn('**failed**', record.report.read_text())

    def test_changed_prediction_csv_is_rejected_before_comparison_is_written(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Run.create('comparison', 'integrity', 'Saved comparison integrity', {'a': {}, 'b': {}}, root=Path(temp))
            folders = []
            for name in ('a', 'b'):
                with run.condition(name) as folder:
                    (folder / 'submission.csv').write_text('changed predictions')
                    (folder / 'evaluation.json').write_text(json.dumps({'sha256': {'submission.csv': hashlib.sha256(b'original predictions').hexdigest()}}))
                    folders.append(folder)
            with patch.object(Run, 'capture_input'), self.assertRaisesRegex(ValueError, 'prediction CSV differ'):
                compare(*folders)
            self.assertFalse((folders[1] / 'comparison.json').exists())
