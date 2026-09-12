"""Audit and compare matched twelve/singleton-group dev200 runs."""
import argparse
import csv
import json
from pathlib import Path
from nara.evaluation.evaluate_dev import ITEMS, read_csv
from nara.evaluation.reporting import write_report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    root = parser.parse_args().run
    def load(group, name):
        return json.loads((root / group / name).read_text())
    manifests = [load(g, 'manifest.json') for g in ('groups12', 'groups21')]
    reports = [load(g, 'report.json') for g in ('groups12', 'groups21')]
    scores = [load(g, 'evaluation.json') for g in ('groups12', 'groups21')]
    for key in ('source_sha256', 'limits', 'policy', 'max_num_seqs', 'max_num_batched_tokens', 'rule_items'):
        assert manifests[0][key] == manifests[1][key], key
    assert manifests[0]['rule_items'] == ['v2', 'v3', 'v22']
    assert len(manifests[0]['groups']) == 12 and len(manifests[1]['groups']) == 21
    assert manifests[1]['groups'] == [[k] for g in manifests[0]['groups'] for k in g]
    assert [r['id'] for r in manifests[0]['counts']] == [r['id'] for r in manifests[1]['counts']]
    assert all(r['records'] == 200 and not r['failed_ids'] for r in reports)
    predictions = [read_csv(root / g / 'submission.csv') for g in ('groups12', 'groups21')]
    truth = read_csv('data/dev_labels.csv')
    assert set(predictions[0]) == set(predictions[1]) == set(truth)
    changed = []
    for rid in truth:
        for key in ITEMS:
            a, b = predictions[0][rid][key], predictions[1][rid][key]
            if a != b:
                assert key not in manifests[0]['rule_items']
                changed.append({'id': rid, 'item': key, 'gold': truth[rid][key],
                                'groups12': a, 'groups21': b, 'corrected': b == truth[rid][key]})
    per_item = []
    for a, b in zip(scores[0]['per_item'], scores[1]['per_item']):
        assert a['item'] == b['item']
        per_item.append({'item': a['item'], 'name': a['name'], 'f1_12': a['f1'], 'f1_21': b['f1'],
                         'f1_delta': b['f1'] - a['f1'], 'fp_12': a['fp'], 'fp_21': b['fp'],
                         'fn_12': a['fn'], 'fn_21': b['fn'],
                         'changed': sum(c['item'] == a['item'] for c in changed)})
    a, b = reports
    result = {'method': 'One timed dev200 pass per configuration; 12 then 21; separate engines; cache reset after smoke; startup excluded; retries/recovery included.',
              'seconds_12': a['prediction_seconds'], 'seconds_21': b['prediction_seconds'],
              'seconds_delta': b['prediction_seconds'] - a['prediction_seconds'],
              'time_ratio': b['prediction_seconds'] / a['prediction_seconds'],
              'changed_judgments': len(changed), 'corrected': sum(c['corrected'] for c in changed),
              'regressed': sum(not c['corrected'] for c in changed), 'per_item': per_item}
    (root / 'comparison.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    for name, rows in [('per_item_comparison.csv', per_item), ('changed_judgments.csv', changed)]:
        if rows:
            with (root / name).open('w', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    lines = ['# Twelve vs twenty-one groups', '', result['method'], '',
             'Same current sources, dev200 order, rule items v2/v3/v22, OFF mode, output2048, engine16, scheduling and recovery policy. Singleton order follows the existing groups. Each run includes an untimed first8 smoke.', '',
             '| Metric | 12 groups | 21 groups |', '|---|---:|---:|']
    for key in ('prediction_seconds', 'model_turns', 'search_rounds', 'output_tokens', 'input_tokens', 'cached_fraction', 'invalid_responses', 'recovery_seconds'):
        lines.append(f'| {key} | {a[key]} | {b[key]} |')
    for key in ('macro_f1', 'micro_f1', 'false_positives', 'false_negatives', 'label_accuracy'):
        lines.append(f'| {key} | {scores[0][key]} | {scores[1][key]} |')
    lines += ['', f"Time change: {result['seconds_delta']:+.3f}s ({(result['time_ratio']-1)*100:+.2f}%).",
              f"Changed judgments: {len(changed)}; corrected {result['corrected']}; regressed {result['regressed']}.", '',
              '## Per item', '', '| Item | Name | F1 12 | F1 21 | Delta | FP 12→21 | FN 12→21 | Changed |', '|---|---|---:|---:|---:|---:|---:|---:|']
    for r in per_item:
        lines.append(f"| {r['item']} | {r['name']} | {r['f1_12']:.6f} | {r['f1_21']:.6f} | {r['f1_delta']:+.6f} | {r['fp_12']}→{r['fp_21']} | {r['fn_12']}→{r['fn_21']} | {r['changed']} |")
    lines += ['', 'Single run per condition: no estimate of timing variance or order effects. Dev accuracy is descriptive, not holdout validation. F1 averages all24items, including zero-support items as zero. Scheduling can alter outputs; this measures the complete grouping change under fixed policy.', '',
              'Artifacts: comparison.json, per_item_comparison.csv, changed_judgments.csv; each run contains manifests, source snapshots, predictions, traces and evaluation.']
    print(write_report(root / 'comparison.md', '\n'.join(lines) + '\n'))
    print(json.dumps({k: v for k, v in result.items() if k != 'per_item'}, indent=2))


if __name__ == '__main__':
    main()
