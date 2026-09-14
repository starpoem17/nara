# How do compact prompts and grouping conditions compare on dev200?

Current judgment: **Historical initial four-condition sweep; groups12 OFF selected for the subsequent H6 question. Later repairs are separate runs.**

Reason and scope: Historical initial four-condition sweep; groups12 OFF selected for the subsequent H6 question. Later repairs are separate runs. Historical local development evidence; no unseen-data or competition-server generalization is established.

## Current interpretation and material history

First-pass failures: groups7 notice063, groups12 notice120, ungroupedON103/147/153. GroupedON remained user-excluded and was not rerun. Compact source/meta were not clipped. Output2048/context32768/batch8; the selection rule prioritized MacroF1, with speed within .01. Final merged scores are owned by the linked repair records, not misrepresented as original first-pass results.

## Run identity and conditions

Run ID: `legacy_compact_baseline`. Historical start time: **unknown**. The available metadata does not establish an orchestration start; initialization/log/preparation timestamps were not substituted. Execution month: September 2026, supported by the original project records and original run names.

Planned/recorded conditions: groups7_off, groups9_off, groups12_off, ungrouped_on. Preserve condition-specific manifests, input snapshots, traces, and budgets; do not infer identical conditions from the folder name.

## Actions, observations, and judgment history

The original execution and analysis artifacts below retain their original bytes. The migration changes their location and introduces explicit run identity; it is not a rerun, re-score, or adoption decision.

Historical initial four-condition sweep; groups12 OFF selected for the subsequent H6 question. Later repairs are separate runs.

Historical comparison and interpretation documents are linked from the area index. Their original bytes are also retained in the migration document archive. Current judgment above governs reuse; historical measurements alone do not override a later withdrawal or narrowed scope.

## Run-specific interpretation

Consult the condition-level observations and retained original interpretation linked below. Missing execution settings are not reconstructed from present defaults.

## Evidence and reproducibility

[Retained execution directory](<../../../../experiments/legacy_compact_baseline>) · [Execution metadata and original-file hashes](<../../../../experiments/legacy_compact_baseline/run.json>)

Source snapshots and original manifests retain historical paths. Do not rewrite their hashes or commands. New code and instructions use the migration mapping; old commands need not execute unchanged. Locally excluded data/model assets require separately restored matching content in another checkout. Exact GPU reproducibility has not been verified by this migration.

Essential evidence is retained here, not solely in temporary work or Git-excluded outputs. The migration inventory identifies every original location and checksum. Task verification and temporary paths are listed in the metadata.

## Retained artifacts

- [comparison.json](<../../../../experiments/legacy_compact_baseline/comparison.json>): original execution or analysis evidence.
- [groups9_off/evaluation.json](<../../../../experiments/legacy_compact_baseline/groups9_off/evaluation.json>): original execution or analysis evidence.
- [groups9_off/report.json](<../../../../experiments/legacy_compact_baseline/groups9_off/report.json>): original execution or analysis evidence.
- [groups9_off/submission.csv](<../../../../experiments/legacy_compact_baseline/groups9_off/submission.csv>): original execution or analysis evidence.
- [groups9_off/trace.jsonl](<../../../../experiments/legacy_compact_baseline/groups9_off/trace.jsonl>): original execution or analysis evidence.
- [manifest.json](<../../../../experiments/legacy_compact_baseline/manifest.json>): original execution or analysis evidence.
- [validation.json](<../../../../experiments/legacy_compact_baseline/validation.json>): original execution or analysis evidence.

## Recorded evaluation values

These are values read from retained evaluations, not newly computed results.

| Evidence | Macro F1 | Micro F1 |
|---|---:|---:|
| [groups9_off](<../../../../experiments/legacy_compact_baseline/groups9_off/evaluation.json>) | 0.22647273210584748 | 0.26 |

## Follow-ups

- [legacy_compact_repair](<legacy_compact_repair.md>): Observed failed baseline notices required a separately executed repair. The repair appended a final-JSON/evidence-at-most-80-characters instruction and set search_rounds=0; original source/criteria and the standard output2048 budget were retained.
- [legacy_compact_h6](<../../rule-evaluation/2026-09/legacy_compact_h6.md>): Baseline scores selected the grouped condition before the H6 sweep; v2/v3 model judgments were replaced with frozen H6 rules.

## Unverified conditions

No new model inference, server run, holdout evaluation, or throughput measurement was performed during relocation. Missing historical timestamps and absent external inputs remain explicit limitations.

- [Original detailed observation: groups9_off/evaluation.md](<../../../../experiments/legacy_compact_baseline/retained_documents/docs/reports/analysis/compact200/groups9_off/evaluation.md>): immutable original-language evidence; current judgment is above.

## Recorded condition evidence

These links identify exact original settings rather than substituting current defaults. Missing values remain unknown.

- [groups12_off/first_pass/report.json](<../../../../experiments/legacy_compact_baseline/groups12_off/first_pass/report.json>). `{"options": {"model_dir": "models/gemma-4-26B-A4B-it-NVFP4", "max_model_len": 32768, "thinking": false, "item_group_size": 4}, "limits": {"batch_size": 8, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false}, "groups": [["v1", "v2", "v3", "v4"], ["v5", "v6", "v7"], ["v8"], ["v9", "v19"], ["v10", "v11", "v12", "v13"], ["v14"], ["v15", "v16"], ["v17", "v18"], ["v20"], ["v21"], ["v22", "v23"], ["v24"]]}`

- [groups7_off/first_pass/report.json](<../../../../experiments/legacy_compact_baseline/groups7_off/first_pass/report.json>). `{"options": {"model_dir": "models/gemma-4-26B-A4B-it-NVFP4", "max_model_len": 32768, "thinking": false, "item_group_size": 9}, "limits": {"batch_size": 8, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false}, "groups": [["v1", "v2", "v3", "v4", "v5", "v6", "v7", "v8"], ["v9", "v19"], ["v10", "v11", "v12", "v13", "v14", "v15", "v16", "v17", "v18"], ["v20"], ["v21"], ["v22", "v23"], ["v24"]]}`

- [groups9_off/report.json](<../../../../experiments/legacy_compact_baseline/groups9_off/report.json>). `{"options": {"model_dir": "models/gemma-4-26B-A4B-it-NVFP4", "max_model_len": 32768, "thinking": false, "item_group_size": 5}, "limits": {"batch_size": 8, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false}, "groups": [["v1", "v2", "v3", "v4"], ["v5", "v6", "v7", "v8"], ["v9", "v19"], ["v10", "v11", "v12", "v13"], ["v14", "v15", "v16", "v17", "v18"], ["v20"], ["v21"], ["v22", "v23"], ["v24"]]}`

- [manifest.json](<../../../../experiments/legacy_compact_baseline/manifest.json>). `{"limits": {"batch_size": 8, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false}}`

- [ungrouped_on/first_pass/report.json](<../../../../experiments/legacy_compact_baseline/ungrouped_on/first_pass/report.json>). `{"options": {"model_dir": "models/gemma-4-26B-A4B-it-NVFP4", "max_model_len": 32768, "thinking": true, "item_group_size": 24}, "limits": {"batch_size": 8, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false}, "groups": [["v1", "v2", "v3", "v4", "v5", "v6", "v7", "v8", "v9", "v10", "v11", "v12", "v13", "v14", "v15", "v16", "v17", "v18", "v19", "v20", "v21", "v22", "v23", "v24"]]}`

- [source](<../../../../experiments/legacy_compact_baseline/source>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

- [code](<../../../../experiments/legacy_compact_baseline/code>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

- [retained_documents](<../../../../experiments/legacy_compact_baseline/retained_documents>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

Migration verification: [check report](<../../../maintenance/structure-migration-verification.md>). Retained migration temporary path: [tmp/structure-migration-20260913](<../../../../tmp/structure-migration-20260913>). This is migration work, not a claim about original execution temporary paths. Essential original evidence is retained under the run directory.
