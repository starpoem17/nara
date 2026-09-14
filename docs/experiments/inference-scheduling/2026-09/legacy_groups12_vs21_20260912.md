# Matched twelve-group versus singleton-group comparison

Current judgment: **Historical exploratory observations; consult retained condition results and the linked question-level interpretation before reuse.**

Reason and scope: Historical exploratory observations; consult retained condition results and the linked question-level interpretation before reuse. Historical local development evidence; no unseen-data or competition-server generalization is established.

## Run identity and conditions

Run ID: `legacy_groups12_vs21_20260912`. Historical start time: **unknown**. The available metadata does not establish an orchestration start; initialization/log/preparation timestamps were not substituted. Execution month: September 2026, supported by the original project records and original run names.

Planned/recorded conditions: recorded execution. Preserve condition-specific manifests, input snapshots, traces, and budgets; do not infer identical conditions from the folder name.

## Actions, observations, and judgment history

The original execution and analysis artifacts below retain their original bytes. The migration changes their location and introduces explicit run identity; it is not a rerun, re-score, or adoption decision.

Historical exploratory observations; consult retained condition results and the linked question-level interpretation before reuse.

Historical comparison and interpretation documents are linked from the area index. Their original bytes are also retained in the migration document archive. Current judgment above governs reuse; historical measurements alone do not override a later withdrawal or narrowed scope.

## Run-specific interpretation

Consult the condition-level observations and retained original interpretation linked below. Missing execution settings are not reconstructed from present defaults.

## Evidence and reproducibility

[Retained execution directory](<../../../../experiments/legacy_groups12_vs21_20260912>) · [Execution metadata and original-file hashes](<../../../../experiments/legacy_groups12_vs21_20260912/run.json>)

Source snapshots and original manifests retain historical paths. Do not rewrite their hashes or commands. New code and instructions use the migration mapping; old commands need not execute unchanged. Locally excluded data/model assets require separately restored matching content in another checkout. Exact GPU reproducibility has not been verified by this migration.

Essential evidence is retained here, not solely in temporary work or Git-excluded outputs. The migration inventory identifies every original location and checksum. Task verification and temporary paths are listed in the metadata.

## Retained artifacts

- [comparison.json](<../../../../experiments/legacy_groups12_vs21_20260912/comparison.json>): original execution or analysis evidence.
- [groups12/evaluation.json](<../../../../experiments/legacy_groups12_vs21_20260912/groups12/evaluation.json>): original execution or analysis evidence.
- [groups12/manifest.json](<../../../../experiments/legacy_groups12_vs21_20260912/groups12/manifest.json>): original execution or analysis evidence.
- [groups12/report.json](<../../../../experiments/legacy_groups12_vs21_20260912/groups12/report.json>): original execution or analysis evidence.
- [groups12/submission.csv](<../../../../experiments/legacy_groups12_vs21_20260912/groups12/submission.csv>): original execution or analysis evidence.
- [groups12/trace.jsonl](<../../../../experiments/legacy_groups12_vs21_20260912/groups12/trace.jsonl>): original execution or analysis evidence.
- [groups21/evaluation.json](<../../../../experiments/legacy_groups12_vs21_20260912/groups21/evaluation.json>): original execution or analysis evidence.
- [groups21/manifest.json](<../../../../experiments/legacy_groups12_vs21_20260912/groups21/manifest.json>): original execution or analysis evidence.
- [groups21/report.json](<../../../../experiments/legacy_groups12_vs21_20260912/groups21/report.json>): original execution or analysis evidence.
- [groups21/submission.csv](<../../../../experiments/legacy_groups12_vs21_20260912/groups21/submission.csv>): original execution or analysis evidence.
- [groups21/trace.jsonl](<../../../../experiments/legacy_groups12_vs21_20260912/groups21/trace.jsonl>): original execution or analysis evidence.

## Recorded evaluation values

These are values read from retained evaluations, not newly computed results.

| Evidence | Macro F1 | Micro F1 |
|---|---:|---:|
| [groups12](<../../../../experiments/legacy_groups12_vs21_20260912/groups12/evaluation.json>) | 0.2869096815183057 | 0.22380106571936056 |
| [groups21](<../../../../experiments/legacy_groups12_vs21_20260912/groups21/evaluation.json>) | 0.26398982003846677 | 0.1693227091633466 |

## Unverified conditions

No new model inference, server run, holdout evaluation, or throughput measurement was performed during relocation. Missing historical timestamps and absent external inputs remain explicit limitations.

- [Original detailed observation: groups12_vs21_20260912/comparison.md](<../../../../experiments/legacy_groups12_vs21_20260912/retained_documents/docs/reports/output/experiments/groups12_vs21_20260912/comparison.md>): immutable original-language evidence; current judgment is above.

- [Original detailed observation: groups12/evaluation.md](<../../../../experiments/legacy_groups12_vs21_20260912/retained_documents/docs/reports/output/experiments/groups12_vs21_20260912/groups12/evaluation.md>): immutable original-language evidence; current judgment is above.

- [Original detailed observation: groups21/evaluation.md](<../../../../experiments/legacy_groups12_vs21_20260912/retained_documents/docs/reports/output/experiments/groups12_vs21_20260912/groups21/evaluation.md>): immutable original-language evidence; current judgment is above.

## Recorded condition evidence

These links identify exact original settings rather than substituting current defaults. Missing values remain unknown.

- [groups12/manifest.json](<../../../../experiments/legacy_groups12_vs21_20260912/groups12/manifest.json>). `{"grouping": "groups12", "groups": [["v1", "v4"], ["v5", "v6", "v7"], ["v8"], ["v9", "v19"], ["v10", "v11", "v12", "v13"], ["v14"], ["v15", "v16"], ["v17", "v18"], ["v20"], ["v21"], ["v23"], ["v24"]], "limits": {"batch_size": 16, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false, "instant_output_tokens": null}, "recovery_policy": "One same-policy rerun of failed notices, then one same-prompt isolated predict per still-failed group. All internal retries, recovery time and events included."}`

- [groups12/report.json](<../../../../experiments/legacy_groups12_vs21_20260912/groups12/report.json>). `{"groups": [["v1", "v4"], ["v5", "v6", "v7"], ["v8"], ["v9", "v19"], ["v10", "v11", "v12", "v13"], ["v14"], ["v15", "v16"], ["v17", "v18"], ["v20"], ["v21"], ["v23"], ["v24"]], "limits": {"batch_size": 16, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false, "instant_output_tokens": null}, "options": {"model_dir": "models/gemma-4-26B-A4B-it-NVFP4", "max_model_len": 32768, "thinking": false, "item_group_size": 4}}`

- [groups21/manifest.json](<../../../../experiments/legacy_groups12_vs21_20260912/groups21/manifest.json>). `{"grouping": "groups21", "groups": [["v1"], ["v4"], ["v5"], ["v6"], ["v7"], ["v8"], ["v9"], ["v19"], ["v10"], ["v11"], ["v12"], ["v13"], ["v14"], ["v15"], ["v16"], ["v17"], ["v18"], ["v20"], ["v21"], ["v23"], ["v24"]], "limits": {"batch_size": 16, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false, "instant_output_tokens": null}, "recovery_policy": "One same-policy rerun of failed notices, then one same-prompt isolated predict per still-failed group. All internal retries, recovery time and events included."}`

- [groups21/report.json](<../../../../experiments/legacy_groups12_vs21_20260912/groups21/report.json>). `{"groups": [["v1"], ["v4"], ["v5"], ["v6"], ["v7"], ["v8"], ["v9"], ["v19"], ["v10"], ["v11"], ["v12"], ["v13"], ["v14"], ["v15"], ["v16"], ["v17"], ["v18"], ["v20"], ["v21"], ["v23"], ["v24"]], "limits": {"batch_size": 16, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false, "instant_output_tokens": null}, "options": {"model_dir": "models/gemma-4-26B-A4B-it-NVFP4", "max_model_len": 32768, "thinking": false, "item_group_size": 1}}`

- [code](<../../../../experiments/legacy_groups12_vs21_20260912/code>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

- [retained_documents](<../../../../experiments/legacy_groups12_vs21_20260912/retained_documents>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

Migration verification: [check report](<../../../maintenance/structure-migration-verification.md>). Retained migration temporary path: [tmp/structure-migration-20260913](<../../../../tmp/structure-migration-20260913>). This is migration work, not a claim about original execution temporary paths. Essential original evidence is retained under the run directory.
