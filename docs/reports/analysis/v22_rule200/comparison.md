Artifacts: [run directory](<../../../../analysis/v22_rule200>). Unlinked artifact names below are relative to that directory.

# v22 rule comparison

Dev200: 5 positive, 195 negative. Success is reported as positive F1 and accuracy. No new LLM inference.

Initial regex was frozen before inspecting per-record v22 labels, after reading input phrasing and aggregate historical scores. Revised regex was adjusted after inspecting dev errors: it is a development fit, not independent validation.

Negotiation: either contract/award metadata contains 협상, or a document contains 협상에 의한 계약. Briefing/mandatory restriction must be linked in a local text span. Revised extraction also recognizes attendance as an entry in the eligibility section and excludes evaluation-target exclusion. These are bounded regex approximations, not a complete semantic parser.

| Run | N | F1 | Accuracy | TP | FP | FN |
|---|---:|---:|---:|---:|---:|---:|
| rule | 200 | 66.67% | 98.50% | 3 | 1 | 2 |
| rule_revised | 200 | 100.00% | 100.00% | 5 | 0 | 0 |
| analysis/colleague200/evaluation.json | 200 | 83.33% | 99.00% | 5 | 2 | 0 |
| analysis/common_prompt_v2_512_final/candidate/evaluation.json | 200 | 88.89% | 99.50% | 4 | 0 | 1 |
| analysis/compact200/groups12_off/evaluation.json | 200 | 61.54% | 97.50% | 4 | 4 | 1 |
| analysis/compact200/groups12_off_h6/evaluation.json | 200 | 76.92% | 98.50% | 5 | 3 | 0 |
| analysis/compact200/groups7_off/evaluation.json | 200 | 76.92% | 98.50% | 5 | 3 | 0 |
| analysis/compact200/groups9_off/evaluation.json | 200 | 71.43% | 98.00% | 5 | 4 | 0 |
| analysis/compact200/ungrouped_on/evaluation.json | 200 | 80.00% | 99.00% | 4 | 1 | 1 |
| analysis/compact200/ungrouped_on_h6/evaluation.json | 200 | 88.89% | 99.50% | 4 | 0 | 1 |
| analysis/continuous200/mixed_continuous_8192/evaluation.json | 200 | 61.54% | 97.50% | 4 | 4 | 1 |
| analysis/gemma4_rag_dev200_forced1/evaluation.json | 200 | 33.33% | 98.00% | 1 | 0 | 4 |
| analysis/gemma4_rag_dev200_thinking_recovered/evaluation.json | 200 | 57.14% | 98.50% | 2 | 0 | 3 |
| analysis/gemma4_rag_dev200_v1/evaluation.json | 200 | 75.00% | 99.00% | 3 | 0 | 2 |
| analysis/hybrid200/composite_six_off/evaluation.json | 200 | 47.06% | 95.50% | 4 | 8 | 1 |
| analysis/hybrid200/composite_six_on1024_batch8/evaluation.json | 200 | 83.33% | 99.00% | 5 | 2 | 0 |
| analysis/hybrid200/composite_six_on256/evaluation.json | 200 | 61.54% | 97.50% | 4 | 4 | 1 |
| analysis/hybrid200/main/evaluation.json | 200 | 90.91% | 99.50% | 5 | 1 | 0 |
| analysis/hybrid200/optimized/evaluation.json | 200 | 61.54% | 97.50% | 4 | 4 | 1 |
| analysis/hybrid200/optimized_off/evaluation.json | 200 | 55.56% | 96.00% | 5 | 8 | 0 |
| analysis/prefix200/evaluation.json | 200 | 60.00% | 98.00% | 3 | 2 | 2 |
| analysis/prefix200_batch11/evaluation.json | 200 | 40.00% | 97.00% | 2 | 3 | 3 |
| analysis/prefix_pipeline200/evaluation.json | 200 | 83.33% | 99.00% | 5 | 2 | 0 |
| output/experiments/engine-refactor-after-20260911/evaluation.json | 200 | 50.00% | 98.00% | 2 | 1 | 3 |
| output/experiments/engine-refactor-before-20260911/evaluation.json | 200 | 90.91% | 99.50% | 5 | 1 | 0 |

## Latest matched comparison (198 successful notices)

| Run | N | F1 | Accuracy | TP | FP | FN |
|---|---:|---:|---:|---:|---:|---:|
| original | 198 | 72.73% | 98.48% | 4 | 2 | 1 |
| candidate | 198 | 88.89% | 99.49% | 4 | 0 | 1 |
| rule | 198 | 66.67% | 98.48% | 3 | 1 | 2 |
| rule_revised | 198 | 100.00% | 100.00% | 5 | 0 | 0 |

## Initial extraction errors

- PPS-DEV-26: eligibility list says 사업설명회에 참석한 자; the initial pattern required an explicit only/eligible phrase.
- PPS-DEV-135: 참석하지 아니한 was missing from the initial absence variants.
- PPS-DEV-193: post-submission presentation evaluation was mistaken for a pre-bid briefing; revised scope excludes evaluation-target exclusion.

All 200 predictions have distinct matching IDs; every positive quote is a source substring <=500 characters. All historical full200 v22 metrics above were recomputed from saved CSVs; stored input/label hashes checked when available. Latest original is restricted to 198 successful traces; failures are not filled with zero.

Reproduce: `python3 analysis/v22_rule200/evaluate.py`. Artifacts include both rule versions, per-notice evidence, metrics and hashes. No production inference changes. Only five positives: independent testing is needed before treating perfect dev fit as generalization.
