# How do H6 rules affect the selected compact grouping and ungrouped condition?

Current judgment: **H6 was adopted in the grouped baseline within the recorded development scope; full-run deltas are not solely causal rule effects.**

Reason and scope: Baseline scores selected the grouped condition before the H6 sweep; v2/v3 model judgments were replaced with frozen H6 rules. Historical local development evidence; no unseen-data or competition-server generalization is established.

## Current interpretation and material history

Groups12H6 MacroF1=.28444815 and ungroupedH6=.25524869. v2F1=.666667/v3=.857143; rules were frozen before scoring and not tuned after these results. Unchanged11 groups still changed195/4000 bits across runs with identical prompts/schemas, so isolate direct saved-output replacement from full-rerun gains. No L40S/holdout guarantee.

## Run identity and conditions

Run ID: `legacy_compact_h6`. Historical start time: **unknown**. The available metadata does not establish an orchestration start; initialization/log/preparation timestamps were not substituted. Execution month: September 2026, supported by the original project records and original run names.

Planned/recorded conditions: groups12_off_h6, ungrouped_on_h6. Preserve condition-specific manifests, input snapshots, traces, and budgets; do not infer identical conditions from the folder name.

## Actions, observations, and judgment history

The original execution and analysis artifacts below retain their original bytes. The migration changes their location and introduces explicit run identity; it is not a rerun, re-score, or adoption decision.

H6 was adopted in the grouped baseline within the recorded development scope; full-run deltas are not solely causal rule effects.

Historical comparison and interpretation documents are linked from the area index. Their original bytes are also retained in the migration document archive. Current judgment above governs reuse; historical measurements alone do not override a later withdrawal or narrowed scope.

## Run-specific interpretation

Consult the condition-level observations and retained original interpretation linked below. Missing execution settings are not reconstructed from present defaults.

## Evidence and reproducibility

[Retained execution directory](<../../../../experiments/legacy_compact_h6>) · [Execution metadata and original-file hashes](<../../../../experiments/legacy_compact_h6/run.json>)

Source snapshots and original manifests retain historical paths. Do not rewrite their hashes or commands. New code and instructions use the migration mapping; old commands need not execute unchanged. Locally excluded data/model assets require separately restored matching content in another checkout. Exact GPU reproducibility has not been verified by this migration.

Essential evidence is retained here, not solely in temporary work or Git-excluded outputs. The migration inventory identifies every original location and checksum. Task verification and temporary paths are listed in the metadata.

## Retained artifacts

- [groups12_off_h6/evaluation.json](<../../../../experiments/legacy_compact_h6/groups12_off_h6/evaluation.json>): original execution or analysis evidence.
- [groups12_off_h6/report.json](<../../../../experiments/legacy_compact_h6/groups12_off_h6/report.json>): original execution or analysis evidence.
- [groups12_off_h6/submission.csv](<../../../../experiments/legacy_compact_h6/groups12_off_h6/submission.csv>): original execution or analysis evidence.
- [groups12_off_h6/trace.jsonl](<../../../../experiments/legacy_compact_h6/groups12_off_h6/trace.jsonl>): original execution or analysis evidence.
- [selection.json](<../../../../experiments/legacy_compact_h6/selection.json>): original execution or analysis evidence.
- [ungrouped_on_h6/evaluation.json](<../../../../experiments/legacy_compact_h6/ungrouped_on_h6/evaluation.json>): original execution or analysis evidence.
- [ungrouped_on_h6/report.json](<../../../../experiments/legacy_compact_h6/ungrouped_on_h6/report.json>): original execution or analysis evidence.
- [ungrouped_on_h6/submission.csv](<../../../../experiments/legacy_compact_h6/ungrouped_on_h6/submission.csv>): original execution or analysis evidence.
- [ungrouped_on_h6/trace.jsonl](<../../../../experiments/legacy_compact_h6/ungrouped_on_h6/trace.jsonl>): original execution or analysis evidence.

## Recorded evaluation values

These are values read from retained evaluations, not newly computed results.

| Evidence | Macro F1 | Micro F1 |
|---|---:|---:|
| [groups12_off_h6](<../../../../experiments/legacy_compact_h6/groups12_off_h6/evaluation.json>) | 0.28444814667801316 | 0.26407766990291265 |
| [ungrouped_on_h6](<../../../../experiments/legacy_compact_h6/ungrouped_on_h6/evaluation.json>) | 0.2552486864986865 | 0.328125 |

## Predecessor

[legacy_compact_baseline](<../../prompt-design/2026-09/legacy_compact_baseline.md>): Baseline scores selected the grouped condition before the H6 sweep; v2/v3 model judgments were replaced with frozen H6 rules.

## Follow-ups

- [legacy_prefix200](<../../inference-scheduling/2026-09/legacy_prefix200.md>): The selected compact H6 baseline motivated source-first prefix scheduling; model/prompt/H6/output2048 remained fixed.

## Unverified conditions

No new model inference, server run, holdout evaluation, or throughput measurement was performed during relocation. Missing historical timestamps and absent external inputs remain explicit limitations.

- [Original detailed observation: groups12_off_h6/evaluation.md](<../../../../experiments/legacy_compact_h6/retained_documents/docs/reports/analysis/compact200/groups12_off_h6/evaluation.md>): immutable original-language evidence; current judgment is above.

- [Original detailed observation: ungrouped_on_h6/evaluation.md](<../../../../experiments/legacy_compact_h6/retained_documents/docs/reports/analysis/compact200/ungrouped_on_h6/evaluation.md>): immutable original-language evidence; current judgment is above.

## Recorded condition evidence

These links identify exact original settings rather than substituting current defaults. Missing values remain unknown.

- [groups12_off_h6/report.json](<../../../../experiments/legacy_compact_h6/groups12_off_h6/report.json>). `{"options": {"model_dir": "models/gemma-4-26B-A4B-it-NVFP4", "max_model_len": 32768, "thinking": false, "item_group_size": 4}, "limits": {"batch_size": 8, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false}, "groups": [["v1", "v4"], ["v5", "v6", "v7"], ["v8"], ["v9", "v19"], ["v10", "v11", "v12", "v13"], ["v14"], ["v15", "v16"], ["v17", "v18"], ["v20"], ["v21"], ["v22", "v23"], ["v24"]]}`

- [ungrouped_on_h6/report.json](<../../../../experiments/legacy_compact_h6/ungrouped_on_h6/report.json>). `{"options": {"model_dir": "models/gemma-4-26B-A4B-it-NVFP4", "max_model_len": 32768, "thinking": true, "item_group_size": 22}, "limits": {"batch_size": 8, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false}, "groups": [["v1", "v4", "v5", "v6", "v7", "v8", "v9", "v10", "v11", "v12", "v13", "v14", "v15", "v16", "v17", "v18", "v19", "v20", "v21", "v22", "v23", "v24"]]}`

- [retained_documents](<../../../../experiments/legacy_compact_h6/retained_documents>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

Migration verification: [check report](<../../../maintenance/structure-migration-verification.md>). Retained migration temporary path: [tmp/structure-migration-20260913](<../../../../tmp/structure-migration-20260913>). This is migration work, not a claim about original execution temporary paths. Essential original evidence is retained under the run directory.
