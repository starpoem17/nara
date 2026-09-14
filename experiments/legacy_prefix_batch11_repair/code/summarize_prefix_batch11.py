"""Audit full dev200 batch11 source-first execution against frozen batch8."""

if __name__ == "__main__":
    raise SystemExit("Archived code: create a fresh registered run; see docs/operations.md.")

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from nara.evaluation.reporting import write_report


def read(path):
    return json.loads(path.read_text())


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def main():
    old_dir, out = Path('analysis/prefix200'), Path('analysis/prefix200_batch11')
    old, new = [read(p / 'report.json') for p in (old_dir, out)]
    previous, score = [read(p / 'evaluation.json') for p in (old_dir, out)]
    a, b = [read(p / 'manifest.json') for p in (old_dir, out)]
    assert new['records'] == score['records'] == 200 and not new['failed_ids']
    assert new['max_num_seqs'] == new['limits']['batch_size'] == 11
    assert old['options'] == new['options'] and old['groups'] == new['groups']
    assert {**old['limits'], 'batch_size': 11} == new['limits']
    assert a['counts'] == b['counts'] and a['groups'] == b['groups']
    changed_sources = []
    for path, digest in b['source_sha256'].items():
        assert hashlib.sha256((out / 'source' / path).read_bytes()).hexdigest() == digest, path
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, path
        if a['source_sha256'][path] != digest:
            changed_sources.append(path)
    assert changed_sources == ['src/experiments/benchmark_prefix200.py'], changed_sources
    for prefix in ('prompt_', 'schema_'):
        for p in old_dir.glob(prefix + '*'):
            assert p.read_bytes() == (out / p.name).read_bytes(), p
    traces, cache = rows(out / 'trace.jsonl'), rows(out / 'cache_trace.jsonl')
    rules = rows(out / 'rules.jsonl')
    assert rules == rows(old_dir / 'rules.jsonl')
    old_traces = {r['record_id']: r for r in rows(old_dir / 'trace.jsonl')}
    ids = [r['id'] for r in rows(Path('data/dev.jsonl'))]
    assert [r['record_id'] for r in traces] == ids
    if 'recovery' in new:
        original = rows(out / 'first_pass/trace.jsonl')
        assert [r['record_id'] for r in original] == ids
        for before, after in zip(original, traces):
            if not before['error']:
                assert before == after
        policy = read(out / 'recovery_policy.json')
        recovery_source = out / 'source/scripts/recover_prefix_batch11.py'
        assert hashlib.sha256(recovery_source.read_bytes()).hexdigest() == policy['source_sha256']
    changed = Counter()
    for r, rule in zip(traces, rules):
        assert not r['error'] and len(r['judgments']) == 24
        assert r['record_id'] == rule['record_id']
        assert [t['items'] for t in r['trace']] == new['groups']
        assert len({t['task_id'] for t in r['trace']}) == 12
        assert all(r['judgments'][k] == v for k, v in rule['judgments'].items())
        for k, v in r['judgments'].items():
            changed[k] += v['위반여부'] != old_traces[r['record_id']]['judgments'][k]['위반여부']
    events = [e for r in traces for t in r['trace'] for e in t['events'] if e['event'] == 'model']
    assert len(events) == len(cache) == new['model_turns']
    for field in ('input_tokens', 'output_tokens'):
        assert sum(e[field] for e in events) == sum(c[field] for c in cache) == new[field]
    assert all(e['thinking_tokens'] == 0 and e['thinking_budget'] is None for e in events)
    assert all(e['input_tokens'] + e['max_output_tokens'] + 128 <= 32768 for e in events)
    assert all(0 <= c['cached_tokens'] <= c['input_tokens'] for c in cache)
    assert sum(c['cached_tokens'] for c in cache) == new['cached_input_tokens']
    batches = read(out / 'model_batches.json')
    by_id = defaultdict(list)
    for batch in batches:
        by_id[batch['record_id']].append(batch)
    assert list(by_id) == ids
    for group in by_id.values():
        assert group[0]['phase'] == 'first' and group[0]['requests'] == 1
        remaining = [v for v in group if v['phase'] == 'remaining']
        assert remaining[0]['requests'] == 11
        assert all(1 <= v['requests'] <= 11 for v in group)
    with (out / 'submission.csv').open() as stream:
        submission = list(csv.reader(stream))
    assert len(submission) == 201 and all(len(row) == 49 for row in submission)
    assert [row[0] for row in submission[1:]] == ids
    phase_times = {}
    for label, folder in [('batch8', old_dir), ('batch11', out)]:
        grouped = defaultdict(lambda: {'calls': 0, 'seconds': 0.0})
        for batch in read(folder / 'model_batches.json'):
            key = f"{batch['phase']}_{batch['requests']}"
            grouped[key]['calls'] += 1
            grouped[key]['seconds'] += batch['seconds']
        phase_times[label] = dict(grouped)
    per_item = []
    for before, after in zip(previous['per_item'], score['per_item']):
        assert before['item'] == after['item']
        per_item.append({'item': after['item'], 'old_f1': before['f1'], 'new_f1': after['f1'],
                         'delta': after['f1'] - before['f1'], 'changed_bits': changed[after['item']]})
    comparison = {'baseline': str(old_dir), 'candidate': str(out),
                  'old_seconds': old['prediction_seconds'], 'new_seconds': new['prediction_seconds'],
                  'time_reduction_fraction': 1 - new['prediction_seconds'] / old['prediction_seconds'],
                  'speedup': old['prediction_seconds'] / new['prediction_seconds'],
                  'macro_f1_delta': score['macro_f1'] - previous['macro_f1'],
                  'micro_f1_delta': score['micro_f1'] - previous['micro_f1'],
                  'changed_bits': sum(changed.values()), 'per_item': per_item, 'batch_timings': phase_times,
                  'first_pass': new.get('first_pass'), 'recovery': new.get('recovery')}
    validation = {'passed': True, 'records': 200, 'judgments': 4800, 'same_prompts_schemas_groups': True,
                  'same_input_token_counts': True, 'same_rules': True, 'source_hashes_match': True,
                  'all_notices_first_1_then_11': True, 'trace_cache_token_totals_match': True,
                  'context_overflows': 0, 'csv_rows': 200, 'csv_columns': 49,
                  'evidence_invalid': score['evidence']['invalid']}
    for name, value in [('comparison.json', comparison), ('validation.json', validation)]:
        (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    report = ['# 12그룹 OFF: 1→8→3 대 1→11', '',
              '| 구성 | 추론(재시도 포함) | 로딩+추론 | Macro F1 | Micro F1 | FP / FN |',
              '|---|---:|---:|---:|---:|---:|']
    for label, runtime, result in [('기존 1→8→3', old, previous), ('이번 1→11', new, score)]:
        report.append(f"| {label} | {runtime['prediction_seconds']:.2f}초 | {runtime['total_seconds']:.2f}초 | {result['macro_f1']:.6f} | {result['micro_f1']:.6f} | {result['false_positives']} / {result['false_negatives']} |")
    report += ['', f"추론 시간 {comparison['time_reduction_fraction']:.2%} 감소, 속도 {comparison['speedup']:.3f}배. Macro 변화 {comparison['macro_f1_delta']:+.6f}, Micro 변화 {comparison['micro_f1_delta']:+.6f}.", '',
               '동일 dev200·Gemma4 NVFP4·RTX5090·12그룹·Thinking OFF·H6 규칙·프롬프트·스키마·출력2048·문맥32768. batch_size와 max_num_seqs만 8→11. 공고 간 순차 실행, 첫 그룹 결과 사용 후 나머지 11개를 함께 제출.',
               f"200건 모두 완료. 잘못된 응답 {new['invalid_responses']}회, 최종 실패 {len(new['failed_ids'])}건, 실제 검색 {new['search_rounds']}회. 전체 입력 토큰 가중 캐시 재사용 {new['cached_fraction']:.2%}.",
               f"기존 대비 판정 {comparison['changed_bits']}/4800개 변경. 항목별 변화와 배치별 시간은 comparison.json.",
               f"근거 원문 불일치 {score['evidence']['invalid']}건, 부재 항목 제외 양성 근거 누락 {score['evidence']['positive_nonabsence_missing']}건. F1은 이진 판정 점수.", '',
               '과거 1회 실행 대비 이번 1회 실행이다. 속도·점수 차이의 반복 재현성을 검증한 결과는 아니다. 배치 변경에 따른 엔진 실행 경로도 달라질 수 있다. 추론 시간은 재시도를 포함하고 개발용 토큰 사전 검사·별도 warmup은 제외한다. 로딩+추론 역시 전체 프로세스 벽시계 시간은 아니다.', '',
               '재현: `MAX_JOBS=2 uv run --locked python src/experiments/benchmark_prefix200.py --batch-size 11 --output FRESH_DIRECTORY`',
               '감사: `python3 src/evaluation/summarize_prefix_batch11.py`', '']
    if 'recovery' in new:
        first, recovery = new['first_pass'], new['recovery']
        report += [f"최초 실행: {first['prediction_seconds']:.2f}초, 실패 {len(first['failed_ids'])}건. 복구 추론 {recovery['prediction_seconds']:.2f}초, 복구용 별도 초기화 {recovery['separate_process_load_seconds']:.2f}초. 표의 추론에는 복구 추론을, 로딩+추론에는 추가 초기화까지 포함.",
                   '복구: 실패 공고 전체를 동일 1→11 설정으로 1회 재실행하고, 여전히 실패한 그룹만 동일 프롬프트·2048토큰 한도로 따로 1회 재실행. 실제로는 3건 모두 전체 공고 재실행으로 성공하여 그룹 단독 복구는 사용하지 않았다. 최초 성공 공고는 동일함을 검증. first_pass/에 최초 기록 보존.', '']
    if (out / 'recovery_aborted.json').exists():
        report += ['복구 보조 코드의 자료형 비교 오류로 중단된 별도 실행이 1회 있었다. 해당 실행은 판정 결과에 반영되지 않았고 추론 시간이 별도 계측되지 않아 위 시간에서도 제외했다. 따라서 로딩+추론 합계는 이번 개발 작업 전체 소요 시간이 아니다. recovery_aborted.log/json에 기록.', '']
    write_report(out / 'comparison.md', '\n'.join(report))
    print(json.dumps({k: v for k, v in comparison.items() if k not in ('per_item', 'batch_timings')}, indent=2))
    print(json.dumps(validation))


if __name__ == '__main__':
    raise SystemExit("Archived experiment: create a new registered run; see docs/operations.md. Historical evidence is read-only.")
    main()
