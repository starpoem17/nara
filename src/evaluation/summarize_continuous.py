"""Audit continuous runs and compare throughput, token-length bins and label quality."""
from nara.paths import source_path
import csv
import hashlib
import json
import re
from pathlib import Path
from nara.evaluation.reporting import write_report
import numpy as np
from nara.evaluation.summarize_hybrid200 import timing
from nara.inference.hybrid_experiment import THINK,GROUPS

ROOT=Path('analysis/continuous200')
def read(p):return json.loads(Path(p).read_text())
def rows(p):return [json.loads(s) for s in Path(p).read_text().splitlines()]
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')

def scores(trace,truth,keys):
    per=[]
    for k in keys:
        yy=[int(truth[r['record_id']][k]) for r in trace];pp=[r['judgments'][k]['위반여부'] for r in trace]
        tp=sum(a==b==1 for a,b in zip(yy,pp));fp=sum(a==0 and b==1 for a,b in zip(yy,pp));fn=sum(a==1 and b==0 for a,b in zip(yy,pp))
        per.append({'feature':k,'tp':tp,'fp':fp,'fn':fn,'f1':2*tp/max(1,2*tp+fp+fn)})
    return {'macro_f1':sum(r['f1'] for r in per)/len(keys),'micro_f1':2*sum(r['tp'] for r in per)/max(1,sum(2*r['tp']+r['fp']+r['fn'] for r in per)),'per_feature':per}

def scheduler_summary(data,elapsed):
    duration=sum(b['time']-a['time'] for a,b in zip(data,data[1:]))
    avg={key:sum(a[key]*(b['time']-a['time']) for a,b in zip(data,data[1:]))/max(duration,1e-9) for key in ['running','waiting','deferred','kv_usage']}
    return {'samples':len(data),'sampled_span_seconds':duration,'time_weighted_mean':avg,
            'peak_running':max(r['running'] for r in data),'peak_kv_usage':max(r['kv_usage'] for r in data),
            'idle_fraction':sum((b['time']-a['time']) for a,b in zip(data,data[1:]) if a['running']==0)/max(duration,1e-9)}

def main():
    selection=read(ROOT/'selection.json');budget=selection['selected_tokens'];plan=read(ROOT/'plan.json')
    postrun=read(ROOT/'postrun_changes.json')
    for p,h in plan['source_sha256'].items():
        expected=postrun[p]['after'] if p in postrun else h
        if p in postrun:assert postrun[p]['before']==h
        assert hashlib.sha256(source_path(p).read_bytes()).hexdigest()==expected,p
        assert hashlib.sha256((ROOT/'source'/p).read_bytes()).hexdigest()==h,p
    truth={r['id']:r for r in csv.DictReader(open('data/dev_labels.csv'))}
    names=['pilot_barrier_8192']+[f'pilot_continuous_{b}' for b in [2048,8192,16384]]+[f'six_continuous_{budget}',f'mixed_continuous_{budget}']
    memory={}
    for b in [2048,8192,16384]:
        log=(ROOT/f'pilot_{b}.log').read_text()
        patterns={'kv_gib':r'Available KV cache memory: ([0-9.]+) GiB',
                  'activation_gib':r'([0-9.]+) GiB for peak activation',
                  'max32k_concurrency':r'Maximum concurrency for 32,768 tokens per request: ([0-9.]+)x'}
        memory[str(b)]={k:float(re.search(pattern,log).group(1)) for k,pattern in patterns.items()}
    dump(ROOT/'engine_memory.json',memory)
    result={};length_rows=[];per=[]
    for name in names:
        folder=ROOT/name;report=read(folder/'report.json');trace=rows(folder/'trace.jsonl');requests=rows(folder/'request_timings.jsonl');life=rows(folder/'lifecycle.jsonl')
        assert not report['failed_ids'],name
        assert len(trace)==report['records'] and len({r['record_id'] for r in trace})==len(trace)
        ee=[e for r in trace for t in r['trace'] for e in t['events'] if e['event']=='model']
        assert len(ee)==len(requests)
        assert sum(e['input_tokens'] for e in ee)==sum(r['input_tokens'] for r in requests)
        assert sum(e['output_tokens'] for e in ee)==sum(r['output_tokens'] for r in requests)
        assert all(e['input_tokens']+e['max_output_tokens']+128<=32768 for e in ee)
        assert all(e['thinking_tokens']==0 for e in ee if e['thinking_budget'] is None)
        assert all(e['thinking_budget'] is None or e['thinking_budget']<=1024 for e in ee)
        keys=[f'v{i}' for i in range(1,25)] if name.startswith('mixed') else THINK
        assert all(set(r['judgments'])==set(keys) for r in trace)
        quality=scores(trace,truth,keys)
        thought_lengths=[e['thinking_tokens'] for e in ee if e['thinking_budget'] is not None]
        result[name]={'report':report,'timing':timing(requests),'quality':quality,
                      'scheduler':scheduler_summary(rows(folder/'scheduler.jsonl'),report['prediction_seconds']),
                      'thinking_length_quantiles':np.quantile(thought_lengths,[0,.25,.5,.75,1]).tolist() if thought_lengths else []}
        if life:
            submitted={r['request_id']:r for r in life if r['event']=='submit'};finished={r['request_id']:r for r in life if r['event']=='complete'}
            assert set(submitted)==set(finished) and len(submitted)==len(requests)
            ordered=sorted(submitted.values(),key=lambda r:r['time']);first=[r['request_id'] for r in ordered[:8]]
            refill={'max_inflight':max(r['inflight'] for r in life),
                    'ninth_submit_before_first_eight_all_finish':ordered[8]['time']<max(finished[k]['time'] for k in first),
                    'ninth_submit_seconds_after_first_completion':ordered[8]['time']-min(finished[k]['time'] for k in first),
                    'remaining_first_eight_at_ninth_submit':sum(finished[k]['time']>ordered[8]['time'] for k in first)}
            assert refill['max_inflight']<=8 and refill['ninth_submit_before_first_eight_all_finish']
            result[name]['refill']=refill
        for label,low,high in [('<=8K',0,8192),('8K..16K',8192,16384),('>16K',16384,32768)]:
            subset=[r for r in requests if low<r['input_tokens']<=high]
            if subset:
                t=timing(subset);length_rows.append({'run':name,'input_bin':label,'requests':len(subset),
                    'mean_prefill':t['mean_prefill_seconds'],'mean_decode':t['mean_decode_seconds'],
                    'mean_queue':t['mean_queue_seconds'],'cached_fraction':t['cached_fraction']})
        for row in quality['per_feature']:per.append({'run':name,**row})
    for filename,records in [('length_bins.csv',length_rows),('per_feature.csv',per)]:
        with (ROOT/filename).open('w') as f:
            w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
    old=read('analysis/hybrid200/six_on1024_batch8/report.json');oldtrace=rows('analysis/hybrid200/six_on1024_batch8/trace.jsonl')
    result['previous_six_batch8']={'seconds':old['seconds'],'quality':scores(oldtrace,truth,THINK)}
    mixed=ROOT/f'mixed_continuous_{budget}'
    assert rows(mixed/'rules.jsonl')==rows('analysis/prefix200/rules.jsonl')
    assert all([list(t['items']) for t in r['trace']]==GROUPS for r in rows(mixed/'trace.jsonl'))
    for r in rows(mixed/'trace.jsonl'):
        for t in r['trace']:
            for e in t['events']:
                if e['event']=='model':assert (e['thinking_budget'] is not None)==(set(t['items'])==set(THINK))
    with (mixed/'submission.csv').open() as f:
        reader=csv.DictReader(f)
        assert reader.fieldnames==['id']+[f'v{i}' for i in range(1,25)]+[f'e{i}' for i in range(1,25)]
        submission=list(reader)
        assert len(submission)==200 and {r['id'] for r in submission}==set(truth)
    if (mixed/'first_pass').exists():
        before=rows(mixed/'first_pass/trace.jsonl');after=rows(mixed/'trace.jsonl')
        for a,b in zip(before,after):
            assert a['record_id']==b['record_id']
            if not a['error']:assert a==b
        recovery=read(mixed/'report.json')['recovery']
        assert hashlib.sha256(Path('src/experiments/recover_continuous.py').read_bytes()).hexdigest()==recovery['policy']['source_sha256']
    evaluation=read(mixed/'evaluation.json')
    assert evaluation['evidence']['invalid']==0
    result[f'mixed_continuous_{budget}']['evidence']=evaluation['evidence']
    history=read('analysis/hybrid200/comparison.json')
    result['historical_full24']={n:{'seconds':history['pipeline_seconds'][n],
        'macro_f1':history['scores'][n]['macro_f1'],'micro_f1':history['scores'][n]['micro_f1']}
        for n in ['hybrid','optimized','optimized_off','groups12','ungrouped']}
    instant=[r for r in rows(mixed/'request_timings.jsonl') if r['thinking_budget'] is None]
    thinking=[r for r in rows(mixed/'request_timings.jsonl') if r['thinking_budget'] is not None]
    result[f'mixed_continuous_{budget}']['by_mode']={'instant':timing(instant),'thinking':timing(thinking)}
    dump(ROOT/'comparison.json',result)
    dump(ROOT/'validation.json',{'passed':True,'full200_six_and_mixed':True,'source_hashes_match':True,'postrun_report_metadata_patch':postrun,'rules_unchanged':True,'input_output_trace_counts_match':True,'max_inflight':8,'refill_before_batch_completion_verified':True})
    text=['# 완료 즉시 요청 보충 및 prefill 토큰 한도 실험','',
          '원문·영어 압축 판단 기준·5그룹·v2/v3 규칙 유지. Gemma4 NVFP4 RTX5090 context32768, thinking1024, output2048, max_num_seqs8, BGE GPU 상주. ON0 미적용.',
          '48건은 입력 길이 순위로 선택한 pilot. 시간으로만 설정을 선택하고 이후200건 전체6항목/5그룹을 검증했다. 모든 시간은 모델 초기화를 제외한다.','',
          '## 48건 대조','', '|실행|한 스텝 토큰 한도|시간|평균 prefill|평균 decode|평균 엔진 대기|최대 KV 사용률|', '|---|---:|---:|---:|---:|---:|---:|']
    for name in names[:4]:
        x=result[name];t=x['timing'];text.append(f'|{name}|{x["report"]["engine"]["max_num_batched_tokens"]}|{x["report"]["prediction_seconds"]:.2f}s|{t["mean_prefill_seconds"]:.3f}s|{t["mean_decode_seconds"]:.3f}s|{t["mean_queue_seconds"]:.3f}s|{x["scheduler"]["peak_kv_usage"]:.1%}|')
    text+=['','|실행|평균 실행 요청|평균 일반 대기|평균 Deferred|','|---|---:|---:|---:|']
    for name in names[:4]:
        a=result[name]['scheduler']['time_weighted_mean'];text.append(f'|{name}|{a["running"]:.2f}|{a["waiting"]:.2f}|{a["deferred"]:.2f}|')
    text+=['','## 토큰 한도와 메모리 수용량','', '|스텝 토큰 한도|Activation 프로파일|KV pool|엔진 계산32K 동시성|','|---|---:|---:|---:|']
    for b,m in memory.items():text.append(f'|{b}|{m["activation_gib"]:.2f}GiB|{m["kv_gib"]:.2f}GiB|{m["max32k_concurrency"]:.2f}|')
    text+=['', '이 모델은30층 중25층 sliding-window(1024),5층 full attention이다. 설치된 vLLM의 sliding KV 예약은 최근1023토큰 + 처리 중인 토큰 상한(동시 스텝 수×max_num_batched_tokens)에 의존한다. 작은 prefill 한도는 activation뿐 아니라 sliding KV의 최악 예약량도 줄인다. 표의 동시성은 초기화 시 계산된32K 기준 값이며 실제 모든 시점의 동시 실행 수나 처리속도와 같지 않다.', '']
    text+=['','## 전체200 검증','', '|실행|시간|Macro F1|Micro F1|점수 범위|','|---|---:|---:|---:|---|']
    oldq=result['previous_six_batch8']['quality'];text.append(f'|기존6항목 ON1024 8건 묶음|{old["seconds"]:.2f}s|{oldq["macro_f1"]:.4f}|{oldq["micro_f1"]:.4f}|6항목|')
    for name in names[4:]:
        x=result[name];q=x['quality'];text.append(f'|{name}|{x["report"]["prediction_seconds"]:.2f}s|{q["macro_f1"]:.4f}|{q["micro_f1"]:.4f}|{"24항목" if name.startswith("mixed") else "6항목"}|')
    text+=['','## 이전 전체24항목 실행과 비교','', '|실행|시간|Macro F1|Micro F1|','|---|---:|---:|---:|']
    labels={'hybrid':'이전5그룹 ON1024 직렬','optimized':'이전5그룹 ON256 배치8','optimized_off':'이전5그룹 전부 OFF','groups12':'이전12그룹 OFF','ungrouped':'이전24항목 일괄 ON + H6'}
    for n,x in result['historical_full24'].items():
        text.append(f'|{labels[n]}|{x["seconds"]:.2f}s|{x["macro_f1"]:.4f}|{x["micro_f1"]:.4f}|')
    x=result[f'mixed_continuous_{budget}'];q=x['quality']
    text.append(f'|이번5그룹 ON1024 연속 처리|{x["report"]["prediction_seconds"]:.2f}s|{q["macro_f1"]:.4f}|{q["micro_f1"]:.4f}|')
    text+=['', '이전5그룹 ON1024는 thinking 직렬 실행이었다. 이번 전체 시간 차이에는 thinking 병렬화와 그룹/모드 사이 대기 제거가 함께 포함되므로, 완료 즉시 보충만의 개선율로 해석하지 않는다. 보충만의 비교는 위6항목 8건 묶음 대조를 참조한다.',
        '양성 근거 상태: '+json.dumps(evaluation['evidence'],ensure_ascii=False)+'. 실패 예측을0으로 채우지 않았다. F1은 이진 판정 점수이며 모든 양성 근거의 충실성을 보장하지 않는다.', '']
    recovery=result[f'mixed_continuous_{budget}']['report'].get('recovery')
    if recovery:
        text+=['복구: 최초 실행 실패 그룹만 원래 프롬프트/모드/토큰 한도로 단독 재시도했다. '+f'추론 {recovery["prediction_seconds"]:.3f}초는 표에 포함, 별도 모델 초기화 {recovery["separate_process_load_seconds"]:.3f}초는 제외. '+
            '성공한 공고는 변경하지 않았으며 first_pass/에 원본을 보존했다. scheduler 통계와 trace_completed는 최초 실행, trace.jsonl/request_timings/lifecycle는 복구 병합 결과이다.', '']
    text+=['','## 입력 길이별 요청 지연','', '|실행|입력 길이|요청 수|평균 prefill|평균 decode|평균 엔진 대기|','|---|---|---:|---:|---:|---:|']
    for r in length_rows:
        if r['run'].startswith('pilot'):text.append(f'|{r["run"]}|{r["input_bin"]}|{r["requests"]}|{r["mean_prefill"]:.3f}s|{r["mean_decode"]:.3f}s|{r["mean_queue"]:.3f}s|')
    text+=['','## 요청 보충 검증','']
    for name in names[4:]:
        a=result[name]['refill'];text.append(f'- {name}: 첫 완료 후 {1000*a["ninth_submit_seconds_after_first_completion"]:.2f}ms에9번째 요청 제출; 당시 첫8건 중 {a["remaining_first_eight_at_ninth_submit"]}건 미완료. 실제 최대 in-flight {a["max_inflight"]}.')
    text+=['', '기존6항목 ON1024는 모든200건의 관측 thinking 본문이1020~1022토큰이었다. 생성 길이가 거의 같아 묶음의 느린 마지막 요청을 기다리는 손실이 제한적이다. 연속 처리는 대기를 줄이지만 신규 prefill과 기존 decode가 자원을 공유하므로 개별 decode 지연은 늘 수 있다.', '']
    text+=['','## 판단','',
        '현재 기본값은 최대8개 요청 + 스텝8192토큰 + chunked prefill이다. pilot에서2048은8192보다 약1.7% 느린 대신 메모리 여유가 더 컸고,16384는 약10.8% 느렸다. 장문 비중이 커질 때2048은 유력한 대안이지만 전체200으로 따로 검증한 결과는 아니다.',
        '완료 즉시 보충의 속도 개선은 같은6항목200건에서1.8%였다. 이6항목 Macro F1은0.5006→0.3915, Micro F1은0.4865→0.3947로 하락해 정확도 보존을 주장할 수 없다. 입력 토큰 및 실제SamplingParams 대조는 adapter_parity.json 참조. 기존 generate도 내부에서FINAL_ONLY로 정규화되므로 반환 옵션이 유효 생성 설정 차이는 아니다. 배치 구성/수치 연산 경로에 따른 변동 가능성은 있으나 이 실험으로 단독 원인을 확정하지 않았다.',
        '이번 전체24항목 결과는 이전12그룹OFF보다 느리고 Macro/Micro F1도 낮았다. 요청 보충 구조는 구현했지만 이번 혼합 설정을 정확도·시간 최선의 설정으로 승격할 근거는 없다.', '']
    text+=['','## 해석 범위','',
       '- max_num_batched_tokens는 한 스텝의 prefill+decode 토큰 예산이다. 전체 문서 길이/출력 한도/동시 요청 개수와 다르다. 긴 입력은 chunked prefill로 나눠 처리된다.',
       '- 긴 입력은 더 많은 prefill 스텝과 KV 공간을 요구한다. 캐시가 있으면 새로 계산할 토큰은 줄지만 저장 공간과 decode의 attention 비용은 남는다.',
       '- 작은 토큰 예산은 decode와 긴 prefill의 교대 간격을 줄일 수 있지만 prefill 스텝 수가 증가한다. 큰 예산은 prefill 처리량을 높일 수 있지만 activation 공간이 늘고 KV 풀과 동시성에 영향을 줄 수 있다. 초기화 메모리 수치는 각 pilot 로그 참조.',
       '- 요청별 prefill=scheduled→first token, decode=first→last token. 동시 실행 구간이 겹친다. 엔진 대기에는 아직 엔진에 제출하지 않은 application queue 시간은 포함되지 않는다.',
       '- Running은 prefill 중인 요청도 포함한다. Deferred에는 grammar 준비 등이 포함되므로 메모리 부족으로 단정하지 않는다. KV 사용률은 할당된 pool 대비 비율이며 전체 GPU peak VRAM이 아니다.',
       '- 스케줄 변경은 greedy 판정에도 영향을 줄 수 있다. pilot48의 단회 시간 선택이며 절대적 최적값/대회 통과를 보장하지 않는다. 전체200 점수도 같은 개발 데이터이다.',
       '- pilot8192는 같은 엔진에서 barrier 다음 continuous 순서로 단회 실행했다. Prefix cache는 초기화했지만 컴파일/grammar 등 다른 warm 상태의 순서 효과는 완전히 제거하지 않았다.',
       '- 46 tests passed including refill under a slow first request, RAG/retry, modes/cache seed, context failure. validation.json: full input/source/rules/events/refill checks.',
       '- 실행: src/experiments/benchmark_continuous.py --kind mixed --tokens '+str(budget)+'. 완료된 출력 디렉터리는 덮어쓰지 않는다. 새 데이터/다른 운영 경로에는 ContinuousPredictor를 동일 인터페이스로 연결한다.', '']
    write_report(ROOT/'comparison.md', '\n'.join(text))
    print(json.dumps({'selected_tokens':budget,'pilot_seconds':{n:result[n]['report']['prediction_seconds'] for n in names[:4]},'full_seconds':{n:result[n]['report']['prediction_seconds'] for n in names[4:]}},indent=2))

if __name__=='__main__':main()
