"""Score a complete dev prediction CSV by ID; labels are used only here."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from nara.evaluation.reporting import write_report

from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

from nara.records import read_records


ITEMS = [f'v{i}' for i in range(1, 25)]


def read_csv(path):
    with Path(path).open(encoding='utf-8', newline='') as stream:
        reader = csv.DictReader(stream)
        required = ['id'] + ITEMS + [f'e{i}' for i in range(1, 25)]
        if reader.fieldnames != required:
            raise ValueError(f'{path}: unexpected columns')
        rows = list(reader)
    if len({r['id'] for r in rows}) != len(rows):
        raise ValueError(f'{path}: duplicate IDs')
    if any(r[k] not in ('0', '1') for r in rows for k in ITEMS):
        raise ValueError(f'{path}: nonbinary or missing judgment')
    return {r['id']: r for r in rows}


def evaluate(run_dir, labels_path, input_path, expected_records, *, item_table_path="data/항목표.json"):
    from nara.experiments.recording import Run
    retained = Run.find(run_dir)
    retained.capture_input(labels_path)
    retained.capture_input(input_path)
    run = Path(run_dir)
    truth, pred = read_csv(labels_path), read_csv(run / 'submission.csv')
    records = {r['id']: r for r in read_records(input_path)}
    if not (set(truth) == set(pred) == set(records)) or len(truth) != expected_records:
        raise ValueError('Expected complete, identical input/label/prediction ID sets')
    table = json.loads(Path(item_table_path).read_text())['항목']
    ids = list(records)
    y = [[int(truth[i][k]) for k in ITEMS] for i in ids]
    p = [[int(pred[i][k]) for k in ITEMS] for i in ids]
    per_item, errors = [], []
    for column, key in enumerate(ITEMS):
        a, b = [row[column] for row in y], [row[column] for row in p]
        tp = sum(t == 1 and v == 1 for t, v in zip(a, b))
        fp = sum(t == 0 and v == 1 for t, v in zip(a, b))
        fn = sum(t == 1 and v == 0 for t, v in zip(a, b))
        row = {'item': key, 'name': table[key]['항목명'], 'support': sum(a),
               'predicted_positive': sum(b), 'tp': tp, 'fp': fp, 'fn': fn,
               'tn': len(a) - tp - fp - fn,
               'precision': precision_score(a, b, zero_division=0),
               'recall': recall_score(a, b, zero_division=0),
               'f1': f1_score(a, b, zero_division=0)}
        per_item.append(row)
        for i, t, v in zip(ids, a, b):
            if t != v:
                errors.append({'id': i, 'item': key, 'name': row['name'],
                               'error': 'FP' if v else 'FN', 'gold': t, 'prediction': v,
                               'gold_evidence': truth[i]['e' + key[1:]],
                               'predicted_evidence': pred[i]['e' + key[1:]]})
    traces = [json.loads(line) for line in (run / 'trace.jsonl').read_text().splitlines()]
    if len(traces) != len(ids) or {r['record_id'] for r in traces} != set(ids):
        raise ValueError('Trace IDs differ from input')
    if any(r['error'] or r['judgments'] is None for r in traces):
        raise ValueError('Cannot report complete evaluation with failed predictions')
    # Cross-check that CSV labels are the actual traced model predictions.
    for record in traces:
        for key in ITEMS:
            if record['judgments'][key]['위반여부'] != int(pred[record['record_id']][key]):
                raise ValueError('CSV and trace predictions disagree')
    events = [e for r in traces for t in r['trace'] for e in t['events']]
    searches = [e for e in events if e['event'] == 'search']
    searched = sum(any(t['search_rounds'] for t in r['trace']) for r in traces)
    evidence = {'nonempty': 0, 'invalid': 0, 'positive_nonabsence_missing': 0}
    for i in ids:
        for key in ITEMS:
            quote = pred[i]['e' + key[1:]]
            positive = pred[i][key] == '1'
            absence = table[key]['부재탐지']
            evidence['positive_nonabsence_missing'] += positive and not absence and not quote
            if quote:
                evidence['nonempty'] += 1
                evidence['invalid'] += (not positive or absence or len(quote) > 500
                    or quote.startswith(('=', '+', '@'))
                    or not any(quote in d['text'] for d in records[i]['docs']))
    macro = f1_score(y, p, average='macro', zero_division=0)
    assert abs(macro - sum(r['f1'] for r in per_item) / 24) < 1e-12
    report = json.loads((run / 'report.json').read_text())
    options, limits = report['options'], report['limits']
    if limits.get('require_search') and any(t['search_rounds'] < 1 or t['retrieval_tokens'] <= 0
                                          for r in traces for t in r['trace']):
        raise ValueError('Required retrieval missing from a successful prediction')
    result = {'records': len(ids), 'judgments': len(ids) * 24,
              'macro_f1': macro, 'micro_f1': f1_score(y, p, average='micro', zero_division=0),
              'macro_precision': precision_score(y, p, average='macro', zero_division=0),
              'macro_recall': recall_score(y, p, average='macro', zero_division=0),
              'label_accuracy': 1 - len(errors) / (len(ids) * 24),
              'exact_match_accuracy': accuracy_score(y, p),
              'exact_match_records': sum(a == b for a, b in zip(y, p)),
              'false_positives': sum(r['fp'] for r in per_item),
              'false_negatives': sum(r['fn'] for r in per_item),
              'zero_positive_items': [r['item'] for r in per_item if r['support'] == 0],
              'zero_division': 0, 'searched_records': searched,
              'retrieved_records': sum(any(t['retrieval_tokens'] > 0 for t in r['trace']) for r in traces),
              'search_rate': searched / len(ids), 'search_rounds': len(searches),
              'search_queries': sum(len(e['queries']) for e in searches),
              'search_errors': sum(e['error'] is not None for e in searches),
              'empty_search_rounds': sum(not e['passage_ids'] for e in searches),
              'invalid_model_responses': sum(e['event'] == 'invalid_response' for e in events),
              'thinking_turns': sum(e.get('thinking_tokens', 0) > 0 for e in events),
              'thinking_text_tokens': sum(e.get('thinking_tokens', 0) for e in events),
              'thinking_budgets': sorted({e['thinking_budget'] for e in events if e.get('thinking_budget') is not None}),
              'evidence_dropped': sum(len(e['evidence_dropped']) for e in events if e['event'] == 'final'),
              'evidence': evidence, 'runtime': report, 'per_item': per_item,
              'sha256': {str(path): hashlib.sha256(Path(path).read_bytes()).hexdigest()
                         for path in [labels_path, input_path, run / 'submission.csv']}}
    (run / 'evaluation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    with (run / 'errors.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['id', 'item', 'name', 'error', 'gold',
            'prediction', 'gold_evidence', 'predicted_evidence'])
        writer.writeheader()
        writer.writerows(errors)
    lines = [f'# Saved dev evaluation: {len(ids)} notices', '',
        f'- Macro positive F1: **{macro:.6f}**; Micro F1: {result["micro_f1"]:.6f}.',
        f'- Label accuracy: {result["label_accuracy"]:.2%}; exact-match notices: {result["exact_match_records"]}/{len(ids)}.',
        f'- False positives: {result["false_positives"]}; false negatives: {result["false_negatives"]}.',
        f'- Notices with retrieval: {searched}; search calls: {len(searches)}; queries: {result["search_queries"]}.',
        f'- Recorded loading plus inference: {report["total_seconds"]:.2f}s; inference: {report["prediction_seconds"]:.2f}s.',
        f'- Model: {options["model_dir"]}; GPU: {report["gpu"]}; context: {options["max_model_len"]}; thinking: {options["thinking"]}.',
        '', 'These times and generation settings come from the saved execution report; evaluation does not run the model.',
        '', '## Per-item observations', '',
        '| Item | Name | Positive labels | Positive predictions | Precision | Recall | F1 | FP | FN |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in per_item:
        lines.append(f'| {r["item"]} | {r["name"]} | {r["support"]} | {r["predicted_positive"]} | '
                     f'{r["precision"]:.3f} | {r["recall"]:.3f} | {r["f1"]:.3f} | {r["fp"]} | {r["fn"]} |')
    lines += ['', '## Interpretation limits', '',
        'The development set does not establish holdout performance. Source-substring checks do not establish legal correctness or qualitative evidence scores.',
        f'Evidence checks: `{json.dumps(evidence)}`; postprocessing dropped {result["evidence_dropped"]} evidence fields.',
        f'All {len(ids)} IDs and CSV/trace judgments match. Failed predictions are not replaced with zero. Undefined per-item F1 is zero and all24 items enter the mean.',
        '', '## Evidence and replay', '',
        '[Machine evaluation](evaluation.json), [error cases](errors.csv), [predictions](submission.csv), [execution settings](report.json).',
        'The owning run metadata identifies source contents, evaluation inputs, and the original command. Use the saved-output replay command in docs/operations.md for a historical read-only run.']
    write_report(run / 'evaluation.md', '\n'.join(lines) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('runtime', 'per_item', 'sha256')}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', required=True)
    parser.add_argument('--labels', default='data/dev_labels.csv')
    parser.add_argument('--input', default='data/dev.jsonl')
    parser.add_argument('--expected-records', type=int, default=200)
    args = parser.parse_args()
    evaluate(args.run_dir, args.labels, args.input, args.expected_records)
