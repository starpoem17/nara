# Can the failed optimized-OFF group be recovered without changing its prompt or budget?

Current judgment: **One failed group was regenerated. Other successful groups and notices were replayed, not newly inferred.**

Reason and scope: Observed optimized-OFF failure triggered separate isolated recovery with unchanged prompt/OFF mode/output2048. Historical local development evidence; no unseen-data or competition-server generalization is established.

## Run identity and conditions

Run ID: `legacy_hybrid_repair`. Historical start time: **unknown**. The available metadata does not establish an orchestration start; initialization/log/preparation timestamps were not substituted. Execution month: September 2026, supported by the original project records and original run names.

Planned/recorded conditions: recorded execution. Preserve condition-specific manifests, input snapshots, traces, and budgets; do not infer identical conditions from the folder name.

## Actions, observations, and judgment history

The original execution and analysis artifacts below retain their original bytes. The migration changes their location and introduces explicit run identity; it is not a rerun, re-score, or adoption decision.

One failed group was regenerated. Other successful groups and notices were replayed, not newly inferred.

Historical comparison and interpretation documents are linked from the area index. Their original bytes are also retained in the migration document archive. Current judgment above governs reuse; historical measurements alone do not override a later withdrawal or narrowed scope.

## Run-specific interpretation

Consult the condition-level observations and retained original interpretation linked below. Missing execution settings are not reconstructed from present defaults.

## Evidence and reproducibility

[Retained execution directory](<../../../../experiments/legacy_hybrid_repair>) · [Execution metadata and original-file hashes](<../../../../experiments/legacy_hybrid_repair/run.json>)

Source snapshots and original manifests retain historical paths. Do not rewrite their hashes or commands. New code and instructions use the migration mapping; old commands need not execute unchanged. Locally excluded data/model assets require separately restored matching content in another checkout. Exact GPU reproducibility has not been verified by this migration.

Essential evidence is retained here, not solely in temporary work or Git-excluded outputs. The migration inventory identifies every original location and checksum. Task verification and temporary paths are listed in the metadata.

## Retained artifacts

- [optimized_off/evaluation.json](<../../../../experiments/legacy_hybrid_repair/optimized_off/evaluation.json>): original execution or analysis evidence.
- [optimized_off/report.json](<../../../../experiments/legacy_hybrid_repair/optimized_off/report.json>): original execution or analysis evidence.
- [optimized_off/submission.csv](<../../../../experiments/legacy_hybrid_repair/optimized_off/submission.csv>): original execution or analysis evidence.
- [optimized_off/trace.jsonl](<../../../../experiments/legacy_hybrid_repair/optimized_off/trace.jsonl>): original execution or analysis evidence.
- [recovery_policy.json](<../../../../experiments/legacy_hybrid_repair/recovery_policy.json>): original execution or analysis evidence.

## Recorded evaluation values

These are values read from retained evaluations, not newly computed results.

| Evidence | Macro F1 | Micro F1 |
|---|---:|---:|
| [optimized_off](<../../../../experiments/legacy_hybrid_repair/optimized_off/evaluation.json>) | 0.19858434294909708 | 0.24624624624624625 |

## Predecessor

[legacy_hybrid200](<legacy_hybrid200.md>): Observed optimized-OFF failure triggered separate isolated recovery with unchanged prompt/OFF mode/output2048.

## Unverified conditions

No new model inference, server run, holdout evaluation, or throughput measurement was performed during relocation. Missing historical timestamps and absent external inputs remain explicit limitations.

- [Original detailed observation: optimized_off/evaluation.md](<../../../../experiments/legacy_hybrid_repair/retained_documents/docs/reports/analysis/hybrid200/optimized_off/evaluation.md>): immutable original-language evidence; current judgment is above.

## Recorded condition evidence

These links identify exact original settings rather than substituting current defaults. Missing values remain unknown.

- [optimized_off/report.json](<../../../../experiments/legacy_hybrid_repair/optimized_off/report.json>). `{"options": {"model_dir": "models/gemma-4-26B-A4B-it-NVFP4", "max_model_len": 32768, "thinking": false, "item_group_size": 6}, "limits": {"batch_size": 8, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false}, "groups": [["v4", "v6", "v7", "v8"], ["v10", "v11", "v12", "v13"], ["v15", "v16", "v17", "v18"], ["v19", "v20", "v21", "v23"], ["v1", "v5", "v9", "v14", "v22", "v24"]]}`

- [code](<../../../../experiments/legacy_hybrid_repair/code>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

- [retained_documents](<../../../../experiments/legacy_hybrid_repair/retained_documents>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

Migration verification: [check report](<../../../maintenance/structure-migration-verification.md>). Retained migration temporary path: [tmp/structure-migration-20260913](<../../../../tmp/structure-migration-20260913>). This is migration work, not a claim about original execution temporary paths. Essential original evidence is retained under the run directory.
