Artifacts: [run directory](<../../../../analysis/CMS_updated_cards_v19_v24_dev200_20260913>). Unlinked artifact names below are relative to that directory.

# CMS 수정 판정카드 v19–v24 dev200 평가

이 보고서는 CMS가 수정한 여섯 판정카드를 제공된 dev 200건에서 한 번 실행한 관찰이다. dev 정답을 활용해 개발된 방법이므로 보지 않은 데이터에 대한 일반화는 검증하지 않았다.

## 결과 요약

- 구조 유효 출력 1,200/1,200개; v19–v24 여섯 항목 macro 양성 F1 **0.488541**.
- 추론 46.37초. 후보 extraction은 생략되어 미측정이며 전체 runtime은 산출하지 않았다.
- 항목별 관찰: v20 FP 85건, v24 FP 40건, v22 양성 F1 1.
- v20의 빈 후보 입력 148건은 정답이 모두 0이었고 그중 50건이 양성으로 예측됐다. 사례 목록과 다른 기술 통계는 [observations.json](<../../../../analysis/CMS_updated_cards_v19_v24_dev200_20260913/observations.json>)에 있다. 이 입력 표현 선택의 효과를 분리한 대조 실험은 하지 않았다.
- 항목별 F1과 macro 값은 독립적인 scikit-learn 계산과 일치했다: [metric_crosscheck.json](<../../../../analysis/CMS_updated_cards_v19_v24_dev200_20260913/metric_crosscheck.json>).
- 근거 의미 제약 실패 46개: 원문 연속 substring 불일치 31개, 음성 판정인데 근거가 null이 아닌 경우 15개.

## 실제 입력과 출력

- 전체 1,200개 실제 프롬프트와 토큰 수: [inputs.jsonl](<../../../../analysis/CMS_updated_cards_v19_v24_dev200_20260913/inputs.jsonl>)
- 여섯 판정카드 source: [v19](<../../../../analysis/CMS_updated_cards_v19_v24_dev200_20260913/source/cards/v19.txt>), [v20](<../../../../analysis/CMS_updated_cards_v19_v24_dev200_20260913/source/cards/v20.txt>), [v21](<../../../../analysis/CMS_updated_cards_v19_v24_dev200_20260913/source/cards/v21.txt>), [v22](<../../../../analysis/CMS_updated_cards_v19_v24_dev200_20260913/source/cards/v22.txt>), [v23](<../../../../analysis/CMS_updated_cards_v19_v24_dev200_20260913/source/cards/v23.txt>), [v24](<../../../../analysis/CMS_updated_cards_v19_v24_dev200_20260913/source/cards/v24.txt>)
- 출력은 요청 항목 하나만 담는 singleton JSON이다. 예: `{"v19":{"위반여부":0,"근거문구":null}}`. 강제한 여섯 구조는 [schemas.json](<../../../../analysis/CMS_updated_cards_v19_v24_dev200_20260913/schemas.json>)에 있다.
- 실행 설정: 최대 동시 요청 16개를 완료되는 대로 refill, 출력 예산 512토큰, thinking OFF, temperature 0, seed 0.
- 각 요청은 사용자 메시지 하나와 chat generation prefix로 구성했다. 별도 system 판단 프롬프트는 없었다.
- CMS가 여러 후보 조각의 연결 표현을 명시하지 않은 부분은 KHJ가 선택했다. 모델에 후보 원문을 작은따옴표로 감싸 업로드 순서대로 표시했다. 문서 ID·종류·문자/행 위치는 모델에게 표시하지 않았고 source/candidates.jsonl에만 보존했다.

실제 입력 전체 예시(PPS-DEV-01:v21, 953토큰):

````text
공공 입찰공고의 v21만 판정하라.

[질문] 공동수급 구성원별 최소 지분율이 계약법과 공동이행 방식의 기준에 맞는가?

[법령·기준] 국가 공동계약운용요령과 지방 입찰·계약 집행기준 제6장에 따른다. 일반적인 공동이행 최소 지분율은 국가 10%, 지방 5%다. 다만 국가 기준은 계약 특성상 필요하면 20% 범위에서 가감할 수 있고 대형공사·주계약자 특례가 있다. 지방 공사의 일부 조정, 분담이행, 서로 다른 법령상 업종 간 공동수급 등 적용 제외·특례를 먼저 확인한다.

1: 공동이행에 구성원 최소 지분율을 두었고, 국가/지방 기준보다 낮으며 적용 가능한 조정·특례가 없다.
0: 공동수급 불허, 분담이행 등 해당 기준 비적용, 기준 충족, 또는 조정 근거가 명시·확인된 경우.

대표사 출자율, 지역업체 의무비율, 분담비율과 ‘구성원별 최소 지분율’을 혼동하지 마라. 숫자가 5%나 10%와 다르다는 이유만으로 확정하지 마라.

[경계 사례]
지방 일반용역 공동이행에서 구성원 최소 3%→1. 국가 일반용역 최소 5%→특례가 없으면 1. 지방 공동이행 최소 5%→0.

[META]
적용계약법: 지방계약법
업무구분: 일반용역
계약방법: 제한경쟁
공동도급구성방식: 공동이행
input_completeness:
  공고문_실재: true
  추출_성공: true
  무탈락: false
  완전관측: false
dropped_doc_counts:
  제안요청서: 1
[원문]
추출된 원문 후보는 다음과 같다. '‣ 기업형태 : 중소기업, 소상공인

공동계약 가능여부 ‣ 공동계약 가능(공동이행) 4항

하도급 가능여부 ‣ 하도급 가능 4항
', '해당된다고 판단될 경우 부정당업자로 제재할 수 있음
아. 낙찰자는 계약체결일까지 당해자격을 계속 유지하여야 함
- 공동수급에 관한 사항 : 공동이행 가능
가. 공동수급체 구성원 전체는 입찰 참가자격을 모두 갖추어야 함
나. 공동수급체 구성원은 대표사를 포함하여 3개사 이하로 하며, 최소 지분율은
5% 이상으로 한다
다. 하나의 업체가 두 개 이상의 공동수급체를 구성하여 중복 불가
라. 공동 수급체인 경우 대표[담당자] 투찰 가능
마. 공동수급협정서는 2026. 2. 18.(수) 18:00 까지국가종합전자조달시스템을 통하여
제출하여야 하며, 대표자를 포함한 구성원들이 각각의 분담내용을 국가종합
전자조달시스템에 제출한 후 반드시 대표자가 공동수급구성원 각각의
출자비율 또는 분담 내용을 승인하고 이를 제출한 것으로 본다
- 하도급에 관한 사항 : 하도급 가능
', '2) 과업수행계획서 제출
착수계 제출 시 과업 특성 및 여건 등을 감안한 과업수행계획서를 제출하여
발주처에 승인을 받아야 하며, 이에 포함될 내용은 다음과 같다.(공동수급일
경우 공동수비인 상호간의 과업 분할협의서 첨부)
가) 세부 공정계획서
'

1이면 비율·대상·방식이 함께 드러나는 한 문서의 연속 원문을 그대로 인용한다(500자 이하). 0이면 null. 적용법·방식·예외를 확인할 수 없으면 0.
JSON만 출력: {"v21":{"위반여부":0,"근거문구":null}}
````

짧은 exact-format 예시:

```text
[원문]
추출된 원문 후보가 없습니다.
```

CMS는 후보가 0개일 때의 입력 표시 문구를 명시하지 않았다. 본 실험에서는 사용자의 명시적 승인에 따라 해당 입력의 [원문]에 ‘추출된 원문 후보가 없습니다.’를 표시했다. 이는 업로드된 후보 목록이 비어 있음을 나타내는 입력 형식 선택이며, 원문에 관련 내용이 없다는 판정이나 추가 판단 규칙이 아니다. 이 입력은 438개였다.

후보 원문과 사용자 지정 표시 형식을 유지하기 위해 PPS-DEV-189의 v24 입력 한 건에 한해 2,024토큰을 허용했다. 이는 CMS가 정한 채팅 템플릿 포함 입력 상한 2,000토큰을 24토큰 초과하는 사용자 승인 예외다. 다른 입력에 대한 상한 초과는 허용하지 않았다.

## 분류 결과

TP/FP/FN/TN, 양성 F1과 정확도는 JSON 파싱과 schema 검증을 통과한 유효 출력만 대상으로 계산했다. 무효·미제출·엔진 오류·길이 종료 출력은 0으로 채우거나 수리하지 않았다. 각 항목의 기대 분모는 200건이다.

| 항목 | 유효/200 | 무효 | TP | FP | FN | TN | 양성 F1(유효만) | 정확도(유효만) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| v19 | 200/200 | 0 | 6 | 20 | 0 | 174 | 0.375000 | 0.900000 |
| v20 | 200/200 | 0 | 5 | 85 | 0 | 110 | 0.105263 | 0.575000 |
| v21 | 200/200 | 0 | 4 | 0 | 2 | 194 | 0.800000 | 0.990000 |
| v22 | 200/200 | 0 | 5 | 0 | 0 | 195 | 1.000000 | 1.000000 |
| v23 | 200/200 | 0 | 4 | 6 | 1 | 189 | 0.533333 | 0.965000 |
| v24 | 200/200 | 0 | 3 | 40 | 5 | 152 | 0.117647 | 0.775000 |

- 여섯 항목 macro 양성 F1(정의된 항목 평균): **0.488541**; 정의 6/6, 미정의 항목 없음.
- 이 값은 v19–v24 여섯 항목의 dev 관찰이며, 전체 v1–v24를 사용하는 대회 평가 점수가 아니다.
- Micro 양성 F1(유효 출력만): **0.253521**; 판정 정확도(유효 출력만): **0.867500**.
- 전체 기대 1,200개 중 유효 1200개, 무효 0개. 무효 사유: `{"by_reason": {}, "by_status": {}}`.
- 양성 F1에서 `2TP+FP+FN=0`이면 값을 0으로 바꾸지 않고 미정의로 기록했다. 정확도는 유효 출력이 0개면 미정의다.

## 근거 관찰

- 구조상 유효한 출력 1200개 중 의미 제약 통과 1154개, 실패 46개.
- 연속 원문 substring 64개; 선택 후보 내부 substring 64개.
- reference 근거 문자열과 exact match 5개. 이 값은 관찰값이며, 다른 연속 원문 인용을 오답으로 정하지 않는다.
- v20 근거는 항상 null이어야 한다. v19·v21·v22·v23·v24는 판정 0이면 null, 판정 1이면 비어 있지 않은 500자 이하의 한 문서 연속 원문이어야 한다. 이 의미 검사는 구조 유효성과 별도로 기록했다.

## 실행 범위

- 입력 준비 3.88초, 모델 로드 63.88초, engine 입력 재검증 0.98초, 추론 46.37초. cache reset before run: True.
- 하드웨어 `NVIDIA GeForce RTX 5090`; 최대 문맥 32,768토큰; 완료 1,200/1,200 요청.
- 입력 1,224,717토큰 중 cached 506,848토큰(41.38%), 출력 30,543토큰. 실제 cache reuse 관찰이며 비캐시 대조가 없어 속도 향상 배수는 산출하지 않았다.
- 로컬 Gemma 4 26B A4B NVFP4 관찰이며 하드웨어와 정밀도가 다른 환경 또는 제출 환경의 정확도·속도를 보장하지 않는다.
- CMS가 만든 candidates.jsonl을 그대로 사용해 extraction을 생략했다. extraction 시간은 미측정이며, 원문 입력부터 extraction·추론까지의 전체 runtime은 검증하거나 산출하지 않았다.
- [source_alignment.json](<../../../../analysis/CMS_updated_cards_v19_v24_dev200_20260913/source_alignment.json>) 독립 점검은 200공고·1,200항목·2,879후보가 원문 문자 범위와 일치함을 확인했다. budget_truncated=true인 20개 후보(v21 2개, v23 18개)는 저장 line_end가 1,800자 절단 전 검색창 끝줄을 가리키지만 start:end와 실제 text는 정확히 일치했다. line 위치는 모델 입력에 없으며 원본 audit 값을 수정하지 않았다.
- v20의 완전관측=true이면서 budget_truncated=true인 입력은 PPS-DEV-088, PPS-DEV-135, PPS-DEV-171 세 건이다. 완전관측은 원본 문서 처리 상태이며 모델이 원문 전체를 보았다는 뜻이 아니다.
- v24 source에서 PPS-DEV-062/049 정답 메모 한 줄만 사용자 승인에 따라 삭제했다. 다른 판정 기준·예시·예외·불확실성 문구는 유지했다.
- predictions.jsonl raw 응답은 SHA256으로 동결한 뒤 평가했다. 재시도·결과 기반 repair·판정 대체는 하지 않았다.

## 산출물

- [metrics.json](<../../../../analysis/CMS_updated_cards_v19_v24_dev200_20260913/metrics.json>): 분모, 혼동행렬, F1, 정확도, 근거 관찰과 runtime.
- [evaluation_cases.jsonl](<../../../../analysis/CMS_updated_cards_v19_v24_dev200_20260913/evaluation_cases.jsonl>): 1,200개별 구조·분류·근거 결과와 보존 raw.
- [predictions.csv](<../../../../analysis/CMS_updated_cards_v19_v24_dev200_20260913/predictions.csv>): ID와 v19–v24 여섯 판정만 포함하며 무효 출력은 빈칸이다.
- [predictions_frozen.json](<../../../../analysis/CMS_updated_cards_v19_v24_dev200_20260913/predictions_frozen.json>): 평가 전에 확인한 원응답 해시와 행 수.

```bash
uv run --locked python -m nara.experiments.cms_updated_cards prepare --output analysis/CMS_updated_cards_v19_v24_dev200_20260913_NEW
uv run --locked python -m nara.experiments.cms_source_alignment --output analysis/CMS_updated_cards_v19_v24_dev200_20260913_NEW/source_alignment.json
uv run --locked python -m nara.experiments.cms_updated_cards run --output analysis/CMS_updated_cards_v19_v24_dev200_20260913_NEW
uv run --locked python -m nara.evaluation.cms_updated_cards --run-dir analysis/CMS_updated_cards_v19_v24_dev200_20260913_NEW
```
