"""Audit timing/F1 plus actual next-source prefill overlap and CUDA graph modes."""
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
from statistics import mean, median

OUT = Path('analysis/prefix_pipeline200')


def read(p): return json.loads(p.read_text())
def rows(p): return [json.loads(s) for s in p.read_text().splitlines()]
def dump(p, value): p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    out = OUT; report = read(out / 'report.json'); manifest = read(out / 'manifest.json')
    score = read(out / 'evaluation.json'); trace = rows(out / 'trace.jsonl')
    requests = rows(out / 'request_timings.jsonl'); life = rows(out / 'lifecycle.jsonl')
    initial = rows(out / 'main/trace.jsonl'); initial_requests = rows(out / 'main/request_timings.jsonl')
    records = rows(Path('data/dev.jsonl')); ids = [r['id'] for r in records]
    assert report['records'] == score['records'] == len(trace) == 200 and not report['failed_ids']
    assert [r['record_id'] for r in trace] == ids
    assert report['engine']['max_num_seqs'] == report['limits']['batch_size'] == 16
    for path, digest in manifest['source_sha256'].items():
        assert hashlib.sha256((out / 'source' / path).read_bytes()).hexdigest() == digest, path
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, path
    for before, after in zip(initial, trace):
        if not before['error']: assert before == after
    for r in trace:
        assert not r['error'] and set(r['judgments']) == {f'v{i}' for i in range(1, 25)}
        assert [t['items'] for t in r['trace']] == report['groups']
    rules = rows(out / 'rules.jsonl')
    assert rules == rows(Path('analysis/prefix200/rules.jsonl'))
    for r, rule in zip(trace, rules):
        assert r['record_id'] == rule['record_id']
        assert all(r['judgments'][k] == v for k, v in rule['judgments'].items())
    events = [e for r in trace for t in r['trace'] for e in t['events'] if e['event'] == 'model']
    assert len(events) == len(requests) == report['model_turns']
    for key in ['input_tokens', 'output_tokens']:
        assert sum(e[key] for e in events) == sum(r[key] for r in requests) == report[key]
    assert all(e['thinking_tokens'] == 0 and e['thinking_budget'] is None for e in events)
    assert all(e['input_tokens'] + e['max_output_tokens'] + 128 <= 32768 for e in events)
    assert sum(r['cached_tokens'] for r in requests) == report['cached_input_tokens']
    active = set(); peak = 0; submits = {}; completions = {}
    for event in life:
        rid = event['request_id']
        if event['event'] == 'submit':
            assert rid not in active and rid not in submits
            active.add(rid); submits[rid] = event; peak = max(peak, len(active))
        else:
            assert rid in active; active.remove(rid); completions[rid] = event
        assert len(active) <= 16
    assert not active and len(submits) == len(completions) == len(requests)
    assert {r['request_id'] for r in requests} == set(submits)
    by_notice = defaultdict(list); seeds = defaultdict(list)
    for request in initial_requests:
        rid, group = request['task_id'].rsplit(':', 1)
        assert rid in ids and 0 <= int(group) < 12
        by_notice[rid].append(request)
        if group == '0': seeds[rid].append(request)
    for rid, all_requests in by_notice.items():
        seed_done = max(r['request_stats']['last_token_ts'] for r in seeds[rid])
        for r in all_requests:
            if not r['task_id'].endswith(':0'):
                assert r['request_stats']['queued_ts'] >= seed_done
    timeline = []; admissions = rows(out / 'admission.jsonl')
    last_done = {rid: max(r['request_stats']['last_token_ts'] for r in rr) for rid, rr in by_notice.items()}
    for event in admissions:
        if event['event'] != 'admit': continue
        rid = event['record_id']; seed = min(seeds[rid], key=lambda r: r['request_stats']['scheduled_ts'])
        start = seed['request_stats']['scheduled_ts']; first_token = seed['request_stats']['first_token_ts']
        older = event['older_live_ids']; old_done = max([last_done[k] for k in older], default=None)
        overlaps = []
        for k in older:
            for r in by_notice[k]:
                if r['task_id'].endswith(':0'): continue
                stats = r['request_stats']
                overlap = min(first_token, stats['last_token_ts']) - max(start, stats['first_token_ts'])
                if overlap > 0: overlaps.append(overlap)
        timeline.append({'record_id': rid, 'reason': event['reason'], 'older_live_ids': older,
            'seed_submit': event['time'], 'prefill_scheduled': start, 'prefill_first_token': first_token,
            'prior_live_last_token': old_done,
            'prefill_starts_before_old_drained': bool(old_done is not None and start < old_done),
            'prefill_overlaps_old_follower_decode': bool(overlaps),
            'max_pair_overlap_seconds': max(overlaps, default=0),
            'prefill_start_lead_seconds': old_done - start if old_done is not None else None,
            'prefill_finish_lead_seconds': old_done - first_token if old_done is not None else None})
    later = [r for r in timeline if r['reason'] != 'startup']
    assert len(timeline) == 200
    early = sum(r['prefill_starts_before_old_drained'] for r in later)
    overlap = sum(r['prefill_overlaps_old_follower_decode'] for r in later)
    schedules = rows(out / 'main/scheduler.jsonl')
    graph_counts = Counter(s['graph']['runtime_mode'] for s in schedules if s['graph'])
    full16 = sum(bool(s['graph']) and s['graph']['runtime_mode'] == 'FULL'
                 and s['graph']['num_unpadded_tokens'] == 16 for s in schedules)
    assert graph_counts['FULL'] > 0, 'No actual FULL CUDA graph execution'
    blockers = Counter(e['reason'] for e in admissions if e['event'] == 'admission_blocked')
    stats = {'notices_after_startup': len(later), 'early_prefill_notices': early,
             'overlap_old_follower_decode_notices': overlap,
             'starts_after_old_drained': len(later) - early,
             'prefill_finish_before_old_drained': sum(r['prefill_finish_lead_seconds'] is not None and r['prefill_finish_lead_seconds'] > 0 for r in later),
             'admission_block_events': dict(blockers), 'graph_counts': dict(graph_counts),
             'full_graph_with_16_real_tokens_steps': full16,
             'peak_inflight_requests': peak, 'mean_sampled_running': mean(s['running'] for s in schedules),
             'peak_sampled_running': max(s['running'] for s in schedules),
             'peak_kv_usage': max(s['kv_usage'] for s in schedules),
             'preempted_request_events': sum(s['preempted_requests'] for s in schedules),
             'max_live_source_tokens': max(e['live_source_tokens'] for e in admissions if e['event'] == 'admit')}
    late = [r for r in later if not r['prefill_starts_before_old_drained']]
    stats['late_prefill_details'] = [{**r, 'prior_block_reasons': sorted({e['reason'] for e in admissions if e['event'] == 'admission_blocked' and e['record_id'] == r['record_id']})} for r in late]
    dump(out / 'prefill_timeline.json', timeline); dump(out / 'scheduling_summary.json', stats)
    with (out / 'submission.csv').open() as f: csv_rows = list(csv.reader(f))
    assert len(csv_rows) == 201 and all(len(r) == 49 for r in csv_rows)
    assert [r[0] for r in csv_rows[1:]] == ids
    comparison = []
    for path in [Path('analysis/prefix200'), Path('analysis/prefix200_batch11'), out]:
        r = read(path / 'report.json'); s = read(path / 'evaluation.json')
        comparison.append({'path': str(path), 'seconds': r['prediction_seconds'],
                           'load_and_inference_seconds': r['total_seconds'],
                           'macro_f1': s['macro_f1'], 'micro_f1': s['micro_f1'],
                           'fp': s['false_positives'], 'fn': s['false_negatives']})
    delta = {'time_reduction_vs_batch11': 1 - comparison[-1]['seconds'] / comparison[1]['seconds'],
             'macro_delta_vs_batch11': score['macro_f1'] - comparison[1]['macro_f1'],
             'micro_delta_vs_batch11': score['micro_f1'] - comparison[1]['micro_f1']}
    validation = {'passed': True, 'records': 200, 'judgments': 4800, 'same_frozen_sources': True,
                  'same_rules': True, 'all_seed_dependencies_verified': True, 'max16_inflight_verified': True,
                  'request_trace_totals_verified': True, 'csv_columns': 49, 'full_graph_observed': True,
                  'early_prefill_observed': early > 0, 'failed_ids': report['failed_ids']}
    dump(out / 'validation.json', validation)
    dump(out / 'comparison.json', {'runs': comparison, 'delta': delta, 'scheduling': stats})
    text = ['# 12그룹 OFF 공고 간 연속 배치·엔진16', '',
            '| 구성 | 200건 추론 | Macro F1 | Micro F1 | FP / FN |', '|---|---:|---:|---:|---:|']
    for label, r in zip(['공고별 1→8→3', '공고별 1→11', '공고 간 연속 배치16'], comparison):
        text.append(f"| {label} | {r['seconds']:.2f}초 | {r['macro_f1']:.6f} | {r['micro_f1']:.6f} | {r['fp']} / {r['fn']} |")
    text += ['', f"1→11 대비 추론 시간 {delta['time_reduction_vs_batch11']:.2%} 감소. Macro 변화 {delta['macro_delta_vs_batch11']:+.6f}, Micro 변화 {delta['micro_delta_vs_batch11']:+.6f}.", '',
             '그룹·프롬프트·모델·Thinking OFF·H6·출력2048 유지. 엔진16, step8192, CUDA FULL_AND_PIECEWISE. 최초2공고 첫 그룹을 준비하고 남은 후속 작업≤16이면 다음 공고 첫 그룹을 우선 제출. 최대3공고·공통 원문48000토큰의 논리적 입장 제한; 물리 KV 메모리 예약량을 뜻하지 않는다.',
             f"초기 준비 이후 {len(later)}공고 중 {early}공고는 기존 공고가 GPU 계산을 모두 끝내기 전에 첫 prefill이 스케줄됐다. 그중 이전 공고 후속 그룹의 decode 구간과 prefill 구간이 겹친 공고는 {overlap}건. prefill까지 먼저 끝난 공고 {stats['prefill_finish_before_old_drained']}건. 프런트엔드 제출 시각뿐 아니라 엔진 scheduled_ts/first_token_ts/last_token_ts로 확인했다.",
             f"FULL graph {graph_counts['FULL']}회, 실제16 decode토큰의 FULL graph {full16}회. 전체 graph 모드 분포 {dict(graph_counts)}. 긴 prefill·혼합 단계에는 부분 graph 또는 graph 미사용이 가능하며 모든 연산이 FULL이라는 뜻은 아니다.",
             f"입장 제한 이벤트 {dict(blockers)}; 실제 동시 요청 최대{peak}; KV사용 최대{stats['peak_kv_usage']:.2%}; 재선점 요청 이벤트{stats['preempted_request_events']}. 제한 이벤트는 공고 수나 독점 GPU 대기 시간을 뜻하지 않는다.",
             f"최초 추론 {report['first_pass']['prediction_seconds']:.2f}초·실패{len(report['first_pass']['failed_ids'])}건, 복구{report['recovery_seconds']:.2f}초, 최종 실패{len(report['failed_ids'])}건. 모델 초기화{report['load_seconds']:.2f}초는 추론에서 제외; 초기화+추론{report['total_seconds']:.2f}초. 사전 검사·16요청 예열·8공고 smoke는 비교 시간에서 제외.",
             f"잘못된 응답{report['invalid_responses']}회, 실제 검색{report['search_rounds']}회, 캐시 토큰 비율{report['cached_fraction']:.2%}. 근거 불일치{score['evidence']['invalid']}·양성 비부재 근거 누락{score['evidence']['positive_nonabsence_missing']}건; F1은 이진 판정만 평가한다.", '',
             '시간·F1은 각 설정 단일 로컬 실행 결과이며 배치/graph/스케줄 변경 효과를 분리한 인과 비교는 아니다. 점수 차이를 배치의 구조적 성능 차이로 단정하지 않는다. prefill/decode 구간은 요청 지연이며 GPU 커널의 동시 실행이나 독점 walltime을 뜻하지 않는다. 다음 prefill의 선행 시작은 GPU가 항상16요청으로 가득 찬다는 보장이 아니다.', '',
             '재현: `MAX_JOBS=2 uv run --locked python scripts/benchmark_prefix_pipeline.py --output NEW_DIRECTORY`',
             '검증: `python3 scripts/summarize_prefix_pipeline.py`', '']
    text += ['선행 시작 예외3건: PPS-DEV-28·121은 긴 원문 합계가48000토큰 입장 한도를 넘어 기존 공고 완료까지 기다렸다. PPS-DEV-137도 앞서 토큰 한도에 막혔고, 마지막 기존 요청 종료 전에 제출됐지만 엔진 prefill 시작은 종료보다18.3ms 늦었다. 소프트웨어 대기열 소진을 무조건 기다리는 구조는 없지만 메모리 입장 제한·제출 지연에 따른 빈 구간은 남는다.', '']
    (out / 'comparison.md').write_text('\n'.join(text))
    print(json.dumps({'runs': comparison, 'delta': delta, 'scheduling': stats, 'validation': validation}, indent=2))


if __name__ == '__main__': main()
