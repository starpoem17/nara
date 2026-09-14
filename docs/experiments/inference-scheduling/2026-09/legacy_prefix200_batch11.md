# Does releasing eleven followers improve prefix execution?

Current judgment: **Historical scheduling comparison; first-pass failures and merged recovery remain explicitly recorded.**

Reason and scope: Prior eight-request scheduling motivated a new batch11 execution; same dev200/prompts/H6/OFF/output2048, batch size and engine concurrency changed8 to11. Historical local development evidence; no unseen-data or competition-server generalization is established.

## Run identity and conditions

Run ID: `legacy_prefix200_batch11`. Historical start time: **unknown**. The available metadata does not establish an orchestration start; initialization/log/preparation timestamps were not substituted. Execution month: September 2026, supported by the original project records and original run names.

Planned/recorded conditions: recorded execution. Preserve condition-specific manifests, input snapshots, traces, and budgets; do not infer identical conditions from the folder name.

## Actions, observations, and judgment history

The original execution and analysis artifacts below retain their original bytes. The migration changes their location and introduces explicit run identity; it is not a rerun, re-score, or adoption decision.

Historical scheduling comparison; first-pass failures and merged recovery remain explicitly recorded.

Historical comparison and interpretation documents are linked from the area index. Their original bytes are also retained in the migration document archive. Current judgment above governs reuse; historical measurements alone do not override a later withdrawal or narrowed scope.

## Run-specific interpretation

Consult the condition-level observations and retained original interpretation linked below. Missing execution settings are not reconstructed from present defaults.

## Evidence and reproducibility

[Retained execution directory](<../../../../experiments/legacy_prefix200_batch11>) · [Execution metadata and original-file hashes](<../../../../experiments/legacy_prefix200_batch11/run.json>)

Source snapshots and original manifests retain historical paths. Do not rewrite their hashes or commands. New code and instructions use the migration mapping; old commands need not execute unchanged. Locally excluded data/model assets require separately restored matching content in another checkout. Exact GPU reproducibility has not been verified by this migration.

Essential evidence is retained here, not solely in temporary work or Git-excluded outputs. The migration inventory identifies every original location and checksum. Task verification and temporary paths are listed in the metadata.

## Retained artifacts

- [first_pass/report.json](<../../../../experiments/legacy_prefix200_batch11/first_pass/report.json>): original execution or analysis evidence.
- [first_pass/trace.jsonl](<../../../../experiments/legacy_prefix200_batch11/first_pass/trace.jsonl>): original execution or analysis evidence.
- [manifest.json](<../../../../experiments/legacy_prefix200_batch11/manifest.json>): original execution or analysis evidence.

## Predecessor

[legacy_prefix200](<legacy_prefix200.md>): Prior eight-request scheduling motivated a new batch11 execution; same dev200/prompts/H6/OFF/output2048, batch size and engine concurrency changed8 to11.

## Follow-ups

- [legacy_prefix_batch11_aborted_repair](<legacy_prefix_batch11_aborted_repair.md>): Three failed initial notices triggered recovery; prompt, OFF mode and output2048 stayed the same, but a helper assertion aborted the execution.

## Unverified conditions

No new model inference, server run, holdout evaluation, or throughput measurement was performed during relocation. Missing historical timestamps and absent external inputs remain explicit limitations.

## Recorded condition evidence

These links identify exact original settings rather than substituting current defaults. Missing values remain unknown.

- [first_pass/report.json](<../../../../experiments/legacy_prefix200_batch11/first_pass/report.json>). `{"options": {"model_dir": "models/gemma-4-26B-A4B-it-NVFP4", "max_model_len": 32768, "thinking": false, "item_group_size": 4}, "limits": {"batch_size": 11, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false}, "groups": [["v1", "v4"], ["v5", "v6", "v7"], ["v8"], ["v9", "v19"], ["v10", "v11", "v12", "v13"], ["v14"], ["v15", "v16"], ["v17", "v18"], ["v20"], ["v21"], ["v22", "v23"], ["v24"]]}`

- [manifest.json](<../../../../experiments/legacy_prefix200_batch11/manifest.json>). `{"groups": [["v1", "v4"], ["v5", "v6", "v7"], ["v8"], ["v9", "v19"], ["v10", "v11", "v12", "v13"], ["v14"], ["v15", "v16"], ["v17", "v18"], ["v20"], ["v21"], ["v22", "v23"], ["v24"]], "limits": {"batch_size": 11, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false}}`

- [source](<../../../../experiments/legacy_prefix200_batch11/source>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

Migration verification: [check report](<../../../maintenance/structure-migration-verification.md>). Retained migration temporary path: [tmp/structure-migration-20260913](<../../../../tmp/structure-migration-20260913>). This is migration work, not a claim about original execution temporary paths. Essential original evidence is retained under the run directory.
