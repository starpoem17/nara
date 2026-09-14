# Completion-driven scheduling and prefill budgets

Artifact base: `analysis/continuous200/`; unqualified JSON/CSV/log/source paths below use this base. Detailed Markdown reports: [index](<../README.md>).

Status: complete. No GPU job active. Main report `docs/experiments/inference-scheduling/continuous-prefill.md`, machine-readable comparison/validation JSON, per-feature and input-length CSVs. Frozen executed sources in `plan.json` + `source/`; only post-run benchmark report metadata patch is listed in `postrun_changes.json` (no inference change). Current supplemental sources/digests in `analysis_manifest.json` + `analysis_source/`.

## Implementation

- `src/inference/continuous.py`: `StreamingModel(base VLLMModel)` submits per-turn params via local LLMEngine.add_request; poll/step returns each FINAL_ONLY completion. Unique external request IDs; each submission snapshots its thinking mode/budget. Uses same Gemma tokenizer/parser/structured schema/sampling settings as frozen adapter.
- `ContinuousPredictor` extends SourceFirstPredictor; max8 in-flight requests; refills after each completion; per-task optional RAG/forced search/retry/context guard, original `_finish` evidence postprocessing. No failed prediction zero-fill. Returns input order, on_record callback streams completion order.
- Optional cache_seed: each record's first group completes before its followers enter the ready queue; siblings prioritized, no global group barrier. Mixed mode uses existing4OFF+1ON1024, frozen H6 rules. ON0 not applied.
- Existing core, prompts, grouped benchmark snapshots untouched; new standalone experiment path in `experiments/legacy_continuous_pilot/code/benchmark_continuous.py`. Factory injects stats/chunked-prefill/token-budget into original adapter during single-threaded initialization only; not an independent service or concurrent model initialization API.
- 46 unit tests passed: new tests explicitly prove ninth request starts before slow first request ends, per-group seed dependencies/modes, retrieval/retry identity, context failure/no zero-fill.

## Experiment plan

48 pilot records chosen without labels by evenly spaced input-length ranks; retain original order. Same6 ON1024 features, output2048/context32768, slots8, BGE GPU resident, original source/criteria. Compare barrier8 vs continuous at8192 in one engine, then continuous2048/16384 separate engines. Reset prefix before each run; barrier-before-continuous order still leaves compilation/grammar warm-state confound. Single pilot pass; selection fastest completed continuous runtime, not scores. Then full200 same6 and mixed5 at selected token budget. Full mixed scheduling differs from prior serial/pair pipeline; retain historical comparison limits.

Raw traces, per-request timing, submit/complete lifecycle, per-step scheduler counts/KV use are stored. `experiments/legacy_continuous_pilot/code/summarize_continuous.py` produces audits, by-length timing, six-feature vs24-feature scores separately; no adding concurrent request intervals as exclusive walltime.

## Interpretation

max_num_batched_tokens bounds prefill+decode work in one engine step, not prompt length or total KV. Chunked prefill permits original long prompts at smaller step budgets. Application waiting before submission is outside request queue timing. Scheduler Running includes partial-prefill requests; Deferred includes grammar readiness; neither proves memory admission failures.

Gemma config30layers:25 sliding_window1024,5 full attention. Installed vLLM SlidingWindowSpec reserves last1023 tokens + max_in_flight_tokens (max_concurrent_batches×max_num_batched_tokens), capped by context, with block alignment. Smaller budget can reduce both activation profile and sliding-KV per-request worst-case reservation. Startup logged32K capacity is a calculation, not observed throughput.

## Results

Pilot48 barrier8192 121.214s; continuous2048 119.597s,8192 117.614s,16384 130.335s. Time-only selected8192. Activation/KV GiB/calculated32K capacity:2048 1.49/10.20/6.36;8192 1.94/9.75/2.47;16384 3.84/7.85/1.14. Peak allocated KV usage52.0/75.0/98.1%; observed queue/deferred states alone do not establish memory root cause. 2048 is memory-headroom alternative, only pilot tested.

Full200 same6 ON1024: old barrier503.510s→continuous494.458s (1.8% faster); six-feature Macro .500577→.391453, Micro .486486→.394737. Accuracy not preserved. Actual tokenizer/SamplingParams audit `adapter_parity.json`: effective input/settings match for audited turn, original offline generate also normalizes FINAL_ONLY. Scheduling/numerical-path sensitivity plausible, no sole cause proved. Old thinking outputs1020–1022tokens across200, consistent with small barrier-tail loss.

Full200 mixed5 ON1024 continuous: first pass781.595s, one failed instant group PPS-DEV-049 v10–v13 (length twice). Isolated original-prompt/mode/budget recovery17.320s succeeds on second internal turn; total inference798.916s, model loads27.503+27.593s separately, total854.012s. 1005 model turns including5 invalid attempts, no RAG invoked. All200×24 complete, nozero-fill. Macro .262739/Micro .272464;82 exact records; FP145/FN106. Evidence80nonempty/0invalid/68positive nonabsence missing: binary F1 does not ensure evidence completeness.

Recovery sources/policy frozen; first_pass/ preserves original trace/report/request/lifecycle/scheduler. Final trace/request/lifecycle merge recovery; scheduler and trace_completed remain first-pass only. Replay verified all successful records unchanged. Evaluation initially wrote JSON/CSV then failed Markdown on missing model_dir; report-only metadata supplemented and evaluator rerun without GPU inference. Benchmark future report fixed; postrun_changes captures before/after.

Full mixed prior comparisons: ON1024 serial2404.813s Macro.274036/Micro.295181; ON256 batch8 709.074s .250386/.263804; allOFF447.139s .198584/.246246;12OFF600.958s .283493/.277372;ungroupedONH6 717.348s .255249/.328125. Mixed speedup vs serial includes thinking parallelism and cross-group scheduling, not pure refill. Current mixed is not best accuracy/time setting.

Refill full200: ninth request after first completion12.35ms(six),15.20ms(mixed), other7 initial requests unfinished; max8. Mixed weighted running7.783. Instant request mean prefill.249s/decode1.745s, cached input fraction68.9%; thinking .665s/22.052s, cache1.1%. Request intervals overlap; not exclusive GPU walltime. Different mode prefixes retained; ON0 not tested.

46 tests passed; final audit checks source snapshots plus explicit report-only patch, all200×24 CSV/IDs, modes/groups, unchanged H6 rules, token/event counts/context, request lifecycle/refill, preserved successful records. Same dev200 and single pilot pass; no held-out or competition-runtime guarantee. `experiments/legacy_continuous_pilot/code/benchmark_continuous.py` is new runnable experiment path; existing submission CLI default is untouched.

[Original aggregate evidence](<../../maintenance/evidence/structure-migration/original_reports/docs/reports/analysis/continuous200/comparison.md>); historical measurements are preserved as source material.
