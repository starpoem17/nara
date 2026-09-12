"""Audit and compare the authorized one-pass common-prompt experiment."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.reporting import write_report
from scripts.evaluate_dev import ITEMS, read_csv
from script import read_records
from sklearn.metrics import f1_score


def read(path):
    return json.loads(path.read_text())


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def score(predictions, truth, ids, table):
    if not ids:
        return None
    y = [[int(truth[i][k]) for k in ITEMS] for i in ids]
    p = [[predictions[i]['judgments'][k]['위반여부'] for k in ITEMS] for i in ids]
    features = []
    for n, key in enumerate(ITEMS):
        actual, predicted = [v[n] for v in y], [v[n] for v in p]
        tp = sum(a == b == 1 for a, b in zip(actual, predicted))
        fp = sum(a == 0 and b == 1 for a, b in zip(actual, predicted))
        fn = sum(a == 1 and b == 0 for a, b in zip(actual, predicted))
        features.append({'item': key, 'name': table[key]['항목명'], 'support': sum(actual),
                         'tp': tp, 'fp': fp, 'fn': fn,
                         'f1': 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0})
    return {'records': len(ids), 'macro_f1': f1_score(y, p, average='macro', zero_division=0),
            'micro_f1': f1_score(y, p, average='micro', zero_division=0),
            'llm22_macro_f1': sum(r['f1'] for r in features if r['item'] not in ('v2', 'v3')) / 22,
            'false_positives': sum(r['fp'] for r in features),
            'false_negatives': sum(r['fn'] for r in features), 'per_item': features}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    args = parser.parse_args()
    out = args.run_dir
    plan = read(out / 'plan.json')
    assert plan['status'] in ('inference_complete', 'audited')
    records = {r['id']: r for r in read_records('data/dev.jsonl')}
    ids = list(records)
    assert len(ids) == 200
    truth = read_csv('data/dev_labels.csv')
    assert set(truth) == set(records)
    table = read(Path('data/항목표.json'))['항목']
    arms, traces, manifests = {}, {}, {}
    unchanged = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() == h
                 for p, h in plan['source_sha256'].items()}
    assert all(unchanged.values()), [p for p, ok in unchanged.items() if not ok]
    for arm in ('original', 'candidate'):
        folder = out / arm
        report, manifest = read(folder / 'report.json'), read(folder / 'manifest.json')
        manifests[arm] = manifest
        data = rows(folder / 'trace.jsonl')
        assert len(data) == 200 and {r['record_id'] for r in data} == set(ids)
        traces[arm] = {r['record_id']: r for r in data}
        events = [e for r in data for t in r['trace'] for e in t['events']]
        model = [e for e in events if e['event'] == 'model']
        search = [e for e in events if e['event'] == 'search']
        failures = [r['record_id'] for r in data if r['error']]
        assert failures == report['failed_ids']
        assert all(e['max_output_tokens'] == 512 and e['output_tokens'] <= 512 for e in model)
        assert all(e['thinking_tokens'] == 0 for e in model)
        assert all(e['input_tokens'] + 512 + 128 <= 32768 for e in model)
        assert all(len(e['queries']) <= 4 and all(len(q) <= 256 for q in e['queries'].values()) for e in search)
        assert all(t['search_rounds'] <= 2 and
                   sum(e['event'] == 'invalid_response' for e in t['events']) <= 2
                   for r in data for t in r['trace'])
        assert all([list(t['items']) for t in r['trace']] == manifest['groups'] for r in data)
        cache = rows(folder / 'cache_trace.jsonl')
        assert len(cache) == len(model)
        for key in ('input_tokens', 'output_tokens'):
            assert sum(e[key] for e in model) == sum(e[key] for e in cache) == report[key]
        batches = read(folder / 'model_batches.json')
        for i in ids:
            first = [b for b in batches if b['record_id'] == i and b['phase'] == 'first']
            remaining = [b for b in batches if b['record_id'] == i and b['phase'] == 'remaining']
            assert first[0]['requests'] == 1 and remaining[0]['requests'] == 11
        prompt = (folder / 'common_prompt.txt').read_text().rstrip('\n')
        assert hashlib.sha256(prompt.encode()).hexdigest() == plan['prompt_sha256'][arm]
        complete = not failures
        full = score(traces[arm], truth, ids, table) if complete else None
        if full:
            official = read(folder / 'evaluation.json')
            for key in ('macro_f1', 'micro_f1', 'false_positives', 'false_negatives'):
                assert abs(full[key] - official[key]) < 1e-12
        evidence = {'nonempty': 0, 'invalid': 0, 'positive_nonabsence_missing': 0}
        for r in data:
            if r['judgments'] is None:
                continue
            for key, cell in r['judgments'].items():
                quote = cell['근거문구']
                positive = cell['위반여부'] == 1
                absence = table[key]['부재탐지']
                evidence['positive_nonabsence_missing'] += positive and not absence and not quote
                if quote:
                    evidence['nonempty'] += 1
                    evidence['invalid'] += (not positive or absence or len(quote) > 500 or
                        not any(quote in d['text'] for d in records[r['record_id']]['docs']))
        assert evidence['invalid'] == 0
        arms[arm] = {'full_score': full, 'runtime': report, 'failed_ids': failures,
                     'evidence_successful_notices': evidence,
                     'search_queries': sum(len(e['queries']) for e in search),
                     'searched_records': sum(any(t['search_rounds'] for t in r['trace']) for r in data),
                     'search_errors': sum(e['error'] is not None for e in search),
                     'empty_search_rounds': sum(not e['passage_ids'] for e in search),
                     'length_terminated_responses': sum(e['finish_reason'] == 'length' for e in model),
                     'evidence_dropped': sum(len(e['evidence_dropped']) for e in events if e['event'] == 'final')}
    for key in ('groups', 'limits', 'source_sha256', 'thinking', 'max_model_len', 'max_num_seqs'):
        assert manifests['original'][key] == manifests['candidate'][key], key
    assert rows(out / 'original/rules.jsonl') == rows(out / 'candidate/rules.jsonl')
    for i in range(1, 13):
        a, b = [(out / arm / f'prompt_{i:02}.txt').read_text() for arm in ('original', 'candidate')]
        assert a.split('\n[user]\n', 1)[1] == b.split('\n[user]\n', 1)[1]
        assert (out / 'original' / f'schema_{i:02}.json').read_bytes() == (out / 'candidate' / f'schema_{i:02}.json').read_bytes()
    paired = [i for i in ids if all(traces[a][i]['judgments'] is not None for a in traces)]
    diagnostic = {a: score(traces[a], truth, paired, table) for a in traces}
    changes = []
    for i in paired:
        for key in ITEMS:
            a, b = [traces[arm][i]['judgments'][key]['위반여부'] for arm in ('original', 'candidate')]
            if a != b:
                gold = int(truth[i][key])
                changes.append({'id': i, 'item': key, 'gold': gold, 'original': a, 'candidate': b,
                                'change': 'fixed' if b == gold else 'regressed'})
    with (out / 'changed_judgments.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['id', 'item', 'gold', 'original', 'candidate', 'change'])
        writer.writeheader(); writer.writerows(changes)
    result = {'arms': arms, 'paired_successful_records': paired, 'paired_scores': diagnostic,
              'paired_score_scope': 'Full200' if len(paired) == 200 else 'Diagnostic only; excludes notices with a failure in either arm',
              'changed_judgments': len(changes), 'fixed': sum(r['change'] == 'fixed' for r in changes),
              'regressed': sum(r['change'] == 'regressed' for r in changes),
              'single_pass': True, 'validation_passed': True}
    (out / 'comparison.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    summary = ''
    if paired:
        a, b = diagnostic['original'], diagnostic['candidate']
        summary = (f"양쪽 공통 성공 {len(paired)}건의 Macro F1: {a['macro_f1']:.6f} → {b['macro_f1']:.6f} "
                   f"(변화 {b['macro_f1']-a['macro_f1']:+.6f}). 오탐 {a['false_positives']} → {b['false_positives']}, "
                   f"미탐 {a['false_negatives']} → {b['false_negatives']}. "
                   "전체200 동일 완료 비교 및 반복 검증은 아니다.")
    lines = ['# 공통 프롬프트 비교: dev200, 응답 512토큰', '', summary, '',
             '기존·수정 프롬프트 각각 1회. 공통 system 문구만 교체. 12그룹, v2/v3 고정 규칙, thinking OFF, 공고별 1→11 처리.',
             '검색 최대 2회·회당 4개 질의, 응답 512, 문맥 32768. 일반 재시도 1회; 별도 복구·추가 추론 없음.', '',
             '| 지표 | 기존 | 수정 |', '|---|---:|---:|']
    def metric(label, values):
        lines.append(f'| {label} | {values[0]} | {values[1]} |')
    metric('완료 공고', [f"{200-len(arms[a]['failed_ids'])}/200" for a in arms])
    for key, label in [('macro_f1','전체200 Macro F1'),('micro_f1','전체200 Micro F1'),('false_positives','전체200 오탐'),('false_negatives','전체200 미탐')]:
        metric(label, [('산출 불가' if arms[a]['full_score'] is None else f"{arms[a]['full_score'][key]:.6f}" if 'f1' in key else arms[a]['full_score'][key]) for a in arms])
    for key, label in [('prediction_seconds','추론 시간(초, 일반 재시도 포함)'),('load_seconds','로딩 시간(초)'),('warmup_seconds','워밍업 시간(초, 추론 시간 제외)'),('search_rounds','검색 횟수'),('invalid_responses','유효하지 않은 응답 수'),('output_tokens','출력 토큰')]:
        metric(label, [round(arms[a]['runtime'][key], 3) for a in arms])
    metric('검색 질의 수', [arms[a]['search_queries'] for a in arms])
    metric('길이 제한 종료 수', [arms[a]['length_terminated_responses'] for a in arms])
    metric('비부재 위반 중 근거 누락(완료 공고)', [arms[a]['evidence_successful_notices']['positive_nonabsence_missing'] for a in arms])
    lines += ['', f'양쪽 모두 완료된 공고: {len(paired)}/200. 판정 변경 {len(changes)}개: 정답으로 개선 {result["fixed"]}, 오답으로 악화 {result["regressed"]}.']
    if len(paired) < 200:
        lines += ['', '**실패 공고를 0으로 채우지 않았다. 다음 점수는 양쪽 공통 성공 공고만의 진단용 비교이며 전체200 성능이 아니다.**']
        lines += ['', '| 진단용 지표 | 기존 | 수정 |', '|---|---:|---:|']
        metric('공통 성공 공고 Macro F1', [f"{diagnostic[a]['macro_f1']:.6f}" if diagnostic[a] else '없음' for a in arms])
    lines += ['', '## 항목별 비교', '', f'양쪽 공통 성공 {len(paired)}건 기준.', '',
              '| 항목 | 이름 | 기존 F1 | 수정 F1 | 변화 | 기존 FP/FN | 수정 FP/FN |', '|---|---|---:|---:|---:|---:|---:|']
    if paired:
        for a, b in zip(diagnostic['original']['per_item'], diagnostic['candidate']['per_item']):
            lines.append(f"| {a['item']} | {a['name']} | {a['f1']:.4f} | {b['f1']:.4f} | {b['f1']-a['f1']:+.4f} | {a['fp']}/{a['fn']} | {b['fp']}/{b['fn']} |")
    lines += ['', '## 확인 범위', '',
              '- 소스·데이터·검색 인덱스 해시 유지, 두 조건의 그룹별 user 문구·출력 스키마 동일, v2/v3 규칙 결과 동일 확인.',
              '- 실제 응답 상한512, thinking 토큰0, 최초 요청 순서1→11, 문맥 예산, 검색 한도, 캐시 기록과 추론 토큰 합계 확인.',
              '- 각1회 및 기존→수정 고정 순서다. 반복 재현성·통계적 유의성·숨겨진 평가셋 성능은 판단하지 않는다.',
              '- 시간은 로컬 RTX5090/NVFP4 측정이다. 법적 정확성 및 근거문구의 의미적 적절성은 별도 평가하지 않았다.',
              '- 운영 프롬프트는 교체하지 않았다. 후보 수정이나 추가 실험을 하지 않았다.',
              '- 추론 전 준비 실패 2건은 별도 폴더에 보존했다: 과거 규칙 해시 검사, 빌드 도구 실행 경로. 공고 예측은 없었으며 준비 실패 시간은 비교 처리 시간에 포함하지 않는다.',
              f"- 기존 실패 ID: {arms['original']['failed_ids']}", f"- 수정 실패 ID: {arms['candidate']['failed_ids']}"]
    path = write_report(out / 'comparison.md', '\n'.join(lines) + '\n')
    (out / 'validation.json').write_text(json.dumps({'passed': True, 'source_unchanged': unchanged,
         'complete_records': {a: 200-len(arms[a]['failed_ids']) for a in arms},
         'all_actual_output_caps': 512, 'paired_records': len(paired)}, ensure_ascii=False, indent=2)+'\n')
    plan['status'] = 'audited'; (out / 'plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'report': str(path), 'paired_records': len(paired),
                     'scores': {a: {k:v for k,v in diagnostic[a].items() if k!='per_item'} if diagnostic[a] else None for a in arms}}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
