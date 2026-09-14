"""The single command executes the same pipeline with or without evaluation."""
from contextlib import ExitStack, redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import tomllib
import unittest
from unittest.mock import patch

from nara.cli import main
from nara.experiments.recording import Run
from nara.inference.pipeline import execute, settings


class CommandTests(unittest.TestCase):
    def test_prediction_and_evaluation_share_defaults_and_export_provenance(self):
        for evaluated in (False, True):
            with self.subTest(evaluated=evaluated), tempfile.TemporaryDirectory() as temp, ExitStack() as stack:
                root = Path(temp)
                data = root / 'data'
                data.mkdir()
                for name in ('test.jsonl', '항목표.json', '정답스키마_디코딩.json', 'labels.csv'):
                    (data / name).write_text('input fixture')
                create = Run.create
                stack.enter_context(patch.object(Run, 'create', side_effect=lambda *a, **kw: create(*a, root=root, **kw)))
                stack.enter_context(patch.object(Run, 'capture'))
                stack.enter_context(patch.object(Run, 'reference'))
                def predict(out, grouping, **options):
                    (out / 'report.json').write_text(json.dumps({'records': 3}))
                    (out / 'submission.csv').write_text('predictions')
                driver = stack.enter_context(patch('nara.inference.pipeline.execute', side_effect=predict))
                evaluator = stack.enter_context(patch('nara.evaluation.evaluate_dev.evaluate'))
                output = root / 'outputs'
                argv = ['--data-dir', str(data), '--output-dir', str(output)]
                if evaluated:
                    argv += ['--labels', str(data / 'labels.csv')]
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(main(argv), 0)
                run = Run(next((root / 'docs/maintenance/evidence').iterdir()))
                driver.assert_called_once()
                self.assertEqual(driver.call_args.args[1], 'groups12')
                options = driver.call_args.kwargs
                self.assertEqual(options['input_path'], data / 'test.jsonl')
                self.assertFalse(options['prepare_only'])
                self.assertFalse(options['smoke_only'])
                condition = run.metadata['conditions']['groups12']
                self.assertEqual(condition['settings']['output_tokens'], 512)
                self.assertFalse(condition['settings']['thinking'])
                self.assertEqual(condition['status'], 'complete')
                self.assertEqual(evaluator.call_count, int(evaluated))
                if evaluated:
                    evaluator.assert_called_once_with(driver.call_args.args[0], data / 'labels.csv',
                        data / 'test.jsonl', 3, item_table_path=data / '항목표.json')
                self.assertEqual((output / 'submission.csv').read_text(), 'predictions')
                provenance = json.loads((output / 'provenance.json').read_text())
                self.assertEqual(provenance['run_directory'], str(run.directory))
                self.assertIn('data/test.jsonl', run.metadata['inputs'])
                self.assertEqual(run.metadata['command'][0], 'nara')

    def test_invalid_combinations_and_existing_outputs_fail_before_run_creation(self):
        with patch.object(Run, 'create') as create, redirect_stdout(io.StringIO()), patch('sys.stderr', new=io.StringIO()):
            for argv in (['--prepare-only', '--smoke-only'], ['--prepare-only', '--labels', 'data/dev_labels.csv'],
                         ['--predecessor', 'previous'], ['--input', 'data/dev.jsonl', '--output-dir', '.'],
                         ['--grouping', 'groups12', 'groups12']):
                with self.subTest(argv=argv), self.assertRaises(SystemExit):
                    main(argv)
            create.assert_not_called()

    def test_only_one_installed_prediction_command(self):
        scripts = tomllib.loads(Path('pyproject.toml').read_text())['project']['scripts']
        self.assertEqual(scripts, {'nara': 'nara.cli:main'})
        self.assertFalse(Path('src/experiments/run_experiment.py').exists())
        self.assertFalse(Path('src/experiments/pipeline.py').exists())

    def test_external_input_is_retained_without_filename_collisions(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run = Run.create('inference', 'test', 'Input retention', {'default': {}}, root=root / 'project')
            for folder in ('first', 'second'):
                source = root / folder / 'notices.jsonl'
                source.parent.mkdir()
                source.write_text(folder)
                run.capture_input(source)
            self.assertEqual(len(run.metadata['inputs']), 2)
            self.assertEqual({(run.directory / item['path']).read_text()
                              for item in run.metadata['inputs'].values()}, {'first', 'second'})

    def test_evaluation_and_comparison_use_supplied_paths(self):
        from nara.evaluation.evaluate_dev import evaluate
        from nara.evaluation.compare_dev_runs import compare
        from nara.inference.predictor import Prediction
        from nara.records import write_submission
        with tempfile.TemporaryDirectory() as temp, redirect_stdout(io.StringIO()):
            root = Path(temp)
            source = root / 'custom.jsonl'
            source.write_text(json.dumps({'id': 'custom', 'meta': {}, 'docs': [
                {'type': '공고문', 'doc_id': 'D', 'text': 'full notice'}]}) + '\n')
            judgments = {f'v{i}': {'위반여부': 0, '근거문구': None} for i in range(1, 25)}
            prediction = Prediction('custom', judgments, None, [])
            labels = root / 'custom-labels.csv'
            write_submission([prediction], labels)
            table = root / 'custom-table.json'
            table.write_bytes(Path('data/항목표.json').read_bytes())
            run = Run.create('inference', 'test', 'Evaluate supplied paths', {'a': {}, 'b': {}}, root=root)
            folders = []
            for name in ('a', 'b'):
                with run.condition(name) as out:
                    write_submission([prediction], out / 'submission.csv')
                    (out / 'trace.jsonl').write_text(json.dumps(vars(prediction)) + '\n')
                    (out / 'report.json').write_text(json.dumps({
                        'options': {'model_dir': 'fixture', 'max_model_len': 32768, 'thinking': False},
                        'limits': {}, 'total_seconds': 1, 'prediction_seconds': 1, 'gpu': 'fixture'}))
                    evaluate(out, labels, source, 1, item_table_path=table)
                folders.append(out)
            compare(*folders, labels=labels, inputs=source)
            result = json.loads((folders[1] / 'comparison.json').read_text())
            self.assertEqual(result['changed_judgments'], 0)
            score = json.loads((folders[1] / 'evaluation.json').read_text())
            self.assertEqual(score['records'], 1)
            self.assertIn(str(source), score['sha256'])

    def test_empty_input_fails_before_model_loading(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / 'empty.jsonl'
            source.write_text('')
            run = Run.create('inference', 'test', 'Empty input',
                {'default': settings('groups12', input_path=source)}, root=Path(temp))
            with patch('nara.inference.engine.TokenCounter') as counter:
                with self.assertRaisesRegex(ValueError, 'at least one notice'), run.condition('default') as out:
                    execute(out, input_path=source)
                counter.assert_not_called()
