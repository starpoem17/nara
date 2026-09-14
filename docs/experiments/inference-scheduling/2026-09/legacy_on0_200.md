# Does zero thinking budget preserve instant judgments and enable prefix reuse?

Current judgment: **Historical paired OFF/ON0 observations; parser and scope limitations are retained.**

Reason and scope: The hybrid cache/mode observations motivated OFF versus ON0 comparison; zero thinking budget and mode differ under the recorded paired conditions. Historical local development evidence; no unseen-data or competition-server generalization is established.

## Run identity and conditions

Run ID: `legacy_on0_200`. Historical start time: **unknown**. The available metadata does not establish an orchestration start; initialization/log/preparation timestamps were not substituted. Execution month: September 2026, supported by the original project records and original run names.

Planned/recorded conditions: recorded execution. Preserve condition-specific manifests, input snapshots, traces, and budgets; do not infer identical conditions from the folder name.

## Actions, observations, and judgment history

The original execution and analysis artifacts below retain their original bytes. The migration changes their location and introduces explicit run identity; it is not a rerun, re-score, or adoption decision.

Historical paired OFF/ON0 observations; parser and scope limitations are retained.

Historical comparison and interpretation documents are linked from the area index. Their original bytes are also retained in the migration document archive. Current judgment above governs reuse; historical measurements alone do not override a later withdrawal or narrowed scope.

## Run-specific interpretation

Consult the condition-level observations and retained original interpretation linked below. Missing execution settings are not reconstructed from present defaults.

## Evidence and reproducibility

[Retained execution directory](<../../../../experiments/legacy_on0_200>) · [Execution metadata and original-file hashes](<../../../../experiments/legacy_on0_200/run.json>)

Source snapshots and original manifests retain historical paths. Do not rewrite their hashes or commands. New code and instructions use the migration mapping; old commands need not execute unchanged. Locally excluded data/model assets require separately restored matching content in another checkout. Exact GPU reproducibility has not been verified by this migration.

Essential evidence is retained here, not solely in temporary work or Git-excluded outputs. The migration inventory identifies every original location and checksum. Task verification and temporary paths are listed in the metadata.

## Retained artifacts

- [comparison.json](<../../../../experiments/legacy_on0_200/comparison.json>): original execution or analysis evidence.
- [manifest.json](<../../../../experiments/legacy_on0_200/manifest.json>): original execution or analysis evidence.

## Predecessor

[legacy_hybrid200](<legacy_hybrid200.md>): The hybrid cache/mode observations motivated OFF versus ON0 comparison; zero thinking budget and mode differ under the recorded paired conditions.

## Unverified conditions

No new model inference, server run, holdout evaluation, or throughput measurement was performed during relocation. Missing historical timestamps and absent external inputs remain explicit limitations.

- [Original detailed observation: on0_200/comparison.md](<../../../../experiments/legacy_on0_200/retained_documents/docs/reports/analysis/on0_200/comparison.md>): immutable original-language evidence; current judgment is above.

## Historical conditions, observations, and decisions

The following retained interpretation records the historical execution and decisions. Commands in it describe that time; current execution instructions are in [operations](../../../operations.md).

### Instant OFF versus thinking ON with zero budget

Artifact base: `analysis/on0_200/`; unqualified JSON/CSV/log/source paths below use this base. Detailed Markdown reports: [index](<../../README.md>).

Completed 2026-09-11. Report: `docs/experiments/inference-scheduling/2026-09/legacy_on0_200.md`; structured results `comparison.json`, changed cells `judgment_changes.csv`. Runner `experiments/legacy_on0_200/code/benchmark_on0.py`, scorer `experiments/legacy_on0_200/code/summarize_on0.py`. No production default change.

#### Design

Same Gemma4 NVFP4/RTX5090, source-first compact criteria, full documents, output2048/context32768, temperature0/seed0, max_num_seqs8, BGE CUDA, optional RAG, one ordinary retry. Existing instant4 groups/16features only. Other8 judgments frozen from hybrid200/main for explicitly composite24 score. Eight length-quantile smoke notices excluded from full timing. Full200 in100 notice pairs; each arm resets prefix cache, runs2 seed requests then6 follower requests; OFF/ON0 order alternates. OFF template/budgetNone versus ON template/budget0; actual engine budgets audited. Six length-quantile probes: cold, OFF G1 seed, ON0 G1 seed, then identical ON1024 six-feature target; rotate order/reset each condition.

#### Results

Both200 complete; no zero-fill, separate recovery, searches or context failures. Actual requests OFF801/ON0803; length retries1/3. Four16-feature inference time359.591902s/375.446646s: ON0 4.409% slower including retries. Ninety-six pairs without either-arm retry/search:328.221783s/311.610273s, ON0 5.061% faster; post-hoc clean subset does not replace total cost. Pair-bootstrap runtime reduction95%[-.241729,.116748], single-run sampling interval, not run-to-run repeatability.

16-feature Macro .131467→.094529; Micro .179245→.151163; FP96→62/FN78→84; label accuracy .945625→.954375. Flips100/3200 across69notices:64 corrected/36 worsened. Positive scarcity means fewer errors can coexist with lower positive F1. Main losses v19/v23 TP1→0/2→0; v8 TP6 stable, FP46→22. Macro delta−.036938, notice-bootstrap95%[-.082256,.007233]; exploratory local-dev result, not statistically established general deterioration. Frozen-other8 composite24 Macro .278187→.253561; not a new full mixed run.

Follow-on ON1024 target cache OFFseed0%→ON0seed97.6026%; mean prefill .736345→.042351s. Six-target wall56.474519→53.039192s (6.083% lower), seed9.450381/9.669057s separately. Same target inputs/budget;1/36 target labels changed across seed modes. Do not assume cache path preserves outputs or extrapolate to complete mixed200 throughput.

#### Zero-budget audit limitation

Parser-reported thinking body0 for all ON0803 replies, budget0 passed to actual engine.800 start immediately with empty thinking delimiters. Two have leading whitespace/separator. PPS-DEV-188 v10–v13 starts with explanatory prose and reaches2048-token length; ordinary retry succeeds. Saved opening tokens prove this; full invalid output omitted by existing safe trace policy. Gemma parser ignores text before start delimiter, or reports thinking=None when no end delimiter, so thinking_tokens0 does not prove no untagged explanatory output. OFF length retry PPS-DEV-01; other ON0 length retries145/152.

#### Decision and artifacts

ON0 changes judgments; not supported as wholesale instant replacement by this run. Cross-mode source cache benefit measured. Full integrated mixed200 ON0 remains untested. All14 frozen inference/input hashes verified, complete IDs/groups/engine budgets/token counts/context/evidence substring checks passed;7 existing related unit tests passed. Source snapshots in source/, post-run scoring source/digests in analysis_source/ and analysis_manifest.json; engine/load/warmup separate. Raw trace/request logs local. Prior hybrid follow-up was static-only; this is its first GPU follow-up.


## Recorded condition evidence

These links identify exact original settings rather than substituting current defaults. Missing values remain unknown.

- [full/off/report.json](<../../../../experiments/legacy_on0_200/full/off/report.json>). `{"groups": [["v4", "v6", "v7", "v8"], ["v10", "v11", "v12", "v13"], ["v15", "v16", "v17", "v18"], ["v19", "v20", "v21", "v23"]], "limits": {"batch_size": 8, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false}}`

- [full/on0/report.json](<../../../../experiments/legacy_on0_200/full/on0/report.json>). `{"groups": [["v4", "v6", "v7", "v8"], ["v10", "v11", "v12", "v13"], ["v15", "v16", "v17", "v18"], ["v19", "v20", "v21", "v23"]], "limits": {"batch_size": 8, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false}}`

- [manifest.json](<../../../../experiments/legacy_on0_200/manifest.json>). `{"model": "models/gemma-4-26B-A4B-it-NVFP4", "groups": [["v4", "v6", "v7", "v8"], ["v10", "v11", "v12", "v13"], ["v15", "v16", "v17", "v18"], ["v19", "v20", "v21", "v23"]], "limits": {"batch_size": 8, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false}}`

- [smoke/off/report.json](<../../../../experiments/legacy_on0_200/smoke/off/report.json>). `{"groups": [["v4", "v6", "v7", "v8"], ["v10", "v11", "v12", "v13"], ["v15", "v16", "v17", "v18"], ["v19", "v20", "v21", "v23"]], "limits": {"batch_size": 8, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false}}`

- [smoke/on0/report.json](<../../../../experiments/legacy_on0_200/smoke/on0/report.json>). `{"groups": [["v4", "v6", "v7", "v8"], ["v10", "v11", "v12", "v13"], ["v15", "v16", "v17", "v18"], ["v19", "v20", "v21", "v23"]], "limits": {"batch_size": 8, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false}}`

- [source](<../../../../experiments/legacy_on0_200/source>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

- [analysis_source](<../../../../experiments/legacy_on0_200/analysis_source>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

- [code](<../../../../experiments/legacy_on0_200/code>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

- [retained_documents](<../../../../experiments/legacy_on0_200/retained_documents>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

Migration verification: [check report](<../../../maintenance/structure-migration-verification.md>). Retained migration temporary path: [tmp/structure-migration-20260913](<../../../../tmp/structure-migration-20260913>). This is migration work, not a claim about original execution temporary paths. Essential original evidence is retained under the run directory.
