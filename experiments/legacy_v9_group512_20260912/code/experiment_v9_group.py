"""Run only v9/v19 on dev200; compare with archived twelve-group predictions."""

if __name__ == "__main__":
    raise SystemExit("Archived code: create a fresh registered run; see docs/operations.md.")

import argparse
import csv
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import shutil
import time

from nara.records import read_records
from nara.inference.predictor import Limits, Turn
from nara.inference.compact_predictor import CRITERIA
from nara.inference.prefix_predictor import SourceFirstPredictor
from nara.inference.engine import TokenCounter, VLLMModel
from nara.experiments.config import MODEL
from nara.evaluation.reporting import write_report

KEYS = ['v9', 'v19']
BASELINE = Path('output/experiments/engine-refactor-after-20260911')
COD = ('Use brief English notes in the thinking channel, at most five words per step. '
       'Take as many steps as needed. Apply this limit only to thinking, not evidence quotes. '
       'Keep the final JSON format unchanged.')


class CoDPredictor(SourceFirstPredictor):
    def _messages(self, record, items):
        messages = super()._messages(record, items)
        messages[0]['content'] += '\n' + COD
        return messages


class RecordedModel(VLLMModel):
    """Record actual generated token IDs and parsed thinking without altering replies."""
    def generate(self, turns):
        self.recorded_turns = iter(turns)
        return super().generate(turns)

    def _reply(self, output, budget):
        from vllm.reasoning.gemma4_utils import parse_thinking_output
        turn = next(self.recorded_turns)
        reply = super()._reply(output, budget)
        if turn.task_id != 'warmup':
            ids = list(output.outputs[0].token_ids)
            raw = self.tokenizer.decode(ids, skip_special_tokens=False)
            parsed = parse_thinking_output(raw)
            user = next(m['content'] for m in turn.messages if m['role'] == 'user')
            record_id = user.split('\n', 1)[0].removeprefix('[공고 ID] ')
            row = dict(record_id=record_id, task_id=turn.task_id, request_id=output.request_id,
                       thinking_budget=budget, max_tokens=turn.max_tokens,
                       token_ids=ids, raw_output=raw, thinking=parsed['thinking'],
                       answer=parsed['answer'], finish_reason=reply.finish_reason,
                       thinking_tokens_reencoded=reply.thinking_tokens)
            with self.raw_path.open('a') as handle:
                handle.write(json.dumps(row, ensure_ascii=False)+'\n')
        return reply


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def score(truth, predicted, key):
    from sklearn.metrics import f1_score
    pairs = [(int(truth[i][key]), int(predicted[i][key])) for i in truth]
    tp = sum(a == b == 1 for a, b in pairs)
    fp = sum(a == 0 and b == 1 for a, b in pairs)
    fn = sum(a == 1 and b == 0 for a, b in pairs)
    f1 = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.
    assert abs(f1 - f1_score([a for a, b in pairs], [b for a, b in pairs], zero_division=0)) < 1e-12
    return dict(tp=tp, fp=fp, fn=fn, tn=len(pairs)-tp-fp-fn,
                precision=tp/(tp+fp) if tp+fp else 0., recall=tp/(tp+fn) if tp+fn else 0., f1=f1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--thinking', action='store_true')
    parser.add_argument('--cod', action='store_true')
    args = parser.parse_args()
    if args.cod and not args.thinking:
        parser.error('--cod requires --thinking')
    predictor_type = CoDPredictor if args.cod else SourceFirstPredictor
    out = args.output
    out.mkdir(parents=True, exist_ok=False)
    records = read_records('data/dev.jsonl')
    assert len(records) == len({r['id'] for r in records}) == 200
    table = json.loads(Path('data/항목표.json').read_text())['항목']
    table = {k: table[k] for k in KEYS}
    schema = json.loads(Path('data/정답스키마_디코딩.json').read_text())['properties']['판정']
    schema['properties'] = {k: schema['properties'][k] for k in KEYS}
    schema['required'] = KEYS
    limits = Limits(batch_size=16, output_tokens=512)
    counter = TokenCounter(MODEL, thinking=args.thinking)
    predictor = predictor_type(counter, None, table, schema, limits=limits)
    old = json.loads((BASELINE/'source/nara/compact_criteria.json').read_text())
    assert CRITERIA['common'] == old['common']
    assert [k for k in CRITERIA['items'] if CRITERIA['items'][k] != old['items'][k]] == ['v9']
    counts = []
    for record in records:
        messages = predictor._messages(record, KEYS)
        assert all(d['text'] in messages[1]['content'] for d in record['docs'])
        assert messages[0]['content'] == old['common'] + ('\n'+COD if args.cod else '')
        assert '[v19] ' + old['items']['v19'] in messages[1]['content']
        count = counter.count_messages(messages)
        assert count + 512 + 128 <= 32768
        counts.append({'id': record['id'], 'input_tokens': count})
    prompt_tokens = {name: counter.count_text('[v9] '+value) for name, value in
                     [('baseline', old['items']['v9']), ('candidate', CRITERIA['items']['v9'])]}
    assert prompt_tokens == {'baseline': 34, 'candidate': 212}
    dump(out/'schema.json', predictor._schema(KEYS, True))
    messages = predictor._messages(records[0], KEYS)
    (out/'prompt.txt').write_text('[system]\n'+messages[0]['content']+'\n[user]\n{NOTICE_ID_META_ALL_DOCUMENTS}\n[판단 기준]\n'+messages[1]['content'].split('\n[판단 기준]\n')[-1]+'\n')
    (out/'baseline_v9.txt').write_text('[v9] '+old['items']['v9']+'\n')
    manifest = dict(groups=[KEYS], original_group_number=4, records=200, thinking=args.thinking, cod=args.cod,
                    cod_instruction=COD if args.cod else None, thinking_budget=256 if args.thinking else None,
                    limits=asdict(limits), model=MODEL, baseline=str(BASELINE), counts=counts,
                    prompt_tokens=prompt_tokens, schedule='consecutive notice batches of 16, one group each',
                    caveat='Historical comparison: prompt, output cap (2048 to 512), scheduling differ.',
                    recovery='One same-512-cap rerun of failed notices after normal internal retry; no zero filling')
    sources = list(Path('src').rglob('*.py')) + [Path('src/inference/compact_criteria.json'), Path(__file__),
              Path('src/cli.py'), Path('data/dev.jsonl'), Path('data/항목표.json'),
              Path('data/정답스키마_디코딩.json')]
    manifest['source_sha256'] = {}
    for path in sources:
        relative = path.resolve().relative_to(Path.cwd())
        target = out/'source'/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        manifest['source_sha256'][str(relative)] = hashlib.sha256(path.read_bytes()).hexdigest()
    dump(out/'manifest.json', manifest)
    print(json.dumps({'stage':'preflight', 'max_input_tokens':max(c['input_tokens'] for c in counts), 'prompt_tokens':prompt_tokens}), flush=True)
    if args.prepare_only:
        return
    from nara.retrieval.search import BGEEncoder, LegalRetriever
    start = time.monotonic()
    retriever = LegalRetriever('model/legal_index', BGEEncoder('models/bge-m3', device='cuda'))
    model = RecordedModel(MODEL, thinking=True, max_num_seqs=16, max_num_batched_tokens=8192, enable_chunked_prefill=True)
    model.thinking = args.thinking
    model.raw_path = out/'raw_responses.jsonl'
    load_seconds = time.monotonic()-start
    dump(out/'engine.json', model.engine_info())
    simple = {'type':'object','properties':{'answer':{'type':'integer'}},'required':['answer'],'additionalProperties':False}
    model.generate([Turn('warmup', [{'role':'user','content':'Return {"answer":5}.'}], simple, 512)])
    assert model.reset_prefix_cache()
    predictor = predictor_type(model, retriever, table, schema, limits=limits)
    results = []
    start = time.monotonic()
    with (out/'attempts.jsonl').open('w') as handle:
        for offset in range(0, len(records), 16):
            selected = records[offset:offset+16]
            batch = predictor.predict(selected, item_groups=[KEYS])
            for p in batch:
                handle.write(json.dumps({'attempt':0, **asdict(p)}, ensure_ascii=False)+'\n')
            failed = [r for r,p in zip(selected,batch) if p.error]
            if failed:
                recovered = predictor.predict(failed, item_groups=[KEYS])
                for p in recovered:
                    handle.write(json.dumps({'attempt':1, **asdict(p)}, ensure_ascii=False)+'\n')
                by_id = {p.record_id:p for p in recovered}
                batch = [by_id.get(p.record_id,p) for p in batch]
            results.extend(batch)
            handle.flush()
            print(json.dumps({'stage':'inference','completed':len(results),'failed':sum(bool(p.error) for p in results),'seconds':time.monotonic()-start}),flush=True)
    elapsed = time.monotonic()-start
    (out/'trace.jsonl').write_text(''.join(json.dumps(asdict(p),ensure_ascii=False)+'\n' for p in results))
    attempts = [json.loads(line) for line in (out/'attempts.jsonl').read_text().splitlines()]
    events = [e for p in attempts for task in p['trace'] for e in task['events']]
    model_events = [e for e in events if e['event']=='model']
    report = dict(records=len(results), prediction_seconds=elapsed, load_seconds=load_seconds,
                  failed_ids=[p.record_id for p in results if p.error], model_turns=len(model_events),
                  invalid_responses=sum(e['event']=='invalid_response' for e in events),
                  searches=sum(e['event']=='search' for e in events),
                  length_stops=sum(e.get('finish_reason')=='length' for e in model_events),
                  thinking_tokens=sum(e.get('thinking_tokens',0) for e in model_events),
                  output_tokens=sum(e['output_tokens'] for e in model_events))
    dump(out/'report.json', report)
    if report['failed_ids']:
        raise RuntimeError('Unresolved predictions; no complete score reported')
    predicted = {}
    for p in results:
        assert set(p.judgments) == set(KEYS)
        record = next(r for r in records if r['id']==p.record_id)
        row = {'id':p.record_id}
        for k in KEYS:
            cell = p.judgments[k]
            row[k] = cell['위반여부']; row['e'+k[1:]] = cell['근거문구'] or ''
            assert not row['e'+k[1:]] or any(row['e'+k[1:]] in d['text'] for d in record['docs'])
        predicted[p.record_id] = row
    with (out/'predictions.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['id','v9','v19','e9','e19']); writer.writeheader();writer.writerows(predicted.values())
    truth = {r['id']:r for r in csv.DictReader(open('data/dev_labels.csv'))}
    archived = {r['id']:r for r in csv.DictReader(open(BASELINE/'submission.csv'))}
    assert set(truth)==set(archived)==set(predicted)
    comparison = {k:{'baseline':score(truth,archived,k),'candidate':score(truth,predicted,k)} for k in KEYS}
    changes = [{'id':i,'item':k,'gold':int(truth[i][k]),'before':int(archived[i][k]),'after':int(predicted[i][k]),'evidence':predicted[i]['e'+k[1:]]}
               for i in truth for k in KEYS if int(archived[i][k]) != int(predicted[i][k])]
    dump(out/'comparison.json',comparison);dump(out/'changed_judgments.json',changes)
    dump(out/'evaluation_provenance.json', {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path('data/dev_labels.csv'), BASELINE/'submission.csv',out/'predictions.csv']})
    lines=['# v9/v19 isolated dev200, output512', '', manifest['caveat'], '', '| Item | Arm | F1 | Precision | Recall | TP | FP | FN |','|---|---|---:|---:|---:|---:|---:|---:|']
    for k, arms in comparison.items():
        for arm,m in arms.items():
            lines.append(f"| {k} | {arm} | {m['f1']:.6f} | {m['precision']:.6f} | {m['recall']:.6f} | {m['tp']} | {m['fp']} | {m['fn']} |")
    lines += ['',f'Inference {elapsed:.3f}s; load {load_seconds:.3f}s. Changed judgments: {len(changes)}.', '', 'Runtime: '+json.dumps(report)]
    write_report(out/'comparison.md','\n'.join(lines)+'\n')
    print(json.dumps({'stage':'complete','comparison':comparison,'report':report}),flush=True)


if __name__ == '__main__':
    raise SystemExit("Archived experiment: create a new registered run; see docs/operations.md. Historical evidence is read-only.")
    main()
