"""Score frozen paired OFF/ON0 predictions and audit actual sampling/cache traces."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from sklearn.metrics import f1_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.evaluate_dev import read_csv
from nara.hybrid_experiment import INSTANT
from script import read_records

KEYS = [k for group in INSTANT for k in group]


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def score(truth, predictions, ids, keys):
    y = np.array([[int(truth[i][k]) for k in keys] for i in ids])
    p = np.array([[predictions[i][k]['위반여부'] for k in keys] for i in ids])
    return {'records': len(ids), 'judgments': y.size,
            'macro_f1': float(f1_score(y, p, average='macro', zero_division=0)),
            'micro_f1': float(f1_score(y, p, average='micro', zero_division=0)),
            'label_accuracy': float((y == p).mean()),
            'exact_match_records': int((y == p).all(axis=1).sum()),
            'fp': int(((y == 0) & (p == 1)).sum()), 'fn': int(((y == 1) & (p == 0)).sum()),
            'per_item': {k: {'f1': float(f1_score(y[:, j], p[:, j], zero_division=0)),
                            'tp': int(((y[:, j] == 1) & (p[:, j] == 1)).sum()),
                            'fp': int(((y[:, j] == 0) & (p[:, j] == 1)).sum()),
                            'fn': int(((y[:, j] == 1) & (p[:, j] == 0)).sum())}
                         for j, k in enumerate(keys)}}


def timings(rows):
    return {'requests': len(rows),
            'input_tokens': sum(r['input_tokens'] for r in rows),
            'output_tokens': sum(r['output_tokens'] for r in rows),
            'thinking_text_tokens': sum(r['thinking_text_tokens'] for r in rows),
            'cache_fraction': sum(r['cached_tokens'] for r in rows) / sum(r['input_tokens'] for r in rows),
            'mean_prefill_seconds': float(np.mean([r['prefill_seconds'] for r in rows])),
            'mean_decode_seconds': float(np.mean([r['decode_seconds'] for r in rows]))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='analysis/on0_200')
    args = parser.parse_args()
    out = Path(args.output)
    manifest = json.loads((out / 'manifest.json').read_text())
    truth = read_csv('data/dev_labels.csv')
    records = {r['id']: r for r in read_records('data/dev.jsonl')}
    table = json.loads(Path('data/항목표.json').read_text())['항목']
    frozen = out / 'source/analysis/hybrid200/main/trace.jsonl'
    assert hashlib.sha256(frozen.read_bytes()).hexdigest() == manifest['source_sha256']['analysis/hybrid200/main/trace.jsonl']
    history = {r['record_id']: r for r in read_jsonl(frozen)}
    traces = {m: {r['record_id']: r for r in read_jsonl(out / 'full' / m / 'trace.jsonl')} for m in ['off', 'on0']}
    assert all(set(t) == set(records) for t in traces.values())
    shared = [i for i in records if all(not traces[m][i]['error'] for m in traces)]
    assert shared
    reports = {m: json.loads((out / 'full' / m / 'report.json').read_text()) for m in traces}
    requests = {m: read_jsonl(out / 'full' / m / 'request_timings.jsonl') for m in traces}
    audit = {}
    for mode in traces:
        budget = 0 if mode == 'on0' else None
        rows = requests[mode]
        assert all(r['thinking_budget'] == budget and r['max_tokens'] == 2048 for r in rows)
        assert all(r['thinking_text_tokens'] == 0 for r in rows)
        assert all(r['input_tokens'] + r['max_tokens'] + 128 <= 32768 for r in rows)
        events = [e for p in traces[mode].values() for t in p['trace'] for e in t['events'] if e['event'] == 'model']
        assert len(events) == len(rows) == reports[mode]['model_turns']
        assert all(e['thinking_budget'] == budget and e['thinking_tokens'] == 0 for e in events)
        evidence = {'nonempty': 0, 'invalid': 0, 'positive_nonabsence_missing': 0}
        for i in shared:
            assert set(traces[mode][i]['judgments']) == set(KEYS)
            for key, cell in traces[mode][i]['judgments'].items():
                quote = cell['근거문구']
                if quote:
                    evidence['nonempty'] += 1
                    evidence['invalid'] += not any(quote in d['text'] for d in records[i]['docs'])
                evidence['positive_nonabsence_missing'] += bool(cell['위반여부'] and not table[key]['부재탐지'] and not quote)
        audit[mode] = {'all': timings(rows),
                       'seed': timings([r for r in rows if r['phase'].endswith('_seed')]),
                       'cached': timings([r for r in rows if r['phase'].endswith('_cached')]),
                       'evidence': evidence, 'opening_text_examples': sorted({r['opening_text'] for r in rows})[:10]}
    predictions = {m: {i: traces[m][i]['judgments'] for i in shared} for m in traces}
    scores = {m: score(truth, predictions[m], shared, KEYS) for m in traces}
    # Resample notices as units; all 16 features remain in every macro average.
    bootstrap_rng = np.random.default_rng(0)
    draws = bootstrap_rng.integers(0, len(shared), size=(2000, len(shared)))
    gold = np.array([[int(truth[i][k]) for k in KEYS] for i in shared], dtype=np.int8)[draws]
    boot_scores = {}
    for mode in traces:
        pred = np.array([[predictions[mode][i][k]['위반여부'] for k in KEYS] for i in shared], dtype=np.int8)[draws]
        tp = ((gold == 1) & (pred == 1)).sum(axis=1)
        denominator = (gold == 1).sum(axis=1) + (pred == 1).sum(axis=1)
        per_feature = np.divide(2 * tp, denominator, out=np.zeros_like(tp, dtype=float), where=denominator != 0)
        boot_scores[mode] = per_feature.mean(axis=1)
    macro_delta_ci = np.quantile(boot_scores['on0'] - boot_scores['off'], [.025, .975]).tolist()
    composites = {m: score(truth, {i: {**history[i]['judgments'], **predictions[m][i]} for i in shared},
                           shared, [f'v{k}' for k in range(1, 25)]) for m in traces}
    flips, evidence_changes, answer_changes = [], 0, 0
    for i in shared:
        off_tasks = {tuple(t['items']): t for t in traces['off'][i]['trace']}
        on_tasks = {tuple(t['items']): t for t in traces['on0'][i]['trace']}
        for group, task in off_tasks.items():
            a = [e['response'] for e in task['events'] if e['event'] == 'model']
            b = [e['response'] for e in on_tasks[group]['events'] if e['event'] == 'model']
            answer_changes += a != b
        for key in KEYS:
            a, b = predictions['off'][i][key], predictions['on0'][i][key]
            evidence_changes += a['근거문구'] != b['근거문구']
            if a['위반여부'] != b['위반여부']:
                gold = int(truth[i][key])
                flips.append({'id': i, 'item': key, 'name': table[key]['항목명'], 'gold': gold,
                              'off': a['위반여부'], 'on0': b['위반여부'],
                              'on0_correct': int(b['위반여부'] == gold),
                              'off_evidence': a['근거문구'], 'on0_evidence': b['근거문구']})
    with (out / 'judgment_changes.csv').open('w') as stream:
        writer = csv.DictWriter(stream, fieldnames=['id', 'item', 'name', 'gold', 'off', 'on0', 'on0_correct', 'off_evidence', 'on0_evidence'])
        writer.writeheader()
        writer.writerows(flips)
    chunks = json.loads((out / 'full/paired_timings.json').read_text())
    off_seconds = np.array([c['conditions']['off']['seconds'] for c in chunks])
    on_seconds = np.array([c['conditions']['on0']['seconds'] for c in chunks])
    rng = np.random.default_rng(0)
    samples = rng.integers(0, len(chunks), size=(5000, len(chunks)))
    reductions = 1 - on_seconds[samples].sum(axis=1) / off_seconds[samples].sum(axis=1)
    runtime = {'off_seconds': float(off_seconds.sum()), 'on0_seconds': float(on_seconds.sum()),
               'on0_time_reduction': float(1 - on_seconds.sum() / off_seconds.sum()),
               'on0_faster_pairs': int((on_seconds < off_seconds).sum()), 'pairs': len(chunks),
               'paired_bootstrap_reduction_95pct': np.quantile(reductions, [.025, .975]).tolist()}
    clean_pairs = [j for j, c in enumerate(chunks) if all(
        not any(e['event'] in ('invalid_response', 'search', 'context_failure')
                for t in traces[m][i]['trace'] for e in t['events'])
        for m in traces for i in c['ids'])]
    if clean_pairs:
        runtime['pairs_without_retry_or_search'] = {
            'pairs': len(clean_pairs), 'off_seconds': float(off_seconds[clean_pairs].sum()),
            'on0_seconds': float(on_seconds[clean_pairs].sum()),
            'on0_time_reduction': float(1 - on_seconds[clean_pairs].sum() / off_seconds[clean_pairs].sum())}
    cache = None
    if (out / 'cache_probes.json').exists():
        probes = json.loads((out / 'cache_probes.json').read_text())
        cache = {}
        for probe in probes:
            # Only the seed mode/cache differs; target input and budget are identical.
            assert len({c['target_requests'][0]['input_sha256'] for c in probe['conditions'].values()}) == 1
            assert all(r['thinking_budget'] == 0 and r['thinking_text_tokens'] == 0
                       for r in probe['conditions']['on0_seed']['seed_requests'])
            assert all(r['thinking_budget'] is None for r in probe['conditions']['off_seed']['seed_requests'])
        for condition in ['cold', 'off_seed', 'on0_seed']:
            cs = [p['conditions'][condition] for p in probes]
            rows = [r for c in cs for r in c['target_requests']]
            assert all(r['thinking_budget'] == 1024 for r in rows)
            cache[condition] = {'records': len(cs), **timings(rows),
                'target_seconds': sum(c['target_seconds'] for c in cs),
                'seed_seconds': sum(c['seed_seconds'] for c in cs),
                'failed': sum(bool(c['target']['error'] or c['seed_error']) for c in cs)}
    nonstandard_openings = [{k: r[k] for k in ['record_id', 'phase', 'output_tokens', 'finish_reason', 'opening_text']}
                            for r in requests['on0'] if not r['opening_text'].startswith('<|channel><channel|>')]
    cache_changes = None
    if cache:
        cache_changes = sum(
            p['conditions']['off_seed']['target']['judgments'][k]['위반여부'] !=
            p['conditions']['on0_seed']['target']['judgments'][k]['위반여부']
            for p in probes for k in p['conditions']['off_seed']['target']['judgments'])
    result = {'scope': '16 instant features; OFF/ON0 freshly rerun; scoring uses paired-complete notices only',
        'paired_complete_records': len(shared), 'excluded_ids': [i for i in records if i not in shared],
        'scores16': scores, 'macro16_delta_bootstrap_95pct': macro_delta_ci, 'composite_scores24': composites, 'reports': reports, 'audit': audit,
        'label_flips': len(flips), 'changed_records': len({r['id'] for r in flips}),
        'off_wrong_on0_correct': sum(r['on0_correct'] for r in flips),
        'off_correct_on0_wrong': sum(not r['on0_correct'] for r in flips),
        'changed_evidence_cells': evidence_changes, 'changed_group_answer_sequences': answer_changes,
        'runtime': runtime, 'cache_probes': cache,
        'on0_nonstandard_openings': nonstandard_openings, 'cache_target_label_changes_off_vs_on0_seed': cache_changes,
        'labels_sha256': hashlib.sha256(Path('data/dev_labels.csv').read_bytes()).hexdigest()}
    dump(out / 'comparison.json', result)
    lines = ['# Instant OFF와 thinking ON + budget 0 비교', '',
        f'Gemma 4 26B A4B NVFP4 / RTX 5090. 공고 200건 × instant 4그룹(16항목)을 두 조건에서 새로 실행했다. '
        f'점수는 양쪽 모두 성공한 {len(shared)}건 기준이다.', '',
        '| 지표 | Instant OFF | ON0 |', '|---|---:|---:|',
        f'| 추론 시간, 초 | {runtime["off_seconds"]:.3f} | {runtime["on0_seconds"]:.3f} |',
        f'| 16항목 Macro F1 | {scores["off"]["macro_f1"]:.6f} | {scores["on0"]["macro_f1"]:.6f} |',
        f'| 16항목 Micro F1 | {scores["off"]["micro_f1"]:.6f} | {scores["on0"]["micro_f1"]:.6f} |',
        f'| 오탐 / 미탐 | {scores["off"]["fp"]} / {scores["off"]["fn"]} | {scores["on0"]["fp"]} / {scores["on0"]["fn"]} |',
        f'| 최종 실패 공고 | {len(reports["off"]["failed_ids"])} | {len(reports["on0"]["failed_ids"])} |',
        f'| 유효하지 않은 응답, 재시도 전 포함 | {reports["off"]["invalid_responses"]} | {reports["on0"]["invalid_responses"]} |',
        f'| 파서가 인식한 thinking 본문 토큰 | {reports["off"]["thinking_tokens"]} | {reports["on0"]["thinking_tokens"]} |', '',
        f'판정 {len(flips)}개, 공고 {result["changed_records"]}건이 달라졌다. OFF 오답→ON0 정답 {result["off_wrong_on0_correct"]}개, '
        f'OFF 정답→ON0 오답 {result["off_correct_on0_wrong"]}개. 근거문구는 {evidence_changes}개 셀에서 달랐다.', '',
        f'ON0 시간 감소율 {runtime["on0_time_reduction"]:.2%}. {len(chunks)}개 공고 쌍 중 ON0가 빠른 쌍 '
        f'{runtime["on0_faster_pairs"]}개. 쌍 단위 부트스트랩 95% 구간 '
        f'{runtime["paired_bootstrap_reduction_95pct"][0]:.2%}~{runtime["paired_bootstrap_reduction_95pct"][1]:.2%}; '
        '단일 실행의 공고 변동 구간이며 반복 실행의 안정성을 보장하지 않는다.', '',
        '## 항목별 F1', '', '| 항목 | 이름 | OFF | ON0 | 차이 |', '|---|---|---:|---:|---:|']
    for key in KEYS:
        a, b = scores['off']['per_item'][key]['f1'], scores['on0']['per_item'][key]['f1']
        lines.append(f'| {key} | {table[key]["항목명"]} | {a:.4f} | {b:.4f} | {b-a:+.4f} |')
    lines += ['', '## Thinking 그룹으로 이어질 때의 캐시', '']
    if cache:
        lines += ['길이 분위수로 고른 6건. 각 조건 시작마다 캐시 초기화, 실제 ON1024 판단을 실행했다. '
                  'seed는 G1, target은 기존 thinking 6항목이다. target 시간에 seed 비용은 포함하지 않는다.', '',
                  '| 앞선 처리 | target 캐시 토큰 비율 | 평균 prefill, 초 | target 총 시간, 초 | seed 총 시간, 초 |',
                  '|---|---:|---:|---:|---:|']
        for condition, c in cache.items():
            lines.append(f'| {condition} | {c["cache_fraction"]:.2%} | {c["mean_prefill_seconds"]:.4f} | '
                         f'{c["target_seconds"]:.3f} | {c["seed_seconds"]:.3f} |')
    clean = runtime['pairs_without_retry_or_search']
    lines += ['', '## 해석', '',
        'ON0는 instant와 동일한 판정을 내지 않았다. 이번 실행에서 F1은 하락했고 재시도 포함 전체 시간은 늘었다. '
        '후속 ON1024 요청의 원문 캐시 공유에는 효과가 있었다. 전체 instant 대체를 채택할 근거는 부족하다.', '',
        f'오탐은 {scores["off"]["fp"]}→{scores["on0"]["fp"]}로 줄었지만 미탐은 '
        f'{scores["off"]["fn"]}→{scores["on0"]["fn"]}로 늘었다. 특히 v8 오탐 감소와 v19/v23 정답 양성 소실이 함께 나타났다. '
        '대부분 음성인 데이터에서 판정 정확도가 높아져도 양성 F1은 낮아질 수 있다.', '',
        f'16항목 Macro F1 차이의 공고 단위 부트스트랩 95% 구간은 {macro_delta_ci[0]:+.4f}~{macro_delta_ci[1]:+.4f}다. '
        '관측된 하락을 다른 표본에서도 확정적으로 재현되는 차이라고 단정하지 않는다.', '',
        f'양쪽 모두 재시도·검색이 없는 {clean["pairs"]}쌍에서는 OFF {clean["off_seconds"]:.3f}초, '
        f'ON0 {clean["on0_seconds"]:.3f}초로 ON0가 {clean["on0_time_reduction"]:.2%} 빨랐다. '
        '이는 사후에 정상 쌍만 고른 설명용 비교이며 전체 비용을 대체하지 않는다.', '',
        f'0토큰 감사의 한계: ON0 응답 {len(requests["on0"])}개 중 '
        f'{len(requests["on0"])-len(nonstandard_openings)}개는 빈 thinking 구분자로 즉시 시작했다. '
        f'나머지 {len(nonstandard_openings)}개에는 앞선 공백·구분선 또는 설명문 조각이 있었다. '
        f'그중 출력 한도에서 중단된 응답은 {sum(r["finish_reason"] == "length" for r in nonstandard_openings)}개다. '
        '파서는 구분자 앞 텍스트를 버리거나 구분자가 없으면 thinking=None으로 처리하므로, '
        '기록된 thinking_tokens=0만으로 설명문 생성까지 완전히 차단됐다고 말할 수 없다. '
        '이 중단은 재시도로 복구됐으며 시간과 오류 횟수에 포함했다.', '',
        f'캐시 진단의 OFF seed와 ON0 seed 뒤 target은 입력과 ON1024 예산이 동일했지만 '
        f'36개 판정 중 {cache_changes}개가 달랐다. 캐시 사용 경로도 출력을 항상 보존한다고 가정할 수 없다. '
        '추가 200건 전체 혼합 파이프라인 실행은 이번 범위에 포함하지 않았다.', '',
        '## 조건과 해석 범위', '',
        '- 같은 엔진, 원문 전체, 압축 판단 기준, 출력 2048, context32768, temperature0, seed0, max_num_seqs8, BGE GPU 상주.',
        '- 공고 2건의 첫 그룹을 실행한 뒤 나머지 6개 요청을 배치 처리. OFF/ON0 순서를 쌍마다 교대하며 각 조건 시작 전 캐시를 초기화했다.',
        '- ON0는 enable_thinking=True, thinking_token_budget=0. 엔진에 실제 전달된 예산과 파서가 인식한 thinking 본문 0토큰을 전 요청에서 확인했다.',
        '- 기존 자율 검색·1회 재시도·근거 후처리를 유지. 실패를 0으로 채우지 않았다. 실패가 있으면 점수는 양쪽 성공 공고만 대상으로 하며 시간은 전체 시도 비용이다.',
        f'- 점수 제외 공고: {result["excluded_ids"]}. 검색 OFF {reports["off"]["search_rounds"]}회, ON0 {reports["on0"]["search_rounds"]}회.',
        f'- 나머지 8항목을 기존 hybrid200/main으로 고정한 합성 24항목 Macro F1: OFF {composites["off"]["macro_f1"]:.6f}, '
        f'ON0 {composites["on0"]["macro_f1"]:.6f}. 전체 파이프라인을 새로 실행한 점수·시간은 아니다.',
        '- 캐시 비율은 토큰 가중 비율이다. prefill/decode는 요청별 지연이며 병렬 요청의 합을 GPU walltime으로 해석하지 않는다.',
        '- 사고 예산 0은 출력 전체 0토큰을 뜻하지 않는다. 채널 구분 토큰과 최종 답변은 생성된다.',
        '- 이번 로컬 모델·dev·배치 조건의 결과다. 다른 양자화·데이터·스케줄러에서의 동일성을 보장하지 않는다.', '',
        '재현: `uv run --locked python scripts/benchmark_on0.py --output NEW_DIRECTORY`, '
        '`uv run --locked python scripts/summarize_on0.py --output NEW_DIRECTORY`.', '',
        '상세: comparison.json, judgment_changes.csv, manifest.json, full/*/trace.jsonl, full/*/request_timings.jsonl, cache_probes.json.']
    (out / 'comparison.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ['scores16', 'composite_scores24', 'reports', 'audit']}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
