# Operations

Moved from the former root README additions. Use [project map](project-structure.md) for targeted code/script navigation; [report index](reports/README.md) for evidence. All commands run from the repository root.

[나라장터 입찰공고 법령 위반사항 모니터링 대회](https://dacon.io/competitions/official/236754/overview/evaluation)에서
수상을 목표로 하는 프로젝트입니다. 공고문·첨부 문서·등록 정보를 읽고 24개 항목의 위반 여부와 근거 문구를 출력합니다.

## 실행 준비

프로젝트 루트에서 실행합니다. Python 3.12.13과 의존성은 다음 명령으로 준비합니다.
모델 설치와 로컬 GPU 검증 방법은 [환경 설정](<environment.md>)에 있습니다.

```bash
uv sync --locked
```

기본 실험에는 아래 로컬 파일이 필요합니다.

- 입력·평가: `data/dev.jsonl` 200건, `data/dev_labels.csv`, 항목표와 정답 스키마
- 모델: `models/gemma-4-26B-A4B-it-NVFP4`, `models/bge-m3`
- 검색 인덱스: `model/legal_index`

모델과 법령패키지를 준비한 뒤 검색 인덱스를 생성할 수 있습니다.

```bash
uv run --locked python -m nara.retrieval.index build
```

## 기본 실험

기본 실험은 **12그룹 · Thinking OFF · 공고 간 연속 배치 · 엔진16** 파이프라인입니다.

```bash
uv run --locked nara-experiment
```

현재 작업 트리의 프롬프트·규칙을 사용해 dev 200건을 실행합니다.
22개 항목은 12개 그룹으로 나누어 모델이 판단하고, v2·v3는 규칙으로 판정합니다. 출력은 실행 시각별
`output/experiments/` 하위 폴더에 저장하며, `--output-dir 새폴더`로 직접 지정할 수 있습니다.
첫 2개 공고의 첫 그룹을 준비하고, 후속 작업이 16개 이하가 되면 다음 공고의 첫 그룹을
선행 투입합니다. 최대 3개 공고·공통 원문 합계 48,000토큰을 유지하며, decode에서
전체 CUDA graph 사용을 확인합니다. 출력·재시도 한도는 2,048토큰, 문맥은 32,768토큰입니다.

8건 예비 실행 후 전체 200건을 측정합니다. 실패한 공고는 같은 설정으로 한 번 다시 실행하고,
그래도 실패하면 성공 그룹을 재사용하면서 실패 그룹만 한 번 더 실행합니다.
이 과정에서도 해결되지 않은 공고가 있으면 CSV와 평가 결과를 생성하지 않습니다.

실행 소스와 해시는 `source/`, `manifest.json`에, 결과와 계측은 `trace.jsonl`,
`report.json`, `request_timings.jsonl`, `scheduler.jsonl` 등에 저장합니다.
복구 시도는 `recovery_attempts.jsonl`에 남기며, 모두 성공하면 `submission.csv`와
`evaluation.json`, `errors.csv`를 실행 폴더에 생성하고, 평가 문서는 `docs/reports/` 아래 같은 실행 경로의 `evaluation.md`에 저장합니다.
본 추론 시간에는 재시도와 복구를 포함하고, 모델 로딩·사전 검사·예열·예비 실행은 제외합니다.

```bash
# GPU 모델을 로딩하지 않고 입력·문맥·소스 스냅샷만 검증
uv run --locked nara-experiment --prepare-only

# 8건 GPU 실행과 전체 graph 사용만 확인
uv run --locked nara-experiment --smoke-only
```

이 진입점은 로컬 dev200 전용이며, 입력·모델 경로와 그룹 설정이 코드에 지정되어 있습니다.
`src/cli.py`의 `--input`, `--limit`, `--thinking` 옵션은 이 명령에 적용되지 않습니다.
설정과 과거 측정 결과는 [파이프라인 문서](<experiments/prefix-pipeline.md>)를 참고합니다.
`src/experiments/benchmark_prefix_pipeline.py`는 과거 소스 해시를 검증하는 재현용 진입점입니다.
새 프롬프트·규칙 실험에는 `src/experiments/run_experiment.py`를 사용합니다.

## 프롬프트와 구현 위치

| 변경 대상 | 파일 |
|---|---|
| 기본 실험의 공통 지시문·항목별 판단 기준 | `src/inference/compact_criteria.json`의 `common`, `items` |
| 원문과 판단 기준의 배치 | `src/inference/compact_predictor.py`, `src/inference/prefix_predictor.py` |
| 12그룹 구성과 v2·v3 제외 | `src/experiments/config.py`의 `PLANS`, `configuration` |
| v2·v3 규칙 | `src/rules/qualification.py` |
| 공고 간 실행 순서·동시 처리 | `src/inference/prefix_pipeline.py`, `src/experiments/benchmark_prefix_pipeline.py` |
| 모델 실행·thinking 예산·캐시·계측 | `src/inference/engine.py` |
| 실패 복구·기록 집계 | `src/inference/recovery.py` |
| `src/cli.py`의 RAG 프롬프트 | `src/inference/prompt.txt` (`--legal-criteria` 사용 시 `src/inference/legal_criteria.json` 추가) |

`src/inference/prompt.txt`를 수정해도 기본 12그룹 실험의 프롬프트는 바뀌지 않습니다.
프롬프트나 규칙 변경 후에는 새 출력 폴더로 실행해 소스 스냅샷과 평가 결과를 함께 보관합니다.

## 최근 검증 결과

아래는 각 보고서에 보존된 실행 결과입니다. 현재 작업 트리의 새 실행 결과와 구분합니다.

- v2·v3 참가자격 구간 보완: 규칙만 dev200에 적용한 결과 F1은 각각 0.9333, 1.0000입니다.
  dev 오류를 보고 수정한 재검증이며, 모델을 포함한 전체 실행 결과는 아닙니다.
  [규칙 검증](<reports/analysis/rule_ab200_revised/report.md>), [표현 변화에 대한 취약성 점검](<reports/analysis/rule_robustness_review/review.md>).
- 로컬 엔진 정리 전후 dev200: 추론 296.61초 → 310.57초, Macro F1 0.26847 → 0.25984였습니다.
  한 쌍의 실행으로 속도·품질 변화의 원인을 확정하지 않습니다.
  [측정 및 검증](<experiments/engine-refactor.md>).
- Instant OFF와 thinking ON/예산 0 비교: 16개 항목에서 ON0는 재시도 포함 시간이 4.41% 늘었고,
  Macro F1은 0.13147 → 0.09453이었습니다. 후속 thinking 요청의 캐시 재사용 효과는 확인했으나
  기본 설정은 OFF를 유지합니다. [ON0 실험](<reports/analysis/on0_200/comparison.md>).
- 실패 복구를 `src/inference/recovery.py`로 통합했습니다. 저장된 GPU 결과 재생과 복구 시뮬레이션으로
  검증했으며, 이 변경에 대한 새 GPU 시간·F1 측정은 없습니다. [복구 검증](<../analysis/recovery_refactor/validation.json>).

## RAG 비교 실행·제출 진입점

동적 RAG 베이스라인과 제출 진입점은 프로젝트 루트의 `src/cli.py`입니다.
이 진입점은 기본 12그룹 실험과 별도이며, 24개 항목 모두 모델로 판단합니다. Gemma가 검색어를 만들면
로컬 BGE-M3와 법령 인덱스로 검색하고, 같은 대화에서 판단을 이어갑니다.

```bash
uv run --locked nara \
  --input data/dev.jsonl --limit 32 --output-dir output/dev32
```

기본값은 공고당 한 대화에서 24개 항목 판단, 검색 최대 2회·회당 4개 질의입니다.
Gemma와 BGE는 같은 GPU에 상주하며 생성과 검색을 번갈아 실행합니다.
결과는 지정한 새 출력 폴더의 submission.csv, trace.jsonl, report.json에 저장됩니다.

- `--item-group-size 6`: 6개 항목씩 별도 대화로 판단한 뒤 합칩니다.
- `--thinking`: thinking을 켭니다. 이때 기본 출력 한도는 4,096토큰이며, OFF는 2,048토큰입니다.
- `--search-rounds 0`: 검색 없는 비교 실험입니다.
- `--embed-device cpu`: 임베딩을 CPU에서 실행합니다.
- `--batch-size 8`: 함께 처리할 판단 대화 수입니다.

로컬 기본 경로는 models/gemma-4-26B-A4B-it-NVFP4, models/bge-m3,
model/legal_index입니다. `src/cli.py`는 `PPS_DATA_DIR`, `PPS_OUTPUT_DIR`, `PPS_MODEL_DIR`, `PPS_EMBED_DIR`를 읽으며,
검색 인덱스는 `--index`로 지정합니다. 기본 `--quantization auto`에서는 모델 설정에 양자화 정보가
없으면 INT8 로딩을 적용합니다. 기본 실험 파이프라인은 이 환경변수 경로 전환을 사용하지 않습니다.
원문이 문맥 한도를 넘거나 재시도 후에도 판단에 실패하면 실패 기록을 남기며 CSV를 생성하지 않습니다.

`uv run --locked nara` 실행과 배포 패키지에는 `src/inference/prompt.txt`가 포함됩니다.
32K, thinking off, 자율 검색 최대 2회로 dev 200건을 평가하려면 새 출력 폴더를 사용합니다.

```bash
uv run --locked nara \
  --input data/dev.jsonl --limit 200 --max-model-len 32768 \
  --search-rounds 2 --output-dir output/dev200
uv run --locked python -m nara.evaluation.evaluate_dev --run-dir output/dev200
```

평가 스크립트는 전체 입력·정답·예측 ID와 추론 로그를 대조합니다.
실행 폴더에 `evaluation.json`, 오탐·미탐의 `errors.csv`를 생성합니다. 항목별 평가 문서는 `docs/reports/` 아래 같은 실행 경로의 `evaluation.md`에 저장합니다.
정답 CSV는 추론에서 읽지 않습니다. 최초 실험은 `analysis/gemma4_rag_dev200_v1/`에 보존합니다.

`--require-search --search-rounds 1`은 첫 응답을 검색 요청으로 강제한 뒤 최종 판정합니다.
긴 공고는 검색어 생성 토큰 한도만 남은 문맥에 맞춰 줄이고, 원문과 최종 출력 예산을 유지합니다.
검색 결과를 문맥에 넣지 못하면 성공으로 처리하지 않습니다.
이전 실험과 비교: `uv run --locked python -m nara.evaluation.compare_dev_runs --baseline 이전폴더 --candidate 이번폴더`.

Thinking을 비교할 때 `--thinking --output-tokens 2048`을 사용하면 기존 출력 한도를 유지합니다.
이 모드는 vLLM thinking 예산을 일반 응답 최대 1,024토큰(출력 한도의 절반),
검색 전용 응답 최대 256토큰(출력 한도의 1/4)으로 제한해 JSON 공간을 남깁니다.
정상적으로 분리된 thinking 텍스트는 원문 대신 토큰 수와 예산을 trace.jsonl에 기록합니다.

세 실험 비교: [실험 보고서](<reports/analysis/gemma4_experiments_summary.md>).
Thinking의 최초 전체 실행은 199/200 성공했고, 실패 1건을 출력 4096으로 복구한 최종 결과는
`analysis/gemma4_rag_dev200_thinking_recovered/`에 있습니다. 최초 로그와 복구 예외도 보존했습니다.

## 혼합 5그룹 비교 실행

비교용 혼합 5그룹 실험은 최대 8개 요청이 모두 끝난 뒤 다음 묶음을 처리합니다.
Instant 4그룹은 thinking OFF, 나머지 6개 항목을 묶은 1그룹은 thinking ON/1,024토큰이며,
v2·v3는 규칙으로 판정합니다.
Instant 응답과 재시도 한도는 모두 512토큰입니다. 잘림·형식 오류 시 1회 재시도합니다.
Thinking 그룹의 전체 출력 한도는 2,048토큰(thinking 최대 1,024)입니다.
`--instant-output-tokens 2048`로 이전 instant 한도를 사용할 수 있습니다.
이 설정은 아래 혼합 실행에 적용하며, `src/cli.py`의 24항목 일괄 실행 기본값은 별도입니다.

```bash
uv run --locked python -m nara.experiments.run_batch_fallback --output-dir output/batch200
```

배치 변경에 따른 출력 차이와 prefill/decode 검증 결과는
[진단 보고서](<reports/analysis/prefill_decode_probe/report.md>)에 있습니다.

## 검증과 파일 보관

```bash
# 자동 테스트
uv run --locked python -m unittest discover -s tests -v

# RAG 베이스라인의 실제 GPU 동작 확인
uv run --locked python -m nara.tools.check_dynamic_rag
```

기본 파이프라인의 입력 검증과 GPU 예비 실행은 위의 `--prepare-only`, `--smoke-only`를 사용합니다.

Git에는 실행 코드, 테스트, 항목 스키마·법령 참고자료, 실험 보고서·메타데이터·코드 스냅샷을 보관합니다.
원시 모델 응답과 실행 JSONL·로그도 `analysis/` 아래 실험 기록으로 공유합니다. 반복된 `source/data/dev.jsonl` 사본, 원본 공고 데이터셋, 모델 가중치·검색 인덱스와 다운로드 ZIP은 로컬에 보관합니다.
실험을 재실행하려면 제공 데이터셋을 `data/`에 준비하고 모델과 검색 인덱스를 설치해야 합니다.
