"""Audit the source-first dev200 run and compare its historical baseline."""
from nara.paths import source_path
import hashlib
import json
from pathlib import Path
from nara.evaluation.reporting import report_path, write_report


def read(path):return json.loads(Path(path).read_text())
def lines(path):return [json.loads(row) for row in Path(path).read_text().splitlines()]


def main():
    out=Path('analysis/prefix200')
    baseline=Path('analysis/compact200/groups12_off_h6')
    new,old=read(out/'report.json'),read(baseline/'report.json')
    score,previous=read(out/'evaluation.json'),read(baseline/'evaluation.json')
    manifest=read(out/'manifest.json')
    context={'max_input_tokens':max(max(c['input_tokens']) for c in manifest['counts']),
             'initial_search_disabled':[c['id'] for c in manifest['counts'] if any(n+2*new['limits']['output_tokens']+256>32768 for n in c['input_tokens'])]}
    (out/'context_check.json').write_text(json.dumps(context,indent=2)+'\n')
    traces=lines(out/'trace.jsonl');cache=lines(out/'cache_trace.jsonl')
    rules=lines(out/'rules.jsonl');old_rules=lines(baseline/'rules.jsonl')
    assert not new['failed_ids'] and len(traces)==200==score['records']
    assert new['groups']==old['groups'] and new['options']==old['options'] and new['limits']==old['limits']
    assert rules==old_rules
    for path,digest in manifest['source_sha256'].items():
        assert hashlib.sha256(source_path(path).read_bytes()).hexdigest()==digest,path
        assert hashlib.sha256((out/'source'/path).read_bytes()).hexdigest()==digest,path
    events=[e for r in traces for t in r['trace'] for e in t['events'] if e['event']=='model']
    assert len(events)==len(cache)==new['model_turns']
    assert sum(e['input_tokens'] for e in events)==sum(c['input_tokens'] for c in cache)==new['input_tokens']
    assert sum(e['output_tokens'] for e in events)==sum(c['output_tokens'] for c in cache)==new['output_tokens']
    assert all(e['thinking_tokens']==0 and e['thinking_budget'] is None for e in events)
    assert all(e['input_tokens']+e['max_output_tokens']+128<=32768 for e in events)
    assert all(c['cached_tokens'] is not None and 0<=c['cached_tokens']<=c['input_tokens'] for c in cache)
    assert sum(c['cached_tokens'] for c in cache)==new['cached_input_tokens']
    for r,rule in zip(traces,rules):
        assert r['record_id']==rule['record_id']
        assert [t['items'] for t in r['trace']]==new['groups']
        assert len({t['task_id'] for t in r['trace']})==12
        assert len(r['judgments'])==24 and all(r['judgments'][k]==v for k,v in rule['judgments'].items())
    phase_stats={}
    for phase in ['first','remaining']:
        rows=[c for c in cache if c['phase']==phase]
        phase_stats[phase]={'requests':len(rows),'input_tokens':sum(c['input_tokens'] for c in rows),
                            'cached_tokens':sum(c['cached_tokens'] for c in rows),
                            'output_tokens':sum(c['output_tokens'] for c in rows)}
        p=phase_stats[phase];p['cached_fraction']=p['cached_tokens']/p['input_tokens']
    before={r['record_id']:r for r in lines(baseline/'trace.jsonl')}
    changed={f'v{i}':sum(r['judgments'][f'v{i}']['위반여부']!=before[r['record_id']]['judgments'][f'v{i}']['위반여부'] for r in traces) for i in range(1,25)}
    per_item=[]
    for a,b in zip(previous['per_item'],score['per_item']):
        assert a['item']==b['item']
        per_item.append({'item':a['item'],'old_f1':a['f1'],'new_f1':b['f1'],'delta':b['f1']-a['f1'],'changed_bits':changed[a['item']]})
    speedup=old['prediction_seconds']/new['prediction_seconds']
    reduction=1-new['prediction_seconds']/old['prediction_seconds']
    result={'baseline':str(baseline),'candidate':str(out),'records':200,
            'old_seconds':old['prediction_seconds'],'new_seconds':new['prediction_seconds'],
            'speedup':speedup,'time_reduction_fraction':reduction,
            'old_macro_f1':previous['macro_f1'],'new_macro_f1':score['macro_f1'],
            'macro_f1_delta':score['macro_f1']-previous['macro_f1'],
            'cached_fraction':new['cached_fraction'],'phase_cache':phase_stats,
            'request_stats_available':new['request_stats_available'],
            'new_projected_1853_minutes':(new['prediction_seconds']/200*1853+new['load_seconds'])/60,
            'old_projected_1853_minutes':(old['prediction_seconds']/200*1853+old['load_seconds'])/60,
            'changed_bits':sum(changed.values()),'per_item':per_item,
            'caveats':['Historical baseline; no measured baseline cache hits or matched uncached control.',
                       'Prompt role/order and scheduling changed together; not a cache-only causal accuracy comparison.',
                       'Rendered token counts include cache hits; unavailable request timing is not zero.',
                       'Single local RTX5090 run; linear1853 projection is not measured L40S latency.']}
    (out/'comparison.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    (out/'validation.json').write_text(json.dumps({'passed':True,'records':200,'judgments':4800,
         'frozen_sources_match':True,'rule_rows_identical':True,'trace_and_cache_totals_match':True,
         'thinking_tokens':0,'context_overflows':0,'evidence_invalid':score['evidence']['invalid']},indent=2)+'\n')
    table=[('| 기존 |',old,previous),('| 공통 원문 prefix 재사용 |',new,score)]
    text=['# 공통 원문 KV 캐시 실험: dev200','',
      f'기존 대비 추론 시간 {reduction:.1%} 감소({speedup:.2f}배 속도). Macro F1 변화 {result["macro_f1_delta"]:+.5f}.','',
      '| 구성 | 200건 추론 | Macro F1 | Micro F1 | FP / FN |',
      '|---|---:|---:|---:|---:|']
    for name,r,s in table:
        text.append(f'{name} {r["prediction_seconds"]/60:.2f}분 | {s["macro_f1"]:.5f} | {s["micro_f1"]:.5f} | {s["false_positives"]} / {s["false_negatives"]} |')
    text += ['', '설정: Gemma4 NVFP4, RTX5090, 32768 context, 12그룹, thinking OFF, output2048, batch8, 고정 v2/v3 규칙. 200건 × 24항목 전체 평가.',
      '', '## 실제 재사용', '',
      f'- 전체 입력 {new["input_tokens"]:,}토큰 중 {new["cached_input_tokens"]:,}토큰({new["cached_fraction"]:.2%})을 vLLM이 캐시 적중으로 보고했다.',
      f'- 첫 그룹: {phase_stats["first"]["cached_fraction"]:.2%}; 나머지 그룹: {phase_stats["remaining"]["cached_fraction"]:.2%}. 비율은 요청 수가 아닌 입력 토큰 가중 비율이다.',
      f'- 입력 처리와 출력을 포함한 모델 호출 {new["model_seconds"]:.2f}초, 생성 출력(재시도 포함) {new["output_tokens"]:,}토큰. thinking {new["thinking_tokens"]}토큰.',
      f'- vLLM 개별 요청 시간 통계 제공: {new["request_stats_available"]}. prefill/decode 시간을 분리 측정한 결과가 아니므로, 전체 절감 시간을 prefill 절감으로 단정하지 않는다.',
      '', '## 변경 범위와 검증', '',
      '- 공통 system 지침 → user의 공고 ID·메타·원문 전체 → 해당 그룹의 부재 항목·법령 판단 기준 순서. 기존 그룹별 system 기준을 user 끝으로 옮겼다.',
      '- 공고별 첫 실제 그룹의 판정이 끝난 후 나머지 11그룹을 batch8로 처리한다. 첫 판정도 사용하며 추가 예열 추론은 없다. 그룹 간 답변을 전달하지 않는다.',
      '- 원문 삭제·요약 없음. 모든 초기 입력과 실제 요청이 32K 예산 이내. v2/v3 규칙과 결과는 기존과 동일.',
      f'- 모델 호출 {new["model_turns"]}, 잘못된 응답 {new["invalid_responses"]}, 최종 실패 {len(new["failed_ids"])}, 실제 RAG 검색 {new["search_rounds"]}.',
      f'- 기존 대비 판정 {result["changed_bits"]}/4800개 변경. 항목별 F1과 변경 수는 comparison.json.',
      f'- 출력 근거 원문 불일치 {score["evidence"]["invalid"]}; 근거 누락 양성(부재 항목 제외) {score["evidence"]["positive_nonabsence_missing"]}. 원문 일치는 판단 타당성을 보증하지 않는다.',
      '', '## 해석 범위', '',
      '- 과거 실행과 비교했다. 과거 캐시 적중량은 측정하지 않았다. 프롬프트 역할·순서와 배치 일정이 함께 바뀌었으므로 캐시만의 정확도 효과는 분리할 수 없다.',
      '- OFF여도 최종 JSON 생성은 남는다. 캐시가 문맥 길이 자체를 줄이지는 않는다. 기존에도 prefix caching 옵션은 켜져 있었으나 그룹별 기준이 원문 앞에 있어 원문 공유가 막혔다.',
      f'- 같은 장비에서 1853건 선형 추정(추론+1회 모델 로드): 기존 {result["old_projected_1853_minutes"]:.1f}분 → 이번 {result["new_projected_1853_minutes"]:.1f}분. warmup·개발용 사전 검증 제외. L40S 실제 측정이나 2시간 보장이 아니다.',
      '', '재현: `uv run --locked python src/experiments/benchmark_prefix200.py --output NEW_DIRECTORY`. `source/`에 실행 코드 스냅샷, `prompt_*.txt`에 실제 템플릿, `cache_trace.jsonl`에 요청별 캐시 계측.', '']
    write_report(out/'comparison.md', '\n'.join(text))
    p=report_path(out/'evaluation.md')
    s=p.read_text().replace('실제 시스템 프롬프트는 system_prompt.txt 참조.','실제 system/user 프롬프트는 prompt_*.txt 참조.').replace('대화당 4항목.','대화당 최대 4항목; v2/v3는 고정 규칙.')
    s=s.replace('- 초기 문맥 길이 측정 파일 없음.',f'- 최대 초기 입력 {max(max(c["input_tokens"]) for c in manifest["counts"]):,}토큰. manifest.json 참조.')
    s=s.replace('uv run --locked python src/cli.py --input data/dev.jsonl --output-dir NEW_OUTPUT_DIR','uv run --locked python src/experiments/benchmark_prefix200.py --output NEW_OUTPUT_DIR')
    s=s.replace('- 초기 검색 제한 수는 별도 측정 필요.', f'- 초기 문맥 예산으로 한 개 이상 그룹의 선택적 검색이 제한된 공고 {len(context["initial_search_disabled"])}건. context_check.json 참조.')
    p.write_text(s)
    print(json.dumps({k:v for k,v in result.items() if k!='per_item'},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
