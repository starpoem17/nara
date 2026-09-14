"""Audit one local engine-refactor dev200 run; raw artifacts stay in output/.

Usage: uv run --locked python src/tools/verify_engine_refactor.py RUN_DIRECTORY
"""

if __name__ == "__main__":
    raise SystemExit("Archived code: create a fresh registered run; see docs/operations.md.")

from collections import Counter, defaultdict
from pathlib import Path
import csv
import hashlib
import json
import sys

out = Path(sys.argv[1])
def rows(name):
    return [json.loads(line) for line in (out / name).read_text().splitlines() if line]
report = json.loads((out / 'report.json').read_text())
manifest = json.loads((out / 'manifest.json').read_text())
evaluation = json.loads((out / 'evaluation.json').read_text())
for name, digest in manifest['source_sha256'].items():
    assert hashlib.sha256((out / 'source' / name).read_bytes()).hexdigest() == digest, name
trace = rows('trace.jsonl')
requests = rows('request_timings.jsonl')
model_events = [event for record in trace for task in record['trace'] for event in task['events'] if event['event'] == 'model']
assert len(trace) == 200
assert all(not record['error'] and set(record['judgments']) == {f'v{i}' for i in range(1, 25)} for record in trace)
assert len(model_events) == len(requests) == report['model_turns']
for key in ('input_tokens', 'output_tokens'):
    assert sum(event[key] for event in model_events) == sum(request[key] for request in requests) == report[key]
assert all(event['thinking_tokens'] == 0 and event['thinking_budget'] is None for event in model_events)
assert sum(request['cached_tokens'] for request in requests) == report['cached_input_tokens']
active = set()
seen = set()
peak = 0
for event in rows('lifecycle.jsonl'):
    rid = event['request_id']
    if event['event'] == 'submit':
        assert rid not in seen
        seen.add(rid)
        active.add(rid)
        peak = max(peak, len(active))
    elif event['event'] == 'complete':
        assert rid in active
        active.remove(rid)
    else:
        raise AssertionError(event)
    assert len(active) <= 16
assert not active and len(seen) == len(requests)
assert seen == {request['request_id'] for request in requests}
by_notice = defaultdict(list)
for request in rows('main/request_timings.jsonl'):
    notice, group = request['task_id'].rsplit(':', 1)
    by_notice[notice].append(request)
    assert 0 <= int(group) < 12
seed_start = {}
last_done = {}
for notice, rr in by_notice.items():
    seeds = [r for r in rr if r['task_id'].endswith(':0')]
    seed_done = max(r['request_stats']['last_token_ts'] for r in seeds)
    seed_start[notice] = min(r['request_stats']['scheduled_ts'] for r in seeds)
    last_done[notice] = max(r['request_stats']['last_token_ts'] for r in rr)
    assert all(r['request_stats']['queued_ts'] >= seed_done for r in rr if not r['task_id'].endswith(':0'))
admits = [event for event in rows('main/admission.jsonl') if event['event'] == 'admit']
assert len(admits) == 200 and all(len(event['older_live_ids']) < 3 for event in admits)
assert all(event['live_source_tokens'] <= 48000 for event in admits)
later = [event for event in admits if event['reason'] != 'startup']
early = sum(seed_start[event['record_id']] < max((last_done[rid] for rid in event['older_live_ids']), default=0) for event in later)
scheduler = rows('main/scheduler.jsonl')
graphs = Counter(event['graph']['runtime_mode'] for event in scheduler if event['graph'])
assert graphs['FULL'] > 0 and early > 0
with (out / 'submission.csv').open() as handle:
    submission = list(csv.reader(handle))
assert len(submission) == 201 and all(len(row) == 49 for row in submission)
assert [row[0] for row in submission[1:]] == [record['record_id'] for record in trace]
summary = {
    'run_dir': str(out), 'records': len(trace), 'prediction_seconds': report['prediction_seconds'],
    'load_seconds': report['load_seconds'], 'recovery_seconds': report['recovery_seconds'],
    'macro_f1': evaluation['macro_f1'], 'micro_f1': evaluation['micro_f1'],
    'failed_ids': report['failed_ids'], 'model_turns': report['model_turns'],
    'cached_input_tokens': report['cached_input_tokens'], 'cached_fraction': report['cached_fraction'],
    'peak_inflight': peak, 'graph_counts': dict(graphs), 'early_prefill_notices': early,
    'notices_after_startup': len(later),
    'full_graph_16_real_tokens_steps': sum(bool(s['graph']) and s['graph']['runtime_mode'] == 'FULL' and s['graph']['num_unpadded_tokens'] == 16 for s in scheduler),
    'peak_kv_usage': max(s['kv_usage'] for s in scheduler),
    'preempted_request_events': sum(s['preempted_requests'] for s in scheduler),
    'source_snapshots_valid': True, 'request_trace_accounting_valid': True,
    'seed_dependency_valid': True, 'submission_shape_valid': True,
}
(out / 'engine_refactor_audit.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
