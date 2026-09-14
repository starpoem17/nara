# Which planned prefill budget is fastest in the continuous scheduling pilot?

Current judgment: **Preplanned pilot compared barrier8192 with continuous2048/8192/16384. Runtime selected the follow-up budget.**

Reason and scope: The hybrid study motivated a new completion-driven pilot; predefined barrier/prefill budgets were compared before choosing the full200 budget. Historical local development evidence; no unseen-data or competition-server generalization is established.

## Run identity and conditions

Run ID: `legacy_continuous_pilot`. Historical start time: **unknown**. The available metadata does not establish an orchestration start; initialization/log/preparation timestamps were not substituted. Execution month: September 2026, supported by the original project records and original run names.

Planned/recorded conditions: pilot_barrier_8192, pilot_continuous_2048, pilot_continuous_8192, pilot_continuous_16384. Preserve condition-specific manifests, input snapshots, traces, and budgets; do not infer identical conditions from the folder name.

## Actions, observations, and judgment history

The original execution and analysis artifacts below retain their original bytes. The migration changes their location and introduces explicit run identity; it is not a rerun, re-score, or adoption decision.

Preplanned pilot compared barrier8192 with continuous2048/8192/16384. Runtime selected the follow-up budget.

Historical comparison and interpretation documents are linked from the area index. Their original bytes are also retained in the migration document archive. Current judgment above governs reuse; historical measurements alone do not override a later withdrawal or narrowed scope.

## Run-specific interpretation

Consult the condition-level observations and retained original interpretation linked below. Missing execution settings are not reconstructed from present defaults.

## Evidence and reproducibility

[Retained execution directory](<../../../../experiments/legacy_continuous_pilot>) · [Execution metadata and original-file hashes](<../../../../experiments/legacy_continuous_pilot/run.json>)

Source snapshots and original manifests retain historical paths. Do not rewrite their hashes or commands. New code and instructions use the migration mapping; old commands need not execute unchanged. Locally excluded data/model assets require separately restored matching content in another checkout. Exact GPU reproducibility has not been verified by this migration.

Essential evidence is retained here, not solely in temporary work or Git-excluded outputs. The migration inventory identifies every original location and checksum. Task verification and temporary paths are listed in the metadata.

## Retained artifacts

- [comparison.json](<../../../../experiments/legacy_continuous_pilot/comparison.json>): original execution or analysis evidence.
- [pilot_barrier_8192/report.json](<../../../../experiments/legacy_continuous_pilot/pilot_barrier_8192/report.json>): original execution or analysis evidence.
- [pilot_barrier_8192/trace.jsonl](<../../../../experiments/legacy_continuous_pilot/pilot_barrier_8192/trace.jsonl>): original execution or analysis evidence.
- [pilot_continuous_16384/report.json](<../../../../experiments/legacy_continuous_pilot/pilot_continuous_16384/report.json>): original execution or analysis evidence.
- [pilot_continuous_16384/trace.jsonl](<../../../../experiments/legacy_continuous_pilot/pilot_continuous_16384/trace.jsonl>): original execution or analysis evidence.
- [pilot_continuous_2048/report.json](<../../../../experiments/legacy_continuous_pilot/pilot_continuous_2048/report.json>): original execution or analysis evidence.
- [pilot_continuous_2048/trace.jsonl](<../../../../experiments/legacy_continuous_pilot/pilot_continuous_2048/trace.jsonl>): original execution or analysis evidence.
- [pilot_continuous_8192/report.json](<../../../../experiments/legacy_continuous_pilot/pilot_continuous_8192/report.json>): original execution or analysis evidence.
- [pilot_continuous_8192/trace.jsonl](<../../../../experiments/legacy_continuous_pilot/pilot_continuous_8192/trace.jsonl>): original execution or analysis evidence.
- [plan.json](<../../../../experiments/legacy_continuous_pilot/plan.json>): original execution or analysis evidence.
- [smoke_continuous_8192/report.json](<../../../../experiments/legacy_continuous_pilot/smoke_continuous_8192/report.json>): original execution or analysis evidence.
- [smoke_continuous_8192/trace.jsonl](<../../../../experiments/legacy_continuous_pilot/smoke_continuous_8192/trace.jsonl>): original execution or analysis evidence.
- [validation.json](<../../../../experiments/legacy_continuous_pilot/validation.json>): original execution or analysis evidence.

## Predecessor

[legacy_hybrid200](<legacy_hybrid200.md>): The hybrid study motivated a new completion-driven pilot; predefined barrier/prefill budgets were compared before choosing the full200 budget.

## Follow-ups

- [legacy_continuous_full200](<legacy_continuous_full200.md>): Pilot runtime selected8192 before full200 six-feature and mixed conditions were launched.

## Unverified conditions

No new model inference, server run, holdout evaluation, or throughput measurement was performed during relocation. Missing historical timestamps and absent external inputs remain explicit limitations.

## Recorded condition evidence

These links identify exact original settings rather than substituting current defaults. Missing values remain unknown.

- [pilot_barrier_8192/report.json](<../../../../experiments/legacy_continuous_pilot/pilot_barrier_8192/report.json>). `{"groups": [["v1", "v5", "v9", "v14", "v22", "v24"]], "options": {"thinking": true, "item_group_size": 6}, "limits": {"batch_size": 8, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false}}`

- [pilot_continuous_16384/report.json](<../../../../experiments/legacy_continuous_pilot/pilot_continuous_16384/report.json>). `{"groups": [["v1", "v5", "v9", "v14", "v22", "v24"]], "options": {"thinking": true, "item_group_size": 6}, "limits": {"batch_size": 8, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false}}`

- [pilot_continuous_2048/report.json](<../../../../experiments/legacy_continuous_pilot/pilot_continuous_2048/report.json>). `{"groups": [["v1", "v5", "v9", "v14", "v22", "v24"]], "options": {"thinking": true, "item_group_size": 6}, "limits": {"batch_size": 8, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false}}`

- [pilot_continuous_8192/report.json](<../../../../experiments/legacy_continuous_pilot/pilot_continuous_8192/report.json>). `{"groups": [["v1", "v5", "v9", "v14", "v22", "v24"]], "options": {"thinking": true, "item_group_size": 6}, "limits": {"batch_size": 8, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false}}`

- [smoke_continuous_8192/report.json](<../../../../experiments/legacy_continuous_pilot/smoke_continuous_8192/report.json>). `{"groups": [["v1", "v5", "v9", "v14", "v22", "v24"]], "options": {"thinking": true, "item_group_size": 6}, "limits": {"batch_size": 8, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false}}`

- [source](<../../../../experiments/legacy_continuous_pilot/source>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

- [analysis_source](<../../../../experiments/legacy_continuous_pilot/analysis_source>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

- [code](<../../../../experiments/legacy_continuous_pilot/code>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

Migration verification: [check report](<../../../maintenance/structure-migration-verification.md>). Retained migration temporary path: [tmp/structure-migration-20260913](<../../../../tmp/structure-migration-20260913>). This is migration work, not a claim about original execution temporary paths. Essential original evidence is retained under the run directory.
