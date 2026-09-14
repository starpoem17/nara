# How does optional legal retrieval behave on dev200?

Current judgment: **Historical exploratory baseline; actual optional searches and development-set limits govern interpretation.**

Reason and scope: Historical exploratory baseline; actual optional searches and development-set limits govern interpretation. Historical local development evidence; no unseen-data or competition-server generalization is established.

## Run identity and conditions

Run ID: `legacy_gemma4_rag_dev200_v1`. Historical start time: **unknown**. The available metadata does not establish an orchestration start; initialization/log/preparation timestamps were not substituted. Execution month: September 2026, supported by the original project records and original run names.

Planned/recorded conditions: recorded execution. Preserve condition-specific manifests, input snapshots, traces, and budgets; do not infer identical conditions from the folder name.

## Actions, observations, and judgment history

The original execution and analysis artifacts below retain their original bytes. The migration changes their location and introduces explicit run identity; it is not a rerun, re-score, or adoption decision.

Historical exploratory baseline; actual optional searches and development-set limits govern interpretation.

Historical comparison and interpretation documents are linked from the area index. Their original bytes are also retained in the migration document archive. Current judgment above governs reuse; historical measurements alone do not override a later withdrawal or narrowed scope.

## Run-specific interpretation

Consult the condition-level observations and retained original interpretation linked below. Missing execution settings are not reconstructed from present defaults.

## Evidence and reproducibility

[Retained execution directory](<../../../../experiments/legacy_gemma4_rag_dev200_v1>) · [Execution metadata and original-file hashes](<../../../../experiments/legacy_gemma4_rag_dev200_v1/run.json>)

Source snapshots and original manifests retain historical paths. Do not rewrite their hashes or commands. New code and instructions use the migration mapping; old commands need not execute unchanged. Locally excluded data/model assets require separately restored matching content in another checkout. Exact GPU reproducibility has not been verified by this migration.

Essential evidence is retained here, not solely in temporary work or Git-excluded outputs. The migration inventory identifies every original location and checksum. Task verification and temporary paths are listed in the metadata.

## Retained artifacts

- [evaluation.json](<../../../../experiments/legacy_gemma4_rag_dev200_v1/evaluation.json>): original execution or analysis evidence.
- [manifest.json](<../../../../experiments/legacy_gemma4_rag_dev200_v1/manifest.json>): original execution or analysis evidence.
- [report.json](<../../../../experiments/legacy_gemma4_rag_dev200_v1/report.json>): original execution or analysis evidence.
- [submission.csv](<../../../../experiments/legacy_gemma4_rag_dev200_v1/submission.csv>): original execution or analysis evidence.
- [trace.jsonl](<../../../../experiments/legacy_gemma4_rag_dev200_v1/trace.jsonl>): original execution or analysis evidence.

## Recorded evaluation values

These are values read from retained evaluations, not newly computed results.

| Evidence | Macro F1 | Micro F1 |
|---|---:|---:|
| [legacy_gemma4_rag_dev200_v1](<../../../../experiments/legacy_gemma4_rag_dev200_v1/evaluation.json>) | 0.1652370809934727 | 0.20728291316526612 |

## Unverified conditions

No new model inference, server run, holdout evaluation, or throughput measurement was performed during relocation. Missing historical timestamps and absent external inputs remain explicit limitations.

- [Original detailed observation: gemma4_rag_dev200_v1/evaluation.md](<../../../../experiments/legacy_gemma4_rag_dev200_v1/retained_documents/docs/reports/analysis/gemma4_rag_dev200_v1/evaluation.md>): immutable original-language evidence; current judgment is above.

- [Original detailed observation: gemma4_rag_dev200_v1/interpretation.md](<../../../../experiments/legacy_gemma4_rag_dev200_v1/retained_documents/docs/reports/analysis/gemma4_rag_dev200_v1/interpretation.md>): immutable original-language evidence; current judgment is above.

## Recorded condition evidence

These links identify exact original settings rather than substituting current defaults. Missing values remain unknown.

- [report.json](<../../../../experiments/legacy_gemma4_rag_dev200_v1/report.json>). `{"options": {"data_dir": "data", "input": "data/dev.jsonl", "output_dir": "analysis/gemma4_rag_dev200_v1", "model_dir": "models/gemma-4-26B-A4B-it-NVFP4", "embed_model": "models/bge-m3", "index": "model/legal_index", "embed_device": "cuda", "embedding_batch_size": 32, "batch_size": 8, "max_model_len": 32768, "gpu_memory_utilization": 0.86, "quantization": "auto", "enforce_eager": false, "thinking": false, "output_tokens": 2048, "search_rounds": 2, "queries_per_round": 4, "round_tokens": 4096, "total_retrieval_tokens": 8192, "item_group_size": 24, "limit": 200}, "limits": {"batch_size": 8, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1}}`

- [source](<../../../../experiments/legacy_gemma4_rag_dev200_v1/source>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

- [retained_documents](<../../../../experiments/legacy_gemma4_rag_dev200_v1/retained_documents>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

Migration verification: [check report](<../../../maintenance/structure-migration-verification.md>). Retained migration temporary path: [tmp/structure-migration-20260913](<../../../../tmp/structure-migration-20260913>). This is migration work, not a claim about original execution temporary paths. Essential original evidence is retained under the run directory.
