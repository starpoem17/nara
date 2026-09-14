Artifacts: [run directory](<../../../../../output/experiments/v9-group512-20260912>). Unlinked artifact names below are relative to that directory.

# v9/v19 isolated dev200, output512

Historical comparison: prompt, output cap (2048 to 512), scheduling differ.

| Item | Arm | F1 | Precision | Recall | TP | FP | FN |
|---|---|---:|---:|---:|---:|---:|---:|
| v9 | baseline | 0.370370 | 0.238095 | 0.833333 | 5 | 16 | 1 |
| v9 | candidate | 0.444444 | 0.285714 | 1.000000 | 6 | 15 | 0 |
| v19 | baseline | 0.470588 | 0.363636 | 0.666667 | 4 | 7 | 2 |
| v19 | candidate | 0.363636 | 0.400000 | 0.333333 | 2 | 3 | 4 |

Inference 152.521s; load 30.028s. Changed judgments: 12.

Runtime: {"records": 200, "prediction_seconds": 152.52087105900046, "load_seconds": 30.027537087999917, "failed_ids": [], "model_turns": 200, "invalid_responses": 0, "searches": 0, "length_stops": 0, "thinking_tokens": 0, "output_tokens": 11609}

Interpretation: v9 fixed 3 FP and added 2 FP; its sole recovered FN (PPS-DEV-051) cites prior delivery experience, not a specific model restriction. Thus higher label F1 does not establish better semantic detection. v19 lost 2 TP (034,037) while removing 4 FP. The unweighted two-item mean F1 decreased from 0.420479 to 0.404040.

Validation: 200 unique records; only v9/v19; all request caps512, thinking0; maximum actual output449; no invalid responses, length stops, searches or recovery. All nonempty evidence is an exact source substring (semantic relevance is separate). v9 positive evidence missing12/21; v19 missing2/5. Sources/input hashes verified; validation.json.
