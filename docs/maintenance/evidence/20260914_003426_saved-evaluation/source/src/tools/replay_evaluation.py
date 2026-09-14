"""Re-evaluate saved predictions in a new retained CPU verification record."""
import argparse
import contextlib
import hashlib
import io
import json
from pathlib import Path
import shutil
from nara.evaluation.evaluate_dev import evaluate
from nara.experiments.recording import ROOT, Run, write_json


def replay(artifacts, *, labels='data/dev_labels.csv', inputs='data/dev.jsonl'):
    source = Path(artifacts).resolve()
    expected = json.loads((source / 'evaluation.json').read_text())
    for path in (Path(labels), Path(inputs)):
        relative = path.resolve().relative_to(ROOT).as_posix()
        recorded = expected['sha256'].get(relative)
        if recorded is None or hashlib.sha256(path.read_bytes()).hexdigest() != recorded:
            raise ValueError(f'Input differs from the saved evaluation or its hash is missing: {relative}')
    run = Run.create('evaluation', 'saved-evaluation',
        'Does the current evaluator reproduce this saved result?',
        {'saved': {'artifacts': source.relative_to(ROOT).as_posix(), 'operation': 'CPU evaluation; no model generation'}},
        verification=True)
    run.capture([ROOT / name for name in ('src/tools/replay_evaluation.py', 'src/evaluation/evaluate_dev.py',
        'src/evaluation/reporting.py', 'src/experiments/recording.py', 'data/항목표.json', 'pyproject.toml', 'uv.lock')])
    run.reference([source / name for name in ('evaluation.json', 'report.json', 'submission.csv', 'trace.jsonl')])
    with run.condition('saved') as directory:
        for name in ('report.json', 'submission.csv', 'trace.jsonl'):
            shutil.copyfile(source / name, directory / name)
        with contextlib.redirect_stdout(io.StringIO()):
            evaluate(directory, labels, inputs, expected['records'])
        actual = json.loads((directory / 'evaluation.json').read_text())
        differences = [key for key in expected if key != 'sha256' and expected[key] != actual.get(key)]
        result = {'source': source.relative_to(ROOT).as_posix(), 'no_gpu_inference': True,
            'input_hashes_match': True, 'fields_compared': len(expected) - 1, 'differing_fields': differences,
            'prediction_csv_identical': (directory / 'submission.csv').read_bytes() == (source / 'submission.csv').read_bytes()}
        write_json(directory / 'parity.json', result)
        if differences or not result['prediction_csv_identical']:
            raise AssertionError(f'Saved-result parity failed: {differences}')
    print(f'Passed: {run.report}')
    return run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifacts', required=True)
    parser.add_argument('--labels', default='data/dev_labels.csv')
    parser.add_argument('--input', default='data/dev.jsonl')
    args = parser.parse_args()
    replay(args.artifacts, labels=args.labels, inputs=args.input)


if __name__ == '__main__':
    main()
