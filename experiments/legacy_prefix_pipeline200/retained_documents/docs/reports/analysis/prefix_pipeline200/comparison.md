Artifacts: [run directory](<../../../../analysis/prefix_pipeline200>). Unlinked artifact names below are relative to that directory.

# 12그룹 OFF 공고 간 연속 배치·엔진16

| 구성 | 200건 추론 | Macro F1 | Micro F1 | FP / FN |
|---|---:|---:|---:|---:|
| 공고별 1→8→3 | 600.96초 | 0.283493 | 0.277372 | 201 / 96 |
| 공고별 1→11 | 561.62초 | 0.267665 | 0.258537 | 204 / 100 |
| 공고 간 연속 배치16 | 303.92초 | 0.268205 | 0.263682 | 196 / 100 |

1→11 대비 추론 시간 45.89% 감소. Macro 변화 +0.000540, Micro 변화 +0.005145.

그룹·프롬프트·모델·Thinking OFF·H6·출력2048 유지. 엔진16, step8192, CUDA FULL_AND_PIECEWISE. 최초2공고 첫 그룹을 준비하고 남은 후속 작업≤16이면 다음 공고 첫 그룹을 우선 제출. 최대3공고·공통 원문48000토큰의 논리적 입장 제한; 물리 KV 메모리 예약량을 뜻하지 않는다.
초기 준비 이후 198공고 중 195공고는 기존 공고가 GPU 계산을 모두 끝내기 전에 첫 prefill이 스케줄됐다. 그중 이전 공고 후속 그룹의 decode 구간과 prefill 구간이 겹친 공고는 180건. prefill까지 먼저 끝난 공고 195건. 프런트엔드 제출 시각뿐 아니라 엔진 scheduled_ts/first_token_ts/last_token_ts로 확인했다.
FULL graph 13675회, 실제16 decode토큰의 FULL graph 206회. 전체 graph 모드 분포 {'FULL': 13675, 'NONE': 943}. 긴 prefill·혼합 단계에는 부분 graph 또는 graph 미사용이 가능하며 모든 연산이 FULL이라는 뜻은 아니다.
입장 제한 이벤트 {'record_window': 64, 'source_token_budget': 23}; 실제 동시 요청 최대16; KV사용 최대51.34%; 재선점 요청 이벤트0. 제한 이벤트는 공고 수나 독점 GPU 대기 시간을 뜻하지 않는다.
최초 추론 303.92초·실패0건, 복구0.00초, 최종 실패0건. 모델 초기화63.65초는 추론에서 제외; 초기화+추론367.56초. 사전 검사·16요청 예열·8공고 smoke는 비교 시간에서 제외.
잘못된 응답3회, 실제 검색0회, 캐시 토큰 비율90.81%. 근거 불일치0·양성 비부재 근거 누락77건; F1은 이진 판정만 평가한다.

시간·F1은 각 설정 단일 로컬 실행 결과이며 배치/graph/스케줄 변경 효과를 분리한 인과 비교는 아니다. 점수 차이를 배치의 구조적 성능 차이로 단정하지 않는다. prefill/decode 구간은 요청 지연이며 GPU 커널의 동시 실행이나 독점 walltime을 뜻하지 않는다. 다음 prefill의 선행 시작은 GPU가 항상16요청으로 가득 찬다는 보장이 아니다.

재현: `MAX_JOBS=2 uv run --locked python scripts/benchmark_prefix_pipeline.py --output NEW_DIRECTORY`
검증: `python3 scripts/summarize_prefix_pipeline.py`

선행 시작 예외3건: PPS-DEV-28·121은 긴 원문 합계가48000토큰 입장 한도를 넘어 기존 공고 완료까지 기다렸다. PPS-DEV-137도 앞서 토큰 한도에 막혔고, 마지막 기존 요청 종료 전에 제출됐지만 엔진 prefill 시작은 종료보다18.3ms 늦었다. 소프트웨어 대기열 소진을 무조건 기다리는 구조는 없지만 메모리 입장 제한·제출 지연에 따른 빈 구간은 남는다.
