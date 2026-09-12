# Instant OFF versus thinking ON with zero budget

Artifact base: `analysis/on0_200/`; unqualified JSON/CSV/log/source paths below use this base. Detailed Markdown reports: [index](../reports/README.md).

Completed 2026-09-11. Report: `docs/reports/analysis/on0_200/comparison.md`; structured results `comparison.json`, changed cells `judgment_changes.csv`. Runner `src/experiments/benchmark_on0.py`, scorer `src/evaluation/summarize_on0.py`. No production default change.

## Design

Same Gemma4 NVFP4/RTX5090, source-first compact criteria, full documents, output2048/context32768, temperature0/seed0, max_num_seqs8, BGE CUDA, optional RAG, one ordinary retry. Existing instant4 groups/16features only. Other8 judgments frozen from hybrid200/main for explicitly composite24 score. Eight length-quantile smoke notices excluded from full timing. Full200 in100 notice pairs; each arm resets prefix cache, runs2 seed requests then6 follower requests; OFF/ON0 order alternates. OFF template/budgetNone versus ON template/budget0; actual engine budgets audited. Six length-quantile probes: cold, OFF G1 seed, ON0 G1 seed, then identical ON1024 six-feature target; rotate order/reset each condition.

## Results

Both200 complete; no zero-fill, separate recovery, searches or context failures. Actual requests OFF801/ON0803; length retries1/3. Four16-feature inference time359.591902s/375.446646s: ON0 4.409% slower including retries. Ninety-six pairs without either-arm retry/search:328.221783s/311.610273s, ON0 5.061% faster; post-hoc clean subset does not replace total cost. Pair-bootstrap runtime reduction95%[-.241729,.116748], single-run sampling interval, not run-to-run repeatability.

16-feature Macro .131467→.094529; Micro .179245→.151163; FP96→62/FN78→84; label accuracy .945625→.954375. Flips100/3200 across69notices:64 corrected/36 worsened. Positive scarcity means fewer errors can coexist with lower positive F1. Main losses v19/v23 TP1→0/2→0; v8 TP6 stable, FP46→22. Macro delta−.036938, notice-bootstrap95%[-.082256,.007233]; exploratory local-dev result, not statistically established general deterioration. Frozen-other8 composite24 Macro .278187→.253561; not a new full mixed run.

Follow-on ON1024 target cache OFFseed0%→ON0seed97.6026%; mean prefill .736345→.042351s. Six-target wall56.474519→53.039192s (6.083% lower), seed9.450381/9.669057s separately. Same target inputs/budget;1/36 target labels changed across seed modes. Do not assume cache path preserves outputs or extrapolate to complete mixed200 throughput.

## Zero-budget audit limitation

Parser-reported thinking body0 for all ON0803 replies, budget0 passed to actual engine.800 start immediately with empty thinking delimiters. Two have leading whitespace/separator. PPS-DEV-188 v10–v13 starts with explanatory prose and reaches2048-token length; ordinary retry succeeds. Saved opening tokens prove this; full invalid output omitted by existing safe trace policy. Gemma parser ignores text before start delimiter, or reports thinking=None when no end delimiter, so thinking_tokens0 does not prove no untagged explanatory output. OFF length retry PPS-DEV-01; other ON0 length retries145/152.

## Decision and artifacts

ON0 changes judgments; not supported as wholesale instant replacement by this run. Cross-mode source cache benefit measured. Full integrated mixed200 ON0 remains untested. All14 frozen inference/input hashes verified, complete IDs/groups/engine budgets/token counts/context/evidence substring checks passed;7 existing related unit tests passed. Source snapshots in source/, post-run scoring source/digests in analysis_source/ and analysis_manifest.json; engine/load/warmup separate. Raw trace/request logs local. Prior hybrid follow-up was static-only; this is its first GPU follow-up.
