https://dacon.io/competitions/official/236754/overview/evaluation

위 데이콘 공모전에서 수상을 노리는 프로젝트

동적 RAG 베이스라인은 프로젝트 루트의 script.py로 실행합니다. Gemma가 검색어를 만들면
로컬 BGE-M3와 법령 인덱스로 검색하고, 같은 대화에서 판단을 이어갑니다.

```bash
uv run --locked python script.py \
  --input data/dev.jsonl --limit 32 --output-dir output/dev32
```

기본값은 공고당 한 대화에서 24개 항목 판단, 검색 최대 2회·회당 4개 질의입니다.
Gemma와 BGE는 같은 GPU에 상주하며 생성과 검색을 번갈아 실행합니다.
결과는 지정한 새 출력 폴더의 submission.csv, trace.jsonl, report.json에 저장됩니다.

- --item-group-size 6: 6개 항목씩 별도 대화로 판단한 뒤 합칩니다.
- --thinking: thinking을 켭니다. 기본값은 꺼짐입니다.
- --search-rounds 0: 검색 없는 비교 실험입니다.
- --embed-device cpu: 임베딩을 CPU에서 실행합니다.
- --batch-size 8: 함께 처리할 판단 대화 수입니다.

로컬 기본 경로는 models/gemma-4-26B-A4B-it-NVFP4, models/bge-m3,
model/legal_index입니다. 대회 환경에서는 PPS_* 경로를 사용하고 제공된
미양자화 Gemma에 INT8 로딩을 적용합니다. 대회 GPU의 속도 검증은 아직 필요합니다.
원문이 문맥 한도를 넘거나 재시도 후에도 판단에 실패하면 실패 기록을 남기며 CSV를 생성하지 않습니다.

자동 검증: `uv run --locked python -m unittest discover -s tests -v`
실제 GPU 동작 검증: `uv run --locked python -m scripts.check_dynamic_rag`

현재 판단 프롬프트는 `nara/prompt.txt`에 있습니다. 실행·패키징 시 `nara/`와 함께 포함합니다.
32K, thinking off, 자율 검색 최대 2회로 dev 200건을 평가하려면 새 출력 폴더를 사용합니다.

```bash
uv run --locked python script.py \
  --input data/dev.jsonl --limit 200 --max-model-len 32768 \
  --search-rounds 2 --output-dir output/dev200
uv run --locked python -m scripts.evaluate_dev --run-dir output/dev200
```

평가 스크립트는 전체 입력·정답·예측 ID와 추론 로그를 대조합니다.
`evaluation.json`, 항목별 결과를 담은 `evaluation.md`, 오탐·미탐의 `errors.csv`를 생성합니다.
정답 CSV는 추론에서 읽지 않습니다. 최초 실험은 `analysis/gemma4_rag_dev200_v1/`에 보존합니다.

`--require-search --search-rounds 1`은 첫 응답을 검색 요청으로 강제한 뒤 최종 판정합니다.
긴 공고는 검색어 생성 토큰 한도만 남은 문맥에 맞춰 줄이고, 원문과 최종 출력 예산을 유지합니다.
검색 결과를 문맥에 넣지 못하면 성공으로 처리하지 않습니다.
이전 실험과 비교: `uv run --locked python -m scripts.compare_dev_runs --baseline 이전폴더 --candidate 이번폴더`.

Thinking을 비교할 때 `--thinking --output-tokens 2048`을 사용하면 기존 출력 한도를 유지합니다.
이 모드는 vLLM thinking 예산을 일반 응답 최대 1,024토큰(출력 한도의 절반),
검색 전용 응답 최대 256토큰(출력 한도의 1/4)으로 제한해 JSON 공간을 남깁니다.
정상적으로 분리된 thinking 텍스트는 원문 대신 토큰 수와 예산을 trace.jsonl에 기록합니다.

세 실험 비교: [실험 보고서](analysis/gemma4_experiments_summary.md).
Thinking의 최초 전체 실행은 199/200 성공했고, 실패 1건을 출력 4096으로 복구한 최종 결과는
`analysis/gemma4_rag_dev200_thinking_recovered/`에 있습니다. 최초 로그와 복구 예외도 보존했습니다.

현재 혼합 5그룹 실험은 최대 8개 요청이 모두 끝난 뒤 다음 묶음을 처리합니다.
Instant 4그룹은 thinking OFF, 나머지 6개 feature 그룹은 thinking ON/1,024토큰이며,
v2·v3는 규칙으로 판정합니다.

```bash
uv run --locked python scripts/run_batch_fallback.py --output-dir output/batch200
```

배치 변경에 따른 출력 차이와 prefill/decode 검증 결과는
[진단 보고서](analysis/prefill_decode_probe/report.md)에 있습니다.

Git에는 실행 코드, 테스트, 항목 스키마·법령 참고자료, 실험 보고서·메타데이터·코드 스냅샷을 보관합니다.
공고 데이터셋, 모델 가중치·검색 인덱스, 다운로드 ZIP, 원시 JSONL 추론 기록과 로그는 로컬에 보관합니다.
실험을 재실행하려면 제공 데이터셋을 `data/`에 준비하고 모델과 검색 인덱스를 설치해야 합니다.
