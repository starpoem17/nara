"""Summarize complete compressed-prompt experiments and H6 feature changes."""
import csv
import json
from pathlib import Path
from nara.evaluation.reporting import report_path, write_report
from nara.evaluation.evaluate_dev import read_csv, ITEMS
from sklearn.metrics import f1_score

ROOT=Path('analysis/compact200')

def main():
    selection=json.loads((ROOT/'selection.json').read_text())
    winner=selection['winner']['plan']
    names=['groups7_off','groups9_off','groups12_off','ungrouped_on',winner+'_off_h6','ungrouped_on_h6']
    rows=[]
    for name in names:
        folder=ROOT/name
        ev=json.loads((folder/'evaluation.json').read_text())
        runtime=json.loads((folder/'report.json').read_text())
        md=report_path(folder/'evaluation.md')
        text=md.read_text().replace('system_prompt.txt','prompt_*.txt').replace('대화당 최대 ', '대화당 ').replace('대화당 ', '대화당 최대 ')
        if runtime.get('recovery') and '첫 실행 실패 공고는' not in text:
            text+='\n첫 실행 실패 공고는 recovery_prompt_*.txt 및 recovery_schema_*.json으로 복구했다. 첫 실행 기록은 first_pass/에 보존했다.\n'
        md.write_text(text)
        rows.append({'name':name,'macro_f1':ev['macro_f1'],'micro_f1':ev['micro_f1'],
                     'tp':sum(r['tp'] for r in ev['per_item']),'fp':ev['false_positives'],'fn':ev['false_negatives'],
                     'exact_match_records':ev['exact_match_records'],
                     'inference_seconds':runtime['prediction_seconds'],
                     'load_seconds':runtime['load_seconds'],'rule_seconds':runtime['rule_seconds'],
                     'first_pass_failures':len(runtime.get('first_pass',{}).get('failed_ids',runtime['failed_ids'])),
                     'recovery_seconds':runtime.get('recovery',{}).get('prediction_seconds',0)+runtime.get('extended_recovery',{}).get('prediction_seconds',0),
                     'extended_output_tokens':runtime.get('extended_recovery',{}).get('actual_output_tokens'),
                     'projected_1853_minutes':(runtime['prediction_seconds']/200*1853+runtime['load_seconds'])/60,
                     'search_rounds':runtime['search_rounds'],'searched_records':ev['searched_records'],
                     'invalid_responses':runtime['invalid_responses'],'model_turns':runtime['model_turns'],
                     'thinking_tokens':runtime['thinking_tokens'],'evidence':ev['evidence'],
                     'per_item':ev['per_item']})
    indexed={r['name']:r for r in rows}
    truth=read_csv('data/dev_labels.csv')
    ids=list(truth)
    pairs=[]
    per_item_changes=[]
    for base in [winner+'_off','ungrouped_on']:
        after=base+'_h6'
        before_csv=read_csv(ROOT/base/'submission.csv')
        after_csv=read_csv(ROOT/after/'submission.csv')
        def score(pred,keys):
            y=[[int(truth[i][k]) for k in keys] for i in ids]
            p=[[int(pred[i][k]) for k in keys] for i in ids]
            return f1_score(y,p,average='macro',zero_division=0)
        other=[k for k in ITEMS if k not in ('v2','v3')]
        # Diagnostic only: merge fixed rule bits into archived baseline predictions,
        # to distinguish direct rule effect from changed 22-feature model judgments.
        replaced={i:{**before_csv[i],**{k:after_csv[i][k] for k in ('v2','v3')}} for i in ids}
        pair={'baseline':base,'hypothesis':after,
              'macro_f1_delta':indexed[after]['macro_f1']-indexed[base]['macro_f1'],
              'rule_only_counterfactual_macro_f1':score(replaced,ITEMS),
              'other22_macro_before':score(before_csv,other),'other22_macro_after':score(after_csv,other),
              'other22_changed_bits':sum(before_csv[i][k]!=after_csv[i][k] for i in ids for k in other),
              'time_ratio':indexed[after]['inference_seconds']/indexed[base]['inference_seconds']}
        pairs.append(pair)
        for k in ITEMS:
            a=next(r for r in indexed[base]['per_item'] if r['item']==k)
            b=next(r for r in indexed[after]['per_item'] if r['item']==k)
            per_item_changes.append({'baseline':base,'item':k,'support':a['support'],
                'f1_before':a['f1'],'f1_after':b['f1'],'delta':b['f1']-a['f1'],
                'tp_before':a['tp'],'tp_after':b['tp'],'fp_before':a['fp'],'fp_after':b['fp'],
                'fn_before':a['fn'],'fn_after':b['fn']})
    rule_trace=[json.loads(l) for l in (ROOT/(winner+'_off_h6')/'rules.jsonl').read_text().splitlines()]
    unchanged=json.loads((ROOT/'unchanged_groups_audit.json').read_text())
    result={'unchanged_group_audit':unchanged,'records':200,'selection':selection,'runs':rows,'pairs':pairs,
            'rule_diagnostics':{'no_eligibility_section':sum(not r['eligibility_sections'] for r in rule_trace),
                                'with_candidates':sum(bool(r['candidates']) for r in rule_trace),
                                'unknown_metadata':sum(bool(r['unknown_metadata']) for r in rule_trace)}}
    (ROOT/'comparison.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    with (ROOT/'per_item_changes.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(per_item_changes[0]));writer.writeheader();writer.writerows(per_item_changes)
    lines=['# 압축 법령 프롬프트 · dev 200건 실험','',
        '모든 공고·첨부 원문을 유지했다. 영어 압축 법령 기준, Gemma 4 NVFP4, 컨텍스트 32,768, 배치 8, 출력 2,048토큰, ON thinking 예산 1,024토큰. RAG는 자율 검색이며 BGE-M3와 제공 법령 인덱스를 사용했다. 각 실행 전 prefix cache를 비웠다. 각 구성 1회 측정.',
        '', '## 전체 결과','',
        '| 구성 | Macro F1 | Micro F1 | TP / FP / FN | 완전일치 | 추론 시간 | 1,853건 환산 | 검색 횟수 |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in rows:
        lines.append(f"| {r['name']} | {r['macro_f1']:.4f} | {r['micro_f1']:.4f} | {r['tp']} / {r['fp']} / {r['fn']} | {r['exact_match_records']}/200 | {r['inference_seconds']/60:.2f}분 | {r['projected_1853_minutes']:.1f}분 | {r['search_rounds']} |")
    chosen=indexed[winner+'_off']
    control=indexed['ungrouped_on']
    best_run=max(rows,key=lambda r:r['macro_f1'])
    lines += ['', f"최고 Macro F1 구성은 **{best_run['name']} ({best_run['macro_f1']:.4f})**이다. 선택된 그룹 OFF는 일괄 ON 대조군 대비 Macro F1이 {chosen['macro_f1']-control['macro_f1']:+.4f}, 추론 시간은 {chosen['inference_seconds']/control['inference_seconds']:.2f}배다. 이 비교는 그룹화와 thinking을 함께 바꾼 실행 전략 비교이며, 그룹화만의 인과 효과를 분리한 결과는 아니다."]
    lines += ['', '추론 시간은 입력 토큰 계산·모델 호출·재시도·검색·H6 규칙을 포함한다. 1,853건 환산은 추론 시간에 1,853/200을 곱하고 해당 단계의 모델·인덱스 로딩을 더한 RTX 5090 단순 추정이다. 오프라인 실험 준비·공통 워밍업은 제외했다. L40S 실측이나 2시간 통과 보장이 아니다.',
        '', '## 그룹 선택','',
        f"결과 확인 전에 Macro F1 최고점과의 차이 ≤0.01이면 추론 시간이 짧은 구성을 선택하기로 고정했다. 선택: **{winner} OFF**. `selection.json`에 후보 점수와 시간을 저장했다.",
        '', '## 가설 6 효과','',
        'v2·v3의 기준과 출력 항목을 모델에서 제거하고, 나머지 22개만 판단했다. 그룹 수는 유지했다. 참가자격 영역의 명시적인 실적 금액 하한을 규칙으로 추출하며, 평가표·서식·계약 후 조건을 제외한다. v2는 적용법 확인 후 추정가격 <2.3억원, v3는 요구 실적금액 >배정예산금액이다. 기본 v3 프롬프트의 분모인 추정가격과 다르다. 동료의 구현 코드나 수치는 제공되지 않아 가설 문서의 후보 규칙을 독립 구현한 결과다.',
        '', '| 비교 | 전체 Macro F1 변화 | v2/v3만 교체한 진단용 F1 | 나머지 22개 F1 전 → 후 | 나머지 22개 변경 수 | 시간 비율 |',
        '|---|---:|---:|---:|---:|---:|']
    for p in pairs:
        lines.append(f"| {p['baseline']} → H6 | {p['macro_f1_delta']:+.4f} | {p['rule_only_counterfactual_macro_f1']:.4f} | {p['other22_macro_before']:.4f} → {p['other22_macro_after']:.4f} | {p['other22_changed_bits']} / 4,400 | {p['time_ratio']:.3f}× |")
    lines += ['', '첫 실행 실패 및 복구 시간: ' + '; '.join(f"{r['name']} {r['first_pass_failures']}건 / {r['recovery_seconds']:.2f}초" for r in rows) + '. 최종 점수는 복구 후 전체200건이다. 복구는 같은 컨텍스트·출력·thinking 설정에서 실패 공고만 모든 그룹 재추론, 검색 없이 최종 JSON, 인용 최대80자로 제한했다. 첫 실행 trace/report는 해당 폴더 first_pass/에 보존했다. 짧은 인용 복구도 실패하면 원문과 thinking 예산을 유지하고 32K에 들어가는 범위에서 출력 한도만 최대4096으로 늘리는 추가 복구를 적용했다(extended_recovery 기록). 표의 추론 시간은 복구 추론을 포함하며, 별도 복구 프로세스 로딩은 report.json에 추가 기록했다.']
    lines += ['', '진단용 F1은 기존 예측의 v2/v3만 규칙 결과로 바꿔 계산한 값이며 별도 모델 추론 실험이 아니다. 실제 H6 결과는 프롬프트·스키마에서 두 항목을 제거한 재추론 결과다.',
        '', '| 구성 | 항목 | 양성 정답 | TP | FP | FN | Precision | Recall | F1 |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for name in [winner+'_off',winner+'_off_h6','ungrouped_on','ungrouped_on_h6']:
        for r in indexed[name]['per_item']:
            if r['item'] in ('v2','v3'):
                lines.append(f"| {name} | {r['item']} | {r['support']} | {r['tp']} | {r['fp']} | {r['fn']} | {r['precision']:.3f} | {r['recall']:.3f} | {r['f1']:.3f} |")
    lines += ['', '## 범위와 한계','',
        '- 모든 구성에 동일한200건·평가기준·공통 기본 한도를 적용했다. 출력 복구 예외는 위에 명시했다. Macro F1은 양성 F1 24개의 평균이며 zero_division=0이다.',
        '- 근거 인용: ' + '; '.join(f"{r['name']} 원문 일치 인용 {r['evidence']['nonempty']}개, 위반·비부재항목 인용 누락 {r['evidence']['positive_nonabsence_missing']}개" for r in rows) + '. 빈 인용은 형식 검증 오류가 아니지만 근거 품질의 한계다.',
        '- 기존 32건 상세 한국어 프롬프트 실험과는 대상·프롬프트 언어·길이가 다르다. 이번 구성끼리의 비교만 통제된 비교다. 그룹 ON은 사용 불가 결정을 유지하며 재실험하지 않았다.',
        '- 규칙은 라벨 평가 전에 고정했다. dev에서 구성을 선택했으므로 이 점수를 독립 검증 성능으로 해석하면 안 된다.',
        f"- 규칙이 참가자격 제목을 인식하지 못한 공고 {result['rule_diagnostics']['no_eligibility_section']}건; 후보 조건이 있는 공고 {result['rule_diagnostics']['with_candidates']}건. 인식 실패·메타 미확인·명시적 금액 하한 없음은 0으로 처리하므로 미탐 위험이 있다. `rules.jsonl`에 원문 위치·후보·제외 사유가 있다.",
        '- 재실행 변동: 그룹 H6에서 변경하지 않은 11개 그룹의 프롬프트·스키마가 동일함을 확인했지만, 해당20항목의 4,000개 판정 중195개(4.875%)가 달라졌다. 따라서 전체 재추론의 F1 차이를 규칙만의 인과 효과로 해석할 수 없다. 원인은 이번 실험에서 분리 검증하지 않았다. `unchanged_groups_audit.json` 참조.',
        '- 규칙 단독 오류분석: v2 오탐3건(059·099·165), 미탐2건(053·062); v3 미탐2건(053·062). 099·165는 서식/실적 기재 문구가 참가자격 영역으로 섞인 추출 한계다. 053·062는 실적 자격 문구가 있음에도 추출하지 못했다. 따라서 가설 자체의 한계와 이 독립 구현의 영역 추출 오류를 구별해야 한다. 점수 확인 후 규칙을 수정하지 않았다.',
        '- 숫자로 표시한 원/천원/백만원/만원/억원 및 혼합 단위를 지원한다. 한글 숫자만 있는 금액, 금액 대신 비율만 있는 조건, 복잡한 선택조건·여러 조건 연결은 이 규칙의 한계다. v3은 가설 범위인 금액만 처리한다.',
        '- 압축은 핵심 조건·금액·예외를 남겼으나 상세 법령 원문 전체를 대체하지 않는다. 법령 원본과 상세 기준은 보존했고 자율 RAG로 조회 가능하다.',
        '', '실제 프롬프트·스키마: 각 구성 폴더 `prompt_*.txt`, `schema_*.json`. 예측·오류·평가·원본 해시: `submission.csv`, `trace.jsonl`, `errors.csv`, `evaluation.json`, `manifest.json`.']
    write_report(ROOT/'comparison.md', '\n'.join(lines)+'\n')
    print(json.dumps({'runs':[{k:v for k,v in r.items() if k!='per_item'} for r in rows],'pairs':pairs},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
