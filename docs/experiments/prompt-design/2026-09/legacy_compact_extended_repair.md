# Can PPS-DEV-147 be recovered with an increased output allowance?

Current judgment: **Only the remaining ON147 failure was recovered with output4096; merged200 is a mixed-attempt/budget result.**

Reason and scope: Standard repair still failed PPS-DEV-147; output allowance increased from 2048 to 4096. Historical local development evidence; no unseen-data or competition-server generalization is established.

## Current interpretation and material history

The standard repair failed147. Extra inference15.3478s used output4096/thinking1024/context32768; other predictions were reused. Final inference totals include attempted repair costs; no uniform-budget or whole-task runtime claim.

## Run identity and conditions

Run ID: `legacy_compact_extended_repair`. Historical start time: **unknown**. The available metadata does not establish an orchestration start; initialization/log/preparation timestamps were not substituted. Execution month: September 2026, supported by the original project records and original run names.

Planned/recorded conditions: recorded execution. Preserve condition-specific manifests, input snapshots, traces, and budgets; do not infer identical conditions from the folder name.

## Actions, observations, and judgment history

The original execution and analysis artifacts below retain their original bytes. The migration changes their location and introduces explicit run identity; it is not a rerun, re-score, or adoption decision.

Only the remaining ON147 failure was recovered with output4096; merged200 is a mixed-attempt/budget result.

Historical comparison and interpretation documents are linked from the area index. Their original bytes are also retained in the migration document archive. Current judgment above governs reuse; historical measurements alone do not override a later withdrawal or narrowed scope.

## Run-specific interpretation

Consult the condition-level observations and retained original interpretation linked below. Missing execution settings are not reconstructed from present defaults.

## Evidence and reproducibility

[Retained execution directory](<../../../../experiments/legacy_compact_extended_repair>) · [Execution metadata and original-file hashes](<../../../../experiments/legacy_compact_extended_repair/run.json>)

Source snapshots and original manifests retain historical paths. Do not rewrite their hashes or commands. New code and instructions use the migration mapping; old commands need not execute unchanged. Locally excluded data/model assets require separately restored matching content in another checkout. Exact GPU reproducibility has not been verified by this migration.

Essential evidence is retained here, not solely in temporary work or Git-excluded outputs. The migration inventory identifies every original location and checksum. Task verification and temporary paths are listed in the metadata.

## Retained artifacts

- [extended_recovery_policy.json](<../../../../experiments/legacy_compact_extended_repair/extended_recovery_policy.json>): original execution or analysis evidence.
- [ungrouped_on/evaluation.json](<../../../../experiments/legacy_compact_extended_repair/ungrouped_on/evaluation.json>): original execution or analysis evidence.
- [ungrouped_on/report.json](<../../../../experiments/legacy_compact_extended_repair/ungrouped_on/report.json>): original execution or analysis evidence.
- [ungrouped_on/submission.csv](<../../../../experiments/legacy_compact_extended_repair/ungrouped_on/submission.csv>): original execution or analysis evidence.
- [ungrouped_on/trace.jsonl](<../../../../experiments/legacy_compact_extended_repair/ungrouped_on/trace.jsonl>): original execution or analysis evidence.

## Recorded evaluation values

These are values read from retained evaluations, not newly computed results.

| Evidence | Macro F1 | Micro F1 |
|---|---:|---:|
| [ungrouped_on](<../../../../experiments/legacy_compact_extended_repair/ungrouped_on/evaluation.json>) | 0.2232817835759012 | 0.25 |

## Predecessor

[legacy_compact_repair](<legacy_compact_repair.md>): Standard repair still failed PPS-DEV-147; output allowance increased from 2048 to 4096.

## Unverified conditions

No new model inference, server run, holdout evaluation, or throughput measurement was performed during relocation. Missing historical timestamps and absent external inputs remain explicit limitations.

- [Original detailed observation: ungrouped_on/evaluation.md](<../../../../experiments/legacy_compact_extended_repair/retained_documents/docs/reports/analysis/compact200/ungrouped_on/evaluation.md>): immutable original-language evidence; current judgment is above.

## Recorded condition evidence

These links identify exact original settings rather than substituting current defaults. Missing values remain unknown.

- [ungrouped_on/report.json](<../../../../experiments/legacy_compact_extended_repair/ungrouped_on/report.json>). `{"options": {"model_dir": "models/gemma-4-26B-A4B-it-NVFP4", "max_model_len": 32768, "thinking": true, "item_group_size": 24}, "limits": {"batch_size": 8, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false}, "groups": [["v1", "v2", "v3", "v4", "v5", "v6", "v7", "v8", "v9", "v10", "v11", "v12", "v13", "v14", "v15", "v16", "v17", "v18", "v19", "v20", "v21", "v22", "v23", "v24"]]}`

- [code](<../../../../experiments/legacy_compact_extended_repair/code>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

- [retained_documents](<../../../../experiments/legacy_compact_extended_repair/retained_documents>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

Migration verification: [check report](<../../../maintenance/structure-migration-verification.md>). Retained migration temporary path: [tmp/structure-migration-20260913](<../../../../tmp/structure-migration-20260913>). This is migration work, not a claim about original execution temporary paths. Essential original evidence is retained under the run directory.
