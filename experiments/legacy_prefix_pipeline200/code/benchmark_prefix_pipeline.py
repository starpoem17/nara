"""Dev200: twelve OFF groups, sixteen engine slots and early next-notice prefill."""

if __name__ == "__main__":
    raise SystemExit("Archived code: create a fresh registered run; see docs/operations.md.")

from experiments.legacy_prefix_pipeline200.code.historical_paths import source_path, recorded_source_key
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import shutil
import time
from nara.records import read_records, write_submission
from nara.inference.predictor import Limits, Turn, Prediction
from nara.inference.prefix_predictor import SourceFirstPredictor, split_predictor
from nara.inference.prefix_pipeline import PrefixPipelinePredictor
from nara.inference.continuous import ContinuousPredictor
from nara.rules.qualification import judge
from nara.rules.briefing import judge as judge_with_briefing
from nara.experiments.config import MODEL, configuration
from nara.records import prediction_payload as safe
from nara.inference.recovery import Attempt, recover_notices
from nara.evaluation.evaluate_dev import evaluate


def dump(path, value): path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
def jsonl(path, values): path.write_text(''.join(json.dumps(v, ensure_ascii=False) + '\n' for v in values))


def measure_prefix_inputs(records, predictor, groups):
    counts = []
    for record in records:
        rendered = []
        for group in groups:
            messages = predictor._messages(record, group)
            assert all(doc['text'] in messages[1]['content'] for doc in record['docs'])
            tokens = predictor.model.render_messages(messages)
            if len(tokens) + predictor.limits.output_tokens + 128 > predictor.model.max_model_len:
                raise ValueError(f"{record['id']}: source and output exceed context; no text was truncated")
            rendered.append(tokens)
        shared = 0
        for column in zip(*rendered):
            if len(set(column)) != 1:
                break
            shared += 1
        counts.append({'id': record['id'], 'shared_prefix_tokens': shared,
                       'input_tokens': [len(tokens) for tokens in rendered]})
    return counts


def main(argv=None, *, verify_reference=True, default_output=Path('analysis/prefix_pipeline200')):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', '--output-dir', type=Path, default=default_output)
    parser.add_argument('--smoke-only', action='store_true')
    parser.add_argument('--grouping', choices=('groups12', 'groups21'), default='groups12',
                        help='Current twelve groups or one group per non-rule item')
    parser.add_argument('--prepare-only', action='store_true', help='Validate current inputs and save source snapshots without loading the GPU model')
    args = parser.parse_args(argv)
    if verify_reference and args.grouping != 'groups12':
        parser.error('Historical reference requires groups12')
    out = args.output; out.mkdir(parents=True, exist_ok=False)
    records = read_records('data/dev.jsonl'); assert len(records) == 200
    table = json.loads(Path('data/항목표.json').read_text())['항목']
    schema = json.loads(Path('data/정답스키마_디코딩.json').read_text())['properties']['판정']
    table, schema, groups = configuration(table, schema, 'groups12', True, briefing_rule=not verify_reference)
    if args.grouping == 'groups21':
        groups = [[key] for group in groups for key in group]
        assert len(groups) == 21
    rule_judge = judge if verify_reference else judge_with_briefing
    old_manifest = None
    if verify_reference:
        old_manifest = json.loads(Path('analysis/prefix200/manifest.json').read_text())
        for name in ['src/inference/compact_criteria.json', 'src/inference/engine.py', 'src/inference/predictor.py',
                     'src/inference/compact_predictor.py', 'src/inference/prefix_predictor.py', 'src/rules/qualification.py',
                     'data/dev.jsonl', 'data/항목표.json', 'data/정답스키마_디코딩.json']:
            assert hashlib.sha256(source_path(name).read_bytes()).hexdigest() == old_manifest['source_sha256'][recorded_source_key(old_manifest['source_sha256'], name)], name
        assert groups == old_manifest['groups']
    limits = Limits(output_tokens=2048 if verify_reference else 512, batch_size=16)
    policy = {'initial_records': 2, 'max_live_records': 3, 'max_live_source_tokens': 48000, 'lookahead_groups': 16}
    sources = ['src/experiments/benchmark_prefix_pipeline.py', 'src/inference/prefix_pipeline.py', 'src/inference/continuous.py',
               'src/inference/engine.py', 'src/inference/predictor.py', 'src/inference/conversation.py',
               'src/inference/prefix_predictor.py', 'src/inference/compact_predictor.py',
               'src/inference/compact_criteria.json', 'src/rules/qualification.py', 'src/rules/briefing.py', 'src/experiments/config.py',
               'src/inference/recovery.py', 'src/records.py',
               'src/runtime.py', 'src/evaluation/evaluate_dev.py', 'src/evaluation/reporting.py', 'src/paths.py', 'src/__init__.py',
               'src/inference/__init__.py', 'src/experiments/__init__.py', 'src/evaluation/__init__.py',
               'src/rules/__init__.py', 'src/retrieval/__init__.py', 'src/retrieval/search.py',
               'pyproject.toml', 'uv.lock',
               'data/dev.jsonl', 'data/항목표.json', 'data/정답스키마_디코딩.json']
    if not verify_reference:
        sources.append('src/experiments/run_experiment.py')
    hashes = {}
    for name in sources:
        target = out / 'source' / name; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(name, target); hashes[name] = hashlib.sha256(source_path(name).read_bytes()).hexdigest()
    manifest = {'grouping': args.grouping, 'groups': groups, 'limits': asdict(limits), 'policy': policy, 'max_num_seqs': 16,
                'max_num_batched_tokens': 8192, 'source_sha256': hashes,
                'source_mode': 'frozen_reference' if verify_reference else 'current',
                'rule_items': ['v2', 'v3'] if verify_reference else ['v2', 'v3', 'v22'],
                'baseline': 'analysis/prefix200_batch11', 'smoke': 'first8 notices; excluded from benchmark',
                'recovery_policy': 'One same-policy rerun of failed notices, then one same-prompt isolated predict per still-failed group. All internal retries, recovery time and events included.'}
    from nara.inference.engine import VLLMModel, TokenCounter
    counter = TokenCounter(MODEL, thinking=False, max_model_len=32768)
    full = SourceFirstPredictor(counter, None, table, schema, limits=limits)
    counts = measure_prefix_inputs(records, full, groups)
    if old_manifest is not None:
        assert counts == old_manifest['counts']
    manifest['counts'] = counts
    source_tokens = {c['id']: c['shared_prefix_tokens'] for c in counts}
    dump(out / 'manifest.json', manifest)
    print(json.dumps({'stage': 'preflight_complete', 'records': 200,
        'source_mode': manifest['source_mode'], 'max_input_tokens': max(max(c['input_tokens']) for c in counts)}), flush=True)
    if args.prepare_only:
        return
    from nara.retrieval.search import BGEEncoder, LegalRetriever
    import torch
    tick = time.monotonic()
    retriever = LegalRetriever('model/legal_index', BGEEncoder('models/bge-m3', device='cuda'))
    base = VLLMModel(MODEL, thinking=True, max_num_seqs=16,
                     max_num_batched_tokens=8192, enable_chunked_prefill=True,
                     collect_scheduler_stats=True)
    base.thinking = False; torch.cuda.synchronize(); load = time.monotonic() - tick
    engine = base.engine_info()
    dump(out / 'engine.json', engine)
    full = SourceFirstPredictor(base, retriever, table, schema, limits=limits)
    simple = {'type': 'object', 'properties': {'answer': {'type': 'integer'}}, 'required': ['answer'], 'additionalProperties': False}
    tick = time.monotonic()
    base.generate([Turn(str(i), [{'role': 'user', 'content': '2+3을 계산하고 {"answer":5}로 답하라.'}], simple, 512) for i in range(16)])
    warmup = time.monotonic() - tick
    with base.observe_scheduler() as scheduler:
        def run(selected, folder):
            folder.mkdir(parents=True, exist_ok=True)
            assert base.reset_prefix_cache(); scheduler.clear()
            stream = base.stream()
            predictor = PrefixPipelinePredictor(stream, retriever, table, schema, limits=limits)
            tick = time.monotonic(); completed = []; rule_time = 0.
            with (folder / 'trace_completed.jsonl').open('w') as handle:
                def saved(p):
                    nonlocal rule_time
                    record = next(r for r in selected if r['id'] == p.record_id)
                    begin = time.monotonic(); rules = rule_judge(record); rule_time += time.monotonic() - begin
                    if p.judgments is not None: p.judgments.update(rules['judgments'])
                    handle.write(json.dumps(safe(p), ensure_ascii=False) + '\n'); handle.flush()
                    completed.append(p)
                    if len(completed) % 5 == 0 or len(completed) == len(selected):
                        print(json.dumps({'stage': folder.name, 'records': len(completed),
                            'seconds': time.monotonic() - tick, 'failures': sum(bool(p.error) for p in completed)}), flush=True)
                results = predictor.predict(selected, item_groups=groups, source_tokens=source_tokens,
                                            on_record=saved, **policy)
            torch.cuda.synchronize(); elapsed = time.monotonic() - tick
            payload = [safe(p) for p in results]
            jsonl(folder / 'trace.jsonl', payload); jsonl(folder / 'request_timings.jsonl', stream.rows)
            jsonl(folder / 'lifecycle.jsonl', stream.lifecycle); jsonl(folder / 'admission.jsonl', predictor.admission)
            jsonl(folder / 'scheduler.jsonl', scheduler)
            report = {'prediction_seconds': elapsed, 'failed_ids': [p.record_id for p in results if p.error],
                      'records': len(selected), 'metrics': predictor.metrics, 'rule_seconds': rule_time}
            dump(folder / 'stage_report.json', report)
            attempt = Attempt(payload, elapsed, list(stream.rows), list(stream.lifecycle), list(scheduler))
            return attempt, list(predictor.admission), report

        smoke, _, _ = run(records[:8], out / 'smoke')
        assert any(s['graph'] and s['graph']['runtime_mode'] == 'FULL' for s in smoke.scheduler), 'No FULL graph in smoke'
        # Smoke checks execution, never uses labels to choose a candidate.
        if args.smoke_only: return
        initial, main_admission, main_report = run(records, out / 'main')

        def retry_group(record, items):
            tick = time.monotonic(); nschedule = len(scheduler)
            stream = base.stream(); base.thinking = False
            isolated = ContinuousPredictor(stream, retriever, table, schema, limits=limits)
            worker = split_predictor(isolated, [items])
            prediction = worker.predict([record], item_groups=[items])[0]
            return Attempt([safe(prediction)], time.monotonic() - tick,
                           list(stream.rows), list(stream.lifecycle), list(scheduler[nschedule:]))

        recovered = recover_notices(records, initial,
            rerun_notices=lambda selected: run(selected, out / 'recovery')[0],
            retry_group=retry_group, replay_group=full.replay_judgments,
            rule_judgments=lambda record: rule_judge(record)['judgments'])
        jsonl(out / 'recovery_attempts.jsonl', [asdict(attempt) for attempt in recovered.attempts[1:]])
        trace = recovered.trace; elapsed = recovered.prediction_seconds
        recovery_time = recovered.recovery_seconds
        all_rows = recovered.requests; lifecycle = recovered.lifecycle
        main_scheduler = recovered.scheduler
        events = [e for r in trace for task in r['trace'] for e in task['events']]
        me = [e for e in events if e['event'] == 'model']
        report = {'name': f'source_first_{args.grouping}_off_pipeline16', 'gpu': torch.cuda.get_device_name(0),
                  'records': 200, 'groups': groups, 'limits': asdict(limits), 'policy': policy, 'engine': engine,
                  'options': {'model_dir': MODEL, 'max_model_len': 32768, 'thinking': False, 'item_group_size': max(map(len, groups))},
                  'prediction_seconds': elapsed, 'load_seconds': load, 'total_seconds': elapsed + load,
                  'warmup_seconds': warmup, 'first_pass': main_report, 'recovery_seconds': recovery_time,
                  'failed_ids': [r['record_id'] for r in trace if r['error']], 'model_turns': len(me),
                  'search_rounds': sum(e['event'] == 'search' for e in events),
                  'invalid_responses': sum(e['event'] == 'invalid_response' for e in events),
                  'context_failures': sum(e['event'] == 'context_failure' for e in events),
                  'input_tokens': sum(e['input_tokens'] for e in me), 'output_tokens': sum(e['output_tokens'] for e in me),
                  'thinking_tokens': sum(e['thinking_tokens'] for e in me),
                  'cached_input_tokens': sum(r['cached_tokens'] for r in all_rows)}
        report['cached_fraction'] = report['cached_input_tokens'] / report['input_tokens']
        dump(out / 'report.json', report); jsonl(out / 'trace.jsonl', trace)
        jsonl(out / 'request_timings.jsonl', all_rows); jsonl(out / 'lifecycle.jsonl', lifecycle)
        jsonl(out / 'scheduler.jsonl', main_scheduler); jsonl(out / 'admission.jsonl', main_admission)
        jsonl(out / 'rules.jsonl', [rule_judge(r) for r in records])
        if not report['failed_ids']:
            write_submission([Prediction(**r) for r in trace], out / 'submission.csv')
            evaluate(out, 'data/dev_labels.csv', 'data/dev.jsonl', 200)
        print(json.dumps({'stage': 'complete', 'seconds': elapsed, 'failed_ids': report['failed_ids']}), flush=True)


if __name__ == '__main__': main()
