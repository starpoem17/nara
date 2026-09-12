Artifacts: [run directory](<../../../../../output/experiments/v9-thinking512-20260912>). Unlinked artifact names below are relative to that directory.

# v9/v19 isolated dev200, output512

Historical comparison: prompt, output cap (2048 to 512), scheduling differ.

| Item | Arm | F1 | Precision | Recall | TP | FP | FN |
|---|---|---:|---:|---:|---:|---:|---:|
| v9 | baseline | 0.370370 | 0.238095 | 0.833333 | 5 | 16 | 1 |
| v9 | candidate | 0.400000 | 0.263158 | 0.833333 | 5 | 14 | 1 |
| v19 | baseline | 0.470588 | 0.363636 | 0.666667 | 4 | 7 | 2 |
| v19 | candidate | 0.400000 | 0.333333 | 0.500000 | 3 | 6 | 3 |

Inference 210.684s; load 26.876s. Changed judgments: 18.

Runtime: {"records": 200, "prediction_seconds": 210.6842727739986, "load_seconds": 26.875844801999847, "failed_ids": [], "model_turns": 201, "invalid_responses": 1, "searches": 0, "length_stops": 1, "thinking_tokens": 51026, "output_tokens": 63070}
