"""Maintained inference: OFF groups, sixteen slots and shared notice prefixes."""
from nara.experiments.recording import Run
from contextlib import closing
from dataclasses import asdict
import json
from pathlib import Path
import time
from nara.records import read_records, write_submission
from nara.inference.predictor import Limits, Turn, Prediction
from nara.inference.prefix_predictor import SourceFirstPredictor, split_predictor
from nara.inference.prefix_pipeline import PrefixPipelinePredictor
from nara.inference.continuous import ContinuousPredictor
from nara.rules.briefing import judge as judge_with_briefing
from nara.experiments.config import MODEL, configuration
from nara.records import prediction_payload as safe
from nara.inference.recovery import Attempt, recover_notices


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


def settings(grouping, *, input_path, data_dir="data", model_dir=MODEL,
             embed_model="models/bge-m3", index="model/legal_index",
             prepare_only=False, smoke_only=False):
    return {"grouping": grouping,
            "phase": "preparation" if prepare_only else "smoke" if smoke_only else "prediction",
            "output_tokens": 512, "thinking": False, "seed": 0,
            **{key: str(Path(value).resolve()) for key, value in {
                "input_path": input_path, "data_dir": data_dir, "model_dir": model_dir,
                "embed_model": embed_model, "index": index}.items()}}


def execute(out, grouping="groups12", *, input_path, data_dir="data", model_dir=MODEL,
            embed_model="models/bge-m3", index="model/legal_index",
            prepare_only=False, smoke_only=False):
    out = Path(out)
    retained = Run.find(out)
    declared = settings(grouping, input_path=input_path, data_dir=data_dir, model_dir=model_dir,
                        embed_model=embed_model, index=index,
                        prepare_only=prepare_only, smoke_only=smoke_only)
    retained.require_active_attempt(out, declared)
    if any(out.iterdir()):
        raise ValueError("Pipeline requires a fresh empty attempt directory")
    records = read_records(input_path)
    if not records:
        raise ValueError('Input must contain at least one notice')
    data_dir = Path(data_dir)
    table = json.loads((data_dir / '항목표.json').read_text())['항목']
    schema = json.loads((data_dir / '정답스키마_디코딩.json').read_text())['properties']['판정']
    table, schema, groups = configuration(table, schema, 'groups12', True, briefing_rule=True)
    if grouping == 'groups21':
        groups = [[key] for group in groups for key in group]
        assert len(groups) == 21
    elif grouping != 'groups12':
        raise ValueError("Unknown grouping")
    rule_judge = judge_with_briefing
    limits = Limits(output_tokens=512, batch_size=16)
    policy = {'initial_records': 2, 'max_live_records': 3, 'max_live_source_tokens': 48000, 'lookahead_groups': 16}
    hashes = retained.metadata["sources"]
    manifest = {'grouping': grouping, 'groups': groups, 'limits': asdict(limits), 'policy': policy, 'max_num_seqs': 16,
                'max_num_batched_tokens': 8192, 'source_sha256': hashes,
                'source_mode': 'current', 'settings': declared,
                'rule_items': ['v2', 'v3', 'v22'],
                'predecessors': retained.metadata['predecessors'], 'smoke': 'first8 notices; excluded from benchmark',
                'recovery_policy': 'One same-policy rerun of failed notices, then one same-prompt isolated predict per still-failed group. All internal retries, recovery time and events included.'}
    from nara.inference.engine import VLLMModel, TokenCounter
    counter = TokenCounter(model_dir, thinking=False, max_model_len=32768)
    full = SourceFirstPredictor(counter, None, table, schema, limits=limits)
    counts = measure_prefix_inputs(records, full, groups)
    manifest['counts'] = counts
    source_tokens = {c['id']: c['shared_prefix_tokens'] for c in counts}
    dump(out / 'manifest.json', manifest)
    print(json.dumps({'stage': 'preflight_complete', 'records': len(records),
        'source_mode': manifest['source_mode'], 'max_input_tokens': max(max(c['input_tokens']) for c in counts)}), flush=True)
    if prepare_only:
        return
    from nara.retrieval.search import BGEEncoder, LegalRetriever
    import torch
    tick = time.monotonic()
    retriever = LegalRetriever(index, BGEEncoder(embed_model, device='cuda'))
    with closing(VLLMModel(model_dir, thinking=True, max_num_seqs=16,
                           max_num_batched_tokens=8192, enable_chunked_prefill=True,
                           collect_scheduler_stats=True)) as base:
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
            if smoke_only:
                if any(r["error"] for r in smoke.trace):
                    raise RuntimeError("Unresolved smoke prediction failures")
                return
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
            report = {'name': f'source_first_{grouping}_off_pipeline16', 'gpu': torch.cuda.get_device_name(0),
                      'records': len(records), 'groups': groups, 'limits': asdict(limits), 'policy': policy, 'engine': engine,
                      'options': {'model_dir': str(model_dir), 'max_model_len': 32768, 'thinking': False, 'item_group_size': max(map(len, groups))},
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
            if report['failed_ids']:
                raise RuntimeError('Unresolved prediction failures: ' + ', '.join(report['failed_ids']))
            print(json.dumps({'stage': 'complete', 'seconds': elapsed, 'failed_ids': report['failed_ids']}), flush=True)
