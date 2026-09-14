# Can the remaining failed thinking notice be recovered with output4096?

Current judgment: **The merged200 result is not a uniform-budget execution; only the failed notice was newly inferred.**

Reason and scope: Initial199/200 success led to a separate output4096 recovery. Historical local development evidence; no unseen-data or competition-server generalization is established.

## Run identity and conditions

Run ID: `legacy_gemma4_thinking_recovery`. Historical start time: **unknown**. The available metadata does not establish an orchestration start; initialization/log/preparation timestamps were not substituted. Execution month: September 2026, supported by the original project records and original run names.

Planned/recorded conditions: recorded execution. Preserve condition-specific manifests, input snapshots, traces, and budgets; do not infer identical conditions from the folder name.

## Actions, observations, and judgment history

The original execution and analysis artifacts below retain their original bytes. The migration changes their location and introduces explicit run identity; it is not a rerun, re-score, or adoption decision.

The merged200 result is not a uniform-budget execution; only the failed notice was newly inferred.

Historical comparison and interpretation documents are linked from the area index. Their original bytes are also retained in the migration document archive. Current judgment above governs reuse; historical measurements alone do not override a later withdrawal or narrowed scope.

## Run-specific interpretation

Consult the condition-level observations and retained original interpretation linked below. Missing execution settings are not reconstructed from present defaults.

## Evidence and reproducibility

[Retained execution directory](<../../../../experiments/legacy_gemma4_thinking_recovery>) · [Execution metadata and original-file hashes](<../../../../experiments/legacy_gemma4_thinking_recovery/run.json>)

Source snapshots and original manifests retain historical paths. Do not rewrite their hashes or commands. New code and instructions use the migration mapping; old commands need not execute unchanged. Locally excluded data/model assets require separately restored matching content in another checkout. Exact GPU reproducibility has not been verified by this migration.

Essential evidence is retained here, not solely in temporary work or Git-excluded outputs. The migration inventory identifies every original location and checksum. Task verification and temporary paths are listed in the metadata.

## Retained artifacts

- [merged/comparison.json](<../../../../experiments/legacy_gemma4_thinking_recovery/merged/comparison.json>): original execution or analysis evidence.
- [merged/evaluation.json](<../../../../experiments/legacy_gemma4_thinking_recovery/merged/evaluation.json>): original execution or analysis evidence.
- [merged/manifest.json](<../../../../experiments/legacy_gemma4_thinking_recovery/merged/manifest.json>): original execution or analysis evidence.
- [merged/report.json](<../../../../experiments/legacy_gemma4_thinking_recovery/merged/report.json>): original execution or analysis evidence.
- [merged/submission.csv](<../../../../experiments/legacy_gemma4_thinking_recovery/merged/submission.csv>): original execution or analysis evidence.
- [merged/trace.jsonl](<../../../../experiments/legacy_gemma4_thinking_recovery/merged/trace.jsonl>): original execution or analysis evidence.

## Recorded evaluation values

These are values read from retained evaluations, not newly computed results.

| Evidence | Macro F1 | Micro F1 |
|---|---:|---:|
| [merged](<../../../../experiments/legacy_gemma4_thinking_recovery/merged/evaluation.json>) | 0.20920359665830682 | 0.2625482625482625 |

## Predecessor

[legacy_gemma4_rag_dev200_thinking](<legacy_gemma4_rag_dev200_thinking.md>): Initial199/200 success led to a separate output4096 recovery.

## Unverified conditions

No new model inference, server run, holdout evaluation, or throughput measurement was performed during relocation. Missing historical timestamps and absent external inputs remain explicit limitations.

- [Original detailed observation: gemma4_rag_dev200_thinking_recovered/comparison.md](<../../../../experiments/legacy_gemma4_thinking_recovery/retained_documents/docs/reports/analysis/gemma4_rag_dev200_thinking_recovered/comparison.md>): immutable original-language evidence; current judgment is above.

- [Original detailed observation: gemma4_rag_dev200_thinking_recovered/evaluation.md](<../../../../experiments/legacy_gemma4_thinking_recovery/retained_documents/docs/reports/analysis/gemma4_rag_dev200_thinking_recovered/evaluation.md>): immutable original-language evidence; current judgment is above.

## Recorded condition evidence

These links identify exact original settings rather than substituting current defaults. Missing values remain unknown.

- [merged/report.json](<../../../../experiments/legacy_gemma4_thinking_recovery/merged/report.json>). `{"options": {"data_dir": "data", "input": "data/dev.jsonl", "output_dir": "analysis/gemma4_rag_dev200_thinking_recovered", "model_dir": "models/gemma-4-26B-A4B-it-NVFP4", "embed_model": "models/bge-m3", "index": "model/legal_index", "embed_device": "cuda", "embedding_batch_size": 32, "batch_size": 8, "max_model_len": 32768, "gpu_memory_utilization": 0.86, "quantization": "auto", "enforce_eager": false, "thinking": true, "output_tokens": 2048, "search_rounds": 2, "require_search": false, "queries_per_round": 4, "round_tokens": 4096, "total_retrieval_tokens": 8192, "item_group_size": 24, "limit": 200}, "limits": {"batch_size": 8, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false}}`

- [recovery/output4096/report.json](<../../../../experiments/legacy_gemma4_thinking_recovery/recovery/output4096/report.json>). `{"options": {"data_dir": "data", "input": "experiments/legacy_gemma4_thinking_recovery/recovery/input.jsonl", "output_dir": "analysis/gemma4_thinking_recovery/output4096", "model_dir": "models/gemma-4-26B-A4B-it-NVFP4", "embed_model": "models/bge-m3", "index": "model/legal_index", "embed_device": "cuda", "embedding_batch_size": 32, "batch_size": 8, "max_model_len": 32768, "gpu_memory_utilization": 0.86, "quantization": "auto", "enforce_eager": false, "thinking": true, "output_tokens": 4096, "search_rounds": 2, "require_search": false, "queries_per_round": 4, "round_tokens": 4096, "total_retrieval_tokens": 8192, "item_group_size": 24, "limit": null}, "limits": {"batch_size": 8, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 4096, "retries": 1, "require_search": false}}`

- [code](<../../../../experiments/legacy_gemma4_thinking_recovery/code>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

- [retained_documents](<../../../../experiments/legacy_gemma4_thinking_recovery/retained_documents>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

Migration verification: [check report](<../../../maintenance/structure-migration-verification.md>). Retained migration temporary path: [tmp/structure-migration-20260913](<../../../../tmp/structure-migration-20260913>). This is migration work, not a claim about original execution temporary paths. Essential original evidence is retained under the run directory.
