# Can the failed mixed continuous group be recovered in isolation?

Current judgment: **Merged200 results include only the failed group as newly generated evidence.**

Reason and scope: Observed mixed-run failure triggered isolated same-prompt/mode/budget recovery. Historical local development evidence; no unseen-data or competition-server generalization is established.

## Run identity and conditions

Run ID: `legacy_continuous_repair`. Historical start time: **unknown**. The available metadata does not establish an orchestration start; initialization/log/preparation timestamps were not substituted. Execution month: September 2026, supported by the original project records and original run names.

Planned/recorded conditions: recorded execution. Preserve condition-specific manifests, input snapshots, traces, and budgets; do not infer identical conditions from the folder name.

## Actions, observations, and judgment history

The original execution and analysis artifacts below retain their original bytes. The migration changes their location and introduces explicit run identity; it is not a rerun, re-score, or adoption decision.

Merged200 results include only the failed group as newly generated evidence.

Historical comparison and interpretation documents are linked from the area index. Their original bytes are also retained in the migration document archive. Current judgment above governs reuse; historical measurements alone do not override a later withdrawal or narrowed scope.

## Run-specific interpretation

Consult the condition-level observations and retained original interpretation linked below. Missing execution settings are not reconstructed from present defaults.

## Evidence and reproducibility

[Retained execution directory](<../../../../experiments/legacy_continuous_repair>) · [Execution metadata and original-file hashes](<../../../../experiments/legacy_continuous_repair/run.json>)

Source snapshots and original manifests retain historical paths. Do not rewrite their hashes or commands. New code and instructions use the migration mapping; old commands need not execute unchanged. Locally excluded data/model assets require separately restored matching content in another checkout. Exact GPU reproducibility has not been verified by this migration.

Essential evidence is retained here, not solely in temporary work or Git-excluded outputs. The migration inventory identifies every original location and checksum. Task verification and temporary paths are listed in the metadata.

## Retained artifacts

- [mixed_continuous_8192/evaluation.json](<../../../../experiments/legacy_continuous_repair/mixed_continuous_8192/evaluation.json>): original execution or analysis evidence.
- [mixed_continuous_8192/report.json](<../../../../experiments/legacy_continuous_repair/mixed_continuous_8192/report.json>): original execution or analysis evidence.
- [mixed_continuous_8192/submission.csv](<../../../../experiments/legacy_continuous_repair/mixed_continuous_8192/submission.csv>): original execution or analysis evidence.
- [mixed_continuous_8192/trace.jsonl](<../../../../experiments/legacy_continuous_repair/mixed_continuous_8192/trace.jsonl>): original execution or analysis evidence.
- [recovery_policy.json](<../../../../experiments/legacy_continuous_repair/recovery_policy.json>): original execution or analysis evidence.

## Recorded evaluation values

These are values read from retained evaluations, not newly computed results.

| Evidence | Macro F1 | Micro F1 |
|---|---:|---:|
| [mixed_continuous_8192](<../../../../experiments/legacy_continuous_repair/mixed_continuous_8192/evaluation.json>) | 0.262738642124607 | 0.27246376811594203 |

## Predecessor

[legacy_continuous_full200](<legacy_continuous_full200.md>): Observed mixed-run failure triggered isolated same-prompt/mode/budget recovery.

## Unverified conditions

No new model inference, server run, holdout evaluation, or throughput measurement was performed during relocation. Missing historical timestamps and absent external inputs remain explicit limitations.

- [Original detailed observation: mixed_continuous_8192/evaluation.md](<../../../../experiments/legacy_continuous_repair/retained_documents/docs/reports/analysis/continuous200/mixed_continuous_8192/evaluation.md>): immutable original-language evidence; current judgment is above.

## Recorded condition evidence

These links identify exact original settings rather than substituting current defaults. Missing values remain unknown.

- [mixed_continuous_8192/report.json](<../../../../experiments/legacy_continuous_repair/mixed_continuous_8192/report.json>). `{"groups": [["v4", "v6", "v7", "v8"], ["v10", "v11", "v12", "v13"], ["v15", "v16", "v17", "v18"], ["v19", "v20", "v21", "v23"], ["v1", "v5", "v9", "v14", "v22", "v24"]], "options": {"thinking": "mixed", "item_group_size": 6, "model_dir": "models/gemma-4-26B-A4B-it-NVFP4", "max_model_len": 32768}, "limits": {"batch_size": 8, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false}}`

- [code](<../../../../experiments/legacy_continuous_repair/code>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

- [retained_documents](<../../../../experiments/legacy_continuous_repair/retained_documents>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

Migration verification: [check report](<../../../maintenance/structure-migration-verification.md>). Retained migration temporary path: [tmp/structure-migration-20260913](<../../../../tmp/structure-migration-20260913>). This is migration work, not a claim about original execution temporary paths. Essential original evidence is retained under the run directory.
