"""Recover failed dev200 notices with unchanged prompts/budgets; retain all costs."""

if __name__ == "__main__":
    raise SystemExit("Archived code: create a fresh registered run; see docs/operations.md.")

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import shutil
import time
from nara.records import read_records, write_submission
from nara.inference.predictor import Limits, Prediction, compact
from nara.inference.prefix_predictor import SourceFirstPredictor, predict_notice, split_predictor
from nara.rules.qualification import judge
from experiments.legacy_prefix200.code.benchmark_prefix200 import ObservedLLM
from nara.experiments.config import MODEL, configuration
from experiments.legacy_hybrid_repair.code.recover_hybrid200 import replay
from nara.evaluation.evaluate_dev import evaluate

OUT = Path('analysis/prefix200_batch11')


def read(p): return json.loads(p.read_text())
def rows(p): return [json.loads(s) for s in p.read_text().splitlines()]
def dump(p, value): p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
def jsonl(p, value): p.write_text(''.join(compact(v) + '\n' for v in value))


def main():
    report = read(OUT / 'report.json')
    assert report['failed_ids'] and 'recovery' not in report
    policy = {'scope': 'One whole-notice 1→11 retry for each failed notice, then one isolated retry per still-failed group',
              'prompt_change': False, 'output_tokens': 2048, 'thinking': False,
              'max_num_seqs': 11, 'internal_retries_per_predict': 1,
              'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    dump(OUT / 'recovery_policy.json', policy)
    shutil.copy2(__file__, OUT / 'source/scripts/recover_prefix_batch11.py')
    saved = OUT / 'first_pass'; saved.mkdir(exist_ok=True)
    for name in ['report.json', 'trace.jsonl', 'model_batches.json', 'notice_timings.json', 'cache_trace.jsonl']:
        if (saved / name).exists():
            assert (OUT / name).read_bytes() == (saved / name).read_bytes()
        else:
            shutil.copy2(OUT / name, saved / name)
    records = {r['id']: r for r in read_records('data/dev.jsonl')}
    trace = rows(saved / 'trace.jsonl')
    table = read(Path('data/항목표.json'))['항목']
    schema = read(Path('data/정답스키마_디코딩.json'))['properties']['판정']
    table, schema, groups = configuration(table, schema, 'groups12', True)
    from nara.retrieval.search import BGEEncoder, LegalRetriever
    from nara.inference.engine import VLLMModel
    import torch
    start = time.monotonic()
    retriever = LegalRetriever('model/legal_index', BGEEncoder('models/bge-m3', device='cuda'))
    model = VLLMModel(MODEL, thinking=True, max_num_seqs=11); model.thinking = False
    torch.cuda.synchronize(); load = time.monotonic() - start
    observer = ObservedLLM(model.llm); model.llm = observer
    full = SourceFirstPredictor(model, retriever, table, schema, limits=Limits(**report['limits']))
    start = time.monotonic(); repairs = []; all_phases = []
    for r in trace:
        if not r['error']: continue
        record = records[r['record_id']]; tick = time.monotonic()
        assert model.llm.reset_prefix_cache()
        prediction, phases = predict_notice(full, record, groups,
            lambda rid, phase: observer.set_phase(rid, 'recovery_' + phase))
        all_phases.extend(phases)
        current = asdict(prediction)
        if prediction.error:
            judgments = {}; errors = []
            for task in current['trace']:
                if any(e['event'] == 'final' for e in task['events']):
                    judgments.update(replay(record, task, full)); continue
                observer.set_phase(record['id'], 'recovery_isolated')
                worker = split_predictor(full, [task['items']])
                repaired = worker.predict([record], item_groups=[task['items']])[0]
                all_phases.append(worker.metrics.copy())
                nt = asdict(repaired)['trace'][0]
                task['events'].extend(nt['events'])
                task['search_rounds'] += nt['search_rounds']
                task['retrieval_tokens'] += nt['retrieval_tokens']
                if repaired.error: errors.append(repaired.error)
                else: judgments.update(repaired.judgments)
            current['error'] = '; '.join(errors) or None
            current['judgments'] = None if errors else judgments
        for old_task, new_task in zip(r['trace'], current['trace']):
            assert list(old_task['items']) == list(new_task['items'])
            old_task['events'].extend(new_task['events'])
            old_task['search_rounds'] += new_task['search_rounds']
            old_task['retrieval_tokens'] += new_task['retrieval_tokens']
            old_task['recovery'] = policy['scope']
        r['error'] = current['error']; r['judgments'] = current['judgments']
        if r['judgments'] is not None: r['judgments'].update(judge(record)['judgments'])
        repair = {'id': record['id'], 'seconds': time.monotonic() - tick,
                  'whole_notice_retry_error': prediction.error, 'final_error': r['error']}
        repairs.append(repair)
        print(json.dumps({'stage': 'recovered_record', **repair}), flush=True)
    torch.cuda.synchronize(); elapsed = time.monotonic() - start
    for r in trace:
        for task in r['trace']:
            for event in task['events']:
                if event['event'] == 'model':
                    try: json.loads(event['response'])
                    except (ValueError, TypeError): event['response'] = '[invalid non-JSON response omitted]'
    cache = rows(saved / 'cache_trace.jsonl') + observer.rows
    jsonl(OUT / 'trace.jsonl', trace); jsonl(OUT / 'cache_trace.jsonl', cache)
    dump(OUT / 'model_batches.json', read(saved / 'model_batches.json') + observer.batches)
    dump(OUT / 'recovery_timings.json', repairs)
    report['first_pass'] = {'failed_ids': report['failed_ids'], 'prediction_seconds': report['prediction_seconds']}
    report['recovery'] = {'policy': policy, 'prediction_seconds': elapsed,
                          'separate_process_load_seconds': load, 'records': repairs}
    report['prediction_seconds'] += elapsed; report['total_seconds'] += elapsed + load
    report['model_seconds'] += sum(p['model_seconds'] for p in all_phases)
    report['retrieval_seconds'] += sum(p['retrieval_seconds'] for p in all_phases)
    report['failed_ids'] = [r['record_id'] for r in trace if r['error']]
    events = [e for r in trace for t in r['trace'] for e in t['events']]
    me = [e for e in events if e['event'] == 'model']
    for key in ['input_tokens', 'output_tokens', 'thinking_tokens']:
        report[key] = sum(e[key] for e in me)
    report['model_turns'] = len(me)
    for key, name in [('invalid_responses', 'invalid_response'), ('search_rounds', 'search'), ('context_failures', 'context_failure')]:
        report[key] = sum(e['event'] == name for e in events)
    report['cached_input_tokens'] = sum(c['cached_tokens'] for c in cache)
    report['cached_fraction'] = report['cached_input_tokens'] / report['input_tokens']
    dump(OUT / 'report.json', report)
    if not report['failed_ids']:
        write_submission([Prediction(**r) for r in trace], OUT / 'submission.csv')
        evaluate(OUT, 'data/dev_labels.csv', 'data/dev.jsonl', 200)
    print(json.dumps({'stage': 'recovery_complete', 'seconds': elapsed, 'failed_ids': report['failed_ids']}), flush=True)


if __name__ == '__main__': main()
