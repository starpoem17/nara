# Five-group mixed-mode dev200

Artifact base: `analysis/hybrid200/`; unqualified JSON/CSV/log/source paths below use this base. Detailed Markdown reports: [index](../reports/README.md).

Completed 2026-09-11. All variants200×24, no remaining failures or context overflow. Canonical report: `docs/reports/analysis/hybrid200/comparison.md`; detailed scores `per_feature.csv`, `comparison.json`; timing `timing_analysis.json`, `cache_analysis.json`; audit `validation.json`.

## Frozen design

Gemma4 NVFP4/RTX5090, context32768, output2048, source-first compact criteria, full original documents, optional BGE RAG. Same H6 rules for v2/v3 (excluded from model criteria/schema). Groups:
- OFF: [v4,v6,v7,v8], [v10,v11,v12,v13], [v15,v16,v17,v18], [v19,v20,v21,v23].
- ON1024: [v1,v5,v9,v14,v22,v24].

Selected on earlier dev200 comparisons; current scores are development evidence, not held-out validation. Primary Macro, secondary Micro; earlier similarity margin .01, prefer faster. <=7 groups constraint retained. No rerun of rejected all-ON7/9/12.

## Runs and artifacts

- `scripts/benchmark_hybrid200.py`: real main200 (per notice OFF seed1, cached OFF3, ON1), isolated same-six OFF200/ON256200, cache24 matched pairs.
- `scripts/benchmark_hybrid_batch_controls.py`: same-six ON1024 batch8; real optimized5 mixed ON256 batch8; real optimized5 allOFF (seed2, cached8).
- `scripts/summarize_hybrid200.py`: audits, composite controls, paired notice bootstrap2000, all24 TP/FP/FN/F1, timing and cache summaries.
- Frozen inputs/code/prompts: `analysis/hybrid200/{manifest.json,source/,prompt_*.txt,decision_plan.json,batch_control_plan.json}`. Never edit running experiment code.
- Composite controls reuse main instant16+rules2 and replace real six-feature outputs. Scores exact for this composition; full-pipeline times are summed-stage estimates. Real main/optimized/optimized_off times are measured.

## Measurement scope

Stats-enabled vLLM RequestStateStats: prefill scheduled→first token; decode first→last; queue separate. Engine request latency, not isolated CUDA kernel time. Concurrent request sums overlap; interval unions also reported. Previous baselines had stats disabled.

Cache probe:12 input-length quantile records×2 repeats; reset cache per condition; alternate cold/warm order. Same target G2,128 generated tokens, unstructured diagnostic, min_tokens128/ignore_eos. Warm seed G1 has separately reported cost. Output hashes differ across all24 pairs despite equal lengths; not bit-identical replay. Diagnostics never become predictions.

Historical baselines: [prefix12](prefix-cache.md), [ungrouped ON H6](compact200.md). Same-group v10–v13 changed27/800 bits vs prefix12 (v10:18,v11:9); grouping effects not causally isolated from batching/numerical paths. Original ON/OFF token templates differ at front, so source KV cannot cross modes.

Time anchor: [colleague](colleague-submission.md) gives provisional local200 inference target533.12s; hardware/quantization/batching dependent, not a competition passing guarantee.

## Results

| Strategy | Inference seconds | Macro | Micro |
|---|---:|---:|---:|
| Prior12 OFF prefix |600.958|.283493|.277372|
| Prior ungrouped ON H6 |717.348|.255249|.328125|
| Five mixed ON1024 serial |2404.813|.274036|.295181|
| Five mixed ON256 optimized |709.074|.250386|.263804|
| Five allOFF optimized |447.139|.198584|.246246|

Same-six controls (other18 frozen): OFF324.340s, full Macro.205367/Micro.243323; ON1024 serial1884.803s, Macro.274036/Micro.295181; ON256 serial720.654s, Macro.213368/Micro.250784; ON1024 batch8 503.510s, Macro.272131/Micro.292683. Batch8 preserved observed aggregate score much better than reducing thinking budget. Composite ON1024 batch8 full time1023.520s is a summed-stage estimate, NOT a full real run.

ON1024 vs OFF: Macro+.068669 (paired bootstrap95% [.03250,.10186]), Micro+.051857 ([.01926,.08784]). ON256 vs OFF only Macro+.008001, CI crosses0. These are exploratory same-dev comparisons. Batch8 speeds group throughput3.74x; not per-record latency3.74x.

Cache matched probes: cold prefill.677833s/decode.953237s/call1.633137s; warm.037932s/.953327s/.993691s;98.402% cached tokens. Prefill94.4% and marginal call39.2% lower; seed call1.631263s extra diagnostic cost. Long15–29K inputs: call55.5% lower. Main instant request sums prefill19.5%, decode80.5%; cached groups prefill6.6%. Main wall78.4% thinking. Pure kernel timing was not measured.

Vs prior12: thinking6 contributes+.048230 to total Macro, instant16 contributes−.057687. Main better7/worse8/tied9 features; v8 FP49 vs15, v20 TP0 vs3. Five allOFF is25.6% faster than prior12 but Macro−.084908. Selected-thinking hypothesis remains worth investigating; current5 partition is not a winning replacement. Keep prior12 as Macro reference and ungroupedON as Micro reference. Future (unmeasured): improve instant grouping within7 cap; continuously supply thinking requests instead of8-record barriers; independently validated conditional thinking. Do not imply mechanism or unseen-data improvement proven.

## Failure and evidence audit

AllOFF first pass444.614s failed PPS-DEV-049 group[v10,v11,v12,v13] after two2048-token length stops. `scripts/recover_hybrid200.py` retried only failed group with identical prompt/OFF/output2048; succeeded2.525s. Main table includes inference repair; separate model reload27.469s is in total_seconds. Originals in optimized_off/first_pass;199 successful records replayed through original postprocessing and verified unchanged. Failed notice's other4 successful groups restored exactly. No zero-fill or label-based retries. Recovery code/policy frozen separately.

Execution audit passed full200/49-column CSV, trace alignment, source hashes, rules equality, request/token accounting and context32768. Prior42 unit tests passed; recovery additionally verifies full successful-record replay. All new RAG choices0 actual searches. Binary F1 excludes evidence completeness: valid nonempty/missing-required evidence main84/65, optimized73/60, optimized_off73/72. Invalid nonempty quotes0 because unchanged postprocessing drops mismatches; missing positives remain. Do not call these submission-ready evidence outputs.

## Follow-up: batching, ON0, ungrouped-only strengths

`docs/reports/analysis/hybrid200/followup_analysis.md` answers user follow-up; no additional GPU inference. Batch8 means8 independent notices×same6 features, one model; first main supplied only1 ON request despite max_num_seqs8. Log weight14.8GiB, KV9.75GiB/80,934tokens, max32K concurrency2.47x; no8×32K guarantee. Mean per-request decode8.742→16.227s and queue.022→1.841s traded for3.74x throughput. No OOM/preemption log; Waiting/Deferred does NOT identify memory as sole cause (grammar readiness also uses skipped queue). No GPU peak time series measured.

ON0 static check accepted by installed SamplingParams; actual PPS-DEV-01 common prefix OFF G1/ON G5=4tokens vs ON G1/ON G5=13,640 of13,928 G5 tokens. Budget is sampling metadata, not prefix key. ON0 may share source KV withON1024 but generation behavior/cache hit/score untested. Preserve max_tokens2048, enable_thinking=True for both, differ only thinking budget; avoid cache eviction before reuse. Main thinking prefill128.17s/2404.81s=5.33% upper bound on direct isolated prefill saving; overlapping batched latency is not additive. Possible indirect KV capacity gain unmeasured.

Only v15,v18,v9 have ungrouped F1 above both prefix12 and main. v15 robust loss: allON TP4/FP12/FN2 F1.364 vs12 TP0/FP3/FN6 and main0/0/6. v18 weak overall: all1/5/6 F1.154 vs12 2/36/5 F1.089 vs main0/4/7; ON benefit vs12 is precision, not recall. v9 all5/9/1 .5 vs12 5/17/1 .357 vs main4/9/2 .421; ON batch8 same6 recovers.533, so no stable grouping weakness proven. v8 excluded:12OFF better than allON.

Source cases: v15 PPS-DEV-18 has total estimated204.246M vs unit1458.90, SME-wide metadata vs small-only body;055 estimated170.909M vs '<100M' metadata plus nonprofit exception;080 estimated116.522M with SME summary vs small-only detailed eligibility. v18 PPS-DEV-039 small-company mentions in summary/submission docs but missing in actual eligibility section. v9 PPS-DEV-050 specific models plus equivalents clause; allON positive evidence refers to maintenance service, not model designation. Analyze against provided labels; not new legal rulings. Hypotheses only: cross-field conflict, category/amount/exception conjunction, absence scope, output calibration, prompt-context and numeric batch differences. All source docs retained; related groups already paired/combined, so 'group related features' alone did not fix v15/v18. Prioritize controlled ON/OFF on existing[v15,v16,v17,v18] before changing grouping. This follow-up analyzed the proposal without launching new GPU runs.

## Subsequent ON0 execution

The static-only ON0 proposal above was later measured on GPU: [paired instant OFF/ON0 dev200](instant-on0.md). Preserve the earlier measurements as historical scope; see the new report for actual output, quality, runtime, cache and zero-budget parser limitations.
