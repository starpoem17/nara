"""Compare two complete dev runs using the same inputs and labels."""
import argparse
import json
from pathlib import Path
from nara.evaluation.reporting import write_report

from nara.evaluation.evaluate_dev import ITEMS, read_csv


def compare(baseline, candidate):
    old, new = Path(baseline), Path(candidate)
    a, b = [json.loads((p / 'evaluation.json').read_text()) for p in (old, new)]
    pa, pb = read_csv(old / 'submission.csv'), read_csv(new / 'submission.csv')
    truth = read_csv('data/dev_labels.csv')
    if set(pa) != set(pb) or set(pa) != set(truth):
        raise ValueError('Run IDs differ')
    for path in ('data/dev.jsonl', 'data/dev_labels.csv'):
        if a['sha256'][path] != b['sha256'][path]:
            raise ValueError('Run inputs/labels differ')
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
    lines = ['# 이전 실험과 비교', '', f'이전: `{old}`', f'이번: `{new}`', '',
             '| 지표 | 이전 | 이번 |', '|---|---:|---:|']
    for name, key in [('Macro F1', 'macro_f1'), ('Micro F1', 'micro_f1'),
                      ('정확도', 'label_accuracy'), ('완전 일치 공고', 'exact_match_records'),
                      ('오탐', 'false_positives'), ('미탐', 'false_negatives'),
                      ('검색 공고', 'searched_records')]:
        lines.append(f'| {name} | {a[key]:.6f} | {b[key]:.6f} |')
    lines += [f'| 로딩 포함 시간(초) | {a["runtime"]["total_seconds"]:.2f} | {b["runtime"]["total_seconds"]:.2f} |',
              '', f'Macro F1 차이: {result["delta_macro_f1"]:+.6f}. 기존 오류 {fixed}개 수정, 새 오류 {broken}개 발생.',
              '', '| 항목 | 이름 | 이전 F1 | 이번 F1 | 차이 |', '|---|---|---:|---:|---:|']
    for r in rows:
        lines.append(f'| {r["item"]} | {r["name"]} | {r["before_f1"]:.3f} | {r["after_f1"]:.3f} | {r["delta_f1"]:+.3f} |')
    lines += ['', '같은 dev 200건의 탐색적 비교이며 독립 테스트 성능 추정이나 통계적 유의성 검정은 아니다.']
    write_report(new / 'comparison.md', '\n'.join(lines) + '\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'per_item'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', required=True)
    parser.add_argument('--candidate', required=True)
    args = parser.parse_args()
    compare(args.baseline, args.candidate)
