"""Compare two complete dev runs using the same inputs and labels."""
import argparse
import json
import hashlib
from nara.experiments.recording import Run
from pathlib import Path
from nara.evaluation.reporting import write_report

from nara.evaluation.evaluate_dev import ITEMS, read_csv


def compare(baseline, candidate, *, labels="data/dev_labels.csv", inputs="data/dev.jsonl"):
    old, new = Path(baseline), Path(candidate)
    retained = Run.find(new)
    if retained.metadata.get("read_only"):
        raise ValueError("Historical results are read-only; compare retained verification copies")
    retained.capture_input(labels)
    a, b = [json.loads((p / 'evaluation.json').read_text()) for p in (old, new)]
    for folder, evaluation in ((old, a), (new, b)):
        saved_hashes = [digest for name, digest in evaluation['sha256'].items() if Path(name).name == 'submission.csv']
        actual_hash = hashlib.sha256((folder / 'submission.csv').read_bytes()).hexdigest()
        if saved_hashes != [actual_hash]:
            raise ValueError('Saved evaluation and prediction CSV differ')
    pa, pb = read_csv(old / 'submission.csv'), read_csv(new / 'submission.csv')
    truth = read_csv(labels)
    if set(pa) != set(pb) or set(pa) != set(truth):
        raise ValueError('Run IDs differ')
    for path in (str(inputs), str(labels)):
        if a['sha256'][path] != b['sha256'][path]:
            raise ValueError('Run inputs/labels differ')
    if hashlib.sha256(Path(labels).read_bytes()).hexdigest() != a['sha256'][str(labels)]:
        raise ValueError('Current labels differ from recorded evaluation labels')
    fixed = sum(pa[i][k] != truth[i][k] and pb[i][k] == truth[i][k] for i in pa for k in ITEMS)
    broken = sum(pa[i][k] == truth[i][k] and pb[i][k] != truth[i][k] for i in pa for k in ITEMS)
    rows = []
    for x, y in zip(a['per_item'], b['per_item']):
        assert x['item'] == y['item'] and x['support'] == y['support']
        rows.append({'item': x['item'], 'name': x['name'], 'before_f1': x['f1'],
                     'after_f1': y['f1'], 'delta_f1': y['f1'] - x['f1'],
                     'before_fp': x['fp'], 'after_fp': y['fp'],
                     'before_fn': x['fn'], 'after_fn': y['fn']})
    result = {'baseline': str(old), 'candidate': str(new),
              'delta_macro_f1': b['macro_f1'] - a['macro_f1'],
              'corrected_judgments': fixed, 'new_errors': broken,
              'changed_judgments': fixed + broken, 'per_item': rows}
    (new / 'comparison.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    lines = ['# Saved condition comparison', '', f'Baseline: `{old}`', f'Candidate: `{new}`', '',
             '| Metric | Baseline | Candidate |', '|---|---:|---:|']
    for name, key in [('Macro F1', 'macro_f1'), ('Micro F1', 'micro_f1'),
                      ('Label accuracy', 'label_accuracy'), ('Exact-match notices', 'exact_match_records'),
                      ('False positives', 'false_positives'), ('False negatives', 'false_negatives'),
                      ('Notices with retrieval', 'searched_records')]:
        lines.append(f'| {name} | {a[key]:.6f} | {b[key]:.6f} |')
    lines += [f'| Recorded loading plus inference (seconds) | {a["runtime"]["total_seconds"]:.2f} | {b["runtime"]["total_seconds"]:.2f} |',
              '', f'Macro F1 difference: {result["delta_macro_f1"]:+.6f}. Corrected {fixed} judgments; introduced {broken} new errors.',
              '', '| Item | Name | Baseline F1 | Candidate F1 | Difference |', '|---|---|---:|---:|---:|']
    for r in rows:
        lines.append(f'| {r["item"]} | {r["name"]} | {r["before_f1"]:.3f} | {r["after_f1"]:.3f} | {r["delta_f1"]:+.3f} |')
    lines += ['', 'This comparison uses the same supplied inputs and labels. It is neither holdout validation nor a significance test.']
    write_report(new / 'comparison.md', '\n'.join(lines) + '\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'per_item'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', required=True)
    parser.add_argument('--candidate', required=True)
    args = parser.parse_args()
    compare(args.baseline, args.candidate)
