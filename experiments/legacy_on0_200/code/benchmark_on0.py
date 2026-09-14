"""Paired instant OFF/ON0 experiment; inference never reads dev labels."""

if __name__ == "__main__":
    raise SystemExit("Archived code: create a fresh registered run; see docs/operations.md.")

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import shutil
import time

from nara.records import read_records
from nara.inference.predictor import Limits, Turn, compact
from nara.inference.hybrid_experiment import INSTANT, THINK, TimedLLM, merge
from nara.inference.prefix_predictor import SourceFirstPredictor, split_predictor
from nara.experiments.config import MODEL, configuration
from experiments.legacy_hybrid200.code.benchmark_hybrid200 import dump, jsonl
from nara.records import prediction_payload as safe


class AuditedLLM(TimedLLM):
    def generate(self, *args, **kwargs):
        from vllm.reasoning.gemma4_utils import parse_thinking_output
        outputs = super().generate(*args, **kwargs)
        params = kwargs['sampling_params']
        for row, output, param in zip(self.rows[-len(outputs):], outputs, params):
            ids = output.outputs[0].token_ids
            text = self.get_tokenizer().decode(ids, skip_special_tokens=False)
            parsed = parse_thinking_output(text)
            row.update(thinking_budget=param.thinking_token_budget,
                       max_tokens=param.max_tokens,
                       thinking_text_tokens=len(self.get_tokenizer().encode(
                           parsed['thinking'] or '', add_special_tokens=False)),
                       output_sha256=hashlib.sha256(compact(list(ids)).encode()).hexdigest(),
                       input_sha256=hashlib.sha256(compact(output.prompt_token_ids).encode()).hexdigest(),
                       opening_token_ids=list(ids[:8]),
                       opening_text=self.get_tokenizer().decode(ids[:8], skip_special_tokens=False)
                           if param.thinking_token_budget in (None, 0) else '[thinking omitted]')
        return outputs


def reset(observer):
    assert observer.reset_prefix_cache()
    observer.rows.clear()
    observer.batches.clear()


def run_arm(predictor, observer, records, mode):
    predictor.model.thinking = mode == 'on0'
    observer.thinking_budget = 0 if mode == 'on0' else None
    partial = {r['id']: [] for r in records}
    phases = []
    started = time.monotonic()
    for phase, groups in [('seed', INSTANT[:1]), ('cached', INSTANT[1:])]:
        observer.set_phase(','.join(r['id'] for r in records), mode + '_' + phase)
        worker = split_predictor(predictor, groups)
        tick = time.monotonic()
        results = worker.predict(records, item_groups=groups)
        phases.append({'phase': phase, 'seconds': time.monotonic() - tick, **worker.metrics})
        for result in results:
            for task in result.trace:
                task['task_id'] = result.record_id + ':' + mode + ':' + phase + ':' + task['task_id']
            partial[result.record_id].append(result)
    return ([merge(r['id'], partial[r['id']]) for r in records],
            {'seconds': time.monotonic() - started, 'phases': phases})


def paired(out, records, predictor, observer, stage):
    folder = out / stage
    folder.mkdir()
    results = {'off': [], 'on0': []}
    chunks = []
    streams = {}
    for mode in results:
        (folder / mode).mkdir()
        streams[mode] = (folder / mode / 'trace.jsonl').open('w')
    try:
        for index in range(0, len(records), 2):
            pair = records[index:index + 2]
            order = ['off', 'on0'] if index // 2 % 2 == 0 else ['on0', 'off']
            chunk = {'ids': [r['id'] for r in pair], 'order': order, 'conditions': {}}
            for mode in order:
                reset(observer)
                predictions, timing = run_arm(predictor, observer, pair, mode)
                chunk['conditions'][mode] = timing
                results[mode].extend(predictions)
                for p in predictions:
                    streams[mode].write(compact(safe(p)) + '\n')
                streams[mode].flush()
                for name, rows in [('request_timings', observer.rows), ('model_batches', observer.batches)]:
                    with (folder / mode / (name + '.jsonl')).open('a') as stream:
                        for row in rows:
                            stream.write(compact({'pair_index': index // 2, **row}) + '\n')
            chunks.append(chunk)
            dump(folder / 'paired_timings.json', chunks)
            print(compact({'stage': stage, 'records': index + len(pair),
                           'seconds': {m: sum(c['conditions'][m]['seconds'] for c in chunks) for m in results},
                           'failed': {m: sum(bool(p.error) for p in results[m]) for m in results}}), flush=True)
    finally:
        for stream in streams.values():
            stream.close()
    for mode, predictions in results.items():
        events = [e for p in predictions for t in p.trace for e in t['events']]
        model_events = [e for e in events if e['event'] == 'model']
        dump(folder / mode / 'report.json', {
            'records': len(records), 'groups': INSTANT, 'thinking': mode == 'on0',
            'thinking_budget': 0 if mode == 'on0' else None,
            'seconds': sum(c['conditions'][mode]['seconds'] for c in chunks),
            'failed_ids': [p.record_id for p in predictions if p.error],
            'model_turns': len(model_events),
            'thinking_tokens': sum(e['thinking_tokens'] for e in model_events),
            'thinking_budgets': sorted({e['thinking_budget'] for e in model_events if e['thinking_budget'] is not None}),
            'invalid_responses': sum(e['event'] == 'invalid_response' for e in events),
            'search_rounds': sum(e['event'] == 'search' for e in events),
            'limits': asdict(predictor.limits)})
    return results


def cache_probes(out, records, predictor, observer):
    """Real ON1024 target after no seed, OFF seed, or ON0 seed; reset each condition."""
    probes = []
    for index, record in enumerate(records):
        conditions = ['cold', 'off_seed', 'on0_seed']
        conditions = conditions[index % 3:] + conditions[:index % 3]
        pair = {'id': record['id'], 'order': conditions, 'conditions': {}}
        for condition in conditions:
            reset(observer)
            seed_seconds = 0.0
            seed_error = None
            if condition != 'cold':
                predictor.model.thinking = condition == 'on0_seed'
                observer.thinking_budget = 0 if predictor.model.thinking else None
                observer.set_phase(record['id'], condition)
                worker = split_predictor(predictor, INSTANT[:1])
                tick = time.monotonic()
                seed = worker.predict([record], item_groups=INSTANT[:1])[0]
                seed_seconds = time.monotonic() - tick
                seed_error = seed.error
            start_row = len(observer.rows)
            predictor.model.thinking = True
            observer.thinking_budget = 1024
            observer.set_phase(record['id'], 'on1024_target')
            worker = split_predictor(predictor, [THINK])
            tick = time.monotonic()
            prediction = worker.predict([record], item_groups=[THINK])[0]
            pair['conditions'][condition] = {
                'target_seconds': time.monotonic() - tick, 'seed_seconds': seed_seconds,
                'seed_error': seed_error, 'target': safe(prediction),
                'target_requests': observer.rows[start_row:], 'seed_requests': observer.rows[:start_row]}
        probes.append(pair)
        dump(out / 'cache_probes.json', probes)
        print(compact({'stage': 'cache_probes', 'pairs': len(probes)}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='analysis/on0_200')
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=False)
    records = read_records('data/dev.jsonl')
    assert len(records) == 200
    table = json.loads(Path('data/항목표.json').read_text())['항목']
    schema = json.loads(Path('data/정답스키마_디코딩.json').read_text())['properties']['판정']
    table, schema, _ = configuration(table, schema, 'groups12', True)
    from nara.inference.engine import VLLMModel
    from transformers import AutoTokenizer
    counter = VLLMModel.__new__(VLLMModel)
    counter.tokenizer = AutoTokenizer.from_pretrained(MODEL, local_files_only=True)
    counter.max_model_len = 32768
    predictor = SourceFirstPredictor(counter, None, table, schema, limits=Limits(output_tokens=2048))
    counts = []
    for record in records:
        for gi, group in enumerate(INSTANT + [THINK]):
            messages = predictor._messages(record, group)
            assert all(d['text'] in messages[1]['content'] for d in record['docs'])
            for mode in [False, True]:
                counter.thinking = mode
                n = counter.count_messages(messages)
                assert n + 2048 + 128 <= 32768
                counts.append({'id': record['id'], 'group': gi, 'thinking': mode, 'input_tokens': n})
    ranked = sorted([r for r in counts if r['group'] == 0 and not r['thinking']], key=lambda r: r['input_tokens'])
    smoke_ids = [ranked[round(i * 199 / 7)]['id'] for i in range(8)]
    probe_ids = [ranked[round(i * 199 / 5)]['id'] for i in range(6)]
    paths = ['src/__init__.py', 'src/runtime.py', 'src/records.py', 'src/paths.py',
             'src/experiments/__init__.py', 'src/experiments/config.py', 'src/inference/__init__.py',
             'src/retrieval/__init__.py', 'src/rules/__init__.py', 'src/evaluation/__init__.py',
             'src/experiments/benchmark_on0.py', 'src/experiments/benchmark_hybrid200.py', 'src/experiments/benchmark_compact200.py',
             'src/inference/hybrid_experiment.py', 'src/inference/engine.py', 'src/inference/predictor.py','src/inference/conversation.py',
             'src/inference/prefix_predictor.py', 'src/inference/compact_predictor.py', 'src/inference/compact_criteria.json',
             'src/rules/qualification.py', 'data/dev.jsonl', 'data/항목표.json', 'data/정답스키마_디코딩.json',
             'analysis/hybrid200/main/trace.jsonl']
    hashes = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths}
    dump(out / 'manifest.json', {
        'model': MODEL, 'records': 200, 'groups': INSTANT, 'limits': asdict(predictor.limits),
        'conditions': {'off': {'enable_thinking': False, 'thinking_token_budget': None},
                       'on0': {'enable_thinking': True, 'thinking_token_budget': 0}},
        'design': '100 pairs of notices in original order; OFF/ON0 order alternates per pair; '
                  'reset prefix cache before each arm; two seed group requests then six cached group requests. '
                  'Same resident engine, max_num_seqs8, BGE CUDA, output2048, seed0, temperature0. '
                  'One ordinary retry; no label-based recovery. Smoke excluded from full measurements.',
        'smoke_ids': smoke_ids, 'probe_ids': probe_ids,
        'smoke_gate': 'No final failures and zero ON0 thinking body tokens after ordinary retries.',
        'full_failure_policy': 'Preserve failures; paired-complete score only if incomplete; never zero-fill.',
        'composite': 'Optional 24-feature score freezes the other 8 judgments from hybrid200/main; not a new full pipeline run.',
        'source_sha256': hashes, 'maximum_input_tokens': max(r['input_tokens'] for r in counts)})
    dump(out / 'context_check.json', counts)
    for path in paths:
        target = out / 'source' / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    print(compact({'stage': 'preflight', 'records': 200, 'max_input': max(r['input_tokens'] for r in counts)}), flush=True)
    if args.prepare_only:
        return
    from nara.retrieval.search import BGEEncoder, LegalRetriever
    import vllm
    tick = time.monotonic()
    retriever = LegalRetriever('model/legal_index', BGEEncoder('models/bge-m3', device='cuda'))
    stock = vllm.LLM
    def measured(**kwargs):
        return stock(disable_log_stats=False, **kwargs)
    vllm.LLM = measured
    try:
        model = VLLMModel(MODEL, thinking=True, max_num_seqs=8)
    finally:
        vllm.LLM = stock
    load_seconds = time.monotonic() - tick
    observer = AuditedLLM(model.llm)
    model.llm = observer
    predictor = SourceFirstPredictor(model, retriever, table, schema, limits=Limits(output_tokens=2048))
    simple = {'type': 'object', 'properties': {'answer': {'type': 'integer'}},
              'required': ['answer'], 'additionalProperties': False}
    warm = time.monotonic()
    for thinking, budget in [(False, None), (True, 0), (True, 1024)]:
        model.thinking = thinking
        observer.thinking_budget = budget
        replies = model.generate([Turn(str(i), [{'role': 'user', 'content': '2+3을 계산하고 {"answer":5}로 답하라.'}], simple, 2048) for i in range(8)])
        assert all(r.finish_reason == 'stop' and json.loads(r.text) == {'answer': 5} for r in replies.values())
        if budget == 0:
            assert all(r.thinking_budget == 0 and r.thinking_tokens == 0 for r in replies.values())
    dump(out / 'engine.json', {'load_seconds': load_seconds, 'warmup_seconds': time.monotonic() - warm,
                              'max_num_seqs': 8, 'max_model_len': 32768, 'disable_log_stats': False})
    by_id = {r['id']: r for r in records}
    smoke = paired(out, [by_id[i] for i in smoke_ids], predictor, observer, 'smoke')
    assert all(not p.error for arm in smoke.values() for p in arm), 'Smoke failed; inspect traces before extending.'
    assert all(e['thinking_tokens'] == 0 and e['thinking_budget'] == 0
               for p in smoke['on0'] for t in p.trace for e in t['events'] if e['event'] == 'model')
    paired(out, records, predictor, observer, 'full')
    cache_probes(out, [by_id[i] for i in probe_ids], predictor, observer)
    print(compact({'stage': 'complete'}), flush=True)


if __name__ == '__main__':
    raise SystemExit("Archived experiment: create a new registered run; see docs/operations.md. Historical evidence is read-only.")
    main()
