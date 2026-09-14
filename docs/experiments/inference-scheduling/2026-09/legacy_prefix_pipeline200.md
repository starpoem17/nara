# Does cross-notice prefix scheduling improve twelve-group execution?

Current judgment: **The execution structure was adopted as the default. Historical output2048 measurements do not establish current output512 scores.**

Reason and scope: Earlier sequential batch11 measurements motivated cross-notice scheduling; engine concurrency/graphs/scheduling changed while historical prompts/H6/output2048 remained fixed. Historical local development evidence; no unseen-data or competition-server generalization is established.

## Run identity and conditions

Run ID: `legacy_prefix_pipeline200`. Historical start time: **unknown**. The available metadata does not establish an orchestration start; initialization/log/preparation timestamps were not substituted. Execution month: September 2026, supported by the original project records and original run names.

Planned/recorded conditions: recorded execution. Preserve condition-specific manifests, input snapshots, traces, and budgets; do not infer identical conditions from the folder name.

## Actions, observations, and judgment history

The original execution and analysis artifacts below retain their original bytes. The migration changes their location and introduces explicit run identity; it is not a rerun, re-score, or adoption decision.

The execution structure was adopted as the default. Historical output2048 measurements do not establish current output512 scores.

Historical comparison and interpretation documents are linked from the area index. Their original bytes are also retained in the migration document archive. Current judgment above governs reuse; historical measurements alone do not override a later withdrawal or narrowed scope.

## Run-specific interpretation

Historical conditions: dev200; twelve OFF groups; output2048, context32768, engine16, step8192, FULL_AND_PIECEWISE graphs; at most three live notices and 48000 summed common-source tokens. Frozen model, prompts, grouping, and H6 rules were used. A first-eight smoke check was excluded from timing.

The timed200 execution took303.9153s versus sequential1→11 at561.6153s (45.89% lower) and the older1→8→3 at600.9577s. MacroF1=.26820460, MicroF1=.26368159, FP196, FN100. Loading took63.6484s; load plus inference367.5637s; excluded smoke16.6997s. All200 completed, three invalid outputs were repaired by the planned internal retry; no separate recovery and no retrieval occurred. Engine, graph, and scheduling settings changed together, so these measurements do not isolate a causal speed improvement.

At the time, the user selected this execution structure as the default. Later changes to output512 and the dev-informed v22 rule are different conditions: this run does not validate their scores or speed. Exact-source evidence checks found zero invalid quotations but77 missing positive non-absence evidence fields; binary F1 is not evidence-quality validation. Detailed original scheduling analysis and adoption history are retained with this report's supporting documents.

## Evidence and reproducibility

[Retained execution directory](<../../../../experiments/legacy_prefix_pipeline200>) · [Execution metadata and original-file hashes](<../../../../experiments/legacy_prefix_pipeline200/run.json>)

Source snapshots and original manifests retain historical paths. Do not rewrite their hashes or commands. New code and instructions use the migration mapping; old commands need not execute unchanged. Locally excluded data/model assets require separately restored matching content in another checkout. Exact GPU reproducibility has not been verified by this migration.

Essential evidence is retained here, not solely in temporary work or Git-excluded outputs. The migration inventory identifies every original location and checksum. Task verification and temporary paths are listed in the metadata.

## Retained artifacts

- [comparison.json](<../../../../experiments/legacy_prefix_pipeline200/comparison.json>): original execution or analysis evidence.
- [evaluation.json](<../../../../experiments/legacy_prefix_pipeline200/evaluation.json>): original execution or analysis evidence.
- [main/trace.jsonl](<../../../../experiments/legacy_prefix_pipeline200/main/trace.jsonl>): original execution or analysis evidence.
- [manifest.json](<../../../../experiments/legacy_prefix_pipeline200/manifest.json>): original execution or analysis evidence.
- [report.json](<../../../../experiments/legacy_prefix_pipeline200/report.json>): original execution or analysis evidence.
- [smoke/trace.jsonl](<../../../../experiments/legacy_prefix_pipeline200/smoke/trace.jsonl>): original execution or analysis evidence.
- [submission.csv](<../../../../experiments/legacy_prefix_pipeline200/submission.csv>): original execution or analysis evidence.
- [trace.jsonl](<../../../../experiments/legacy_prefix_pipeline200/trace.jsonl>): original execution or analysis evidence.
- [validation.json](<../../../../experiments/legacy_prefix_pipeline200/validation.json>): original execution or analysis evidence.

## Recorded evaluation values

These are values read from retained evaluations, not newly computed results.

| Evidence | Macro F1 | Micro F1 |
|---|---:|---:|
| [legacy_prefix_pipeline200](<../../../../experiments/legacy_prefix_pipeline200/evaluation.json>) | 0.26820459734577634 | 0.263681592039801 |

## Predecessor

[legacy_prefix_batch11_repair](<legacy_prefix_batch11_repair.md>): Earlier sequential batch11 measurements motivated cross-notice scheduling; engine concurrency/graphs/scheduling changed while historical prompts/H6/output2048 remained fixed.

## Unverified conditions

No new model inference, server run, holdout evaluation, or throughput measurement was performed during relocation. Missing historical timestamps and absent external inputs remain explicit limitations.

- [Original detailed observation: prefix_pipeline200/comparison.md](<../../../../experiments/legacy_prefix_pipeline200/retained_documents/docs/reports/analysis/prefix_pipeline200/comparison.md>): immutable original-language evidence; current judgment is above.

- [Original detailed observation: prefix_pipeline200/evaluation.md](<../../../../experiments/legacy_prefix_pipeline200/retained_documents/docs/reports/analysis/prefix_pipeline200/evaluation.md>): immutable original-language evidence; current judgment is above.

## Recorded condition evidence

These links identify exact original settings rather than substituting current defaults. Missing values remain unknown.

- [manifest.json](<../../../../experiments/legacy_prefix_pipeline200/manifest.json>). `{"groups": [["v1", "v4"], ["v5", "v6", "v7"], ["v8"], ["v9", "v19"], ["v10", "v11", "v12", "v13"], ["v14"], ["v15", "v16"], ["v17", "v18"], ["v20"], ["v21"], ["v22", "v23"], ["v24"]], "limits": {"batch_size": 16, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false}, "recovery_policy": "One same-policy rerun of failed notices, then one same-prompt isolated predict per still-failed group. All internal retries, recovery time and events included."}`

- [report.json](<../../../../experiments/legacy_prefix_pipeline200/report.json>). `{"groups": [["v1", "v4"], ["v5", "v6", "v7"], ["v8"], ["v9", "v19"], ["v10", "v11", "v12", "v13"], ["v14"], ["v15", "v16"], ["v17", "v18"], ["v20"], ["v21"], ["v22", "v23"], ["v24"]], "limits": {"batch_size": 16, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false}, "options": {"model_dir": "models/gemma-4-26B-A4B-it-NVFP4", "max_model_len": 32768, "thinking": false, "item_group_size": 4}}`

- [source](<../../../../experiments/legacy_prefix_pipeline200/source>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

- [analysis_source](<../../../../experiments/legacy_prefix_pipeline200/analysis_source>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

- [code](<../../../../experiments/legacy_prefix_pipeline200/code>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

- [retained_documents](<../../../../experiments/legacy_prefix_pipeline200/retained_documents>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

Migration verification: [check report](<../../../maintenance/structure-migration-verification.md>). Retained migration temporary path: [tmp/structure-migration-20260913](<../../../../tmp/structure-migration-20260913>). This is migration work, not a claim about original execution temporary paths. Essential original evidence is retained under the run directory.
