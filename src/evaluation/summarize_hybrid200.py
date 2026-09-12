"""Audit mixed-mode results, controlled costs and per-feature comparisons."""
from nara.paths import source_path
from copy import deepcopy
import csv
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from nara.evaluation.reporting import report_path, write_report
import numpy as np
from nara.records import write_submission
from nara.inference.predictor import Prediction
from nara.inference.hybrid_experiment import THINK,GROUPS
from nara.evaluation.evaluate_dev import evaluate,read_csv,ITEMS

ROOT=Path('analysis/hybrid200')
def read(path):return json.loads(Path(path).read_text())
def rows(path):return [json.loads(s) for s in Path(path).read_text().splitlines()]
def dump(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def events(trace):return [e for r in trace for t in r['trace'] for e in t['events'] if e['event']=='model']


def composite(name,main,main_report,main_times):
    source=ROOT/name;target=ROOT/('composite_'+name);target.mkdir(exist_ok=True)
    alt=rows(source/'trace.jsonl');report=read(source/'report.json')
    assert not report['failed_ids'] and len(alt)==200
    by_id={r['record_id']:r for r in alt};combined=[]
    for old in main:
        new=deepcopy(old);replacement=by_id[old['record_id']]
        assert set(replacement['judgments'])==set(THINK)
        new['judgments'].update(replacement['judgments'])
        new['trace']=[t for t in new['trace'] if set(t['items'])!=set(THINK)]+replacement['trace']
        assert all(new['judgments'][k]==old['judgments'][k] for k in ITEMS if k not in THINK)
        combined.append(new)
    (target/'trace.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in combined))
    removed=sum(p['seconds'] for r in main_times for p in r['phases'] if p['phase']=='thinking')
    rr=deepcopy(main_report)
    rr['name']=target.name;rr['prediction_seconds']=main_report['prediction_seconds']-removed+report['seconds']
    rr['total_seconds']=rr['prediction_seconds']+rr['load_seconds']
    rr['options']['thinking']=False if name=='six_off' else f'mixed {name}'
    rr['derived']=True;rr['time_is_estimate']=True
    rr['composition']='Reuse main instant16 and frozen rules2; replace only six-feature group with separately measured control. Cold OFF group has no preceding instant document cache, so this overestimates an all-OFF warm pipeline.'
    ee=events(combined)
    for key in ['input_tokens','output_tokens','thinking_tokens']:rr[key]=sum(e[key] for e in ee)
    rr['model_turns']=len(ee)
    rr.pop('model_seconds',None);rr.pop('retrieval_seconds',None)
    rr['invalid_responses']=sum(e['event']=='invalid_response' for r in combined for t in r['trace'] for e in t['events'])
    rr['search_rounds']=sum(e['event']=='search' for r in combined for t in r['trace'] for e in t['events'])
    dump(target/'report.json',rr)
    if (target/'submission.csv').exists():(target/'submission.csv').unlink()
    write_submission([Prediction(**r) for r in combined],target/'submission.csv')
    evaluate(target,'data/dev_labels.csv','data/dev.jsonl',200)
    return read(target/'evaluation.json')


def interval_union_breakdown(requests):
    points=[]
    for r in requests:
        s=r['request_stats'];a,b,c=s['scheduled_ts'],s['first_token_ts'],s['last_token_ts']
        points.extend([(a,1,0),(b,-1,1),(c,0,-1)])
    points.sort();out={'prefill_only_seconds':0.,'decode_only_seconds':0.,'overlap_seconds':0.}
    p=d=0;previous=None
    for t,dp,dd in points:
        if previous is not None and (p or d):
            key='overlap_seconds' if p and d else ('prefill_only_seconds' if p else 'decode_only_seconds')
            out[key]+=t-previous
        p+=dp;d+=dd;previous=t
    return out


def timing(requests):
    pref=sum(r['prefill_seconds'] for r in requests);dec=sum(r['decode_seconds'] for r in requests)
    n=len(requests);inp=sum(r['input_tokens'] for r in requests);out=sum(r['output_tokens'] for r in requests)
    return {'requests':n,'prefill_request_seconds':pref,'decode_request_seconds':dec,
        'prefill_request_fraction':pref/(pref+dec),'decode_request_fraction':dec/(pref+dec),
        'mean_prefill_seconds':pref/n,'mean_decode_seconds':dec/n,
        'mean_queue_seconds':sum(r['queue_seconds'] for r in requests)/n,
        'p95_prefill_seconds':float(np.quantile([r['prefill_seconds'] for r in requests],.95)),
        'input_tokens':inp,'output_tokens':out,'cached_fraction':sum(r['cached_tokens'] for r in requests)/inp,
        'aggregate_decode_tokens_per_request_second':(out-n)/dec,
        'interval_union':interval_union_breakdown(requests)}


def bootstrap_delta(a,b,truth,seed=42):
    # Paired notice bootstrap: descriptive development-data uncertainty, not a new holdout.
    ids=list(truth);y=np.array([[int(truth[i][k]) for k in ITEMS] for i in ids])
    aa=np.array([[int(a[i][k]) for k in ITEMS] for i in ids]);bb=np.array([[int(b[i][k]) for k in ITEMS] for i in ids])
    rng=np.random.default_rng(seed);deltas=[]
    def f(z,yy):
        tp=((z==1)&(yy==1)).sum(axis=0);fp=((z==1)&(yy==0)).sum(axis=0);fn=((z==0)&(yy==1)).sum(axis=0)
        denominator=2*tp+fp+fn
        return np.divide(2*tp,denominator,out=np.zeros(24),where=denominator!=0).mean(),2*tp.sum()/max(1,denominator.sum())
    for _ in range(2000):
        index=rng.integers(0,len(ids),len(ids));x=f(aa[index],y[index]);z=f(bb[index],y[index]);deltas.append([x[0]-z[0],x[1]-z[1]])
    ci=np.quantile(deltas,[.025,.975],axis=0)
    return {'macro_delta_95ci':ci[:,0].tolist(),'micro_delta_95ci':ci[:,1].tolist(),'resamples':2000,'unit':'notice; exploratory, same development data'}


def main():
    base=ROOT/'main';main_trace=rows(base/'trace.jsonl');main_report=read(base/'report.json');main_times=read(base/'notice_timings.json')
    assert not main_report['failed_ids'] and len(main_trace)==200
    scores={'hybrid':read(base/'evaluation.json'),'optimized':read(ROOT/'optimized/evaluation.json'),'optimized_off':read(ROOT/'optimized_off/evaluation.json')}
    for name in ['six_off','six_on256','six_on1024_batch8']:scores[name]=composite(name,main_trace,main_report,main_times)
    scores['groups12']=read('analysis/prefix200/evaluation.json')
    scores['ungrouped']=read('analysis/compact200/ungrouped_on_h6/evaluation.json')
    # Artifact verification and request timing accounting.
    for name in ['main','optimized','optimized_off','six_off','six_on256','six_on1024_batch8']:
        folder=ROOT/name;report=read(folder/'report.json');trace=rows(folder/'trace.jsonl');rr=rows(folder/'request_timings.jsonl')
        assert not report['failed_ids'] and len(trace)==200
        ee=events(trace);assert len(ee)==len(rr)
        assert sum(e['input_tokens'] for e in ee)==sum(r['input_tokens'] for r in rr)
        assert sum(e['output_tokens'] for e in ee)==sum(r['output_tokens'] for r in rr)
        assert all(e['input_tokens']+e['max_output_tokens']+128<=32768 for e in ee)
        assert all(r['cached_tokens'] is not None and 0<=r['cached_tokens']<=r['input_tokens'] for r in rr)
        if name in ['main','optimized','optimized_off']:
            assert all([t['items'] for t in r['trace']]==GROUPS for r in trace)
            old_rules=rows('analysis/prefix200/rules.jsonl');rules=rows(folder/'rules.jsonl');assert old_rules==rules
        for r in trace:
            for t in r['trace']:
                expected=bool(set(t['items'])==set(THINK) and name not in ['six_off','optimized_off'])
                for e in [e for e in t['events'] if e['event']=='model']:
                    assert (e['thinking_budget'] is not None)==expected
                    if not expected:assert e['thinking_tokens']==0
                    if name in ['optimized','six_on256'] and expected:assert e['thinking_budget']<=256
    for name in ['main','optimized','optimized_off']:
        folder=ROOT/name
        with (folder/'submission.csv').open() as f:
            reader=csv.DictReader(f);assert reader.fieldnames==['id']+ITEMS+['e'+k[1:] for k in ITEMS]
            data=list(reader);assert len(data)==200 and all(len(r)==49 for r in data)
        assert read(folder/'evaluation.json')['evidence']['invalid']==0
        report=read(folder/'report.json')
        if 'recovery' in report:
            original=rows(folder/'first_pass/trace.jsonl');current=rows(folder/'trace.jsonl')
            for before,after in zip(original,current):
                assert before['record_id']==after['record_id']
                if not before['error']:assert before==after
            digest=report['recovery']['policy']['source_sha256']
            assert hashlib.sha256(Path('src/experiments/recover_hybrid200.py').read_bytes()).hexdigest()==digest
            assert hashlib.sha256((ROOT/'source/scripts/recover_hybrid200.py').read_bytes()).hexdigest()==digest
    manifest=read(ROOT/'manifest.json')
    for path,digest in manifest['source_sha256'].items():
        assert hashlib.sha256(source_path(path).read_bytes()).hexdigest()==digest,path
        assert hashlib.sha256((ROOT/'source'/path).read_bytes()).hexdigest()==digest,path
    batch_plan=read(ROOT/'batch_control_plan.json')
    assert hashlib.sha256(source_path(batch_plan['source']).read_bytes()).hexdigest()==batch_plan['sha256']
    assert hashlib.sha256((ROOT/'source'/batch_plan['source']).read_bytes()).hexdigest()==batch_plan['sha256']
    stage_stats={}
    for name in ['main','optimized','optimized_off']:
        rr=rows(ROOT/name/'request_timings.jsonl')
        for phase in sorted({r['phase'] for r in rr}):stage_stats[name+'_'+phase]=timing([r for r in rr if r['phase']==phase])
        stage_stats[name+'_instant_all']=timing([r for r in rr if r['phase'].startswith('instant')])
    for name in ['six_off','six_on256','six_on1024_batch8']:stage_stats[name]=timing(rows(ROOT/name/'request_timings.jsonl'))
    pairs=read(ROOT/'probes/pairs.json')
    cache={}
    for condition in ['cold','warm']:
        rr=[p['conditions'][condition] for p in pairs]
        cache[condition]={'pairs':len(rr),'total_wall_seconds':sum(r['seconds'] for r in rr),
                          'total_seed_seconds':sum(r['seed_seconds'] for r in rr),**timing(rr)}
    cache['prefill_reduction_fraction']=1-cache['warm']['prefill_request_seconds']/cache['cold']['prefill_request_seconds']
    cache['wall_reduction_fraction']=1-cache['warm']['total_wall_seconds']/cache['cold']['total_wall_seconds']
    cache['decode_reduction_fraction']=1-cache['warm']['decode_request_seconds']/cache['cold']['decode_request_seconds']
    cache['identical_output_pairs']=sum(p['conditions']['cold']['output_sha256']==p['conditions']['warm']['output_sha256'] for p in pairs)
    ordered=sorted(pairs,key=lambda p:p['input_tokens']);cache['by_input_length']=[]
    for i in range(0,len(ordered),8):
        subset=ordered[i:i+8]
        entry={'input_range':[min(p['input_tokens'] for p in subset),max(p['input_tokens'] for p in subset)],'pairs':len(subset)}
        for c in ['cold','warm']:
            entry[c+'_mean_prefill']=sum(p['conditions'][c]['prefill_seconds'] for p in subset)/len(subset)
            entry[c+'_mean_wall']=sum(p['conditions'][c]['seconds'] for p in subset)/len(subset)
        cache['by_input_length'].append(entry)
    cache['fixed_output_tokens']=128
    cache['scope']='Marginal reuse after another group seeds prefix; seed cost reported separately. 24 pairs from12 length-stratified notices; fixed-length unstructured decode diagnostic, not full pipeline speedup.'
    dump(ROOT/'timing_analysis.json',stage_stats);dump(ROOT/'cache_analysis.json',cache)
    feature_rows=[]
    mapped={name:{r['item']:r for r in score['per_item']} for name,score in scores.items()}
    for k in ITEMS:
        row={'feature':k,'name':mapped['hybrid'][k]['name'],'mode':'rule' if k in ['v2','v3'] else ('thinking' if k in THINK else 'instant')}
        for name in scores:
            for metric in ['f1','tp','fp','fn']:row[f'{name}_{metric}']=mapped[name][k][metric]
        row['hybrid_delta_vs_12']=row['hybrid_f1']-row['groups12_f1'];row['hybrid_delta_vs_ungrouped']=row['hybrid_f1']-row['ungrouped_f1']
        row['optimized_delta_vs_12']=row['optimized_f1']-row['groups12_f1'];row['optimized_delta_vs_ungrouped']=row['optimized_f1']-row['ungrouped_f1']
        feature_rows.append(row)
    with (ROOT/'per_feature.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(feature_rows[0]));w.writeheader();w.writerows(feature_rows)
    costs={'hybrid':main_report['prediction_seconds'],'optimized':read(ROOT/'optimized/report.json')['prediction_seconds'],'optimized_off':read(ROOT/'optimized_off/report.json')['prediction_seconds']}
    for name in ['six_off','six_on256','six_on1024_batch8']:costs[name]=read(ROOT/('composite_'+name)/'report.json')['prediction_seconds']
    costs['groups12']=scores['groups12']['runtime']['prediction_seconds'];costs['ungrouped']=scores['ungrouped']['runtime']['prediction_seconds']
    thinking_costs={'on1024_serial':sum(p['seconds'] for r in main_times for p in r['phases'] if p['phase']=='thinking')}
    for name in ['six_off','six_on256','six_on1024_batch8']:thinking_costs[name]=read(ROOT/name/'report.json')['seconds']
    opt_times=read(ROOT/'optimized/notice_timings.json')
    thinking_costs['on256_batch8']=sum(p['seconds'] for r in opt_times for p in r['phases'] if p['phase']=='thinking_batch')
    truth=read_csv('data/dev_labels.csv');control=read_csv(ROOT/'composite_six_off/submission.csv')
    uncertainty={name:bootstrap_delta(read_csv(path),control,truth) for name,path in [('on1024',base/'submission.csv'),('on256',ROOT/'composite_six_on256/submission.csv')]}
    uncertainty['on1024_batch8_vs_serial']=bootstrap_delta(read_csv(ROOT/'composite_six_on1024_batch8/submission.csv'),read_csv(base/'submission.csv'),truth)
    actual_off=read_csv(ROOT/'optimized_off/submission.csv')
    actual_on=read_csv(ROOT/'optimized/submission.csv')
    instant_changes=sum(actual_on[i][k]!=actual_off[i][k] for i in actual_off for k in ITEMS if k not in THINK and k not in ['v2','v3'])
    uncertainty['optimized_vs_optimized_off']=bootstrap_delta(actual_on,actual_off,truth)
    results={'scores':{n:{k:s[k] for k in ['macro_f1','micro_f1','false_positives','false_negatives','exact_match_records','evidence','searched_records','invalid_model_responses']} for n,s in scores.items()},
             'pipeline_seconds':costs,'six_feature_seconds':thinking_costs,'control_bootstrap':uncertainty,
             'instant_bits_changed_between_optimized_on_off':instant_changes,
             'six_feature_macro_f1':{n:sum(mapped[n][k]['f1'] for k in THINK)/6 for n in scores},
             'feature_rows':feature_rows,'caveats':['Previous group/mode comparisons are historical and confounded; new same-six controls reuse other predictions.',
                 'Composite times are summed-stage estimates; optimized and main times are measured end to end.',
                 'Batching can change greedy outputs numerically. Same dev200 used for earlier feature selection; not held-out proof.',
                 'Request prefill/decode are engine intervals, not pure GPU kernel times. Concurrent intervals must not be added as exclusive walltime.']}
    dump(ROOT/'comparison.json',results)
    dump(ROOT/'validation.json',{'passed':True,'records_per_variant':200,'features':24,'source_hashes_match':True,'rule_rows_identical':True,'request_metrics_available':True,'context_overflows':0,'scope':'Execution and artifact checks; does not assert all positive judgments have valid evidence' })
    write_report(results,stage_stats,cache,scores)
    print(json.dumps({k:v for k,v in results.items() if k!='feature_rows'},ensure_ascii=False,indent=2))


def write_report(result,stats,cache,scores):
    names={'hybrid':'5그룹 ON1024 순차','optimized':'5그룹 ON256·thinking batch8','optimized_off':'5그룹 모두OFF·캐시 batch8',
           'six_off':'5그룹 OFF 대조(판정 합성)','six_on256':'5그룹 ON256 순차(판정 합성)',
           'six_on1024_batch8':'5그룹 ON1024 batch8(판정 합성)',
           'groups12':'기존12그룹 OFF 캐싱','ungrouped':'기존 일괄 ON'}
    text=['# 5그룹 혼합 모드: dev200 측정','',
       'Gemma4 NVFP4 / RTX5090 / context32768 / source-first / 제공 법령 BGE RAG 선택 / 가설6 고정. 모든 판정은200건×24항목.',
       'Thinking 대상 v1,v5,v9,v14,v22,v24; 나머지16개는4개 instant 그룹; v2/v3는 기존 규칙. 기준 문구·원문 보존.','',
       '선택한6개 feature의 thinking 가설에는 근거가 있지만, 현재5그룹 구성 전체는 기존 전략의 대체안으로 채택하기 어렵다. 캐시는 prefill을 크게 줄였고, ON1024의 배치 처리는 성능을 거의 유지하며 처리량을 높였다. 반면 ON256 예산 축소와 instant 재그룹화는 성능 손실을 보였다.',
       '기존12그룹은 Macro 기준, 기존 일괄ON은 Micro 기준으로 유지할 가치가 있다. 이번 모두OFF는 로컬 시간 면에서 빠르지만 성능 하락이 커서 속도만으로 우수한 전략이라 판단하지 않는다.','',
       '그룹: OFF [v4,v6,v7,v8] / [v10,v11,v12,v13] / [v15,v16,v17,v18] / [v19,v20,v21,v23], ON [v1,v5,v9,v14,v22,v24].','',
       '## 1. Instant prefill/decode와 캐시','',
       'Prefill 구간=스케줄 시작→첫 토큰, decode 구간=첫→마지막 토큰. 대기는 별도. vLLM 엔진 지연이며 순수 CUDA 커널 시간이 아니다.',
       '아래 비율은 요청별 구간 시간을 합산한 비율이다. 동시 요청이 겹치므로 GPU walltime 비율로 해석하지 않는다. 겹침을 분리한 interval_union도 timing_analysis.json에 저장했다.','',
       '| 순차 기본안의 구간 | 요청 수 | 평균 prefill | 평균 decode | prefill 비율 | 캐시 토큰 비율 |',
       '|---|---:|---:|---:|---:|---:|']
    for key,label in [('main_instant_first','Instant 첫 그룹'),('main_instant_cached','Instant 나머지3그룹'),('main_instant_all','Instant 전체')]:
        s=stats[key];text.append(f'| {label} | {s["requests"]} | {s["mean_prefill_seconds"]:.4f}s | {s["mean_decode_seconds"]:.4f}s | {s["prefill_request_fraction"]:.1%} | {s["cached_fraction"]:.2%} |')
    union=stats['main_instant_all']['interval_union']
    text += ['', f'동시 요청의 겹침을 제거한 instant 엔진 구간: prefill만 {union["prefill_only_seconds"]:.2f}s, decode만 {union["decode_only_seconds"]:.2f}s, 두 구간 겹침 {union["overlap_seconds"]:.2f}s. 이것도 CUDA 커널별 프로파일이 아닌 엔진 타임스탬프 기준이다.']
    text += ['', '서로 다른 그룹의 첫 호출과 후속 호출만 비교하면 출력 길이·배치 차이가 섞인다. 아래는 입력 길이 분위수12건을2회씩 반복한 동일 프롬프트 대조이다. 출력128토큰 고정, cold/warm 순서 교대, 조건마다 캐시 초기화. Warm은 다른 instant 그룹으로 원문 prefix를 먼저 생성했다.','',
       '| 동일 입력·128토큰 출력 대조 | 평균 prefill | 평균 decode | 평균 전체 호출 | 캐시 적중 |', '|---|---:|---:|---:|---:|']
    for mode in ['cold','warm']:
        s=cache[mode];text.append(f'| {mode} | {s["mean_prefill_seconds"]:.4f}s | {s["mean_decode_seconds"]:.4f}s | {s["total_wall_seconds"]/s["pairs"]:.4f}s | {s["cached_fraction"]:.2%} |')
    text += ['', '| 입력 길이 구간 | Cold 전체 호출 | Warm 전체 호출 | 감소 |', '|---|---:|---:|---:|']
    for b in cache['by_input_length']:
        text.append(f'| {b["input_range"][0]}–{b["input_range"][1]}토큰 | {b["cold_mean_wall"]:.3f}s | {b["warm_mean_wall"]:.3f}s | {1-b["warm_mean_wall"]/b["cold_mean_wall"]:.1%} |')
    text += [f'\nPrefill 구간 {cache["prefill_reduction_fraction"]:.1%}, 전체 호출 {cache["wall_reduction_fraction"]:.1%} 감소. 출력 토큰열까지 동일한 쌍 {cache["identical_output_pairs"]}/24.',
       f'캐시를 만드는 seed 호출 비용은 warm 대상 호출 시간과 별도이며 평균 {cache["warm"]["total_seed_seconds"]/24:.4f}s였다. 첫 원문 계산 비용은 사라지지 않는다. 본 실험의 seed는 계측용이며 실제 파이프라인에서는 첫 instant 그룹의 유효 판정을 함께 얻는다.',
       'Cold/warm 출력 길이는 같지만 생성 토큰열은 달랐다. 따라서 동일 문장의 재생 속도가 아닌 동일 프롬프트·동일 길이 생성 대조이며, 캐시/배치 경로가 greedy 출력에도 영향을 줄 수 있다.',
       'ON과 OFF는 템플릿 시작 토큰이 달라 원문 prefix를 공유하지 못한다. 따라서 mixed 모드는 원문을 모드별로 처리한다.','',
       '## 2. Thinking 비용과 효율 개선','',
       '같은6개 feature·같은 판단 문구의 ON/OFF 대조. 단독 OFF는 원문 캐시가 미리 없는 조건이어서, 기존 instant 캐시를 사용할 수 있는 실제 all-OFF 파이프라인보다 비싸게 측정될 수 있다.','',
       '| 6개 feature 처리 방식 | 200건 해당 그룹 시간 | OFF 대비 |', '|---|---:|---:|']
    costs=result['six_feature_seconds'];off=costs['six_off']
    for key,label in [('six_off','OFF 순차'),('on1024_serial','ON1024 순차'),('six_on256','ON256 순차'),('six_on1024_batch8','ON1024 batch8'),('on256_batch8','ON256 batch8')]:
        text.append(f'| {label} | {costs[key]:.2f}s | {costs[key]/off:.2f}배 |')
    text += ['', 'ON256 batch8 시간은 실제 optimized 파이프라인의 thinking 구간 합이다. ON1024 batch8은 같은6항목 단독 측정이다. Optimized는 instant도 공고2건씩 첫 그룹을 병렬 처리한 뒤 후속6요청이 prefix를 재사용한다. 따라서 전체 최적화는 양쪽 모드의 배치와 thinking 예산을 함께 바꾼다.','',
       '| 파이프라인 | 200건 처리 시간 | Macro F1 | Micro F1 | FP/FN | 시간 성격 |', '|---|---:|---:|---:|---:|---|']
    for n in ['groups12','ungrouped','hybrid','six_off','six_on256','six_on1024_batch8','optimized','optimized_off']:
        s=scores[n];text.append(f'| {names[n]} | {result["pipeline_seconds"][n]/60:.2f}분 | {s["macro_f1"]:.5f} | {s["micro_f1"]:.5f} | {s["false_positives"]}/{s["false_negatives"]} | {"측정" if n in ["groups12","ungrouped","hybrid","optimized","optimized_off"] else "단계 합산 추정"} |')
    text += ['', '판정 합성 대조는 기본안의 instant16개·규칙2개를 그대로 두고, 실제로 다시 추론한6개만 교체했다. 따라서 나머지 feature의 재실행 변동이 ON/OFF 효과에 섞이지 않는다. 합성 파이프라인 시간은 기본안의 thinking 구간을 빼고 대조 구간을 더한 추정이며, 전체 재실행 실측과 구분한다.',
       '', '같은 instant 판정을 고정했을 때 thinking의 전체 Macro/Micro 변화(ON−OFF), 공고 단위 paired bootstrap95% 구간:', '']
    for n in ['on1024','on256']:
        ci=result['control_bootstrap'][n];variant='hybrid' if n=='on1024' else 'six_on256'
        text.append(f'- {n}: Macro {scores[variant]["macro_f1"]-scores["six_off"]["macro_f1"]:+.5f}, 구간 {ci["macro_delta_95ci"]}; Micro {scores[variant]["micro_f1"]-scores["six_off"]["micro_f1"]:+.5f}, 구간 {ci["micro_delta_95ci"]}.')
    text += ['', f'ON1024의 순차→batch8은 해당 그룹을 {costs["on1024_serial"]/costs["six_on1024_batch8"]:.2f}배 빠르게 처리했다. 나머지 판정을 고정한 전체 Macro 변화는 {scores["six_on1024_batch8"]["macro_f1"]-scores["hybrid"]["macro_f1"]:+.5f}이다. 반면 ON256 순차는 ON1024 대비 Macro {scores["six_on256"]["macro_f1"]-scores["hybrid"]["macro_f1"]:+.5f}: 예산 축소보다 공고 간 배치가 성능 보존에 유리했다.',
             f'기본안 전체 시간 중 thinking 구간은 {costs["on1024_serial"]/result["pipeline_seconds"]["hybrid"]:.1%}. 캐시가 빨라져도 긴 thinking decode 비용은 남는다. batch8은 처리량 개선이며 공고 한 건의 응답 지연이 같은 배율로 줄었다는 뜻은 아니다.']
    text += ['', f'실측 optimized ON/OFF의 instant16개 판정도 배치 구성이 달라 {result["instant_bits_changed_between_optimized_on_off"]}/3200개 변했다. 따라서 thinking만의 효과는 instant판정을 고정한 대조를 우선한다. 동일 dev200으로 이전 feature 선택도 했으므로 독립 검증이나 확정적 유의성 입증은 아니다.','',
       '## 3. 24개 feature 비교','',
       '| Feature | 항목명 | 이번 모드 | 기존12 OFF | 기존 일괄ON | 5그룹 ON1024 순차 | 5그룹 ON256 batch8 | 5그룹 모두OFF 최적화 |', '|---|---|---|---:|---:|---:|---:|---:|']
    for r in result['feature_rows']:
        text.append(f'| {r["feature"]} | {r["name"]} | {r["mode"]} | {r["groups12_f1"]:.3f} | {r["ungrouped_f1"]:.3f} | {r["hybrid_f1"]:.3f} | {r["optimized_f1"]:.3f} | {r["optimized_off_f1"]:.3f} |')
    text += ['', '표는 항목별 F1. 모든 구성의 TP/FP/FN/F1 및 기준 대비 변화는 per_feature.csv. 기존12/일괄은 과거 실행이므로 새로운 그룹화의 순수 인과 효과로 단정하지 않는다. v2/v3 규칙 결과는 동일하다. optimized_off는 같은5그룹 모두OFF이며, 공고2건의 첫 그룹을 처리한 후 나머지8요청이 원문 cache를 공유한다.',
       '', '## 실행·검증과 해석 범위','',
       '- main, optimized, optimized_off:200건 전체 실측. 나머지 대조군도 해당6항목200건 전체를 실제 추론했다. 실패를0으로 채우지 않았다. 검증 결과 validation.json.',
       '- 원본·판단 기준·고정 규칙 해시 및 실제 입력+출력+128<=32768 확인. 성공한 응답의 thinking 본문은 저장하지 않고 토큰 수만 보관했다.',
       '- Stats logging을 활성화한 이번 계측과 비활성화했던 이전 실행 사이에 소량의 계측 비용 차이가 있을 수 있다.',
       '- 대회75분 동료 제출을 이용한 초기화 보정 근사는 로컬200건 약533초를 잠정 처리 경계로 제시했으나, GPU/양자화/배치/캐시별 속도비 차이를 반영하지 못하므로 통과 보장이 아니다.',
       '- 재현: src/experiments/benchmark_hybrid200.py 다음 src/experiments/benchmark_hybrid_batch_controls.py; 출력 실패가 남으면 src/experiments/recover_hybrid200.py, 마지막 src/evaluation/summarize_hybrid200.py. 기존 결과 디렉터리 보존. source/와 manifest.json, batch_control_plan.json에 실행 코드·설정 동결.', '']
    text += ['## 이번 그룹화의 손익', '']
    for label,mode in [('Thinking6','thinking'),('Instant16','instant')]:
        delta=sum(r['hybrid_f1']-r['groups12_f1'] for r in result['feature_rows'] if r['mode']==mode)/24
        text.append(f'- 기존12 대비 {label}의 전체 Macro 변화 기여분: {delta:+.5f}.')

    for variant in ['hybrid','optimized','optimized_off']:
        for baseline in ['groups12','ungrouped']:
            better=[r['feature'] for r in result['feature_rows'] if r[variant+'_f1']>r[baseline+'_f1']+1e-12]
            worse=[r['feature'] for r in result['feature_rows'] if r[variant+'_f1']<r[baseline+'_f1']-1e-12]
            text.append(f'- {names[variant]} vs {names[baseline]}: 개선 {len(better)}개({",".join(better)}), 악화 {len(worse)}개({",".join(worse)}), 동일 {24-len(better)-len(worse)}개.')
    text += ['', '현재5그룹의 순차 ON1024는 선택한6항목에 thinking을 쓰는 효과를 보여주지만, 기존12그룹을 전체 Macro로 넘지 못했다. 특히 instant v8의 FP 증가와 v20의 TP 소실이 문제다. 이 결과만으로 법령 기준을 다시 조정하거나 dev 라벨에 맞춰 규칙을 추가하지 않았다.',
             '후속 후보(미실험): v8과 v20을 분리하는 재구성으로 총7그룹 이내 유지(그룹 내 간섭이 원인인지는 미검증); thinking 작업을 묶음 전체 완료 대기 없이 빈 실행 슬롯에 연속 공급; OFF의 모호한 사례만 thinking 재검토하는 라우팅. 라우팅 기준과 새 그룹은 별도 검증 세트에서 시간·재현율 손실을 검증해야 한다.', '']
    repair=read(ROOT/'optimized_off/report.json').get('recovery')
    if repair:
        text += [f'모두OFF의 첫 실행에서 실패한 그룹만 동일 프롬프트·OFF 모드로 복구했다. 복구 추론 {repair["prediction_seconds"]:.2f}s는 표의 처리 시간에 포함했다. 실험상 별도 모델 초기화 {repair["separate_process_load_seconds"]:.2f}s는 추가로 들었으며 total_seconds에 포함된다. 최초 결과는 optimized_off/first_pass에 보존했고, 정상 공고는 변경하지 않았다.', '']
    text += ['## 근거 출력 및 비교의 한계', '', '| 실측 구성 | 원문 일치 근거 | 근거가 필요한 양성 중 누락 | 실제 RAG 검색 공고 |', '|---|---:|---:|---:|']
    for n in ['groups12','ungrouped','hybrid','optimized','optimized_off']:
        s=scores[n];e=s['evidence']
        text.append(f'| {names[n]} | {e["nonempty"]} | {e["positive_nonabsence_missing"]} | {s["searched_records"]} |')
    text += ['', 'F1은 이진 라벨 점수이며 근거 완성도를 포함하지 않는다. 원문과 불일치한 근거는 기존 후처리가 제거했으나, 해당 양성 라벨은 유지했다. 실행 검증 통과가 모든 근거의 완성을 뜻하지 않는다.',
             '기존12그룹과 이번5그룹에서 v10/v11/v12/v13은 동일한 그룹·기준인데도 800개 판정 중27개가 달랐다(v10 18개, v11 9개). 따라서 과거 실행 대비 변화에는 그룹 구성 이외의 스케줄·수치 경로 변화도 섞여 있다. unchanged_group_audit.json 참조.', '']
    write_report(ROOT/'comparison.md', '\n'.join(text))
    # Fix generic evaluator descriptions that assume a single mode/old system prompt.
    for folder in [ROOT/'main',ROOT/'optimized',ROOT/'optimized_off']+[ROOT/('composite_'+n) for n in ['six_off','six_on256','six_on1024_batch8']]:
        path=report_path(folder/'evaluation.md');s=path.read_text()
        s=s.replace('실제 시스템 프롬프트는 system_prompt.txt 참조.','그룹별 실제 템플릿은 ../prompt_*.txt 참조.')
        s=s.replace('대화당 6항목.','대화당 최대6항목; v2/v3는 고정 규칙.')
        note='\n모드별 시간·판정 합성 여부·실제 재현 명령은 ../comparison.md 참조.\n'
        if note not in s:s+=note
        path.write_text(s)

if __name__=='__main__':main()
