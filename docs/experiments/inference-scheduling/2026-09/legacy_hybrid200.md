# How do predefined mixed-thinking and batching controls affect dev200 behavior?

Current judgment: **Predefined main, batch controls, and cache probes are retained as a sweep. It was not adopted as a winning replacement.**

Reason and scope: Predefined main, batch controls, and cache probes are retained as a sweep. It was not adopted as a winning replacement. Historical local development evidence; no unseen-data or competition-server generalization is established.

## Run identity and conditions

Run ID: `legacy_hybrid200`. Historical start time: **unknown**. The available metadata does not establish an orchestration start; initialization/log/preparation timestamps were not substituted. Execution month: September 2026, supported by the original project records and original run names.

Planned/recorded conditions: main, six_off, six_on256, six_on1024_batch8, optimized, optimized_off, cache probes. Preserve condition-specific manifests, input snapshots, traces, and budgets; do not infer identical conditions from the folder name.

## Actions, observations, and judgment history

The original execution and analysis artifacts below retain their original bytes. The migration changes their location and introduces explicit run identity; it is not a rerun, re-score, or adoption decision.

Predefined main, batch controls, and cache probes are retained as a sweep. It was not adopted as a winning replacement.

Historical comparison and interpretation documents are linked from the area index. Their original bytes are also retained in the migration document archive. Current judgment above governs reuse; historical measurements alone do not override a later withdrawal or narrowed scope.

## Run-specific interpretation

Consult the condition-level observations and retained original interpretation linked below. Missing execution settings are not reconstructed from present defaults.

## Evidence and reproducibility

[Retained execution directory](<../../../../experiments/legacy_hybrid200>) · [Execution metadata and original-file hashes](<../../../../experiments/legacy_hybrid200/run.json>)

Source snapshots and original manifests retain historical paths. Do not rewrite their hashes or commands. New code and instructions use the migration mapping; old commands need not execute unchanged. Locally excluded data/model assets require separately restored matching content in another checkout. Exact GPU reproducibility has not been verified by this migration.

Essential evidence is retained here, not solely in temporary work or Git-excluded outputs. The migration inventory identifies every original location and checksum. Task verification and temporary paths are listed in the metadata.

## Retained artifacts

- [comparison.json](<../../../../experiments/legacy_hybrid200/comparison.json>): original execution or analysis evidence.
- [composite_six_off/evaluation.json](<../../../../experiments/legacy_hybrid200/composite_six_off/evaluation.json>): original execution or analysis evidence.
- [composite_six_off/report.json](<../../../../experiments/legacy_hybrid200/composite_six_off/report.json>): original execution or analysis evidence.
- [composite_six_off/submission.csv](<../../../../experiments/legacy_hybrid200/composite_six_off/submission.csv>): original execution or analysis evidence.
- [composite_six_off/trace.jsonl](<../../../../experiments/legacy_hybrid200/composite_six_off/trace.jsonl>): original execution or analysis evidence.
- [composite_six_on1024_batch8/evaluation.json](<../../../../experiments/legacy_hybrid200/composite_six_on1024_batch8/evaluation.json>): original execution or analysis evidence.
- [composite_six_on1024_batch8/report.json](<../../../../experiments/legacy_hybrid200/composite_six_on1024_batch8/report.json>): original execution or analysis evidence.
- [composite_six_on1024_batch8/submission.csv](<../../../../experiments/legacy_hybrid200/composite_six_on1024_batch8/submission.csv>): original execution or analysis evidence.
- [composite_six_on1024_batch8/trace.jsonl](<../../../../experiments/legacy_hybrid200/composite_six_on1024_batch8/trace.jsonl>): original execution or analysis evidence.
- [composite_six_on256/evaluation.json](<../../../../experiments/legacy_hybrid200/composite_six_on256/evaluation.json>): original execution or analysis evidence.
- [composite_six_on256/report.json](<../../../../experiments/legacy_hybrid200/composite_six_on256/report.json>): original execution or analysis evidence.
- [composite_six_on256/submission.csv](<../../../../experiments/legacy_hybrid200/composite_six_on256/submission.csv>): original execution or analysis evidence.
- [composite_six_on256/trace.jsonl](<../../../../experiments/legacy_hybrid200/composite_six_on256/trace.jsonl>): original execution or analysis evidence.
- [main/evaluation.json](<../../../../experiments/legacy_hybrid200/main/evaluation.json>): original execution or analysis evidence.
- [main/report.json](<../../../../experiments/legacy_hybrid200/main/report.json>): original execution or analysis evidence.
- [main/submission.csv](<../../../../experiments/legacy_hybrid200/main/submission.csv>): original execution or analysis evidence.
- [main/trace.jsonl](<../../../../experiments/legacy_hybrid200/main/trace.jsonl>): original execution or analysis evidence.
- [manifest.json](<../../../../experiments/legacy_hybrid200/manifest.json>): original execution or analysis evidence.
- [optimized/evaluation.json](<../../../../experiments/legacy_hybrid200/optimized/evaluation.json>): original execution or analysis evidence.
- [optimized/report.json](<../../../../experiments/legacy_hybrid200/optimized/report.json>): original execution or analysis evidence.
- [optimized/submission.csv](<../../../../experiments/legacy_hybrid200/optimized/submission.csv>): original execution or analysis evidence.
- [optimized/trace.jsonl](<../../../../experiments/legacy_hybrid200/optimized/trace.jsonl>): original execution or analysis evidence.
- [six_off/report.json](<../../../../experiments/legacy_hybrid200/six_off/report.json>): original execution or analysis evidence.
- [six_off/trace.jsonl](<../../../../experiments/legacy_hybrid200/six_off/trace.jsonl>): original execution or analysis evidence.
- [six_on1024_batch8/report.json](<../../../../experiments/legacy_hybrid200/six_on1024_batch8/report.json>): original execution or analysis evidence.
- [six_on1024_batch8/trace.jsonl](<../../../../experiments/legacy_hybrid200/six_on1024_batch8/trace.jsonl>): original execution or analysis evidence.
- [six_on256/report.json](<../../../../experiments/legacy_hybrid200/six_on256/report.json>): original execution or analysis evidence.
- [six_on256/trace.jsonl](<../../../../experiments/legacy_hybrid200/six_on256/trace.jsonl>): original execution or analysis evidence.
- [validation.json](<../../../../experiments/legacy_hybrid200/validation.json>): original execution or analysis evidence.

## Recorded evaluation values

These are values read from retained evaluations, not newly computed results.

| Evidence | Macro F1 | Micro F1 |
|---|---:|---:|
| [composite_six_off](<../../../../experiments/legacy_hybrid200/composite_six_off/evaluation.json>) | 0.205367395136561 | 0.2433234421364985 |
| [composite_six_on1024_batch8](<../../../../experiments/legacy_hybrid200/composite_six_on1024_batch8/evaluation.json>) | 0.2721307039954581 | 0.2926829268292683 |
| [composite_six_on256](<../../../../experiments/legacy_hybrid200/composite_six_on256/evaluation.json>) | 0.21336817023292434 | 0.2507836990595611 |
| [main](<../../../../experiments/legacy_hybrid200/main/evaluation.json>) | 0.27403603550605277 | 0.29518072289156627 |
| [optimized](<../../../../experiments/legacy_hybrid200/optimized/evaluation.json>) | 0.2503856821784453 | 0.26380368098159507 |

## Follow-ups

- [legacy_on0_200](<legacy_on0_200.md>): The hybrid cache/mode observations motivated OFF versus ON0 comparison; zero thinking budget and mode differ under the recorded paired conditions.
- [legacy_hybrid_repair](<legacy_hybrid_repair.md>): Observed optimized-OFF failure triggered separate isolated recovery with unchanged prompt/OFF mode/output2048.
- [legacy_continuous_pilot](<legacy_continuous_pilot.md>): The hybrid study motivated a new completion-driven pilot; predefined barrier/prefill budgets were compared before choosing the full200 budget.

## Unverified conditions

No new model inference, server run, holdout evaluation, or throughput measurement was performed during relocation. Missing historical timestamps and absent external inputs remain explicit limitations.

- [Original detailed observation: hybrid200/comparison.md](<../../../../experiments/legacy_hybrid200/retained_documents/docs/reports/analysis/hybrid200/comparison.md>): immutable original-language evidence; current judgment is above.

- [Original detailed observation: composite_six_off/evaluation.md](<../../../../experiments/legacy_hybrid200/retained_documents/docs/reports/analysis/hybrid200/composite_six_off/evaluation.md>): immutable original-language evidence; current judgment is above.

- [Original detailed observation: composite_six_on1024_batch8/evaluation.md](<../../../../experiments/legacy_hybrid200/retained_documents/docs/reports/analysis/hybrid200/composite_six_on1024_batch8/evaluation.md>): immutable original-language evidence; current judgment is above.

- [Original detailed observation: composite_six_on256/evaluation.md](<../../../../experiments/legacy_hybrid200/retained_documents/docs/reports/analysis/hybrid200/composite_six_on256/evaluation.md>): immutable original-language evidence; current judgment is above.

- [Original detailed observation: hybrid200/followup_analysis.md](<../../../../experiments/legacy_hybrid200/retained_documents/docs/reports/analysis/hybrid200/followup_analysis.md>): immutable original-language evidence; current judgment is above.

- [Original detailed observation: main/evaluation.md](<../../../../experiments/legacy_hybrid200/retained_documents/docs/reports/analysis/hybrid200/main/evaluation.md>): immutable original-language evidence; current judgment is above.

- [Original detailed observation: optimized/evaluation.md](<../../../../experiments/legacy_hybrid200/retained_documents/docs/reports/analysis/hybrid200/optimized/evaluation.md>): immutable original-language evidence; current judgment is above.

## Recorded condition evidence

These links identify exact original settings rather than substituting current defaults. Missing values remain unknown.

- [composite_six_off/report.json](<../../../../experiments/legacy_hybrid200/composite_six_off/report.json>). `{"options": {"model_dir": "models/gemma-4-26B-A4B-it-NVFP4", "max_model_len": 32768, "thinking": false, "item_group_size": 6}, "limits": {"batch_size": 8, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false}, "groups": [["v4", "v6", "v7", "v8"], ["v10", "v11", "v12", "v13"], ["v15", "v16", "v17", "v18"], ["v19", "v20", "v21", "v23"], ["v1", "v5", "v9", "v14", "v22", "v24"]]}`

- [composite_six_on1024_batch8/report.json](<../../../../experiments/legacy_hybrid200/composite_six_on1024_batch8/report.json>). `{"options": {"model_dir": "models/gemma-4-26B-A4B-it-NVFP4", "max_model_len": 32768, "thinking": "mixed six_on1024_batch8", "item_group_size": 6}, "limits": {"batch_size": 8, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false}, "groups": [["v4", "v6", "v7", "v8"], ["v10", "v11", "v12", "v13"], ["v15", "v16", "v17", "v18"], ["v19", "v20", "v21", "v23"], ["v1", "v5", "v9", "v14", "v22", "v24"]]}`

- [composite_six_on256/report.json](<../../../../experiments/legacy_hybrid200/composite_six_on256/report.json>). `{"options": {"model_dir": "models/gemma-4-26B-A4B-it-NVFP4", "max_model_len": 32768, "thinking": "mixed six_on256", "item_group_size": 6}, "limits": {"batch_size": 8, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false}, "groups": [["v4", "v6", "v7", "v8"], ["v10", "v11", "v12", "v13"], ["v15", "v16", "v17", "v18"], ["v19", "v20", "v21", "v23"], ["v1", "v5", "v9", "v14", "v22", "v24"]]}`

- [main/report.json](<../../../../experiments/legacy_hybrid200/main/report.json>). `{"options": {"model_dir": "models/gemma-4-26B-A4B-it-NVFP4", "max_model_len": 32768, "thinking": "mixed: four OFF, six-feature group ON1024", "item_group_size": 6}, "limits": {"batch_size": 8, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false}, "groups": [["v4", "v6", "v7", "v8"], ["v10", "v11", "v12", "v13"], ["v15", "v16", "v17", "v18"], ["v19", "v20", "v21", "v23"], ["v1", "v5", "v9", "v14", "v22", "v24"]]}`

- [manifest.json](<../../../../experiments/legacy_hybrid200/manifest.json>). `{"groups": [["v4", "v6", "v7", "v8"], ["v10", "v11", "v12", "v13"], ["v15", "v16", "v17", "v18"], ["v19", "v20", "v21", "v23"], ["v1", "v5", "v9", "v14", "v22", "v24"]], "limits": {"batch_size": 8, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false}}`

- [optimized/report.json](<../../../../experiments/legacy_hybrid200/optimized/report.json>). `{"options": {"model_dir": "models/gemma-4-26B-A4B-it-NVFP4", "max_model_len": 32768, "thinking": "mixed: four OFF, six-feature ON256 batch8", "item_group_size": 6}, "limits": {"batch_size": 8, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false}, "groups": [["v4", "v6", "v7", "v8"], ["v10", "v11", "v12", "v13"], ["v15", "v16", "v17", "v18"], ["v19", "v20", "v21", "v23"], ["v1", "v5", "v9", "v14", "v22", "v24"]]}`

- [optimized_off/first_pass/report.json](<../../../../experiments/legacy_hybrid200/optimized_off/first_pass/report.json>). `{"options": {"model_dir": "models/gemma-4-26B-A4B-it-NVFP4", "max_model_len": 32768, "thinking": false, "item_group_size": 6}, "limits": {"batch_size": 8, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false}, "groups": [["v4", "v6", "v7", "v8"], ["v10", "v11", "v12", "v13"], ["v15", "v16", "v17", "v18"], ["v19", "v20", "v21", "v23"], ["v1", "v5", "v9", "v14", "v22", "v24"]]}`

- [source](<../../../../experiments/legacy_hybrid200/source>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

- [code](<../../../../experiments/legacy_hybrid200/code>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

- [retained_documents](<../../../../experiments/legacy_hybrid200/retained_documents>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

Migration verification: [check report](<../../../maintenance/structure-migration-verification.md>). Retained migration temporary path: [tmp/structure-migration-20260913](<../../../../tmp/structure-migration-20260913>). This is migration work, not a claim about original execution temporary paths. Essential original evidence is retained under the run directory.
