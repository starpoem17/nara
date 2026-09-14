"""Run the maintained Gemma pipeline, optionally evaluate the same predictions."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys

from nara.inference import pipeline
from nara.experiments.config import MODEL
from nara.experiments.recording import ROOT, Run


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', default=os.environ.get('PPS_DATA_DIR', 'data'))
    parser.add_argument('--input', help='Default: test.jsonl.gz, then test.jsonl in data-dir')
    parser.add_argument('--labels', help='Evaluate completed predictions against this CSV')
    parser.add_argument('--output-dir', default=os.environ.get('PPS_OUTPUT_DIR'),
                        help='Copy final artifacts to a fresh directory, retaining provenance')
    parser.add_argument('--model-dir', default=os.environ.get('PPS_MODEL_DIR', MODEL))
    parser.add_argument('--embed-model', default=os.environ.get('PPS_EMBED_DIR', 'models/bge-m3'))
    parser.add_argument('--index', default='model/legal_index')
    parser.add_argument('--grouping', nargs='+', choices=('groups12', 'groups21'), default=['groups12'])
    parser.add_argument('--summary', default='prediction')
    parser.add_argument('--question', default='Execute the maintained inference pipeline on the supplied notices.')
    phase = parser.add_mutually_exclusive_group()
    phase.add_argument('--prepare-only', action='store_true')
    phase.add_argument('--smoke-only', action='store_true')
    parser.add_argument('--experiment', action='store_true', help='Record a hypothesis experiment instead of a routine execution')
    parser.add_argument('--predecessor', help='Prior experimental run ID for a result-triggered follow-up')
    parser.add_argument('--reason', help='Reason for the result-triggered follow-up')
    args = parser.parse_args(argv)
    if len(set(args.grouping)) != len(args.grouping):
        parser.error('Each grouping may appear only once')
    if args.predecessor and not args.experiment:
        parser.error('--predecessor requires --experiment')
    if args.labels and (args.prepare_only or args.smoke_only):
        parser.error('--labels requires a complete prediction run')
    data_dir = Path(args.data_dir).resolve()
    input_path = Path(args.input).resolve() if args.input else data_dir / 'test.jsonl.gz'
    if not args.input and not input_path.exists():
        input_path = data_dir / 'test.jsonl'
    labels = Path(args.labels).resolve() if args.labels else None
    for path in [input_path, data_dir / '항목표.json', data_dir / '정답스키마_디코딩.json', *([labels] if labels else [])]:
        if not path.is_file():
            parser.error(f'Input file not found: {path}')
    output = Path(args.output_dir).resolve() if args.output_dir else None
    if output is not None and output.exists():
        parser.error('output-dir already exists; choose a fresh directory')
    options = dict(input_path=input_path, data_dir=data_dir,
                   model_dir=Path(args.model_dir).resolve(), embed_model=Path(args.embed_model).resolve(),
                   index=Path(args.index).resolve(), prepare_only=args.prepare_only, smoke_only=args.smoke_only)
    conditions = {name: {**pipeline.settings(name, **options), 'labels': str(labels) if labels else None}
                  for name in args.grouping}
    run = Run.create('inference-scheduling', args.summary, args.question, conditions,
        predecessor=args.predecessor, reason=args.reason, verification=not args.experiment,
        command=['nara', *(sys.argv[1:] if argv is None else argv)])
    try:
        sources = [p for p in (ROOT / 'src').rglob('*') if p.is_file() and '__pycache__' not in p.parts]
        run.capture(sources + [ROOT / 'pyproject.toml', ROOT / 'uv.lock'])
        for path in [input_path, data_dir / '항목표.json', data_dir / '정답스키마_디코딩.json']:
            run.capture_input(path)
        run.reference([options['model_dir'], options['embed_model'], options['index']])
        run.compare_provenance()
        artifacts = []
        for grouping in args.grouping:
            with run.condition(grouping) as directory:
                pipeline.execute(directory, grouping, **options)
                if labels:
                    from nara.evaluation.evaluate_dev import evaluate
                    count = json.loads((directory / 'report.json').read_text())['records']
                    evaluate(directory, labels, input_path, count, item_table_path=data_dir / '항목표.json')
            artifacts.append((grouping, directory))
        if labels and len(artifacts) == 2:
            from nara.evaluation.compare_dev_runs import compare
            compare(artifacts[0][1], artifacts[1][1], labels=labels, inputs=input_path)
        if output is not None:
            output.mkdir(parents=True)
            for grouping, directory in artifacts:
                destination = output if len(artifacts) == 1 else output / grouping
                destination.mkdir(exist_ok=True)
                for path in directory.iterdir():
                    if path.is_file():
                        shutil.copyfile(path, destination / path.name)
            (output / 'provenance.json').write_text(json.dumps({
                'run_id': run.directory.name, 'run_directory': str(run.directory),
                'report': str(run.report), 'artifacts': {g: str(p) for g, p in artifacts}}, indent=2) + '\n')
    except BaseException as exc:
        run = Run(run.directory)
        run.metadata.update(status='failed', error=f'{type(exc).__name__}: {exc}')
        run.save()
        raise
    run = Run(run.directory)
    print(f'Run: {run.directory}\nReport: {run.report}')
    if output is not None:
        print(f'Output: {output}')
    return run


if __name__ == '__main__':
    main()
