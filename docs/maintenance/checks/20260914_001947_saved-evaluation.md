# Does the current evaluator reproduce this saved result?

Current judgment: **not assessed**. Execution success does not establish adoption.

Run ID: `20260914_001947_saved-evaluation`. Planned comparison: saved.

## Question and conditions

Does the current evaluator reproduce this saved result?

## Judgment history

The run was created with the conditions below; no results have been assessed.

## Limits

Do not infer unseen-data performance or repeatability from one execution.

<!-- execution:start -->
## Execution evidence

Execution status: **complete**. Judgment: **not assessed**.

[Run directory](<../evidence/20260914_001947_saved-evaluation>) · [Metadata](<../evidence/20260914_001947_saved-evaluation/run.json>)

| Condition | Status | Attempts | Settings |
|---|---|---:|---|
| [saved](<../evidence/20260914_001947_saved-evaluation/conditions/saved>) | complete | 1 | `{"artifacts": "experiments/legacy_prefix_pipeline200", "operation": "CPU evaluation; no model generation"}` |

Sources recorded; fresh inference reproducibility not verified.
<!-- execution:end -->

<!-- generated-7b06ad6a6c6c85df:start -->
## conditions/saved/attempt_1/evaluation.md

Artifacts: [condition directory](<../evidence/20260914_001947_saved-evaluation/conditions/saved/attempt_1>).

# Saved dev evaluation: 200 notices

- Macro positive F1: **0.268205**; Micro F1: 0.263682.
- Label accuracy: 93.83%; exact-match notices: 74/200.
- False positives: 196; false negatives: 100.
- Notices with retrieval: 0; search calls: 0; queries: 0.
- Recorded loading plus inference: 367.56s; inference: 303.92s.
- Model: models/gemma-4-26B-A4B-it-NVFP4; GPU: NVIDIA GeForce RTX 5090; context: 32768; thinking: False.

These times and generation settings come from the saved execution report; evaluation does not run the model.

## Per-item observations

| Item | Name | Positive labels | Positive predictions | Precision | Recall | F1 | FP | FN |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| v1 | 참가자격 특정기관 제한 | 7 | 8 | 0.250 | 0.286 | 0.267 | 6 | 5 |
| v2 | 고시금액 미만 실적제한 | 7 | 8 | 0.625 | 0.714 | 0.667 | 3 | 2 |
| v3 | 실적제한 1배수 이상 | 8 | 6 | 1.000 | 0.750 | 0.857 | 0 | 2 |
| v4 | 고시금액 이상 특정기관, 특정실적 | 6 | 9 | 0.556 | 0.833 | 0.667 | 4 | 1 |
| v5 | 고시금액 이상 지역제한 | 7 | 12 | 0.333 | 0.571 | 0.421 | 8 | 3 |
| v6 | 고시금액 미만 지역제한 시,군,구 | 6 | 10 | 0.100 | 0.167 | 0.125 | 9 | 5 |
| v7 | 고시금액 미만 지역제한 인접 확대 | 7 | 6 | 0.333 | 0.286 | 0.308 | 4 | 5 |
| v8 | 중복제한 (실적+지역) | 6 | 15 | 0.200 | 0.500 | 0.286 | 12 | 3 |
| v9 | 과업지시서 특정 모델명 명시 | 6 | 22 | 0.227 | 0.833 | 0.357 | 17 | 1 |
| v10 | 중기간 경쟁제품 입찰 직생 없음 | 7 | 24 | 0.083 | 0.286 | 0.129 | 22 | 5 |
| v11 | 중기간 경쟁제품 입찰 중소 없음 | 6 | 8 | 0.000 | 0.000 | 0.000 | 8 | 6 |
| v12 | 일반제품 직생 제한 | 6 | 0 | 0.000 | 0.000 | 0.000 | 0 | 6 |
| v13 | 중기간 경쟁제품 소기업, 소상공인 제한 | 6 | 0 | 0.000 | 0.000 | 0.000 | 0 | 6 |
| v14 | 고시금액 이상 일반물품 중소기업 제한 | 8 | 14 | 0.071 | 0.125 | 0.091 | 13 | 7 |
| v15 | 1억 이상- 고시금액미만 소기업 제한 | 6 | 8 | 0.000 | 0.000 | 0.000 | 8 | 6 |
| v16 | 1억 이상- 고시금액미만 중소기업 제한 없음 | 6 | 16 | 0.000 | 0.000 | 0.000 | 16 | 6 |
| v17 | 1억원 미만 일반물품 중소기업 제한 | 6 | 13 | 0.000 | 0.000 | 0.000 | 13 | 6 |
| v18 | 1억원 미만 일반물품 소기업 제한 없음 | 7 | 31 | 0.097 | 0.429 | 0.158 | 28 | 4 |
| v19 | 물품공급 확약서 입찰 시 제출 | 6 | 11 | 0.364 | 0.667 | 0.471 | 7 | 2 |
| v20 | 입찰참가자격 (SW) | 5 | 4 | 0.250 | 0.200 | 0.222 | 3 | 4 |
| v21 | 공동 5% (10%) | 6 | 0 | 0.000 | 0.000 | 0.000 | 0 | 6 |
| v22 | 현장설명회 참석업체 (자격으로 제한 여부) * 계약방법 협상만 적용 | 5 | 7 | 0.714 | 1.000 | 0.833 | 2 | 0 |
| v23 | 현장설명회 (공고기간) * 계약방법 협상 + 계약법 지방만 적용 | 5 | 8 | 0.375 | 0.600 | 0.462 | 5 | 2 |
| v24 | 공고서와 나라장터 입력값 상이 | 8 | 9 | 0.111 | 0.125 | 0.118 | 8 | 7 |

## Interpretation limits

The development set does not establish holdout performance. Source-substring checks do not establish legal correctness or qualitative evidence scores.
Evidence checks: `{"nonempty": 89, "invalid": 0, "positive_nonabsence_missing": 77}`; postprocessing dropped 76 evidence fields.
All 200 IDs and CSV/trace judgments match. Failed predictions are not replaced with zero. Undefined per-item F1 is zero and all24 items enter the mean.

## Evidence and replay

[Machine evaluation](<../evidence/20260914_001947_saved-evaluation/conditions/saved/attempt_1/evaluation.json>), [error cases](<../evidence/20260914_001947_saved-evaluation/conditions/saved/attempt_1/errors.csv>), [predictions](<../evidence/20260914_001947_saved-evaluation/conditions/saved/attempt_1/submission.csv>), [execution settings](<../evidence/20260914_001947_saved-evaluation/conditions/saved/attempt_1/report.json>).
The owning run metadata identifies source contents, evaluation inputs, and the original command. Use the saved-output replay command in docs/operations.md for a historical read-only run.
<!-- generated-7b06ad6a6c6c85df:end -->
