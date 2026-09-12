"""Reproduce v22-only predictions and comparisons; run from repository root."""
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.reporting import write_report
OUT = Path(__file__).parent

def read_csv(path):
    rows = list(csv.DictReader(Path(path).open(encoding='utf-8', newline='')))
    assert len({r['id'] for r in rows}) == len(rows)
    assert all(r['v22'] in ('0', '1') for r in rows)
    return {r['id']: r for r in rows}

def score(pred, gold):
    assert set(pred) == set(gold)
    tp = sum(int(gold[i]['v22']) == 1 and int(pred[i]['v22']) == 1 for i in gold)
    fp = sum(int(gold[i]['v22']) == 0 and int(pred[i]['v22']) == 1 for i in gold)
    fn = sum(int(gold[i]['v22']) == 1 and int(pred[i]['v22']) == 0 for i in gold)
    return dict(records=len(gold), tp=tp, fp=fp, fn=fn, tn=len(gold)-tp-fp-fn,
                precision=tp/(tp+fp) if tp+fp else 0, recall=tp/(tp+fn) if tp+fn else 0,
                f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0, accuracy=1-(fp+fn)/len(gold))

records = [json.loads(l) for l in Path('data/dev.jsonl').read_text().splitlines()]
assert len(records) == 200 and len({r['id'] for r in records}) == 200
predictions, timings = {}, {}
for name in ('rule', 'rule_revised'):
    spec = importlib.util.spec_from_file_location(name, OUT / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    start = time.perf_counter()
    rows = [module.predict(r) for r in records]
    timings[name] = time.perf_counter()-start
    for record, row in zip(records, rows):
        assert not row['v22'] or (row['e22'] and len(row['e22']) <= 500 and any(row['e22'] in d['text'] for d in record['docs']))
    path = OUT / ('predictions.jsonl' if name == 'rule' else 'predictions_revised.jsonl')
    serialized = ''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in rows)
    if name == 'rule':
        assert path.read_text() == serialized, 'Initial frozen predictions changed'
    else:
        path.write_text(serialized)
    predictions[name] = {r['id']: r for r in rows}
# Labels are loaded only after both input-only passes have finished.
gold = read_csv('data/dev_labels.csv')
result = {'scope': 'dev200; revised rule was adjusted after inspecting these dev errors, not held out',
          'rule_scores': {k: score(p, gold) for k, p in predictions.items()},
          'prediction_seconds': timings, 'baselines': [], 'errors': {}}
for name, p in predictions.items():
    result['errors'][name] = [dict(id=i, gold=int(gold[i]['v22']), prediction=p[i]['v22'], gold_evidence=gold[i]['e22'], predicted_evidence=p[i]['e22']) for i in gold if int(gold[i]['v22']) != p[i]['v22']]
for root in ('analysis', 'output'):
    for path in sorted(Path(root).rglob('evaluation.json')):
        saved = json.loads(path.read_text())
        if not isinstance(saved, dict) or saved.get('records') != 200:
            continue
        item = next((v for v in saved.get('per_item', []) if v['item'] == 'v22'), None)
        if item is None:
            continue
        csv_path = path.parent / 'submission.csv'
        assert csv_path.exists(), csv_path
        p = read_csv(csv_path)
        measured = score(p, gold)
        for key in ('tp', 'fp', 'fn', 'f1'):
            assert abs(measured[key] - item[key]) < 1e-12, (path, key)
        for source in ('data/dev.jsonl', 'data/dev_labels.csv'):
            expected_hash = saved.get('sha256', {}).get(source)
            if expected_hash:
                assert hashlib.sha256(Path(source).read_bytes()).hexdigest() == expected_hash
        result['baselines'].append(dict(path=str(path), **measured))
# Latest original run has two failed notices; compare only jointly successful IDs.
base = Path('analysis/common_prompt_v2_512_final')
traces = [json.loads(l) for l in (base/'original/trace.jsonl').read_text().splitlines()]
original = {r['record_id']: {'v22': r['judgments']['v22']['위반여부']} for r in traces if not r['error'] and r['judgments'] is not None}
assert len(original) == 198
paired_gold = {i: gold[i] for i in original}
candidate = read_csv(base/'candidate/submission.csv')
result['paired198'] = {'original': score(original, paired_gold), 'candidate': score({i:candidate[i] for i in original}, paired_gold)}
for name, p in predictions.items():
    result['paired198'][name] = score({i:p[i] for i in original}, paired_gold)
result['sha256'] = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path('data/dev.jsonl'), Path('data/dev_labels.csv'), OUT/'rule.py', OUT/'rule_revised.py', OUT/'predictions.jsonl', OUT/'predictions_revised.jsonl']}
(OUT/'comparison.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
lines = ['# v22 rule comparison', '', 'Dev200: 5 positive, 195 negative. Success is reported as positive F1 and accuracy. No new LLM inference.', '',
'Initial regex was frozen before inspecting per-record v22 labels, after reading input phrasing and aggregate historical scores. Revised regex was adjusted after inspecting dev errors: it is a development fit, not independent validation.', '',
'Negotiation: either contract/award metadata contains 협상, or a document contains 협상에 의한 계약. Briefing/mandatory restriction must be linked in a local text span. Revised extraction also recognizes attendance as an entry in the eligibility section and excludes evaluation-target exclusion. These are bounded regex approximations, not a complete semantic parser.', '',
'| Run | N | F1 | Accuracy | TP | FP | FN |', '|---|---:|---:|---:|---:|---:|---:|']
for name, s in list(result['rule_scores'].items()) + [(b['path'], b) for b in result['baselines']]:
    lines.append(f"| {name} | {s['records']} | {s['f1']:.2%} | {s['accuracy']:.2%} | {s['tp']} | {s['fp']} | {s['fn']} |")
lines += ['', '## Latest matched comparison (198 successful notices)', '', '| Run | N | F1 | Accuracy | TP | FP | FN |', '|---|---:|---:|---:|---:|---:|---:|']
for name,s in result['paired198'].items():
    lines.append(f"| {name} | 198 | {s['f1']:.2%} | {s['accuracy']:.2%} | {s['tp']} | {s['fp']} | {s['fn']} |")
lines += ['', '## Initial extraction errors', '',
'- PPS-DEV-26: eligibility list says 사업설명회에 참석한 자; the initial pattern required an explicit only/eligible phrase.',
'- PPS-DEV-135: 참석하지 아니한 was missing from the initial absence variants.',
'- PPS-DEV-193: post-submission presentation evaluation was mistaken for a pre-bid briefing; revised scope excludes evaluation-target exclusion.', '',
'All 200 predictions have distinct matching IDs; every positive quote is a source substring <=500 characters. All historical full200 v22 metrics above were recomputed from saved CSVs; stored input/label hashes checked when available. Latest original is restricted to 198 successful traces; failures are not filled with zero.', '',
'Reproduce: `python3 analysis/v22_rule200/evaluate.py`. Artifacts include both rule versions, per-notice evidence, metrics and hashes. No production inference changes. Only five positives: independent testing is needed before treating perfect dev fit as generalization.']
report = write_report(OUT/'comparison.md', '\n'.join(lines)+'\n')
print(json.dumps({k:v for k,v in result.items() if k in ('rule_scores','paired198','prediction_seconds','errors')}, ensure_ascii=False, indent=2))
print(report)
