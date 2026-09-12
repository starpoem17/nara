"""Score frozen complete Gemma outputs; label access is confined to this stage."""
import csv, hashlib, json
from pathlib import Path
import numpy as np
from nara.inference.predictor import Predictor, Limits
from nara.records import read_records
from nara.evaluation.reporting import write_report

OUT=Path('analysis/ljm_static_law_v2_v8_20260912')
KEYS=[f'v{i}' for i in range(2,9)]

def loadl(path): return [json.loads(line) for line in path.read_text().splitlines()]
def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def writecsv(path,rows):
    with path.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def metrics(truth,pred,keys):
    rows=[]
    for k in keys:
        tp=sum(truth[i][k]==1 and pred[i][k]==1 for i in truth)
        fp=sum(truth[i][k]==0 and pred[i][k]==1 for i in truth)
        fn=sum(truth[i][k]==1 and pred[i][k]==0 for i in truth)
        rows.append({'item':k,'support':tp+fn,'predicted_positive':tp+fp,'tp':tp,'fp':fp,'fn':fn,'tn':len(truth)-tp-fp-fn,
                     'precision':tp/(tp+fp) if tp+fp else 0,'recall':tp/(tp+fn) if tp+fn else 0,'f1':2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0})
    tp=sum(r['tp'] for r in rows);fp=sum(r['fp'] for r in rows);fn=sum(r['fn'] for r in rows)
    return {'per_item':rows,'macro_f1':sum(r['f1'] for r in rows)/len(rows),'micro_f1':2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0,'tp':tp,'fp':fp,'fn':fn}

def table(rows):
    text=['| 항목 | 정답 양성 | 예측 양성 | 정밀도 | 재현율 | F1 | FP | FN |','|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in rows:text.append(f"| {r['item']} | {r['support']} | {r['predicted_positive']} | {r['precision']:.3f} | {r['recall']:.3f} | {r['f1']:.3f} | {r['fp']} | {r['fn']} |")
    return '\n'.join(text)

def main():
    runtime=json.loads((OUT/'runtime.json').read_text())
    assert all(not x for x in runtime['failures'].values()),'Resolve inference failures before scoring'
    records={r['id']:r for r in read_records('data/dev.jsonl')}
    fulltable=json.loads(Path('data/항목표.json').read_text())['항목'];itemtable={k:fulltable[k] for k in KEYS}
    schema=json.loads(Path('data/정답스키마_디코딩.json').read_text())['properties']['판정']
    schema['properties']={k:schema['properties'][k] for k in KEYS};schema['required']=KEYS
    checker=Predictor(None,None,itemtable,schema,limits=Limits(search_rounds=0,output_tokens=512))
    predictions={};traces={};audits={}
    for arm in ['baseline','candidate']:
        rows=loadl(OUT/arm/'trace.jsonl'); assert len(rows)==200 and {r['record_id'] for r in rows}==set(records)
        traces[arm]={r['record_id']:r for r in rows};predictions[arm]={}
        events=[];quotes=0;empty=0;csvrows=[]
        for row in rows:
            rid=row['record_id'];assert row['error'] is None and set(row['judgments'])==set(KEYS)
            replay={}
            assert len(row['trace'])==7
            for task in row['trace']:
                replay.update(checker.replay_judgments(records[rid],task));events.extend(task['events'])
            assert replay==row['judgments']
            predictions[arm][rid]={k:int(row['judgments'][k]['위반여부']) for k in KEYS}
            line={'id':rid,**predictions[arm][rid]}
            for k in KEYS:
                quote=row['judgments'][k]['근거문구'];line['e'+k[1:]]=quote or ''
                if predictions[arm][rid][k]:
                    if quote:
                        assert len(quote)<=500 and any(quote in d['text'] for d in records[rid]['docs']);quotes+=1
                    else:empty+=1
            csvrows.append(line)
        writecsv(OUT/arm/'predictions_v2_v8.csv',csvrows)
        models=[e for e in events if e['event']=='model']
        audits[arm]={'records':200,'judgments':1400,'model_calls':len(models),'searches':sum(e['event']=='search' for e in events),
                     'invalid_responses':sum(e['event']=='invalid_response' for e in events),
                     'length_stops':sum(e['finish_reason']=='length' for e in models),
                     'input_tokens':sum(e['input_tokens'] for e in models),'output_tokens':sum(e['output_tokens'] for e in models),
                     'thinking_tokens':sum(e.get('thinking_tokens',0) for e in models),
                     'positive_quotes_exact':quotes,'positive_quotes_missing':empty,
                     'quotes_dropped':sum(len(e['evidence_dropped']) for e in events if e['event']=='final')}
        assert audits[arm]['searches']==0
    # Open labels only after both complete arms pass trace and evidence replay.
    gold={r['id']:r for r in csv.DictReader(Path('data/dev_labels.csv').open(encoding='utf-8'))}
    assert set(gold)==set(records)
    truth={i:{k:int(gold[i][k]) for k in KEYS} for i in records}
    scores={a:metrics(truth,predictions[a],KEYS) for a in predictions}
    originals=loadl(OUT/'original/candidate_flags.jsonl')
    scores['scan']=metrics(truth,{r['id']:{k:int(v) for k,v in r['scan'].items()} for r in originals},KEYS)
    scores['extractor']=metrics(truth,{r['id']:{k:int(v) for k,v in r['extractor'].items()} for r in originals},KEYS[2:6])
    errors=[];changes=[];orig_errors=[]
    for rid in records:
        for key in KEYS:
            target=truth[rid][key];a=predictions['baseline'][rid][key];b=predictions['candidate'][rid][key]
            common={'id':rid,'item':key,'name':fulltable[key]['항목명'],'gold':target,'gold_evidence':gold[rid]['e'+key[1:]],
                    'baseline':a,'candidate':b,'baseline_evidence':traces['baseline'][rid]['judgments'][key]['근거문구'] or '',
                    'candidate_evidence':traces['candidate'][rid]['judgments'][key]['근거문구'] or ''}
            if a!=target or b!=target:errors.append(common)
            if a!=b:changes.append({**common,'transition':'corrected' if b==target else 'regressed'})
    for row in originals:
        for method in ['scan','extractor']:
            for key,value in row[method].items():
                if int(value)!=truth[row['id']][key]:orig_errors.append({'method':method,'id':row['id'],'item':key,'error':'FP' if value else 'FN','gold_evidence':gold[row['id']]['e'+key[1:]]})
    writecsv(OUT/'errors.csv',errors)
    if changes:writecsv(OUT/'changes.csv',changes)
    writecsv(OUT/'original/errors.csv',orig_errors)
    # Paired notice bootstrap of fixed outputs, not model-run reproducibility.
    ids=list(records); y=np.array([[truth[i][k] for k in KEYS] for i in ids]); a=np.array([[predictions['baseline'][i][k] for k in KEYS] for i in ids]);b=np.array([[predictions['candidate'][i][k] for k in KEYS] for i in ids])
    def macro(y,p):
        tp=((y==1)&(p==1)).sum(0);fp=((y==0)&(p==1)).sum(0);fn=((y==1)&(p==0)).sum(0);den=2*tp+fp+fn
        return np.divide(2*tp,den,out=np.zeros(7,dtype=float),where=den!=0).mean()
    rng=np.random.default_rng(20260912);diffs=[]
    for _ in range(2000):
        ix=rng.integers(0,200,200);diffs.append(macro(y[ix],b[ix])-macro(y[ix],a[ix]))
    audit=json.loads((OUT/'extraction_audit.json').read_text())
    duplicate_ids={r['id'] for r in audit['v7_single_unique_token_candidates']}
    duplicate_truth={i:truth[i] for i in duplicate_ids}
    duplicate_impact={a:metrics(duplicate_truth,{i:predictions[a][i] for i in duplicate_ids},['v7']) for a in predictions}
    dump(OUT/'duplicate_v7_impact.json',{'records':len(duplicate_ids),'scores':duplicate_impact,'positive_gold_ids':[i for i in duplicate_ids if truth[i]['v7']]})
    comparison={'changed':len(changes),'corrected':sum(r['transition']=='corrected' for r in changes),'regressed':sum(r['transition']=='regressed' for r in changes),
                'macro_f1_delta':scores['candidate']['macro_f1']-scores['baseline']['macro_f1'],
                'paired_notice_bootstrap_95ci':np.quantile(diffs,[.025,.975]).tolist(),'bootstrap_repetitions':2000,'bootstrap_seed':20260912}
    result={'scores':scores,'comparison':comparison,'audits':audits,'runtime':runtime,'labels_sha256':hashlib.sha256(Path('data/dev_labels.csv').read_bytes()).hexdigest()}
    dump(OUT/'evaluation.json',result)
    lines=['# LJM v2~v8: 고정 법령 프롬프트 + Gemma 비교 실험','',
           '## 실험 조건','',
           '- dev 200건, v2~v8의 7개 항목(조건별 1,400판정). 기존 21그룹의 단독 항목 방식을 사용하며 v2·v3도 이번 실험에서는 규칙 대체 없이 Gemma가 판정한다.',
           '- 기준: 전체 공고 원문·메타데이터 + 해당 항목의 배포 법령 요약·발췌. 가설: 동일 입력 + 원본 LJM 코드의 후보 플래그·추출 문맥.',
           '- 검색 없음. 로컬 Gemma 4 26B A4B NVFP4, thinking OFF, temperature 0, seed 0, 출력 한도 512, 문맥 32768, 최대 동시 요청 8.',
           '- 공고별 두 조건의 실행 순서를 번갈아 적용. 각 조건 시작 시 prefix cache 초기화, 첫 항목 처리 뒤 나머지 6개 처리. 실제 21그룹 전체 실행의 속도와 직접 비교할 수 없다.',
           '- 원본 LJM 코드는 수정하지 않음. 스캐너의 입력·출력 위치만 실행 시 변경. 추출 문맥은 중복 제거 후 합계 1,600자까지 표시(문맥당 최대 500자). 원본 추출 결과는 별도 저장. 공고 원문은 자르지 않음.',
           '- 정답 라벨은 모든 추론을 완료하고 로그 검증을 통과한 뒤 채점 단계에서만 읽음. 이번 결과를 보고 프롬프트를 튜닝하거나 재실험하지 않음. 기존 코드의 과거 dev 활용 여부는 통제하지 못함.','',
           '## 두 조건 결과','',
           f"7항목 Macro F1: **{scores['baseline']['macro_f1']:.4f} → {scores['candidate']['macro_f1']:.4f}** (차이 {comparison['macro_f1_delta']:+.4f}).",'',
           '| 항목 | 정답 양성 | 기준 F1 | 가설 F1 | 기준 FP/FN | 가설 FP/FN |','|---|---:|---:|---:|---:|---:|']
    for x,z in zip(scores['baseline']['per_item'],scores['candidate']['per_item']):lines.append(f"| {x['item']} | {x['support']} | {x['f1']:.3f} | {z['f1']:.3f} | {x['fp']}/{x['fn']} | {z['fp']}/{z['fn']} |")
    lines+=['',f"바뀐 판정 {comparison['changed']}개: 정답으로 수정 {comparison['corrected']}개, 오답으로 변경 {comparison['regressed']}개.",
            f"고정 출력에 대한 공고 단위 paired bootstrap 95% 구간(Macro F1 차이): {comparison['paired_notice_bootstrap_95ci']}. 2,000회, seed 20260912. 실행 반복 변동성에 대한 구간은 아니다.",'',
            '## 기준 조건 상세','',table(scores['baseline']['per_item']),'','## 가설 조건 상세','',table(scores['candidate']['per_item']),'',
            '## 원본 후보 추출 성능','',
            '후보 플래그를 양성으로 간주해 계산한 수치이며 최종 법령 판정 성능과 구별해야 한다. 특히 넓은 후보 추출기의 정밀도 저하는 설계 목적과 함께 해석한다.','',
            '### scan_candidates.py (v2~v8)','',table(scores['scan']['per_item']),'',
            '### v4_v7_candidate_extractor.py (v4~v7)','',table(scores['extractor']['per_item']),'',
            '## 추출 코드 구조 점검','',
            f"별도 추출기의 v7 후보 중 {len(duplicate_ids)}건은 인접 표현 없이 동일 지역 토큰 하나가 반복된 경우다. 원문에 지역 하나만 있는 합성 예제에서도 v7 후보가 되는 것을 재현했다. 이 {len(duplicate_ids)}건의 정답 v7 양성은 {sum(truth[i]['v7'] for i in duplicate_ids)}건이며, 최종 v7 오탐은 기준 {duplicate_impact['baseline']['fp']}건 → 가설 {duplicate_impact['candidate']['fp']}건이다. 이 집계는 해당 문맥 구조와 판정의 연관을 보여주며, 개별 프롬프트 요소의 단독 인과효과를 증명하지 않는다.",
            '- 금액 파서는 「최근 3년간 2025년 수행실적 2건, 1억원 이상」에서 3·2025·2도 금액으로 추출한다. 이번 모델 힌트에는 이 파싱 금액 배열을 직접 넣지 않고 문맥과 후보 플래그를 제공했으므로, 숫자 파싱 자체의 최종 판정 영향은 분리 검증하지 않았다.',
            '- 원본 gemma_prompt()는 검색을 요구하는 문자열 생성 함수이므로 그대로 호출하지 않았다. 실제 Gemma 연결에는 기존 구조화 판정 인터페이스와 이번에 고정한 법령 카드를 사용했다.', '',
            '## 해석상 고정한 선택과 한계','',
            '- v3: 배포 조문의 추정가격 1배 초과를 채택했다. 항목표는 「1배수 이상 / 사업예산 기준」, 원본 스캐너는 배정예산 초과여서 동일한 가설식이 아니다. 두 Gemma 조건에는 같은 법령 기준을 제공했다.',
            '- v4: 물품·용역 실적의 고시금액은 2.3억원으로 고정했다. 원본 스캐너의 지방 5억원 등 지역제한 기준 재사용과 다르다.',
            '- v5~v7: 지방 일반 물품·용역은 기관별로 구분하고 배포되지 않은 행안부 고시 금액은 임의로 보충하지 않았다. 기준자료의 미확정 부분은 정답 라벨의 공식 해석을 확정하지 못한다.',
            '- 후보 플래그는 최종 판단을 강제하지 않는다. 미탐 공고도 전부 Gemma에 입력하므로 이 실험은 후보만 모델에 보내는 선별 방식이나 호출 수 절감 실험이 아니다.',
            '- 법령 직접 주입의 효과와 RAG 대비 효과를 분리 검증한 실험이 아니다. 두 조건 모두 법령을 직접 넣었으며 LJM 힌트 추가 효과를 측정한다.',
            '- dev 200건은 숨겨진 평가 분포를 대표하지 않으며 본 결과는 단일 반복이다. 7항목 평균은 대회의 24항목 Macro F1과 다르다.','',
            '## 실행 검증과 비용','',
            f"추론 시간: 기준 {runtime['arm_seconds']['baseline']:.2f}초, 가설 {runtime['arm_seconds']['candidate']:.2f}초. 모델 로딩 {runtime['load_seconds']:.2f}초는 공통 비용으로 별도 집계.",'',
            '```json',json.dumps(audits,ensure_ascii=False,indent=2),'```','',
            '모든 저장 판정은 마지막 정상 JSON 응답을 기존 검증기로 재생하여 일치 확인했다. 유효 근거의 원문 일치는 법적 적절성까지 보증하지 않는다.','',
            '## 재현 및 산출물','',
            '- `manifest.json`: 고정 조건·소스 및 법령 해시. `source/run.py`: 실행 당시 코드.',
            '- `legal_cards.json`, `prompts/`, `hints.json`: 실제 법령 카드·공통 프롬프트·스키마·공고별 추가 힌트.',
            '- `baseline/trace.jsonl`, `candidate/trace.jsonl`: 정상·재시도 응답과 판정 로그.',
            '- 조건별 `predictions_v2_v8.csv`, `evaluation.json`, `errors.csv`, `changes.csv`, `original/`: 판정·점수·오류·원본 추출.',
            '- 평가 재생: `uv run --locked python analysis/ljm_static_law_v2_v8_20260912/source/score.py`.',
            '- 추론 재실행: `source/run.py`의 OUT을 새 디렉토리로 지정하고 prepare → 생성된 source/run.py run 순서로 실행. 기존 산출물 덮어쓰기는 거부한다.']
    report=write_report(OUT/'report.md','\n'.join(lines)+'\n')
    print(json.dumps({'report':str(report),'scores':scores,'comparison':comparison,'audits':audits},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
