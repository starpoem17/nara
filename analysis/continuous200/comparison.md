# 완료 즉시 요청 보충 및 prefill 토큰 한도 실험

원문·영어 압축 판단 기준·5그룹·v2/v3 규칙 유지. Gemma4 NVFP4 RTX5090 context32768, thinking1024, output2048, max_num_seqs8, BGE GPU 상주. ON0 미적용.
48건은 입력 길이 순위로 선택한 pilot. 시간으로만 설정을 선택하고 이후200건 전체6항목/5그룹을 검증했다. 모든 시간은 모델 초기화를 제외한다.

## 48건 대조

|실행|한 스텝 토큰 한도|시간|평균 prefill|평균 decode|평균 엔진 대기|최대 KV 사용률|
|---|---:|---:|---:|---:|---:|---:|
|pilot_barrier_8192|8192|121.21s|1.313s|16.381s|1.963s|72.4%|
|pilot_continuous_2048|2048|119.60s|0.819s|17.857s|1.045s|52.0%|
|pilot_continuous_8192|8192|117.61s|0.825s|18.179s|0.395s|75.0%|
|pilot_continuous_16384|16384|130.34s|0.946s|16.996s|2.617s|98.1%|

|실행|평균 실행 요청|평균 일반 대기|평균 Deferred|
|---|---:|---:|---:|
|pilot_barrier_8192|6.86|0.00|0.87|
|pilot_continuous_2048|7.46|0.00|0.44|
|pilot_continuous_8192|7.71|0.00|0.17|
|pilot_continuous_16384|6.49|0.00|1.00|

## 토큰 한도와 메모리 수용량

|스텝 토큰 한도|Activation 프로파일|KV pool|엔진 계산32K 동시성|
|---|---:|---:|---:|
|2048|1.49GiB|10.20GiB|6.36|
|8192|1.94GiB|9.75GiB|2.47|
|16384|3.84GiB|7.85GiB|1.14|

이 모델은30층 중25층 sliding-window(1024),5층 full attention이다. 설치된 vLLM의 sliding KV 예약은 최근1023토큰 + 처리 중인 토큰 상한(동시 스텝 수×max_num_batched_tokens)에 의존한다. 작은 prefill 한도는 activation뿐 아니라 sliding KV의 최악 예약량도 줄인다. 표의 동시성은 초기화 시 계산된32K 기준 값이며 실제 모든 시점의 동시 실행 수나 처리속도와 같지 않다.


## 전체200 검증

|실행|시간|Macro F1|Micro F1|점수 범위|
|---|---:|---:|---:|---|
|기존6항목 ON1024 8건 묶음|503.51s|0.5006|0.4865|6항목|
|six_continuous_8192|494.46s|0.3915|0.3947|6항목|
|mixed_continuous_8192|798.92s|0.2627|0.2725|24항목|

## 이전 전체24항목 실행과 비교

|실행|시간|Macro F1|Micro F1|
|---|---:|---:|---:|
|이전5그룹 ON1024 직렬|2404.81s|0.2740|0.2952|
|이전5그룹 ON256 배치8|709.07s|0.2504|0.2638|
|이전5그룹 전부 OFF|447.14s|0.1986|0.2462|
|이전12그룹 OFF|600.96s|0.2835|0.2774|
|이전24항목 일괄 ON + H6|717.35s|0.2552|0.3281|
|이번5그룹 ON1024 연속 처리|798.92s|0.2627|0.2725|

이전5그룹 ON1024는 thinking 직렬 실행이었다. 이번 전체 시간 차이에는 thinking 병렬화와 그룹/모드 사이 대기 제거가 함께 포함되므로, 완료 즉시 보충만의 개선율로 해석하지 않는다. 보충만의 비교는 위6항목 8건 묶음 대조를 참조한다.
양성 근거 상태: {"nonempty": 80, "invalid": 0, "positive_nonabsence_missing": 68}. 실패 예측을0으로 채우지 않았다. F1은 이진 판정 점수이며 모든 양성 근거의 충실성을 보장하지 않는다.

복구: 최초 실행 실패 그룹만 원래 프롬프트/모드/토큰 한도로 단독 재시도했다. 추론 17.320초는 표에 포함, 별도 모델 초기화 27.593초는 제외. 성공한 공고는 변경하지 않았으며 first_pass/에 원본을 보존했다. scheduler 통계와 trace_completed는 최초 실행, trace.jsonl/request_timings/lifecycle는 복구 병합 결과이다.


## 입력 길이별 요청 지연

|실행|입력 길이|요청 수|평균 prefill|평균 decode|평균 엔진 대기|
|---|---|---:|---:|---:|---:|
|pilot_barrier_8192|<=8K|22|0.778s|16.028s|1.656s|
|pilot_barrier_8192|8K..16K|13|1.335s|16.472s|2.332s|
|pilot_barrier_8192|>16K|13|2.195s|16.888s|2.113s|
|pilot_continuous_2048|<=8K|22|0.316s|17.377s|0.978s|
|pilot_continuous_2048|8K..16K|13|0.715s|17.716s|1.421s|
|pilot_continuous_2048|>16K|13|1.774s|18.811s|0.781s|
|pilot_continuous_8192|<=8K|22|0.333s|17.400s|0.534s|
|pilot_continuous_8192|8K..16K|13|0.744s|18.639s|0.499s|
|pilot_continuous_8192|>16K|13|1.738s|19.039s|0.057s|
|pilot_continuous_16384|<=8K|22|0.579s|16.629s|1.809s|
|pilot_continuous_16384|8K..16K|13|0.937s|16.755s|2.681s|
|pilot_continuous_16384|>16K|13|1.575s|17.857s|3.921s|

## 요청 보충 검증

- six_continuous_8192: 첫 완료 후 12.35ms에9번째 요청 제출; 당시 첫8건 중 7건 미완료. 실제 최대 in-flight 8.
- mixed_continuous_8192: 첫 완료 후 15.20ms에9번째 요청 제출; 당시 첫8건 중 7건 미완료. 실제 최대 in-flight 8.

기존6항목 ON1024는 모든200건의 관측 thinking 본문이1020~1022토큰이었다. 생성 길이가 거의 같아 묶음의 느린 마지막 요청을 기다리는 손실이 제한적이다. 연속 처리는 대기를 줄이지만 신규 prefill과 기존 decode가 자원을 공유하므로 개별 decode 지연은 늘 수 있다.


## 판단

현재 기본값은 최대8개 요청 + 스텝8192토큰 + chunked prefill이다. pilot에서2048은8192보다 약1.7% 느린 대신 메모리 여유가 더 컸고,16384는 약10.8% 느렸다. 장문 비중이 커질 때2048은 유력한 대안이지만 전체200으로 따로 검증한 결과는 아니다.
완료 즉시 보충의 속도 개선은 같은6항목200건에서1.8%였다. 이6항목 Macro F1은0.5006→0.3915, Micro F1은0.4865→0.3947로 하락해 정확도 보존을 주장할 수 없다. 입력 토큰 및 실제SamplingParams 대조는 adapter_parity.json 참조. 기존 generate도 내부에서FINAL_ONLY로 정규화되므로 반환 옵션이 유효 생성 설정 차이는 아니다. 배치 구성/수치 연산 경로에 따른 변동 가능성은 있으나 이 실험으로 단독 원인을 확정하지 않았다.
이번 전체24항목 결과는 이전12그룹OFF보다 느리고 Macro/Micro F1도 낮았다. 요청 보충 구조는 구현했지만 이번 혼합 설정을 정확도·시간 최선의 설정으로 승격할 근거는 없다.


## 해석 범위

- max_num_batched_tokens는 한 스텝의 prefill+decode 토큰 예산이다. 전체 문서 길이/출력 한도/동시 요청 개수와 다르다. 긴 입력은 chunked prefill로 나눠 처리된다.
- 긴 입력은 더 많은 prefill 스텝과 KV 공간을 요구한다. 캐시가 있으면 새로 계산할 토큰은 줄지만 저장 공간과 decode의 attention 비용은 남는다.
- 작은 토큰 예산은 decode와 긴 prefill의 교대 간격을 줄일 수 있지만 prefill 스텝 수가 증가한다. 큰 예산은 prefill 처리량을 높일 수 있지만 activation 공간이 늘고 KV 풀과 동시성에 영향을 줄 수 있다. 초기화 메모리 수치는 각 pilot 로그 참조.
- 요청별 prefill=scheduled→first token, decode=first→last token. 동시 실행 구간이 겹친다. 엔진 대기에는 아직 엔진에 제출하지 않은 application queue 시간은 포함되지 않는다.
- Running은 prefill 중인 요청도 포함한다. Deferred에는 grammar 준비 등이 포함되므로 메모리 부족으로 단정하지 않는다. KV 사용률은 할당된 pool 대비 비율이며 전체 GPU peak VRAM이 아니다.
- 스케줄 변경은 greedy 판정에도 영향을 줄 수 있다. pilot48의 단회 시간 선택이며 절대적 최적값/대회 통과를 보장하지 않는다. 전체200 점수도 같은 개발 데이터이다.
- pilot8192는 같은 엔진에서 barrier 다음 continuous 순서로 단회 실행했다. Prefix cache는 초기화했지만 컴파일/grammar 등 다른 warm 상태의 순서 효과는 완전히 제거하지 않았다.
- 46 tests passed including refill under a slow first request, RAG/retry, modes/cache seed, context failure. validation.json: full input/source/rules/events/refill checks.
- 실행: scripts/benchmark_continuous.py --kind mixed --tokens 8192. 완료된 출력 디렉터리는 덮어쓰지 않는다. 새 데이터/다른 운영 경로에는 ContinuousPredictor를 동일 인터페이스로 연결한다.
