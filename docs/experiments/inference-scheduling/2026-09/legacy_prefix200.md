# Does source-first prefix reuse reduce grouped inference time?

Current judgment: **Historical twelve-group reference; superseded as the default by the cross-notice pipeline.**

Reason and scope: The selected compact H6 baseline motivated source-first prefix scheduling; model/prompt/H6/output2048 remained fixed. Historical local development evidence; no unseen-data or competition-server generalization is established.

## Run identity and conditions

Run ID: `legacy_prefix200`. Historical start time: **unknown**. The available metadata does not establish an orchestration start; initialization/log/preparation timestamps were not substituted. Execution month: September 2026, supported by the original project records and original run names.

Planned/recorded conditions: recorded execution. Preserve condition-specific manifests, input snapshots, traces, and budgets; do not infer identical conditions from the folder name.

## Actions, observations, and judgment history

The original execution and analysis artifacts below retain their original bytes. The migration changes their location and introduces explicit run identity; it is not a rerun, re-score, or adoption decision.

Historical twelve-group reference; superseded as the default by the cross-notice pipeline.

Historical comparison and interpretation documents are linked from the area index. Their original bytes are also retained in the migration document archive. Current judgment above governs reuse; historical measurements alone do not override a later withdrawal or narrowed scope.

## Run-specific interpretation

Consult the condition-level observations and retained original interpretation linked below. Missing execution settings are not reconstructed from present defaults.

## Evidence and reproducibility

[Retained execution directory](<../../../../experiments/legacy_prefix200>) · [Execution metadata and original-file hashes](<../../../../experiments/legacy_prefix200/run.json>)

Source snapshots and original manifests retain historical paths. Do not rewrite their hashes or commands. New code and instructions use the migration mapping; old commands need not execute unchanged. Locally excluded data/model assets require separately restored matching content in another checkout. Exact GPU reproducibility has not been verified by this migration.

Essential evidence is retained here, not solely in temporary work or Git-excluded outputs. The migration inventory identifies every original location and checksum. Task verification and temporary paths are listed in the metadata.

## Retained artifacts

- [comparison.json](<../../../../experiments/legacy_prefix200/comparison.json>): original execution or analysis evidence.
- [evaluation.json](<../../../../experiments/legacy_prefix200/evaluation.json>): original execution or analysis evidence.
- [manifest.json](<../../../../experiments/legacy_prefix200/manifest.json>): original execution or analysis evidence.
- [report.json](<../../../../experiments/legacy_prefix200/report.json>): original execution or analysis evidence.
- [submission.csv](<../../../../experiments/legacy_prefix200/submission.csv>): original execution or analysis evidence.
- [trace.jsonl](<../../../../experiments/legacy_prefix200/trace.jsonl>): original execution or analysis evidence.
- [validation.json](<../../../../experiments/legacy_prefix200/validation.json>): original execution or analysis evidence.

## Recorded evaluation values

These are values read from retained evaluations, not newly computed results.

| Evidence | Macro F1 | Micro F1 |
|---|---:|---:|
| [legacy_prefix200](<../../../../experiments/legacy_prefix200/evaluation.json>) | 0.2834927277302597 | 0.2773722627737226 |

## Predecessor

[legacy_compact_h6](<../../rule-evaluation/2026-09/legacy_compact_h6.md>): The selected compact H6 baseline motivated source-first prefix scheduling; model/prompt/H6/output2048 remained fixed.

## Follow-ups

- [legacy_prefix200_batch11](<legacy_prefix200_batch11.md>): Prior eight-request scheduling motivated a new batch11 execution; same dev200/prompts/H6/OFF/output2048, batch size and engine concurrency changed8 to11.

## Unverified conditions

No new model inference, server run, holdout evaluation, or throughput measurement was performed during relocation. Missing historical timestamps and absent external inputs remain explicit limitations.

- [Original detailed observation: prefix200/comparison.md](<../../../../experiments/legacy_prefix200/retained_documents/docs/reports/analysis/prefix200/comparison.md>): immutable original-language evidence; current judgment is above.

- [Original detailed observation: prefix200/evaluation.md](<../../../../experiments/legacy_prefix200/retained_documents/docs/reports/analysis/prefix200/evaluation.md>): immutable original-language evidence; current judgment is above.

## Recorded condition evidence

These links identify exact original settings rather than substituting current defaults. Missing values remain unknown.

- [manifest.json](<../../../../experiments/legacy_prefix200/manifest.json>). `{"groups": [["v1", "v4"], ["v5", "v6", "v7"], ["v8"], ["v9", "v19"], ["v10", "v11", "v12", "v13"], ["v14"], ["v15", "v16"], ["v17", "v18"], ["v20"], ["v21"], ["v22", "v23"], ["v24"]], "limits": {"batch_size": 8, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false}}`

- [report.json](<../../../../experiments/legacy_prefix200/report.json>). `{"options": {"model_dir": "models/gemma-4-26B-A4B-it-NVFP4", "max_model_len": 32768, "thinking": false, "item_group_size": 4}, "limits": {"batch_size": 8, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false}, "groups": [["v1", "v4"], ["v5", "v6", "v7"], ["v8"], ["v9", "v19"], ["v10", "v11", "v12", "v13"], ["v14"], ["v15", "v16"], ["v17", "v18"], ["v20"], ["v21"], ["v22", "v23"], ["v24"]]}`

- [source](<../../../../experiments/legacy_prefix200/source>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

- [code](<../../../../experiments/legacy_prefix200/code>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

- [retained_documents](<../../../../experiments/legacy_prefix200/retained_documents>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

Migration verification: [check report](<../../../maintenance/structure-migration-verification.md>). Retained migration temporary path: [tmp/structure-migration-20260913](<../../../../tmp/structure-migration-20260913>). This is migration work, not a claim about original execution temporary paths. Essential original evidence is retained under the run directory.
