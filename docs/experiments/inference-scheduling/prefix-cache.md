# Source-first prefix reuse: dev200

Historical implementation/command details below describe the recorded study. Current execution uses [operations](../../operations.md); archived entrypoints are disabled and future executions require a fresh run.

Completed 2026-09-11. Report: [comparison](<2026-09/legacy_prefix200.md>). Artifacts: `analysis/prefix200/` (`comparison.json`, `validation.json`); predecessor [compact200](<../prompt-design/compact200.md>). RTX5090, same local Gemma4 NVFP4/32768, groups12 OFF H6, output2048, batch8, optional RAG. No grouped ON rerun.

Change: `src/inference/prefix_predictor.py` keeps common system; moves existing group criteria/absence IDs from system to the end of user, after unchanged notice ID/meta/full documents. Per notice, complete first real group, then remaining11 through normal batch8. Reuse first answer in merged24; never put answers into another group's prompt. Frozen `src/inference/predictor.py`, model adapter, criteria and H6 unchanged. Main `script.py` remains previous default; use experiment runner explicitly.

Runner: `uv run --locked python -m nara.experiments.benchmark_prefix200 --output FRESH_DIRECTORY`; `--prepare-only` performs all200×12 tokenizer/source/criteria preflight. One thinking-capable engine with OFF template/sampling, matching historical comparator. Common warmup excluded, reset prefix cache once before timed loop, never between phases/notices. `ObservedLLM` proxy records vLLM RequestOutput cache counts without modifying requests/results. Capture scripts and source hashes in manifest/source; summarize/audit with `python3 experiments/legacy_prefix200/code/summarize_prefix200.py` (default artifact directory).

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

## Batch11 follow-up (2026-09-11)

Report: [batch11 comparison](<2026-09/legacy_prefix_batch11_repair.md>). Artifacts: `analysis/prefix200_batch11/{comparison.json,validation.json}`. Runner now accepts `--batch-size 11` (default8 unchanged); changes both Limits.batch_size and engine max_num_seqs. Same source-first prompts/schemas/groups/input-token counts, model adapter, criteria and H6 hashes; all200 first phases begin1, remaining phases begin11. No cross-notice concurrency.

Full200 inference incl completed recovery561.6153s vs600.9577s (6.55% faster); Macro .26766451 vs.28349273, Micro .25853659 vs.27737226; FP204/FN100 vs201/96;251/4800 label flips. First pass550.8362s failed022/066/075 after output/parse retries;9invalid responses total. Whole-notice retries using identical1→11 prompts/budgets succeeded all3 in10.7791s; isolated fallback policy unused. Initial load27.0508s + recovery load28.0450s; measured load+inference616.7111s vs627.9808s. Warmup/dev preflight excluded. One earlier recovery helper crashed on list/tuple comparison after inference; its unmeasured overhead is excluded, disclosed in recovery_aborted.json/log. Do not call616.71s total development walltime.

GPU generate timing: first-group196.456s; main11-way281.825s; subsequent singleton retries48.971s; successful recovery10.329s. Existing8-way271.080s plus remaining batches107.454s. Fewer waves help, but retry costs offset part of savings; different output lengths/scheduling confound a pure batching speed claim. Cache90.93%, no searches/context overflows/final failures. Quotes invalid0, positive nonabsence missing88. Binary F1 only.

`experiments/legacy_prefix_batch11_repair/code/recover_prefix_batch11.py` preserves first_pass artifacts and all failed/recovery model events. `experiments/legacy_prefix_batch11_repair/code/summarize_prefix_batch11.py` checks same source/input/rules,200×24 completeness,49-column CSV, token totals,1→11 submissions and unchanged originally successful records. Prefix unit tests3 passed. Single historical comparison; no repeat/generalization claim. User treats batch-induced numerical variation as outside optimization scope; a single F1 change is not grounds to reject batch11. Follow-up cross-notice execution: [prefix pipeline](<prefix-pipeline.md>).
