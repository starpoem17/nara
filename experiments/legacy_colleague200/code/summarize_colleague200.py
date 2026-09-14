"""Score faithful ZIP reproduction; audit dev few-shot overlap and calibrate time."""

if __name__ == "__main__":
    raise SystemExit("Archived code: create a fresh registered run; see docs/operations.md.")

import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import unicodedata
from nara.evaluation.reporting import write_report
from sklearn.metrics import f1_score,precision_score,recall_score
from nara.evaluation.evaluate_dev import read_csv,ITEMS

OUT=Path('analysis/colleague200')

def read(p):return json.loads(Path(p).read_text())
def rows(p):return [json.loads(s) for s in Path(p).read_text().splitlines()]

def main():
    report=read(OUT/'report.json')
    pred=read_csv(OUT/'submission.csv');truth=read_csv('data/dev_labels.csv')
    records={r['id']:r for r in rows('data/dev.jsonl')}
    prompts=rows(OUT/'prompts.jsonl');responses=rows(OUT/'responses.jsonl')
    assert len(pred)==200 and set(pred)==set(truth)==set(records)=={p['id'] for p in prompts}
    spec=importlib.util.spec_from_file_location('colleague_audit',OUT/'original/src/cli.py')
    stock=importlib.util.module_from_spec(spec);spec.loader.exec_module(stock)
    by_id={r['id']:r for r in responses}
    parsing=[]
    for i in pred:
        text=by_id.get(i,{}).get('response','')
        parsed,missing=stock.parse_judgment(text)
        final=stock.postprocess(parsed,stock.normalize(records[i]))
        assert stock.to_row(i,final)=={'id':i,**{k:int(pred[i][k]) for k in ITEMS},**{f'e{j}':pred[i][f'e{j}'] for j in range(1,25)}}
        parsing.append({'id':i,'missing_items':missing,'finish_reason':by_id.get(i,{}).get('finish_reason')})
    def score(ids):
        y=[[int(truth[i][k]) for k in ITEMS] for i in ids]
        p=[[int(pred[i][k]) for k in ITEMS] for i in ids]
        per_item=[]
        for j,k in enumerate(ITEMS):
            a=[r[j] for r in y];b=[r[j] for r in p]
            tp=sum(t==1 and v==1 for t,v in zip(a,b));fp=sum(t==0 and v==1 for t,v in zip(a,b));fn=sum(t==1 and v==0 for t,v in zip(a,b))
            per_item.append({'item':k,'support':sum(a),'predicted_positive':sum(b),'tp':tp,'fp':fp,'fn':fn,'f1':f1_score(a,b,zero_division=0)})
        return {'records':len(ids),'judgments':len(ids)*24,'macro_f1':f1_score(y,p,average='macro',zero_division=0),
                'micro_f1':f1_score(y,p,average='micro',zero_division=0),
                'macro_precision':precision_score(y,p,average='macro',zero_division=0),
                'macro_recall':recall_score(y,p,average='macro',zero_division=0),
                'exact_match_records':sum(a==b for a,b in zip(y,p)),
                'false_positives':sum(r['fp'] for r in per_item),'false_negatives':sum(r['fn'] for r in per_item),'per_item':per_item}
    evaluation=score(list(records))
    evidence={'nonempty':0,'invalid_single_document':0,'positive_nonabsence_missing':0}
    for i in records:
        for j,k in enumerate(ITEMS,1):
            e=pred[i][f'e{j}'];hit=pred[i][k]=='1'
            evidence['positive_nonabsence_missing']+=int(hit and k not in stock.ABSENCE and not e)
            if e:
                evidence['nonempty']+=1
                evidence['invalid_single_document']+=int(not hit or k in stock.ABSENCE or len(e)>500 or e.startswith(('=','+','@')) or not any(e in unicodedata.normalize('NFC',d['text']) for d in records[i]['docs']))
    evaluation['evidence']=evidence
    evaluation['missing_items_filled_with_zero']=sum(len(r['missing_items']) for r in parsing)
    evaluation['fully_invalid_records']=sum(len(r['missing_items'])==24 for r in parsing)
    assert evaluation['missing_items_filled_with_zero']==report['메운_항목수']
    assert evaluation['fully_invalid_records']==200-report['유효JSON']
    assert abs(evaluation['macro_f1']-sum(r['f1'] for r in evaluation['per_item'])/24)<1e-12
    assert sum(r['input_tokens'] for r in responses)==report['input_tokens']
    assert sum(r['output_tokens'] for r in responses)==report['output_tokens']
    # Exact rendering used by the original casebook function; inspect final prompts after fitting.
    book=read(OUT/'original/model/casebook.json')['items'];line_map={};all_ids=set()
    for k,item in book.items():
        for kind,label in [('positive',1),('negative',0)]:
            all_ids.update(e['id'] for e in item[kind])
            ex=item[kind][0];snippet=str(ex.get('snippet') or '').replace('\r','').replace('\n',' ').strip()[:240]
            meta=ex.get('meta') or {}
            info=', '.join(str(meta.get(x)) for x in ('법령','업무','계약방법','추정가격') if meta.get(x) not in (None,''))
            line=f"- {k} {'위반' if label else '정상'} 예시"+(f' ({info})' if info else '')+f": {snippet or '(문구 없음)'}"
            line_map.setdefault(line,[]).append({'item':k,'label':label,'source_id':ex['id']})
    overlap=[];used_ids=set()
    for p in prompts:
        user=p['messages'][1]['content']
        fewshot=user.split('[dev 정답 사례 참고 — 근거는 현재 공고에서 다시 찾을 것]\n',1)[1].split('\n\n[문서]',1)[0]
        examples=[]
        for line in fewshot.splitlines():
            assert line in line_map, line
            examples.extend(line_map[line])
        used_ids.update(e['source_id'] for e in examples)
        overlap.append({'id':p['id'],'selected_examples':examples,'self_examples':[e for e in examples if e['source_id']==p['id']]})
    self_ids=[r['id'] for r in overlap if r['self_examples']]
    audit={'casebook_source_notice_count':len(all_ids),'actually_used_source_notice_count':len(used_ids),
           'self_example_notice_count':len(self_ids),'self_example_ids':self_ids,
           'self_example_pairs':sum(len(r['self_examples']) for r in overlap),
           'casebook_unlisted_subset_diagnostic':score([i for i in records if i not in all_ids]),
           'caveat':'Casebook was built from this dev200. Full score is an in-development reproduction, not independent held-out performance. Excluding listed IDs does not undo dev-driven prompt design.'}
    assert report['stage_times']['law_articles']>0
    assert len(responses)==200 and all(r['input_tokens']+1536<=16384 for r in responses)
    assert all(r['id']==p['id'] for r,p in zip(responses,prompts))
    token_deltas=[r['input_tokens']-p['counted_tokens'] for r,p in zip(responses,prompts)]
    evaluation['actual_minus_counted_input_tokens']={str(d):token_deltas.count(d) for d in sorted(set(token_deltas))}
    assert report['engine']['default_template_matches_thinking_off']
    for f in read(OUT/'archive_manifest.json')['files']:
        assert hashlib.sha256((OUT/'original'/f['local_path']).read_bytes()).hexdigest()==f['sha256']
    local_total=report['run_seconds_precise'];local_inference=report['model_chat_seconds']
    # Direct relative calibration requires no assumption about the hidden evaluation count.
    anchor=75.0;limit=120.0
    adjusted=local_total-report['stage_times']['runner_load_seconds']-report['stage_times']['law_index_seconds']
    calibration={'reported_server_minutes':anchor,'server_limit_minutes':limit,'anchor_source':'user-reported successful submission',
                 'colleague_local200_total_seconds':local_total,'colleague_local200_inference_seconds':local_inference,
                 'local200_total_threshold_seconds':local_total*limit/anchor,
                 'colleague_local200_excluding_measured_load_and_index_seconds':adjusted,
                 'local200_processing_threshold_seconds':adjusted*limit/anchor,
                 'adjustment_scope':'Subtract measured local model loading and index construction; retain per-record prompt preparation. Import and teardown overhead were not separately timed. Assume server startup is small relative to75 minutes; this is not a calibrated stage-by-stage hardware model.',
                 'local200_inference_threshold_seconds':local_inference*limit/anchor,
                 'heuristic_formula':'server_minutes(candidate) = 75 * local200_seconds(candidate) / local200_seconds(colleague)',
                 'scope':'One-anchor heuristic. Total-time ratio includes fixed startup costs; inference-only ratio ignores unknown server startup share. Both assume comparable data and hardware scaling; neither guarantees passing.',
                 'our_candidates':[]}
    for name,path in [('12그룹 OFF + KV 캐싱 + H6','analysis/prefix200/report.json'),('일괄 ON + H6','analysis/compact200/ungrouped_on_h6/report.json')]:
        r=read(path);total=r['total_seconds'];inference=r['prediction_seconds']
        calibration['our_candidates'].append({'name':name,'local_total_seconds':total,'local_inference_seconds':inference,
            'estimated_server_minutes_total_ratio':anchor*total/local_total,
            'estimated_server_minutes_inference_ratio':anchor*inference/local_inference,
            'estimated_server_minutes_adjusted_ratio':anchor*inference/adjusted})
    for filename,obj in [('evaluation.json',evaluation),('casebook_audit.json',audit),('calibration.json',calibration),('parsing_audit.json',parsing),('selected_examples.json',overlap)]:
        (OUT/filename).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
    errors=[{'id':i,'item':k,'gold':truth[i][k],'prediction':pred[i][k],'gold_evidence':truth[i]['e'+k[1:]],'predicted_evidence':pred[i]['e'+k[1:]]} for i in records for k in ITEMS if truth[i][k]!=pred[i][k]]
    with (OUT/'errors.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(errors[0]) if errors else ['id','item','gold','prediction','gold_evidence','predicted_evidence']);w.writeheader();w.writerows(errors)
    summary=['# 동료 제출물: 로컬 dev200 재현','',
        '원본: submit_today_fewshot_rag.zip. 대회 75분은 사용자 제공 정보이며 서버 로그는 제공되지 않았다.','',
        '| 측정 | 결과 |','|---|---:|',
        f'| 모델 로드(원본 계측) | {report["stage_times"]["runner_load_seconds"]:.2f}초 |',
        f'| 법령 BM25 색인 | {report["stage_times"]["law_index_seconds"]:.2f}초 / {report["stage_times"]["law_articles"]}개 조문 |',
        f'| 모델 추론 | {local_inference:.2f}초 ({local_inference/60:.2f}분) |',
        f'| 원본 run 전체 | {local_total:.2f}초 ({local_total/60:.2f}분) |',
        f'| Macro F1 | {evaluation["macro_f1"]:.6f} |',f'| Micro F1 | {evaluation["micro_f1"]:.6f} |',
        f'| FP / FN | {evaluation["false_positives"]} / {evaluation["false_negatives"]} |',
        f'| 24항목 모두 정답 | {evaluation["exact_match_records"]}/200 |',
        f'| 전부 파싱 실패 / 0으로 채운 항목 | {evaluation["fully_invalid_records"]} / {evaluation["missing_items_filled_with_zero"]} |','',
        '## 실행 조건','',
        '- 원본 src/cli.py와 casebook.json 바이트 보존. Windows ZIP 경로 구분자만 로컬 디렉터리로 정규화했다.',
        '- 원본 16384 문맥, 출력1536, seed20260826, chunk128, GPU 메모리0.92, 문서 초기12000자 및 축소 로직, 24항목 일괄, 후처리 모두 유지. 가설6/그룹화 미적용.',
        '- 로컬 RTX5090의 기존 Gemma4 NVFP4 사용: INT8 강제 설정을 생략하여 체크포인트 양자화 자동 인식, MoE backend=cutlass. 나머지 엔진 기본값 유지. 대회 L40S/INT8와 동일 조건은 아니다.',
        f'- 실제 엔진 설정: {json.dumps(report["engine"]["resolved"],ensure_ascii=False)}. 기본 chat template는 thinking OFF와 일치.',
        f'- 요청 {len(responses)}건, 입력 {report["input_tokens"]:,}토큰, 출력 {report["output_tokens"]:,}토큰. 최대 실제 입력 {max(r["input_tokens"] for r in responses):,}토큰. 모든 요청 16K 예산 내.',
        '- 실제 입력은 원본 토큰 추정보다 모든 공고에서1토큰 많았다. 실제 요청 기준으로도 전부16K 내였다.',
        '- 별도 모델 warmup 없이 최초 실행의 초기화·컴파일 비용 포함. 원본 모델 로드 계측 바깥의 vLLM import 등도 run 전체에는 포함된다. 계측 파일 직렬화는 전체 시간에서 제외.',
        '', '## 성능 해석','',
        f'- 사례집 출처 공고 {len(all_ids)}건 모두 평가 dev에 포함. 실제 프롬프트에 사용된 사례 출처 {len(used_ids)}건. 자기 공고의 라벨 사례가 자기 프롬프트에 들어간 공고 {len(self_ids)}건({audit["self_example_pairs"]}항목 사례).',
        '- 따라서 전체 F1은 제출물 개발 데이터 재현 성능이다. 독립된 검증 점수로 기존 실험과 우열을 확정할 수 없다. 사례 제거 등 모델 입력 변경은 하지 않았다.',
        f'- 근거 검사: {json.dumps(evidence,ensure_ascii=False)}. 원본은 문서들을 줄바꿈으로 연결해 인용을 검사하며, 이번 감사에서는 개별 문서 일치도 확인했다.',
        '', '## 75분 실행을 이용한 시간 기준','',
        f'- 단순 비례식: 대회 예상 시간 = 75분 × (후보의 로컬200건 시간 ÷ 동료의 로컬200건 시간).',
        f'- 75분을 대회 전체 실행 시간으로 가정한 단순 경계는 로컬 전체 시간의 1.6배, **{calibration["local200_total_threshold_seconds"]/60:.2f}분**이다. 하지만 200건에서는 고정 초기화 비용이 과대 반영된다.',
        f'- 측정된 모델 로드·법령 색인 시간을 제외하고 건별 프롬프트 준비는 포함하면 동료 로컬 처리 시간은 {adjusted:.2f}초. 1.6배 경계는 **{calibration["local200_processing_threshold_seconds"]/60:.2f}분**이다. 서버 초기화가 전체75분 중 작고, 작업별 장비 속도비가 같다는 근사다. import·종료 비용은 별도 측정하지 못했다.',
        f'- GPU 추론 시간만 비교하면 경계는 {calibration["local200_inference_threshold_seconds"]/60:.2f}분이지만 BM25/프롬프트 준비 비용을 빠뜨리므로 전체 실행75분의 환산에는 적절하지 않다. 참고 수치로만 보관한다.',
        '', '| 우리 후보 | 로컬200 추론 | 대회 추정: 전체 시간 비율 | 대회 추정: 초기화 보정 근사 |', '|---|---:|---:|---:|']
    for c in calibration['our_candidates']:
        summary.append(f'| {c["name"]} | {c["local_inference_seconds"]/60:.2f}분 | {c["estimated_server_minutes_total_ratio"]:.1f}분 | {c["estimated_server_minutes_adjusted_ratio"]:.1f}분 |')
    summary += ['', '- 이는 한 번의 제출을 기준으로 한 경험적 환산이다. 평가 공고 수를 추정해 넣지 않았다. 200건과 실제 평가의 길이·출력 분포, 고정 로딩 비용, NVFP4/INT8, batch와 prefix cache에 따른 장비별 속도 차이를 분리하지 못한다.',
        '- 특히 KV 캐싱 그룹과 일괄 few-shot은 입력 처리·출력 생성 비중이 달라 환산 계수가 같다고 보장할 수 없다. 경계값 바로 아래를 안전한 통과 시간으로 해석하지 않는다.',
        '', '재현: `uv run --locked python src/experiments/benchmark_colleague200.py` (기존 출력이 있으면 중단). 평가: `uv run --locked python src/evaluation/summarize_colleague200.py`. 실제 프롬프트·응답·캐시 계측·사례 중복은 같은 디렉터리 JSON 파일 참조.', '']
    write_report(OUT/'comparison.md', '\n'.join(summary))
    (OUT/'validation.json').write_text(json.dumps({'passed':True,'records':200,'judgments':4800,'original_hashes_match':True,'csv_matches_original_postprocess':True,'prompt_ids_match_actual':True,'actual_minus_counted_tokens':evaluation['actual_minus_counted_input_tokens'],'context_overflows':0,'law_index_active':True},indent=2)+'\n')
    print(json.dumps({'score':{k:v for k,v in evaluation.items() if k!='per_item'},'overlap':{k:v for k,v in audit.items() if k!='casebook_unlisted_subset_diagnostic'},'calibration':calibration},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
