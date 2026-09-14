Artifacts: [run directory](<../../../../../output/experiments/v9-cod512-20260912>). Unlinked artifact names below are relative to that directory.

# v9/v19 isolated dev200, output512

Historical comparison: prompt, output cap (2048 to 512), scheduling differ.

| Item | Arm | F1 | Precision | Recall | TP | FP | FN |
|---|---|---:|---:|---:|---:|---:|---:|
| v9 | baseline | 0.370370 | 0.238095 | 0.833333 | 5 | 16 | 1 |
| v9 | candidate | 0.416667 | 0.277778 | 0.833333 | 5 | 13 | 1 |
| v19 | baseline | 0.470588 | 0.363636 | 0.666667 | 4 | 7 | 2 |
| v19 | candidate | 0.526316 | 0.384615 | 0.833333 | 5 | 8 | 1 |

Inference 220.643s; load 27.054s. Changed judgments: 19.

Runtime: {"records": 200, "prediction_seconds": 220.64255459599917, "load_seconds": 27.053528858999925, "failed_ids": [], "model_turns": 206, "invalid_responses": 6, "searches": 0, "length_stops": 6, "thinking_tokens": 47486, "output_tokens": 61357}
