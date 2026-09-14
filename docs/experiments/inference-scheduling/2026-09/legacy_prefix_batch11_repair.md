# Can the corrected helper recover the three failed batch11 notices?

Current judgment: **Corrected recovery completed the three failed notices; final200 includes preserved initial successes.**

Reason and scope: The helper assertion was corrected and inference restarted under the same prompt/OFF/output2048 conditions. Aborted execution time is excluded from the reported timing. Historical local development evidence; no unseen-data or competition-server generalization is established.

## Current interpretation and material history

Initial inference550.84s plus corrected recovery10.78s yields561.62s; additional recovery initialization28.05s is separate. One helper execution aborted after inference, with outputs/time not retained, and is excluded from those totals. Same1→11/OFF/output2048 retained in the corrected recovery; no isolated-group generation was actually needed.

## Run identity and conditions

Run ID: `legacy_prefix_batch11_repair`. Historical start time: **unknown**. The available metadata does not establish an orchestration start; initialization/log/preparation timestamps were not substituted. Execution month: September 2026, supported by the original project records and original run names.

Planned/recorded conditions: recorded execution. Preserve condition-specific manifests, input snapshots, traces, and budgets; do not infer identical conditions from the folder name.

## Actions, observations, and judgment history

The original execution and analysis artifacts below retain their original bytes. The migration changes their location and introduces explicit run identity; it is not a rerun, re-score, or adoption decision.

Corrected recovery completed the three failed notices; final200 includes preserved initial successes.

Historical comparison and interpretation documents are linked from the area index. Their original bytes are also retained in the migration document archive. Current judgment above governs reuse; historical measurements alone do not override a later withdrawal or narrowed scope.

## Run-specific interpretation

Consult the condition-level observations and retained original interpretation linked below. Missing execution settings are not reconstructed from present defaults.

## Evidence and reproducibility

[Retained execution directory](<../../../../experiments/legacy_prefix_batch11_repair>) · [Execution metadata and original-file hashes](<../../../../experiments/legacy_prefix_batch11_repair/run.json>)

Source snapshots and original manifests retain historical paths. Do not rewrite their hashes or commands. New code and instructions use the migration mapping; old commands need not execute unchanged. Locally excluded data/model assets require separately restored matching content in another checkout. Exact GPU reproducibility has not been verified by this migration.

Essential evidence is retained here, not solely in temporary work or Git-excluded outputs. The migration inventory identifies every original location and checksum. Task verification and temporary paths are listed in the metadata.

## Retained artifacts

- [comparison.json](<../../../../experiments/legacy_prefix_batch11_repair/comparison.json>): original execution or analysis evidence.
- [evaluation.json](<../../../../experiments/legacy_prefix_batch11_repair/evaluation.json>): original execution or analysis evidence.
- [recovery_policy.json](<../../../../experiments/legacy_prefix_batch11_repair/recovery_policy.json>): original execution or analysis evidence.
- [report.json](<../../../../experiments/legacy_prefix_batch11_repair/report.json>): original execution or analysis evidence.
- [submission.csv](<../../../../experiments/legacy_prefix_batch11_repair/submission.csv>): original execution or analysis evidence.
- [trace.jsonl](<../../../../experiments/legacy_prefix_batch11_repair/trace.jsonl>): original execution or analysis evidence.
- [validation.json](<../../../../experiments/legacy_prefix_batch11_repair/validation.json>): original execution or analysis evidence.

## Recorded evaluation values

These are values read from retained evaluations, not newly computed results.

| Evidence | Macro F1 | Micro F1 |
|---|---:|---:|
| [legacy_prefix_batch11_repair](<../../../../experiments/legacy_prefix_batch11_repair/evaluation.json>) | 0.2676645128195669 | 0.25853658536585367 |

## Predecessor

[legacy_prefix_batch11_aborted_repair](<legacy_prefix_batch11_aborted_repair.md>): The helper assertion was corrected and inference restarted under the same prompt/OFF/output2048 conditions. Aborted execution time is excluded from the reported timing.

## Follow-ups

- [legacy_prefix_pipeline200](<legacy_prefix_pipeline200.md>): Earlier sequential batch11 measurements motivated cross-notice scheduling; engine concurrency/graphs/scheduling changed while historical prompts/H6/output2048 remained fixed.

## Unverified conditions

No new model inference, server run, holdout evaluation, or throughput measurement was performed during relocation. Missing historical timestamps and absent external inputs remain explicit limitations.

- [Original detailed observation: prefix200_batch11/comparison.md](<../../../../experiments/legacy_prefix_batch11_repair/retained_documents/docs/reports/analysis/prefix200_batch11/comparison.md>): immutable original-language evidence; current judgment is above.

- [Original detailed observation: prefix200_batch11/evaluation.md](<../../../../experiments/legacy_prefix_batch11_repair/retained_documents/docs/reports/analysis/prefix200_batch11/evaluation.md>): immutable original-language evidence; current judgment is above.

## Recorded condition evidence

These links identify exact original settings rather than substituting current defaults. Missing values remain unknown.

- [report.json](<../../../../experiments/legacy_prefix_batch11_repair/report.json>). `{"options": {"model_dir": "models/gemma-4-26B-A4B-it-NVFP4", "max_model_len": 32768, "thinking": false, "item_group_size": 4}, "limits": {"batch_size": 11, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false}, "groups": [["v1", "v4"], ["v5", "v6", "v7"], ["v8"], ["v9", "v19"], ["v10", "v11", "v12", "v13"], ["v14"], ["v15", "v16"], ["v17", "v18"], ["v20"], ["v21"], ["v22", "v23"], ["v24"]]}`

- [source](<../../../../experiments/legacy_prefix_batch11_repair/source>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

- [analysis_source](<../../../../experiments/legacy_prefix_batch11_repair/analysis_source>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

- [code](<../../../../experiments/legacy_prefix_batch11_repair/code>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

- [retained_documents](<../../../../experiments/legacy_prefix_batch11_repair/retained_documents>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

Migration verification: [check report](<../../../maintenance/structure-migration-verification.md>). Retained migration temporary path: [tmp/structure-migration-20260913](<../../../../tmp/structure-migration-20260913>). This is migration work, not a claim about original execution temporary paths. Essential original evidence is retained under the run directory.
