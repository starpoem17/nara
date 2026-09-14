"""Explain historical label flips and raw-token repeat/adapter/schedule controls."""

if __name__ == "__main__":
    raise SystemExit("Archived code: create a fresh registered run; see docs/operations.md.")

from experiments.legacy_prefix_pipeline200.code.historical_paths import source_path
import csv
import hashlib
import json
from pathlib import Path
from nara.evaluation.reporting import write_report
import numpy as np
from nara.inference.hybrid_experiment import THINK
from experiments.legacy_continuous_pilot.code.summarize_continuous import scores
from vllm.reasoning.gemma4_utils import parse_thinking_output
ROOT=Path('analysis/continuous_diagnosis')
def read(p):return json.loads(Path(p).read_text())
def rows(p):return [json.loads(s) for s in Path(p).read_text().splitlines()]
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def firstdiff(a,b):return next((i for i,(x,y) in enumerate(zip(a,b)) if x!=y),min(len(a),len(b)))

def main():
    a=rows('analysis/hybrid200/six_on1024_batch8/trace.jsonl');b=rows('analysis/continuous200/six_continuous_8192/trace.jsonl')
    truth={r['id']:r for r in csv.DictReader(open('data/dev_labels.csv'))}
    diffs=[]
    for x,y in zip(a,b):
        assert x['record_id']==y['record_id']
        for k in THINK:
            p=x['judgments'][k]['위반여부'];q=y['judgments'][k]['위반여부'];g=int(truth[x['record_id']][k])
            if p!=q:diffs.append({'id':x['record_id'],'feature':k,'old':p,'new':q,'gold':g,'change':'lost' if p==g else 'gained'})
    qa=scores(a,truth,THINK);qb=scores(b,truth,THINK)
    features=[]
    for x,y in zip(qa['per_feature'],qb['per_feature']):
        features.append({'feature':x['feature'],'support':x['tp']+x['fn'],'old_tp':x['tp'],'new_tp':y['tp'],
            'old_fp':x['fp'],'new_fp':y['fp'],'old_f1':x['f1'],'new_f1':y['f1'],'macro_delta_contribution':(y['f1']-x['f1'])/6})
    y=np.array([[int(truth[r['record_id']][k]) for k in THINK] for r in a])
    aa=np.array([[r['judgments'][k]['위반여부'] for k in THINK] for r in a]);bb=np.array([[r['judgments'][k]['위반여부'] for k in THINK] for r in b])
    def calc(p,t):
        tp=((p==1)&(t==1)).sum(0);fp=((p==1)&(t==0)).sum(0);fn=((p==0)&(t==1)).sum(0);d=2*tp+fp+fn
        return np.array([np.divide(2*tp,d,out=np.zeros(6),where=d!=0).mean(),2*tp.sum()/max(1,d.sum())])
    rng=np.random.default_rng(42);boot=[]
    for _ in range(5000):
        idx=rng.integers(0,200,200);boot.append(calc(bb[idx],y[idx])-calc(aa[idx],y[idx]))
    history={'flipped_bits':len(diffs),'changed_records':len({r['id'] for r in diffs}),'lost':sum(r['change']=='lost' for r in diffs),
        'gained':sum(r['change']=='gained' for r in diffs),'old_quality':qa,'new_quality':qb,'features':features,
        'paired_notice_bootstrap_95ci_new_minus_old':np.quantile(boot,[.025,.975],axis=0).T.tolist(),
        'bootstrap_scope':'Fixed predictions, resample notices; not repeated-inference variance; exploratory development set'}
    with (ROOT/'historical_flips.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(diffs[0]));w.writeheader();w.writerows(diffs)
    plan=read(ROOT/'plan.json');runs={name:read(ROOT/(name+'.json')) for name in plan['stages']}
    from transformers import AutoTokenizer
    from nara.experiments.config import MODEL
    tokenizer=AutoTokenizer.from_pretrained(MODEL,local_files_only=True)
    end=tokenizer.convert_tokens_to_ids('<channel|>')
    pairs=[('old_barrier_1','old_barrier_2'),('old_barrier_2','new_barrier'),('new_barrier','new_continuous_1'),('new_continuous_1','new_continuous_2'),('old_barrier_1','new_continuous_1')]
    comparisons=[];examples=[];qualities={}
    for n,run in runs.items():
        trace=[]
        for r in run['raw']:
            reply=run['replies'][r['id']];assert reply['finish_reason']=='stop'
            action=json.loads(reply['text']);assert action['action']=='final'
            trace.append({'record_id':r['id'],'judgments':action['judgments']})
        qualities[n]=scores(trace,truth,THINK)
    for an,bn in pairs:
        xx={r['id']:r for r in runs[an]['raw']};yy={r['id']:r for r in runs[bn]['raw']};raw_changed=thinking_changed=answer_changed=bits=0;div=[];before_answer=0
        ap={r['record_id']:r['params'] for r in runs[an]['effective_sampling']};bp={r['record_id']:r['params'] for r in runs[bn]['effective_sampling']}
        assert ap==bp
        for rid,x in xx.items():
            z=yy[rid];assert x['input_token_sha256']==z['input_token_sha256']
            tx=parse_thinking_output(x['raw_text']);tz=parse_thinking_output(z['raw_text'])
            labelsx=json.loads(tx['answer'])['judgments'];labelsz=json.loads(tz['answer'])['judgments']
            changed=[k for k in THINK if labelsx[k]['위반여부']!=labelsz[k]['위반여부']];bits+=len(changed)
            raw_changed+=x['token_ids']!=z['token_ids'];thinking_changed+=tx['thinking']!=tz['thinking'];answer_changed+=tx['answer']!=tz['answer']
            if x['token_ids']!=z['token_ids']:
                at=firstdiff(x['token_ids'],z['token_ids']);div.append(at)
                cutoff=min(x['token_ids'].index(end),z['token_ids'].index(end));early=at<cutoff;before_answer+=early
                examples.append({'a':an,'b':bn,'id':rid,'first_divergent_output_token_0based':at,'inside_thinking':early,'changed_features':changed,
                    'a_text_near_divergence':tokenizer.decode(x['token_ids'][max(0,at-12):at+18]),'b_text_near_divergence':tokenizer.decode(z['token_ids'][max(0,at-12):at+18])})
        comparisons.append({'a':an,'b':bn,'records':24,'raw_changed_records':raw_changed,'thinking_changed_records':thinking_changed,
            'answer_changed_records':answer_changed,'label_flips':bits,'divergences_inside_thinking':before_answer,
            'first_divergence_token_min_median_max':np.quantile(div,[0,.5,1]).tolist() if div else []})
    for p,h in plan['source_sha256'].items():assert hashlib.sha256(source_path(p).read_bytes()).hexdigest()==h,p
    prior={r['record_id']:r for r in a}
    legacy24_flips=sum(json.loads(reply['text'])['judgments'][k]['위반여부']!=prior[rid]['judgments'][k]['위반여부']
        for rid,reply in runs['old_barrier_1']['replies'].items() for k in THINK)
    history['diagnostic_old_barrier_vs_historical_first24_label_flips']=legacy24_flips
    result={'historical':history,'controls':comparisons,'control_qualities':qualities,'control_seconds':{n:r['seconds'] for n,r in runs.items()},
        'engine':read(ROOT/'engine.json'),'input_audit':{k:v for k,v in read(ROOT/'input_audit.json').items() if k!='checks'}}
    dump(ROOT/'summary.json',result);dump(ROOT/'divergences.json',examples)
    dump(ROOT/'validation.json',{'passed':True,'all200_input_and_postprocessing_audited':True,'all120_control_request_routes_verified_from_actual_prompt_tokens':True,'effective_sampling_equal':True,'all_control_responses_final_stop':True,'sources_unchanged':True})
    text=['# 8건 대기와 완료 즉시 보충의 정확도 차이 진단','',
        '이전200건 판정 비교와, 입력 순서 앞24건의 같은 엔진 반복/호출 API/스케줄 분리 실험. 24건은 원래 순서로 선택했으며 전체 성능 재평가가 아니다.','',
        '## 기존200건 차이','',f'총1200판정 중 {history["flipped_bits"]}개({history["flipped_bits"]/1200:.2%}), {history["changed_records"]}공고가 변했다. 정답→오답17, 오답→정답9, 순 오답 증가8. 양성은41/1200.',
        '', '|항목|양성 수|TP 기존→신규|FP 기존→신규|F1 기존→신규|','|---|---:|---:|---:|---:|']
    for r in features:text.append(f'|{r["feature"]}|{r["support"]}|{r["old_tp"]}→{r["new_tp"]}|{r["old_fp"]}→{r["new_fp"]}|{r["old_f1"]:.4f}→{r["new_f1"]:.4f}|')
    text+=['', '5000회 공고 단위 paired bootstrap의 신규−기존95%구간(Macro,Micro): '+str(history['paired_notice_bootstrap_95ci_new_minus_old'])+'. 고정된 두 예측을 재표집한 값이며 추론 반복 간 분산은 아니다.', '',
        '## 원인 분리 실험','', '|비교|원문 토큰열이 달라진 공고/24|판정 변화/144|thinking 안에서 최초 분기|','|---|---:|---:|---:|']
    for c in comparisons:text.append(f'|{c["a"]} → {c["b"]}|{c["raw_changed_records"]}|{c["label_flips"]}|{c["divergences_inside_thinking"]}|')
    text+=['','|실행|시간|6항목 Macro F1|6항목 Micro F1|','|---|---:|---:|---:|']
    for n,q in qualities.items():text.append(f'|{n}|{runs[n]["seconds"]:.2f}s|{q["macro_f1"]:.4f}|{q["micro_f1"]:.4f}|')
    text+=['', 'old_barrier는 기존VLLMModel.generate, new_barrier는 새StreamingModel을 사용하되8개 모두 기다림, new_continuous는 같은StreamingModel에서 완료 즉시 보충. 모든 단계는 같은24개 Turn, 32K/8192step/8slots/ON1024/temp0/seed0이고 prefix cache를 매번 비웠다. 단계 순서는 고정이며 grammar/컴파일 등 warm 상태는 유지된다. raw 캡처용 CPU 계측이 있어 이 시간은 종전 처리량 벤치마크를 대체하지 않는다.', '',
        '## 확인한 사항','',
        '- 200건 전부 기존/신규 경로의 메시지, 순서 포함 JSON 스키마, 토큰 ID를 대조했다. 과거 두 실행의 입력 토큰 길이도 모두 일치했다. 과거 로그의 엔진 설정 문자열도 일치한다.',
        '- 과거 원본 응답400개를 기존 후처리로 재생한 판정이 각각 최종 결과와 일치한다. 해당6항목 비교에는 검색/재시도/출력 한도 실패가 없다.',
        '- 실제GPU 출력에 붙은 prompt_token_ids로 공고ID를 독립 복원해 요청/응답 연결을 검증했다. 모든120개 통과. sampling params도 단계 간 일치했다.',
        '- 실제엔진은 multiprocessing=True, batch_invariant=False. vLLM은 기본 설정에서 재현성을 보장하지 않으며 offline scheduling 고정 또는 batch invariance 설정을 안내한다: https://docs.vllm.ai/en/stable/usage/reproducibility/',
        '- 같은 입력에도 batch shape/계산 순서에 따라 작은 수치 차이가 생기면 greedy top1과 이후thinking 경로가 달라질 수 있다. 특정attention/MoE/NVFP4 커널을 직접 분리한 실험은 아니므로 어느 커널의 책임인지는 확정하지 않는다.',
        '- 과거200건은 thinking 원문/토큰ID를 저장하지 않았으므로 과거26개 변화의 최초 분기점을 직접 복원할 수 없다. 이번 raw-token 진단은 메커니즘과 반복성 점검이다.', '']
    text+=['## 結論'.replace('結論','결론'), '',
        '같은 엔진의 기존8건 대기 반복과 새API8건 대기는24건 모두 생성 토큰이 완전히 같았다. 완료 즉시 보충으로 바꾸면 첫8건은 같지만 이후16건은thinking 초반4~22번째 토큰부터 분기했다(0-based3~21). 그중12건의 최종 답변 문자열,8개 이진 판정이 달랐다. 연속 처리 자체를 반복하면 다시 전부 동일했다.',
        '이 대조는 애플리케이션 API/ID/후처리 결함보다 배치 구성에 민감한 엔진 생성 경로를 가리킨다. 반복마다 무작위로 흔들린 현상은 이번 대조에서 관측되지 않았다. 다른 요청의 문서가 프롬프트에 섞였다는 증거도 없다. 배치 내 토큰 조합과 prefill/decode 혼합이 달라지면 GPU 계산 크기/연산 경로가 바뀌고 작은 수치 차이가 greedy 선택을 바꾸는 것이 유력한 메커니즘이다. logits/커널별 계측은 하지 않아 NVFP4,MoE,attention 중 특정원인을 확정하지 않았다.',
        f'이번 계측된 기존 방식도 과거 동일24건과 {legacy24_flips}개 판정이 다르다. 원래200건 비교는 별도 엔진 실행이며 이번 raw 관측 훅도CPU 제출 시간을 추가한다. warm/계측/내부스케줄 효과를 모두 분리한 것이 아니므로 과거26개 변화 전부가 완료 즉시 보충 때문이라고 결론내리지 않는다.',
        '양성41개뿐인6항목에서는 TP3개 감소와 FP5개 증가만으로 Micro F1이.4865→.3947로 바뀐다. v1은양성7개 중TP4→2로F1 .7273→.4000. 드문 양성에 대한F1의 민감성이 큰 점수 차이를 확대한다. 이는 오류를 무시할 이유가 아니라 지표와 실제변화 개수를 함께 봐야 하는 이유다.',
        '다음 설정 비교는 배치/순서/엔진 조건과 반복 분산을 함께 기록해야 한다. 동일한 스케줄의 재현성을 높이는 설정과, 서로 다른 배치에서도 출력을 같게 만드는 batch invariance는 별개다. vLLM문서는 offline multiprocessing 비활성화 또는batch invariance를 제안하지만 현재Gemma4 NVFP4 경로의호환성/속도는 여기서 검증하지 않았으며 운영 설정도 변경하지 않았다. 정확도 안정성을 확인하기 전1.8% 속도 차이만으로 전략을 확정할 근거는 부족하다.', '']
    write_report(ROOT/'report.md', '\n'.join(text))
    print(json.dumps({'historical':{k:v for k,v in history.items() if k not in ['old_quality','new_quality','features']},'controls':comparisons},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
