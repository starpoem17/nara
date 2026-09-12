import csv,hashlib,json,shutil
from pathlib import Path
from nara.evaluation.reporting import write_report
OUT=Path('analysis/ljm_static_law_v2_v8_20260912')
e=json.loads((OUT/'evaluation.json').read_text());h=json.loads((OUT/'hints.json').read_text())
records={r['id']:r for r in (json.loads(s) for s in Path('data/dev.jsonl').read_text().splitlines())}
changes=list(csv.DictReader((OUT/'changes.csv').open(encoding='utf-8-sig')))
selected=[('PPS-DEV-071','v4'),('PPS-DEV-081','v4'),('PPS-DEV-054','v3'),('PPS-DEV-070','v6'),('PPS-DEV-063','v7'),('PPS-DEV-06','v8')]
notes={
 ('PPS-DEV-071','v4'):'공공기관 또는 민간단체 실적을 모두 허용한다. 기준 조건이 이를 특정기관 실적 제한으로 판정했으나 힌트 추가 조건에서는 0으로 수정됐다. 민간 실적의 배제 여부를 구별한 개선 사례다.',
 ('PPS-DEV-081','v4'):'기준 조건의 인용은 용역 참여 실적 1건당 1점을 부여하는 평가 문구다. 힌트 추가 후 0으로 수정됐다. 참가자격과 평가 배점을 구별한 개선 사례다.',
 ('PPS-DEV-054','v3'):'실적 하한은 1억원, 메타 추정가격은 327,272,727원, 문서 사업예산은 360,000,000원이다. 어느 분모를 사용해도 1억원이 1배를 초과하지 않는다. 스캐너 후보는 false인데도 문맥 추가 후 0→1 오탐으로 바뀌었다. 이 사례의 오류를 v3의 분모 해석 차이로만 설명할 수 없다.',
 ('PPS-DEV-070','v6'):'공고는 강원도 안의 단위=기초 지역에 소재지를 제한한다. 두 원본 추출기 모두 v6 후보 true이고 실제 제한 문구도 힌트에 들어갔지만 Gemma는 1→0으로 바뀌었다. 따라서 새 미탐이 단순히 후보 누락 때문에 생겼다고 설명할 수 없다.',
 ('PPS-DEV-063','v7'):'원문은 대구광역시 또는 경상북도 소재 업체를 허용한다. 두 원본 추출기 모두 v7 후보 false이고 모델은 1→0으로 바뀌었다. 인접 표현이나 익명 지역 토큰 수에 의존하는 규칙이 실제 지역명을 나열한 조건을 놓친 사례다. 음성 플래그가 최종 미탐에 기여했을 가능성은 있으나 필드별 ablation으로 확인한 것은 아니다.',
 ('PPS-DEV-06','v8'):'특정기관 실적 조건은 있지만 메타 지역제한여부=N이고 제한지역코드도 없다. 기준 조건은 실적 조건만 인용해 중복제한 양성으로 판정했으나 힌트 추가 후 0으로 수정됐다. 지역+실적의 동시 충족 여부를 다시 구별한 사례다.',
}
lines=['# LJM v2~v8 해석과 사례 검토','',
 '본 문서는 완료된 dev 200건 결과를 해석한 것이다. 정답은 제공 라벨 기준이며 법령 해석의 공식 확정이나 숨겨진 평가 성능을 뜻하지 않는다. 사례 설명은 원문·메타·추출 힌트·출력의 대조이며 모델 내부 추론을 관측한 것은 아니다.','',
 '## 판단','',
 '**원본 LJM 힌트를 전 항목에 일괄 추가하는 방식은 아직 채택하기 어렵다. 이번 실행에서 v4가 가장 유망하고, v3·v6는 악화됐다.**','',
 '| 항목 | 이번 실행의 판단 | 다음 검토 방향 |','|---|---|---|',
 '| v2 | 힌트 추가로 오탐 116→98, 여전히 과다. 원본 스캐너는 TP7/FP1/FN0. | 필수 실적 조건의 존재를 수치 비교 전에 확인. 규칙을 단순 참고 문구로 제공하는 방식의 한계 검토. |',
 '| v3 | F1 .889→.762. 추가 오탐 3건, 개선 0건. 원본 스캐너 TP8/FP0/FN0. | 추출한 요구금액·예산·추정가격·비교식을 명시적으로 검증. 이번 실험은 원본 파싱 금액 배열을 직접 제공하지 않았음. |',
 '| v4 | F1 .226→.462. TP6 유지, FP41→14. | 이번 실행에서 가장 유망한 근거 보강 대상. 공공·민간 동등 인정과 평가표 구별을 유지. |',
 '| v5 | F1 .175→.206. TP7 유지, FP66→54. | 기관별 기준금액·실제 소재지 자격 여부를 더 명확히 구별해야 함. 행안부 고시액 미확정 분기 존재. |',
 '| v6 | F1 .108→.097. FP99→53이나 TP6→3. | 현재 방식 채택 보류. 기초지역 자격 문구를 추출해도 모델이 놓치는 문제를 먼저 확인. |',
 '| v7 | F1 .385→.500. FP14→5이나 TP5→4. | 정밀도 개선과 미탐 증가를 함께 평가. 지역 토큰 중복 제거와 실제 지역명 나열 인식 필요. |',
 '| v8 | F1 .231→.240. TP6 유지, FP40→38. | 개선 폭 작음. 동일 참가자에 대한 실적 AND 지역의 명시적 연결 확인이 필요. |','',
 '총 229판정 변화 중 기존 오탐 168건을 고쳤고, 새로운 오탐 57건과 새로운 미탐 4건이 생겼다. 기존 미탐을 복구한 사례는 없다. 양성 재현율 전체는 45/47→41/47이다.','',
 '7항목 Macro F1 차이 +.03852의 공고 단위 bootstrap 95% 구간은 [-.01381,+.07955]로 0을 포함한다. 이번 단일 실행의 개선 관측과 일반화된 개선 주장을 구별해야 한다.','',
 '원본 스캐너의 후보 플래그를 그대로 판정으로 간주하면 7항목 Macro F1=.50055, TP23/FP10/FN24다. 두 Gemma 조건보다 이 참고 점수는 높지만 양성 47건 중 24건을 놓친다. 법령 해석(특히 v3 분모·v4 금액)도 다르므로 같은 목적의 확정 판정기라고 취급하지 않는다.','',
 '별도 v4~v7 추출기의 재현율은 각각 1.000/.714/.833/.286이다. v7은 111건이나 후보로 잡으면서 정답 양성 7건 중 2건만 포착했다. 후보만 Gemma에 보내는 선별 방식으로 사용하기에는 특히 v7의 누락이 크다.','',
 '## 근거 품질과 비용','',
 '가설 조건의 양성 308판정 중 145개에는 최종 유효 근거가 없다(144개는 원문 불일치 등으로 기존 검증기가 제거, 1개는 모델이 null 출력). 정상 JSON 응답 1,400개를 받았다는 사실과 근거 품질은 다르다. 출력 길이 초과·재시도·검색·실패는 양쪽 모두 0건이다.','',
 f"추론 시간은 {e['runtime']['arm_seconds']['baseline']:.2f}초→{e['runtime']['arm_seconds']['candidate']:.2f}초, +{(e['runtime']['arm_seconds']['candidate']/e['runtime']['arm_seconds']['baseline']-1)*100:.2f}%다. 공통 모델 로딩은 {e['runtime']['load_seconds']:.2f}초이며 원본 두 추출기는 합계 약 0.45초다. 로컬 RTX 5090/NVFP4 결과로 실제 21그룹 전체 실행이나 대회 서버 시간을 뜻하지 않는다.",'',
 '## 대표 사례','']
case_rows=[]
for rid,key in selected:
 row=next(r for r in changes if r['id']==rid and r['item']==key)
 meta={k:records[rid]['meta'].get(k) for k in ['적용계약법','업무구분','계약방법','배정예산금액','입찰추정가격','지역제한여부','제한지역코드목록']}
 item={**row,'meta':meta,'hint':h[rid][key],'review':notes[(rid,key)]};case_rows.append(item)
 lines += [f"### {rid} / {key}: {row['baseline']}→{row['candidate']} (정답 {row['gold']})",'',notes[(rid,key)],'']
 quote=row['baseline_evidence'] or row['candidate_evidence'] or row['gold_evidence']
 if quote:lines+=['공고에서 인용된 문구:','', '> '+quote.replace('\n','\n> '),'']
 lines+=['후보 플래그: '+json.dumps({k:v for k,v in h[rid][key].items() if k.endswith('candidate')},ensure_ascii=False),'']
lines+=['## 자료','', '[전체 수치와 실행 조건](report.md). 전체 229개 변화는 `changes.csv`, 선택 사례의 메타·힌트는 `reviewed_cases.json`에 저장했다. 법령 카드·추출 코드·Gemma 프롬프트는 결과 확인 후 변경하지 않았다.']
(OUT/'reviewed_cases.json').write_text(json.dumps(case_rows,ensure_ascii=False,indent=2)+'\n')
write_report(OUT/'case_review.md','\n'.join(lines)+'\n')
summary='''# LJM static-law v2–v8 experiment

[Measured report](../reports/analysis/ljm_static_law_v2_v8_20260912/report.md), [case review](../reports/analysis/ljm_static_law_v2_v8_20260912/case_review.md). Artifacts: `analysis/ljm_static_law_v2_v8_20260912/`; frozen `source/run.py` and `source/score.py`. User requested Gemma plus direct per-feature supplied law, no RAG. Seven singleton groups, including v2/v3 moved from rules for this experiment; not a full groups21 run.

Matched dev200, full source/meta preserved, static law baseline vs same + unmodified LJM scan/extractor flags and deduplicated 1600-character context display. OFF, output512, seed0/temp0, NVFP4/5090, max8. Alternating arm order per notice, reset cache per arm, source-first singleton then six followers. Labels opened only by scoring after both arms passed response replay. No after-score prompt tuning. Existing user code may already be dev-informed.

Macro7 .30306986→.34158568 (+.03851582), Micro .19148936→.23098592. TP45→41, FP378→267, FN2→6. 229 changes:168 old FPs fixed,57 new FPs,4 new FNs; no FN recovery. Per-item F1 baseline→candidate: v2 .1077→.125; v3 .8889→.7619; v4 .2264→.4615; v5 .175→.2059; v6 .1081→.0968; v7 .3846→.5; v8 .2308→.24. Bootstrap2000 paired-notice fixed-output macro delta95CI[-.013814,.079546]; not run-repeat uncertainty. Prioritize v4 follow-up; avoid blanket adoption, especially v3/v6.

Each arm1400 normal model calls,0retry/length/search/failure, all200 complete, no zero-fill. Max initial31207 with512+128 reserve. Input17,144,909→17,774,480; output77,950→72,932. Inference507.5088s→531.9881s (+4.823%); shared load27.2824s. Exact positive quotes203/423→163/308; missing220→145, dropped219→144. Valid JSON does not imply valid evidence.

Original scanner candidate-as-label Macro7 .50055, TP23/FP10/FN24. v2F1 .9333,v3 1.0, v7 recall0; broad extractor v4–7 recall1/.714/.833/.286, v7 111candidates with2TP. Full-context audit:46 v7 candidates with one repeated unique anonymized region token/no adjacency cue; one gold positive, final v7FP3→0 in that subset. Synthetic single-region input reproduces v7 duplication bug. Numeric parser also captures years/counts; parsed-amount array was NOT injected, so no isolated final-effect claim.

Interpretation choices: v3 statute-first >estimated price vs scanner >allocated budget and item-table ≥budget; v4 goods/services experience threshold230m vs scanner local500m. Regional thresholds use supplied law; missing local notice amount not invented. Static-law vs RAG effect, flag vs context effect, hidden distribution, and repeatability remain untested. User source and production src unchanged; experiment helpers archived only as artifacts.
'''
Path('docs/experiments/ljm-static-law.md').write_text(summary)
index=Path('docs/README.md');text=index.read_text()
row='| LJM v2–v8 candidates with direct per-feature law and Gemma | [LJM static-law experiment](experiments/ljm-static-law.md) |\n'
if row not in text:
 anchor='| Full200 compressed-criteria OFF groups and v2/v3 rule experiments | [Compact dev200](experiments/compact200.md) |\n'
 assert anchor in text;text=text.replace(anchor,anchor+row);index.write_text(text)
index=Path('docs/reports/README.md');text=index.read_text()
row='| [ljm_static_law_v2_v8_20260912](../../analysis/ljm_static_law_v2_v8_20260912/) | [summary](../experiments/ljm-static-law.md) | [report](analysis/ljm_static_law_v2_v8_20260912/report.md) · [case review](analysis/ljm_static_law_v2_v8_20260912/case_review.md) |\n'
if row not in text:
 anchor='|---|---|---|\n';assert anchor in text;text=text.replace(anchor,anchor+row,1);index.write_text(text)
for name in ['prepare','run','audit','score']:
 source=Path('/tmp')/f'ljm_{name}.log'
 if source.exists():shutil.copy2(source,OUT/f'{name}.log')
manifest=json.loads((OUT/'manifest.json').read_text())
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==value for p,value in manifest['hashes'].items())
print('Reports written; all frozen source/input/law hashes unchanged.')
