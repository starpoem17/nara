# Source-first prefix reuse: dev200

Completed 2026-09-11. Artifacts: `analysis/prefix200/comparison.md`, `.json`, `validation.json`; predecessor [compact200](compact200.md). RTX5090, same local Gemma4 NVFP4/32768, groups12 OFF H6, output2048, batch8, optional RAG. No grouped ON rerun.

Change: `nara/prefix_predictor.py` keeps common system; moves existing group criteria/absence IDs from system to the end of user, after unchanged notice ID/meta/full documents. Per notice, complete first real group, then remaining11 through normal batch8. Reuse first answer in merged24; never put answers into another group's prompt. Frozen `nara/inference.py`, model adapter, criteria and H6 unchanged. Main `script.py` remains previous default; use experiment runner explicitly.

Runner: `uv run --locked python scripts/benchmark_prefix200.py --output FRESH_DIRECTORY`; `--prepare-only` performs all200×12 tokenizer/source/criteria preflight. One thinking-capable engine with OFF template/sampling, matching historical comparator. Common warmup excluded, reset prefix cache once before timed loop, never between phases/notices. `ObservedLLM` proxy records vLLM RequestOutput cache counts without modifying requests/results. Capture scripts and source hashes in manifest/source; summarize/audit with `python3 scripts/summarize_prefix200.py` (default artifact directory).

| Measure | Historical groups12 OFF H6 | Source-first |
|---|---:|---:|
| Inference seconds incl retries |1819.6749|600.9577|
| Model-call seconds (includes adapter work) |1807.3784|588.2062|
| Macro F1 |.28444815|.28349273|
| Micro F1 |.26407767|.27737226|
| FP / FN |294 / 85|201 / 96|
| Model turns |2402|2405|
| Rendered input tokens |27473035|27582101|
| Output tokens |123762|120575|
| Measured cached input tokens |unavailable|25083872|

3.02796x speed;66.9744% less time; Macro delta -.00095542. Cache reuse90.9426% of input tokens overall,1.6759% for first200 requests,98.9857% for remaining2205. Token-weighted ratios, not request hit rates. Prefix caching was already enabled in predecessor, but group system criteria broke common prefix before source. Request timing stats unavailable (`disable_log_stats=True`); no measured prefill/decode split. Do not equate rendered tokens with recomputed tokens or walltime savings with pure prefill savings. Source caching does not free context window.

Full200/4800 evaluated,5 invalid responses recovered by ordinary1retry,0 final failures,0 searches,0 thinking tokens. Initial input max29252; shared prefixes2298..29050; all actual input+output+128<=32768. Three notices had some initial optional searches disabled by context (11,143,197; exact IDs in context_check.json). All rules/diagnostics identical to predecessor, H6 frozen hash850ebdceff80371dc8bd4859813e86e017552941b44dfdb4773b672576c925ba. No source clipping/label prompt leak.38 unit tests + artifact audit passed. Emitted quotes97, invalid0; nonabsence positive missing evidence75. Exact substring validation is not semantic evidence validation.

390/4800 decisions changed despite near-equal Macro F1; per-item changes in comparison.json. Prompt role/order and schedule changed together; single historical comparison cannot isolate pure cache effect on accuracy. Prior unchanged-prompt repeat variability also documented in compact200. No labels used to tune this candidate.

Local1853 linear projection incl one measured load27.023s:93.25min vs historical281.46min. Excludes dev preflight/common warmup; not measured1853 or L40S and not a2h guarantee. Ungrouped ON H6 prior projection111.2min remains a separate comparator; no new ON run.
