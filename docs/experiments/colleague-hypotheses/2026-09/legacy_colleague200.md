# How does the supplied colleague submission behave on local dev200?

Current judgment: **Historical local timing anchor; reported server time lacks matching server logs and scope verification.**

Reason and scope: Historical local timing anchor; reported server time lacks matching server logs and scope verification. Historical local development evidence; no unseen-data or competition-server generalization is established.

## Run identity and conditions

Run ID: `legacy_colleague200`. Historical start time: **unknown**. The available metadata does not establish an orchestration start; initialization/log/preparation timestamps were not substituted. Execution month: September 2026, supported by the original project records and original run names.

Planned/recorded conditions: recorded execution. Preserve condition-specific manifests, input snapshots, traces, and budgets; do not infer identical conditions from the folder name.

## Actions, observations, and judgment history

The original execution and analysis artifacts below retain their original bytes. The migration changes their location and introduces explicit run identity; it is not a rerun, re-score, or adoption decision.

Historical local timing anchor; reported server time lacks matching server logs and scope verification.

Historical comparison and interpretation documents are linked from the area index. Their original bytes are also retained in the migration document archive. Current judgment above governs reuse; historical measurements alone do not override a later withdrawal or narrowed scope.

## Run-specific interpretation

Consult the condition-level observations and retained original interpretation linked below. Missing execution settings are not reconstructed from present defaults.

## Evidence and reproducibility

[Retained execution directory](<../../../../experiments/legacy_colleague200>) · [Execution metadata and original-file hashes](<../../../../experiments/legacy_colleague200/run.json>)

Source snapshots and original manifests retain historical paths. Do not rewrite their hashes or commands. New code and instructions use the migration mapping; old commands need not execute unchanged. Locally excluded data/model assets require separately restored matching content in another checkout. Exact GPU reproducibility has not been verified by this migration.

Essential evidence is retained here, not solely in temporary work or Git-excluded outputs. The migration inventory identifies every original location and checksum. Task verification and temporary paths are listed in the metadata.

## Retained artifacts

- [evaluation.json](<../../../../experiments/legacy_colleague200/evaluation.json>): original execution or analysis evidence.
- [report.json](<../../../../experiments/legacy_colleague200/report.json>): original execution or analysis evidence.
- [submission.csv](<../../../../experiments/legacy_colleague200/submission.csv>): original execution or analysis evidence.
- [validation.json](<../../../../experiments/legacy_colleague200/validation.json>): original execution or analysis evidence.

## Recorded evaluation values

These are values read from retained evaluations, not newly computed results.

| Evidence | Macro F1 | Micro F1 |
|---|---:|---:|
| [legacy_colleague200](<../../../../experiments/legacy_colleague200/evaluation.json>) | 0.19689106866142744 | 0.22009569377990432 |

## Unverified conditions

No new model inference, server run, holdout evaluation, or throughput measurement was performed during relocation. Missing historical timestamps and absent external inputs remain explicit limitations.

- [Original detailed observation: colleague200/comparison.md](<../../../../experiments/legacy_colleague200/retained_documents/docs/reports/analysis/colleague200/comparison.md>): immutable original-language evidence; current judgment is above.

## Historical conditions, observations, and decisions

The following retained interpretation records the historical execution and decisions. Commands in it describe that time; current execution instructions are in [operations](../../../operations.md).

### Colleague submitted ZIP: dev200 timing anchor

Artifact base: `analysis/colleague200/`; unqualified JSON/CSV/log/source paths below use this base. Detailed Markdown reports: [index](<../../README.md>).

Completed2026-09-11; `docs/experiments/colleague-hypotheses/2026-09/legacy_colleague200.md`, `evaluation.json`, `calibration.json`, `casebook_audit.json`, `validation.json`. User reports this exact submission took75min in competition and passed120min; no server log/timing-scope/count supplied. No new submission performed.

Archive `submit_today_fewshot_rag.zip`: script.py, requirements.txt(comments only), model\casebook.json. Preserve file bytes under `analysis/colleague200/original/`; normalize Windows separator for extraction. Hashes in archive_manifest.json/run_manifest.json. `user/` untouched. Runner `experiments/legacy_colleague200/code/benchmark_colleague200.py` imports original, delegates original run unchanged, records prompts/requests and model/index times. Local changes only checkpoint path, quant=None(auto native NVFP4), Cutlass MoE backend for RTX5090. No source/prompts/rules/retrieval tuning.

Original settings:16384 context, output1536, seed20260826,temp0,chunk128(default engine max_num_seqs256,max_num_batched_tokens8192),gpuutil.92,prefixcache enabled(default),native chat template OFF(no toggle),all24 together, no H6. Plain BM25 law RAG2538 articles, top6/5000chars; fewshot rank24items by term presence, select top8, first positive+negative each, total4500chars. Document heads1200chars each + keyword paragraphs, starting12000chars; iterative document shrink.46/200 shrunk below initial budget. Actual max14846tokens vs counter14845; every request had exactly+1token discrepancy, still input+1536<=16384.

Measured:200/200 successful outputs,2chat calls(128,72),all finish_reason=stop,0filled/invalid items,0CSV errors. Model load76.7355s; BM25 index.2130s; model chat243.6022s; complete run410.1491s (original internal report408.9s excludes wrapper return teardown). First engine init/compile included; no separate warmup. Pre-inference elapsed165.2277s. Remaining prep/import/teardown about89.6s; not all pure prompt prep. Input2465856,output127553,cached451200. No embedding model/BGE.

Scores: Macro.19689107,Micro.22009569,FP219,FN107,exact36/200.154 emitted quotes all match a single source document;45 nonabsence positives missing quotes. Source model/server precision differs; cannot claim server score reproduction. Original zero-fill fallback preserved, but not used. Audit re-applied exact stock parser/postprocess to every raw response and checked49columnCSV/200IDs, source hashes, actual contexts and token totals. `uv run --locked python -m nara.evaluation.summarize_colleague200` regenerates all evaluation/comparison artifacts.

Few-shot leakage:casebook explicitly constructed from dev200;144examples drawn from80unique notices. Actual prompts use32unique source notices;19 notices receive their own labeled example,27such feature-example pairs. Complete score is development-data reproduction, not independent validation. Diagnostic120 IDs absent from casebook have Macro.09522059/Micro.12048193; selection changes class distribution and dev-driven prompt design remains, so not held-out performance. Do not silently remove examples; faithful submitted pipeline is the user's requested benchmark.

75min anchor: naive local200 full-runtime threshold410.1491*120/75=656.2385s(10m56s). This overweights fixed model startup in a200notice run. Subtract measured local model load+index, retain per-notice prep:reference333.2006s; rough processing threshold533.1209s(8m53s). Assumes reported75min covers full server run, server startup is relatively small and hardware scaling transfers across pipelines. Import/teardown not separately isolated. Infer-only389.7635s(6m30s) threshold omits considerable prep and is not appropriate for full-runtime calibration.

Our candidates:prefix groups12OFFH6 local601s processing/628s incl load→naive114.8min server, startup-adjusted135.3min. UngroupedONH6 local717.3s/745.5s→136.3/161.5min. These are heuristic scenarios, not measurements or passing/failing verdicts. RTX5090NVFP4 vs L40SINT8, different batch/cache utilization, source/output length distributions and fixed costs prevent universal conversion. No assumed hidden count used. Earlier local1853 extrapolations are local-only and cannot establish server passage. Timing target about9min processing is provisional, not a guaranteed threshold.


## Recorded condition evidence

These links identify exact original settings rather than substituting current defaults. Missing values remain unknown.

No standalone execution-settings manifest is available for this record. Retained code, results, and original observation documents define the recoverable scope; no defaults were invented.

- [source](<../../../../experiments/legacy_colleague200/source>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

- [code](<../../../../experiments/legacy_colleague200/code>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

- [retained_documents](<../../../../experiments/legacy_colleague200/retained_documents>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

Migration verification: [check report](<../../../maintenance/structure-migration-verification.md>). Retained migration temporary path: [tmp/structure-migration-20260913](<../../../../tmp/structure-migration-20260913>). This is migration work, not a claim about original execution temporary paths. Essential original evidence is retained under the run directory.
