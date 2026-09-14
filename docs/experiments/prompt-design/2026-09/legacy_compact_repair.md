# Can failed compact-baseline notices be recovered under the original allowance?

Current judgment: **Post-result standard repair; successful predecessor predictions were reused and the remaining ON147 failure led to another run.**

Reason and scope: Observed failed baseline notices required a separately executed repair. The repair appended a final-JSON/evidence-at-most-80-characters instruction and set search_rounds=0; original source/criteria and the standard output2048 budget were retained. Historical local development evidence; no unseen-data or competition-server generalization is established.

## Current interpretation and material history

Repair appended a finalJSON/evidence-at-most80 instruction and disabled search, retaining original source/criteria/output2048. Groups7 and12 repair inference was8.5312s and2.3585s; standardON repair44.3340s still failed147. This is not an unchanged-prompt repair.

## Run identity and conditions

Run ID: `legacy_compact_repair`. Historical start time: **unknown**. The available metadata does not establish an orchestration start; initialization/log/preparation timestamps were not substituted. Execution month: September 2026, supported by the original project records and original run names.

Planned/recorded conditions: recorded execution. Preserve condition-specific manifests, input snapshots, traces, and budgets; do not infer identical conditions from the folder name.

## Actions, observations, and judgment history

The original execution and analysis artifacts below retain their original bytes. The migration changes their location and introduces explicit run identity; it is not a rerun, re-score, or adoption decision.

Post-result standard repair; successful predecessor predictions were reused and the remaining ON147 failure led to another run.

Historical comparison and interpretation documents are linked from the area index. Their original bytes are also retained in the migration document archive. Current judgment above governs reuse; historical measurements alone do not override a later withdrawal or narrowed scope.

## Run-specific interpretation

Consult the condition-level observations and retained original interpretation linked below. Missing execution settings are not reconstructed from present defaults.

## Evidence and reproducibility

[Retained execution directory](<../../../../experiments/legacy_compact_repair>) · [Execution metadata and original-file hashes](<../../../../experiments/legacy_compact_repair/run.json>)

Source snapshots and original manifests retain historical paths. Do not rewrite their hashes or commands. New code and instructions use the migration mapping; old commands need not execute unchanged. Locally excluded data/model assets require separately restored matching content in another checkout. Exact GPU reproducibility has not been verified by this migration.

Essential evidence is retained here, not solely in temporary work or Git-excluded outputs. The migration inventory identifies every original location and checksum. Task verification and temporary paths are listed in the metadata.

## Retained artifacts

- [groups12_off/evaluation.json](<../../../../experiments/legacy_compact_repair/groups12_off/evaluation.json>): original execution or analysis evidence.
- [groups12_off/report.json](<../../../../experiments/legacy_compact_repair/groups12_off/report.json>): original execution or analysis evidence.
- [groups12_off/submission.csv](<../../../../experiments/legacy_compact_repair/groups12_off/submission.csv>): original execution or analysis evidence.
- [groups12_off/trace.jsonl](<../../../../experiments/legacy_compact_repair/groups12_off/trace.jsonl>): original execution or analysis evidence.
- [groups7_off/evaluation.json](<../../../../experiments/legacy_compact_repair/groups7_off/evaluation.json>): original execution or analysis evidence.
- [groups7_off/report.json](<../../../../experiments/legacy_compact_repair/groups7_off/report.json>): original execution or analysis evidence.
- [groups7_off/submission.csv](<../../../../experiments/legacy_compact_repair/groups7_off/submission.csv>): original execution or analysis evidence.
- [groups7_off/trace.jsonl](<../../../../experiments/legacy_compact_repair/groups7_off/trace.jsonl>): original execution or analysis evidence.
- [recovery_policy.json](<../../../../experiments/legacy_compact_repair/recovery_policy.json>): original execution or analysis evidence.

## Recorded evaluation values

These are values read from retained evaluations, not newly computed results.

| Evidence | Macro F1 | Micro F1 |
|---|---:|---:|
| [groups12_off](<../../../../experiments/legacy_compact_repair/groups12_off/evaluation.json>) | 0.2642055223650767 | 0.25 |
| [groups7_off](<../../../../experiments/legacy_compact_repair/groups7_off/evaluation.json>) | 0.22154488024053243 | 0.2777777777777778 |

## Predecessor

[legacy_compact_baseline](<legacy_compact_baseline.md>): Observed failed baseline notices required a separately executed repair. The repair appended a final-JSON/evidence-at-most-80-characters instruction and set search_rounds=0; original source/criteria and the standard output2048 budget were retained.

## Follow-ups

- [legacy_compact_extended_repair](<legacy_compact_extended_repair.md>): Standard repair still failed PPS-DEV-147; output allowance increased from 2048 to 4096.

## Unverified conditions

No new model inference, server run, holdout evaluation, or throughput measurement was performed during relocation. Missing historical timestamps and absent external inputs remain explicit limitations.

- [Original detailed observation: groups12_off/evaluation.md](<../../../../experiments/legacy_compact_repair/retained_documents/docs/reports/analysis/compact200/groups12_off/evaluation.md>): immutable original-language evidence; current judgment is above.

- [Original detailed observation: groups7_off/evaluation.md](<../../../../experiments/legacy_compact_repair/retained_documents/docs/reports/analysis/compact200/groups7_off/evaluation.md>): immutable original-language evidence; current judgment is above.

## Recorded condition evidence

These links identify exact original settings rather than substituting current defaults. Missing values remain unknown.

- [groups12_off/report.json](<../../../../experiments/legacy_compact_repair/groups12_off/report.json>). `{"options": {"model_dir": "models/gemma-4-26B-A4B-it-NVFP4", "max_model_len": 32768, "thinking": false, "item_group_size": 4}, "limits": {"batch_size": 8, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false}, "groups": [["v1", "v2", "v3", "v4"], ["v5", "v6", "v7"], ["v8"], ["v9", "v19"], ["v10", "v11", "v12", "v13"], ["v14"], ["v15", "v16"], ["v17", "v18"], ["v20"], ["v21"], ["v22", "v23"], ["v24"]]}`

- [groups7_off/report.json](<../../../../experiments/legacy_compact_repair/groups7_off/report.json>). `{"options": {"model_dir": "models/gemma-4-26B-A4B-it-NVFP4", "max_model_len": 32768, "thinking": false, "item_group_size": 9}, "limits": {"batch_size": 8, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false}, "groups": [["v1", "v2", "v3", "v4", "v5", "v6", "v7", "v8"], ["v9", "v19"], ["v10", "v11", "v12", "v13", "v14", "v15", "v16", "v17", "v18"], ["v20"], ["v21"], ["v22", "v23"], ["v24"]]}`

- [ungrouped_on/before_extended_recovery/report.json](<../../../../experiments/legacy_compact_repair/ungrouped_on/before_extended_recovery/report.json>). `{"options": {"model_dir": "models/gemma-4-26B-A4B-it-NVFP4", "max_model_len": 32768, "thinking": true, "item_group_size": 24}, "limits": {"batch_size": 8, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false}, "groups": [["v1", "v2", "v3", "v4", "v5", "v6", "v7", "v8", "v9", "v10", "v11", "v12", "v13", "v14", "v15", "v16", "v17", "v18", "v19", "v20", "v21", "v22", "v23", "v24"]]}`

- [code](<../../../../experiments/legacy_compact_repair/code>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

- [retained_documents](<../../../../experiments/legacy_compact_repair/retained_documents>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

Migration verification: [check report](<../../../maintenance/structure-migration-verification.md>). Retained migration temporary path: [tmp/structure-migration-20260913](<../../../../tmp/structure-migration-20260913>). This is migration work, not a claim about original execution temporary paths. Essential original evidence is retained under the run directory.
