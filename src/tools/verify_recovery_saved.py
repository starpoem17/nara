"""Validate replay and recovery using saved dev200 outputs; no GPU inference.

Usage: uv run --locked python src/tools/verify_recovery_saved.py SAVED_RUN
"""
from nara.paths import source_path, recorded_source_key
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from nara.inference.predictor import Limits
from nara.inference.prefix_predictor import SourceFirstPredictor
from nara.inference.recovery import Attempt, recover_notices
from nara.rules.qualification import judge
from nara.experiments.config import configuration
from nara.records import read_records


def main():
    folder = Path(sys.argv[1])
    report = json.loads((folder / 'report.json').read_text())
    manifest = json.loads((folder / 'manifest.json').read_text())
    for name in ['data/dev.jsonl', 'data/항목표.json', 'data/정답스키마_디코딩.json', 'src/rules/qualification.py']:
        assert hashlib.sha256(source_path(name).read_bytes()).hexdigest() == manifest['source_sha256'][recorded_source_key(manifest['source_sha256'], name)], name
    records = read_records('data/dev.jsonl')
    by_id = {r['id']: r for r in records}
    trace = [json.loads(s) for s in (folder / 'trace.jsonl').read_text().splitlines()]
    table = json.loads(Path('data/항목표.json').read_text())['항목']
    schema = json.loads(Path('data/정답스키마_디코딩.json').read_text())['properties']['판정']
    table, schema, groups = configuration(table, schema, 'groups12', True)
    predictor = SourceFirstPredictor(None, None, table, schema, limits=Limits(**report['limits']))
    count = 0
    for row in trace:
        restored = {}
        for task in row['trace']:
            restored.update(predictor.replay_judgments(by_id[row['record_id']], task))
            count += 1
        restored.update(judge(by_id[row['record_id']])['judgments'])
        assert restored == row['judgments'], row['record_id']
    def forbidden(*args):
        raise AssertionError('Successful run must not invoke recovery')
    unchanged = recover_notices(records, Attempt(trace, report['prediction_seconds']),
        rerun_notices=forbidden, retry_group=forbidden, replay_group=forbidden, rule_judgments=forbidden)
    assert unchanged.trace == trace and unchanged.prediction_seconds == report['prediction_seconds']

    # Simulate exhausted first groups on two real notices. Responses are replayed,
    # never newly generated; this is failure-path validation, not a benchmark.
    damaged = deepcopy(trace)
    targets = {trace[0]['record_id'], trace[-1]['record_id']}
    originals = {r['record_id']: r for r in trace}
    for row in damaged:
        if row['record_id'] in targets:
            row['error'] = 'simulated failure'; row['judgments'] = None
            row['trace'][0]['events'] = [e for e in row['trace'][0]['events'] if e['event'] != 'final']
    rerun = deepcopy([r for r in damaged if r['record_id'] in targets])
    for row in rerun:
        row['trace'].reverse()
    calls = []
    def run(selected):
        assert {r['id'] for r in selected} == targets
        return Attempt(list(reversed(rerun)), 1.)
    def retry(record, items):
        calls.append((record['id'], items))
        original = originals[record['id']]
        task = next(t for t in original['trace'] if t['items'] == items)
        return Attempt([{'record_id': record['id'], 'error': None,
                         'judgments': {k: original['judgments'][k] for k in items}, 'trace': [task]}], .1)
    recovered = recover_notices(records, Attempt(damaged, report['prediction_seconds']),
        rerun_notices=run, retry_group=retry, replay_group=predictor.replay_judgments,
        rule_judgments=lambda record: judge(record)['judgments'])
    assert len(calls) == 2 and all(items == groups[0] for _, items in calls)
    for old, new in zip(trace, recovered.trace):
        assert old['record_id'] == new['record_id']
        assert old['judgments'] == new['judgments'] and new['error'] is None
        if old['record_id'] not in targets:
            assert old == new
    assert all(r['error'] for r in rerun)
    summary = {'saved_run': str(folder), 'records': len(trace), 'replayed_groups': count,
               'all_judgments_and_evidence_identical': True, 'no_failure_path_unchanged': True,
               'simulated_failed_notices': len(targets), 'isolated_groups_replayed': len(calls),
               'simulation_final_judgments_identical': True, 'gpu_inference_performed': False,
               'original_attempts_preserved': True, 'base_trace_sha256': hashlib.sha256((folder / 'trace.jsonl').read_bytes()).hexdigest()}
    Path('analysis/recovery_refactor/validation.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
