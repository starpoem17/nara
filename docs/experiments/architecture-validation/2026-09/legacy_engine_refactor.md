# Does the maintained engine refactor preserve behavior under matched before/after execution?

Current judgment: **Adopted engine refactor; historical matched observations and CPU verification have separately recorded scopes.**

Reason and scope: Adopted engine refactor; historical matched observations and CPU verification have separately recorded scopes. Historical local development evidence; no unseen-data or competition-server generalization is established.

## Run identity and conditions

Run ID: `legacy_engine_refactor`. Historical start time: **unknown**. The available metadata does not establish an orchestration start; initialization/log/preparation timestamps were not substituted. Execution month: September 2026, supported by the original project records and original run names.

Planned/recorded conditions: before, after. Preserve condition-specific manifests, input snapshots, traces, and budgets; do not infer identical conditions from the folder name.

## Actions, observations, and judgment history

The original execution and analysis artifacts below retain their original bytes. The migration changes their location and introduces explicit run identity; it is not a rerun, re-score, or adoption decision.

Adopted engine refactor; historical matched observations and CPU verification have separately recorded scopes.

Historical comparison and interpretation documents are linked from the area index. Their original bytes are also retained in the migration document archive. Current judgment above governs reuse; historical measurements alone do not override a later withdrawal or narrowed scope.

## Run-specific interpretation

Consult the condition-level observations and retained original interpretation linked below. Missing execution settings are not reconstructed from present defaults.

## Evidence and reproducibility

[Retained execution directory](<../../../../experiments/legacy_engine_refactor>) · [Execution metadata and original-file hashes](<../../../../experiments/legacy_engine_refactor/run.json>)

Source snapshots and original manifests retain historical paths. Do not rewrite their hashes or commands. New code and instructions use the migration mapping; old commands need not execute unchanged. Locally excluded data/model assets require separately restored matching content in another checkout. Exact GPU reproducibility has not been verified by this migration.

Essential evidence is retained here, not solely in temporary work or Git-excluded outputs. The migration inventory identifies every original location and checksum. Task verification and temporary paths are listed in the metadata.

## Retained artifacts

- [after/evaluation.json](<../../../../experiments/legacy_engine_refactor/after/evaluation.json>): original execution or analysis evidence.
- [after/manifest.json](<../../../../experiments/legacy_engine_refactor/after/manifest.json>): original execution or analysis evidence.
- [after/report.json](<../../../../experiments/legacy_engine_refactor/after/report.json>): original execution or analysis evidence.
- [after/submission.csv](<../../../../experiments/legacy_engine_refactor/after/submission.csv>): original execution or analysis evidence.
- [after/trace.jsonl](<../../../../experiments/legacy_engine_refactor/after/trace.jsonl>): original execution or analysis evidence.
- [before/evaluation.json](<../../../../experiments/legacy_engine_refactor/before/evaluation.json>): original execution or analysis evidence.
- [before/manifest.json](<../../../../experiments/legacy_engine_refactor/before/manifest.json>): original execution or analysis evidence.
- [before/report.json](<../../../../experiments/legacy_engine_refactor/before/report.json>): original execution or analysis evidence.
- [before/submission.csv](<../../../../experiments/legacy_engine_refactor/before/submission.csv>): original execution or analysis evidence.
- [before/trace.jsonl](<../../../../experiments/legacy_engine_refactor/before/trace.jsonl>): original execution or analysis evidence.

## Recorded evaluation values

These are values read from retained evaluations, not newly computed results.

| Evidence | Macro F1 | Micro F1 |
|---|---:|---:|
| [after](<../../../../experiments/legacy_engine_refactor/after/evaluation.json>) | 0.2598439023890363 | 0.2613065326633166 |
| [before](<../../../../experiments/legacy_engine_refactor/before/evaluation.json>) | 0.26847403649018803 | 0.26634382566585957 |

## Unverified conditions

No new model inference, server run, holdout evaluation, or throughput measurement was performed during relocation. Missing historical timestamps and absent external inputs remain explicit limitations.

- [Original detailed observation: engine-refactor-after-20260911/evaluation.md](<../../../../experiments/legacy_engine_refactor/retained_documents/docs/reports/output/experiments/engine-refactor-after-20260911/evaluation.md>): immutable original-language evidence; current judgment is above.

- [Original detailed observation: engine-refactor-before-20260911/evaluation.md](<../../../../experiments/legacy_engine_refactor/retained_documents/docs/reports/output/experiments/engine-refactor-before-20260911/evaluation.md>): immutable original-language evidence; current judgment is above.

## Historical conditions, observations, and decisions

The following retained interpretation records the historical execution and decisions. Commands in it describe that time; current execution instructions are in [operations](../../../operations.md).

### Local engine module refactor: dev200 before/after

Completed 2026-09-11. User selected the local engine deepening, required compatibility with existing experiment calls, and approved automatic tests plus a matched 200-record before/after comparison. Implementation/interface: [local engine](<../../../architecture/local-engine.md>).

#### Change and controls

Engine-specific rendering, sampling, reply conversion, request identity, cache reset and scheduler observation now reside in `src/inference/engine.py`. `StreamingModel` remains importable from `nara.continuous`. Default execution uses explicit engine options and an observation scope that restores the engine callback on exit. Isolated-group recovery scheduler rows now enter the root aggregate alongside their request/lifecycle rows.

Only three runtime source files differ: `src/inference/engine.py`, `src/inference/continuous.py`, `experiments/legacy_prefix_pipeline200/code/benchmark_prefix_pipeline.py`. Inputs, criteria, H6 rules, groups, budgets, admission policy, dependency lock and effective engine configuration were held fixed. All 200 initial prompt lengths/common-prefix counts match. The baseline includes pre-existing working-copy H6 edits; it is not the historical `experiments/legacy_prefix_pipeline200` run or a clean checkout of the earlier commit.

Both runs: local Gemma NVFP4/RTX5090, 12 OFF groups, 16 slots, step budget8192, context32768, output2048, initial2/live3/source48000/lookahead16. Warmup and first8 smoke are excluded from prediction time; internal retries and any recovery are included. Both runs had zero outer recovery time.

#### Measurements

| Metric | Before | After |
|---|---:|---:|
| Prediction seconds | 296.6103 | 310.5711 |
| Model/retriever load seconds | 30.1413 | 27.4461 |
| Macro F1 | 0.268474 | 0.259844 |
| Micro F1 | 0.266344 | 0.261307 |
| Failed notices | 0 | 0 |
| Model requests | 2401 | 2403 |
| Invalid responses / internal retries | 1 | 3 |
| Output tokens | 114724 | 117245 |
| Cached input fraction | 90.8425% | 90.7775% |
| Peak requests in flight | 16 | 16 |
| Actual FULL graph steps | 12923 | 14419 |
| FULL steps with16 real tokens | 197 | 268 |
| Early next-notice prefill | 197/198 | 197/198 |
| Preempted request events | 0 | 0 |

After was13.9609s (+4.7068%) slower in this paired measurement; Macro F1 decreased0.008630. Output tokens increased2.20%; 227/4800 binary judgments and91 evidence fields changed. Neither the observed differences nor one pair of runs establish their cause or a repeatable performance/quality change. This refactor is not reported as a speed or F1 improvement.

#### Verification

- Existing64 tests passed before; 74 passed after (10 new tests, including three recovery outcomes). Engine tests use a deterministic raw-engine adapter, not a replacement for the production engine module.
- Real GPU run audit passed:200 complete records,49-column CSV, unique request IDs, request/trace/token totals, zero thinking, seed completion before followers, source-window limits, FULL graphs and early prefill. Archived source hashes match; live runtime sources remained unchanged throughout each run.
- Real tokenizer and installed vLLM request parity against the archived before implementation is recorded in `experiments/legacy_engine_refactor/support/engine_audit/request_parity.json`: all2400 initial requests have identical complete token-ID payloads and sampling fields; 12 OFF/ON, search/final and output-budget variants also match. This stops at request submission; it does not claim identical generated output.

#### Artifacts and reproduction

Tracked summary/provenance: `experiments/legacy_engine_refactor/support/engine_audit/comparison.json`; request-parity evidence: `experiments/legacy_engine_refactor/support/engine_audit/request_parity.json`.

Local raw runs, reports, manifests and source snapshots (ignored `output/`):
- Before: `output/experiments/engine-refactor-before-20260911/`
- After: `output/experiments/engine-refactor-after-20260911/`
- GPU-free after preflight: `output/experiments/engine-refactor-preflight-20260911/`

```bash
uv run --locked python -m unittest discover -s tests
uv run --locked nara-experiment --output-dir FRESH_DIRECTORY
uv run --locked python -m nara.tools.verify_engine_refactor FRESH_DIRECTORY
uv run --locked python -m nara.tools.check_engine_request_parity output/experiments/engine-refactor-before-20260911
```

The archived before source is required for differential request verification. Source/data digests are included in comparison.json; raw data and full run snapshots stay local. Historical report/recovery redesign and judgment-conversation consolidation remain separate work.


## Recorded condition evidence

These links identify exact original settings rather than substituting current defaults. Missing values remain unknown.

- [after/manifest.json](<../../../../experiments/legacy_engine_refactor/after/manifest.json>). `{"groups": [["v1", "v4"], ["v5", "v6", "v7"], ["v8"], ["v9", "v19"], ["v10", "v11", "v12", "v13"], ["v14"], ["v15", "v16"], ["v17", "v18"], ["v20"], ["v21"], ["v22", "v23"], ["v24"]], "limits": {"batch_size": 16, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false, "instant_output_tokens": null}, "recovery_policy": "One same-policy rerun of failed notices, then one same-prompt isolated predict per still-failed group. All internal retries, recovery time and events included."}`

- [after/report.json](<../../../../experiments/legacy_engine_refactor/after/report.json>). `{"groups": [["v1", "v4"], ["v5", "v6", "v7"], ["v8"], ["v9", "v19"], ["v10", "v11", "v12", "v13"], ["v14"], ["v15", "v16"], ["v17", "v18"], ["v20"], ["v21"], ["v22", "v23"], ["v24"]], "limits": {"batch_size": 16, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false, "instant_output_tokens": null}, "options": {"model_dir": "models/gemma-4-26B-A4B-it-NVFP4", "max_model_len": 32768, "thinking": false, "item_group_size": 4}}`

- [before/manifest.json](<../../../../experiments/legacy_engine_refactor/before/manifest.json>). `{"groups": [["v1", "v4"], ["v5", "v6", "v7"], ["v8"], ["v9", "v19"], ["v10", "v11", "v12", "v13"], ["v14"], ["v15", "v16"], ["v17", "v18"], ["v20"], ["v21"], ["v22", "v23"], ["v24"]], "limits": {"batch_size": 16, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false, "instant_output_tokens": null}, "recovery_policy": "One same-policy rerun of failed notices, then one same-prompt isolated predict per still-failed group. All internal retries, recovery time and events included."}`

- [before/report.json](<../../../../experiments/legacy_engine_refactor/before/report.json>). `{"groups": [["v1", "v4"], ["v5", "v6", "v7"], ["v8"], ["v9", "v19"], ["v10", "v11", "v12", "v13"], ["v14"], ["v15", "v16"], ["v17", "v18"], ["v20"], ["v21"], ["v22", "v23"], ["v24"]], "limits": {"batch_size": 16, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false, "instant_output_tokens": null}, "options": {"model_dir": "models/gemma-4-26B-A4B-it-NVFP4", "max_model_len": 32768, "thinking": false, "item_group_size": 4}}`

- [code](<../../../../experiments/legacy_engine_refactor/code>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

- [retained_documents](<../../../../experiments/legacy_engine_refactor/retained_documents>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

Migration verification: [check report](<../../../maintenance/structure-migration-verification.md>). Retained migration temporary path: [tmp/structure-migration-20260913](<../../../../tmp/structure-migration-20260913>). This is migration work, not a claim about original execution temporary paths. Essential original evidence is retained under the run directory.
