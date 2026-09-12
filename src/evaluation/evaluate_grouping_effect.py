"""Post-hoc accuracy/cost analysis of frozen grouping timing predictions.

Does not run models, change predictions, tune prompts, or fill failures with zero.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from nara.evaluation.reporting import write_report
from sklearn.metrics import f1_score

ITEMS=[f'v{i}' for i in range(1,25)]
NAMES=['ungrouped','groups7','groups9','groups12']


def scores(ids, truth, predictions):
    y=[[int(truth[i][k]) for k in ITEMS] for i in ids]
    p=[[predictions[i]['judgments'][k]['위반여부'] for k in ITEMS] for i in ids]
    per_item=[]
    for j,k in enumerate(ITEMS):
        a,b=[row[j] for row in y],[row[j] for row in p]
        tp=sum(t==v==1 for t,v in zip(a,b))
        fp=sum(t==0 and v==1 for t,v in zip(a,b))
        fn=sum(t==1 and v==0 for t,v in zip(a,b))
        per_item.append({'item':k,'support':sum(a),'tp':tp,'fp':fp,'fn':fn,
                         'f1':float(f1_score(a,b,zero_division=0))})
    macro=float(f1_score(y,p,average='macro',zero_division=0))
    assert abs(macro-sum(row['f1'] for row in per_item)/24)<1e-12
    tp,fp,fn=(sum(row[k] for row in per_item) for k in ['tp','fp','fn'])
    return {'records':len(ids),'positive_labels':sum(map(sum,y)),'macro_f1':macro,
            'micro_f1':float(f1_score(y,p,average='micro',zero_division=0)),
            'tp':tp,'fp':fp,'fn':fn,'label_accuracy':1-(fp+fn)/(len(ids)*24),
            'exact_records':sum(a==b for a,b in zip(y,p)),
            'zero_support_items':[row['item'] for row in per_item if not row['support']],
            'per_item':per_item}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',default='analysis/grouping_time32')
    args=parser.parse_args()
    out=Path(args.input)
    manifest=json.loads((out/'manifest.json').read_text())
    timing=json.loads((out/'report.json').read_text())
    timing_rows={row['name']:row for row in timing['runs']}
    label_path=Path('data/dev_labels.csv')
    with label_path.open(newline='') as stream:
        label_rows=list(csv.DictReader(stream))
    truth={row['id']:row for row in label_rows}
    assert len(truth)==len(label_rows)
    ids=manifest['sample_ids']
    assert len(set(ids))==len(ids) and set(ids)<=set(truth)
    predictions={}
    hashes={str(label_path):hashlib.sha256(label_path.read_bytes()).hexdigest()}
    for name in NAMES:
        path=out/name/'trace.jsonl'
        rows=[json.loads(line) for line in path.read_text().splitlines()]
        assert [row['record_id'] for row in rows]==ids
        predictions[name]={row['record_id']:row for row in rows}
        for row in rows:
            if row['error'] is None:
                assert row['judgments'] is not None and set(row['judgments'])==set(ITEMS)
                assert all(type(v['위반여부']) is int and v['위반여부'] in [0,1] for v in row['judgments'].values())
        hashes[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
    common=[i for i in ids if all(predictions[n][i]['error'] is None and predictions[n][i]['judgments'] is not None for n in NAMES)]
    results={name:scores(common,truth,predictions[name]) for name in NAMES}
    base=results['ungrouped']
    changes=[]
    for name,result in results.items():
        result['delta_macro_f1']=result['macro_f1']-base['macro_f1']
        result['seconds_32']=timing_rows[name]['seconds']
        result['relative_time']=timing_rows[name]['seconds']/timing_rows['ungrouped']['seconds']
        result['normal_output_records']=sum(predictions[name][i]['error'] is None for i in ids)
        result['failed_ids']=[i for i in ids if predictions[name][i]['error']]
        result['projected_1853_seconds_with_model_load']=timing_rows[name]['seconds_per_notice']*1853+timing['load_seconds']
        paired={'corrected':0,'regressed':0,'still_correct':0,'still_wrong':0}
        for i in common:
            for key in ITEMS:
                gold=int(truth[i][key])
                before=predictions['ungrouped'][i]['judgments'][key]['위반여부']
                after=predictions[name][i]['judgments'][key]['위반여부']
                category=('still_correct' if before==gold else 'corrected') if after==gold else ('regressed' if before==gold else 'still_wrong')
                paired[category]+=1
                if before!=after:
                    changes.append({'plan':name,'id':i,'item':key,'gold':gold,'ungrouped':before,'grouped':after,'change':category})
        assert sum(paired.values())==len(common)*24
        result['paired_labels']=paired
    result={'kind':'post-hoc evaluation of frozen predictions; no new inference',
            'common_records':len(common),'common_ids':common,'excluded_from_common':[i for i in ids if i not in common],
            'sample_records':len(ids),'zero_division':0,'score_items':ITEMS,
            'official_evaluation':{'url':'https://dacon.io/competitions/official/236754/overview/evaluation',
                'verified_date':'2026-09-10','test_records':1853,'script_limit_seconds':7200,
                'metric':'mean positive-class F1 over all 24 items'},
            'results':results,'supplementary_all_successful':{
                name:scores([i for i in ids if predictions[name][i]['error'] is None],truth,predictions[name]) for name in NAMES},
            'sha256':hashes}
    (out/'effect.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    with (out/'paired_changes.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=['plan','id','item','gold','ungrouped','grouped','change'])
        writer.writeheader();writer.writerows(changes)
    with (out/'effect_per_item.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=['item','support']+[f'{name}_{metric}' for name in NAMES for metric in ['f1','tp','fp','fn']])
        writer.writeheader()
        for j,key in enumerate(ITEMS):
            row={'item':key,'support':base['per_item'][j]['support']}
            row.update({f'{name}_{metric}':results[name]['per_item'][j][metric] for name in NAMES for metric in ['f1','tp','fp','fn']})
            writer.writerow(row)
    lines=['# 그룹 분할의 정확도 효과와 시간 비용',
        '이번 표본에서는 그룹 분할이 대회 주 지표 Macro F1을 높였다. 12개 그룹의 증가폭이 가장 컸다. 그러나 오탐과 실행시간이 늘었고, 현재 고정 분할 방식은 2시간 제출 제한에 맞는 실행안으로 검증되지 않았다.',
        '## 비교 방법',
        f'추론 때 고정한 결과를 그대로 두고 정답 라벨을 사후 대조했다. 네 구성이 모두 정상 출력한 동일 {len(common)}건(744개 이진 판정)을 주 비교 대상으로 삼았다. 제외된 PPS-DEV-085는 9그룹의 출력 실패이며, 어느 구성에서도 주 비교 점수에 넣지 않았다. 실패를 0으로 채우지 않았다. 전체 표본 32건에서의 출력 완성률도 따로 표시한다.',
        f"정답 위반은 {base['positive_labels']}개다. 정답 위반이 없는 5개 항목({', '.join(base['zero_support_items'])})도 평균에 포함하고 F1 분모가 0이면 0으로 처리했다. 공식 평가 데이터는 모든 항목에 위반 사례가 있으므로 이 소표본의 점수 절댓값을 리더보드 점수로 해석하지 않는다.",
        '## 정확도와 비용',
        '| 구성 | 공통 31건 Macro F1 | 일괄 대비 | Micro F1 | TP / FP / FN | 24개 모두 정답인 공고 | 32건 실측 시간 배수 | 정상 출력 |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for name,row in results.items():
        lines.append(f"| {timing_rows[name]['groups']}그룹 | {row['macro_f1']:.4f} | {row['delta_macro_f1']*100:+.2f}%p | {row['micro_f1']:.4f} | {row['tp']} / {row['fp']} / {row['fn']} | {row['exact_records']}/31 | {row['relative_time']:.2f}배 | {row['normal_output_records']}/32 |")
    lines += ['', '시간은 기존 32건 처리 시도 전체 실측이며, 정확도는 공통 31건이다. 시간과 정확도가 서로 다른 분모라는 점을 명시한다. 9그룹은 재시도 후에도 1건이 미완료이므로 완전한 32건 정상 출력까지의 시간은 아니다.',
        '- 7그룹: Macro F1 +1.60%p에 시간 4.96배. TP는 3개 증가했지만 FP는 19개 증가했다. Micro F1과 공고 전체 일치 수는 감소했다. 이 표본에서 비용 대비 이득이 작다.\n- 9그룹: Macro F1 +8.56%p이나 시간 6.15배, FP 25개 증가, 출력 실패 1건. 주 지표 개선은 있으나 모든 정확도 지표가 좋아진 것은 아니다.\n- 12그룹: Macro F1 +11.67%p, Micro F1도 증가했다. TP 7→15, FN 21→13으로 위반 검출이 개선됐다. 다만 FP 12→31, 공고 전체 일치 13→10으로 오탐 비용이 있다. 시간은 7.78배다.',
        '## 실제 평가 규모와 2시간 제한',
        '공식 평가 입력은 **1,853건**, 코드 실행 제한은 **모델 로딩·초기화 포함 2시간**이다. 기존 200건 환산은 개발 표본 규모의 참고치이며 제출 시간 판단의 기준 규모로는 부족했다. [공식 평가 안내](https://dacon.io/competitions/official/236754/overview/evaluation) (2026-09-10 확인).',
        '| 구성 | 로컬 표본 처리량 ×1,853건 + 로딩 26.8초 |', '|---|---:|']
    for name,row in results.items():
        seconds=row['projected_1853_seconds_with_model_load']
        lines.append(f"| {timing_rows[name]['groups']}그룹 | 약 {seconds/3600:.2f}시간 ({seconds/60:.1f}분) |")
    lines += ['', '이는 L40S 서버 실측이나 시간 보장이 아니다. RTX 5090/NVFP4의 길이별 표본 32건 평균을 선형 환산했으며, 32K 공통 적합 후보에서 제외된 긴 공고 21건과 실제 평가 분포를 반영하지 않는다. 9그룹의 추가 실패 복구 시간도 포함하지 않았다. 일괄도 서버에서 2시간 이내인지 추가 검증해야 한다. 그룹 방식은 로컬 단순 환산부터 제한을 크게 넘으므로 현재 설정을 그대로 채택할 근거가 부족하다.',
        '## 판단',
        '**효과는 있었다: 이 표본에서 주 지표 개선은 12그룹 > 9그룹 > 7그룹 순이다. 하지만 시간 제약을 포함하면 현재 7·9·12회 고정 분할을 그대로 사용하는 것은 권하지 않는다.** 일괄을 시간 비교의 기준으로 유지하면서, 추가 호출이 필요한 항목만 선택하거나 그룹별 thinking 예산을 조정하는 방식을 후속 실험 대상으로 삼을 수 있다. 이는 제안이며 이번 평가에서 구현·검증한 결과가 아니다.',
        '공통 31건·위반 28개인 소표본이며 길이 선택과 성공 교집합 조건이 있다. 그룹별 점수 차이를 전체 dev 200건이나 평가 데이터에서 재현되는 일반적 개선으로 확정하지 않는다. 제공 dev 자체도 평가 분포를 대표하지 않는다. 근거문구 정성 점수는 평가하지 않았다.',
        '보충: 구성별 정상 출력 전체를 대상으로 한 점수는 effect.json의 supplementary_all_successful에 저장했다. 9그룹만 분모가 31이라 이 보충 점수끼리 순위를 비교하지 않는다.',
        '파일: [수치·출처·입력 해시](effect.json), [항목별 결과](effect_per_item.csv), [일괄 대비 바뀐 판정](paired_changes.csv), [시간 실측 보고서](comparison.md).',
        '재현: `uv run --locked python src/evaluation/evaluate_grouping_effect.py` (새 모델 호출 없음).']
    write_report(out/'effect.md', '\n\n'.join(lines).replace('|\n\n|','|\n|')+'\n')
    print(json.dumps({name:{k:v for k,v in row.items() if k!='per_item'} for name,row in results.items()},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
