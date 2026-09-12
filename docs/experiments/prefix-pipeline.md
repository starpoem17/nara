# Source-first twelve-group pipeline16

Artifact base: `analysis/prefix_pipeline200/`; unqualified JSON/CSV/log/source paths below use this base. Detailed Markdown reports: [index](../reports/README.md).

Completed2026-09-11. User explicitly authorized cross-notice continuous scheduling again, superseding the earlier mixed-five barrier-only direction for this experiment. The measured run used `src/experiments/benchmark_prefix_pipeline.py` with frozen prompts/groups/model/H6. User subsequently selected this execution structure as the default experiment pipeline. Do not interpret one batch-dependent F1 fluctuation as structural quality degradation.

## Default experiment entrypoint

`uv run --locked nara-experiment` runs current source code on dev200 with the measured twelve-group OFF/engine16 scheduling defaults. Timestamped `output/experiments/` directory by default; `--output-dir`/`--output` chooses a fresh directory. `--prepare-only` measures all current prompt token lengths/common prefixes and snapshots sources without GPU model loading; `--smoke-only` also runs first8 and verifies actual FULL graphs. Normal execution retains warmup, smoke, timed200, unchanged-budget recovery and evaluation. Current output cap changed from2048 to512 on2026-09-12 for all groups, internal retries, notice reruns and isolated recovery; both groups12 and groups21 use512. Historical-reference mode and measured results below retain output2048. No new GPU result is claimed for the512default.

Default runs do not require historical analysis manifests or matching old H6/prompt hashes. Current tokens/common-prefix lengths are recomputed, context overflow rejected without clipping, current code copied/hashed in manifest/source. Existing `src/experiments/benchmark_prefix_pipeline.py` retains historical-reference assertions for explicit reproduction; exact past runs require the archived source versions. `script.py` remains the ungrouped comparison/submission entrypoint; `src/experiments/run_batch_fallback.py` is historical mixed-five comparison. They are not the default experimental workflow.

Current12-group rule extraction (2026-09-12): default `src/experiments/run_experiment.py` and sequential `src/experiments/benchmark_prefix200.py` opt into `configuration(..., briefing_rule=True)`. LLM handles21items in12groups; group11 is `[v23]`, rules handle v2/v3/v22. `src/rules/briefing.py::judge(record)` returns existing H6 judgments plus dev-informed v22 and exact-source evidence; matches frozen `analysis/v22_rule200/predictions_revised.jsonl` for all200inputs. Metadata/document negotiation detection and regex decisions are unchanged from that revision. Evidence is capped at500chars without changing binary decisions. Rules are merged on first pass, notice rerun, isolated recovery and final logs/CSV. Source snapshots include the rule module; manifests record rule_items.

Scope: other grouping strategies, hybrid and explicit historical-reference pipeline keep H6-only behavior; shared configuration defaults remain historical unless explicitly opted in. Generic compact benchmark variants remain historical comparisons. No GPU comparison or new speed/v23 score claim. The100% dev v22 result remains dev-informed, not holdout validation. Tests exercise actual12requests/21modelitems,49-column output, initial/recovery rule merge, negative briefing scope, frozen-prediction parity and unaffected legacy groups.

Recovery ownership and attempt artifacts: [failed-notice recovery](../architecture/recovery.md). The default runner delegates the existing retry policy to `src/inference/recovery.py` and saves `recovery_attempts.jsonl` alongside aggregate traces.

## Singleton comparison (2026-09-12)

Current runner accepts `--grouping groups21`; default remains `groups12`. Singleton order flattens existing groups; v2/v3/v22 remain rules. Reproduce each with `uv run --locked nara-experiment --grouping groups12 --output FRESH12` and `--grouping groups21 --output FRESH21`. Summarize paired subfolders with `src/evaluation/summarize_singleton_groups.py PARENT`.

Matched dev200, one timed pass each (12 then21), same source hashes/settings, separate engines and reset caches after untimed smoke: 313.81897s→326.12438s (+12.30540s,+3.9212%). MacroF1 .28690968→.26398982; MicroF1 .22380107→.16932271. FP347→766, FN90→68; 713changed judgments,158corrected/555regressed. Rules unchanged; failures/recovery/search0 in both. Model turns2402→4201; output120636→144273; token-weighted cache90.7649%→94.6301%. Time variance/order effects are unmeasured; accuracy includes scheduling-dependent changes. See [comparison](../reports/output/experiments/groups12_vs21_20260912/comparison.md) and artifacts `output/experiments/groups12_vs21_20260912/`.

## Schedule and scope

`src/inference/prefix_pipeline.py` subclasses existing ContinuousPredictor for unchanged turn construction, validation/retry/RAG/postprocessing. First2notices admitted together; per-notice first real group completes before11followers. At outstanding follower count≤16, prioritize the next notice's first group at next free slot; never wait for all16 requests. At most3live notices and48000 summed common-source tokens; input order preserved for admission, final output restored to input order. This is a logical source budget, not a physical KV allocation formula. Modes allOFF; maxseq16, step8192, context32768, output2048, graphs FULL_AND_PIECEWISE, same NVFP4/RTX5090. Main/callback trace, engine request times, lifecycle, admissions, per-step scheduler/actualgraph modes captured. No source/text/results shared across notice prompts.

## Results

Full200303.9153s vs sequential1→11 561.6153s (45.89% lower), old1→8→3 600.9577s. Macro .26820460 vs.26766451/.28349273; Micro .26368159 vs.25853659/.27737226. FP196/FN100. Finalfailures0,3invalidresponses repaired by normal retry, no extra recovery, noRAG, nocontextoverflow. Load63.6484s incl engine init/compilation; load+inference367.5637s. Preflight/warmup1.2976s/first8smoke16.6997s excluded. Single historical comparison, simultaneous engine/graph/schedule changes; no isolated-causal speed or F1 claim.

After startup2,195/198next notices started prefill before prior live notices' GPU last token;180had prefill-latency interval overlap with old follower decode;195also reached first token before all prior live work ended. This verifies early admission and engine scheduling, not simultaneous GPUkernel execution. Exceptions028/121: source sum54611/50751 exceeds48000 even with one old notice.137: earlier source-budget block, later submitted before old finish but scheduled18.3ms after; complete-drain latency not entirely eliminated.

Actualgraphs FULL13675steps/NONE943/PIECEWISE0; FULL with16real tokens206steps. Mixed/long-prefill steps can run withoutgraphs. Peak requests16, mean sampled running7.8607; do not imply16always full. PeakKV51.34%,preempted requests0,tokenweighted cache90.81%. Source budget max47226; windowblock64/sourceblock23events. Future capacity tuning could relax conservative admission, but not measured here.

## Artifacts and audit

`docs/reports/analysis/prefix_pipeline200/comparison.md`, `scheduling_summary.json`, `prefill_timeline.json`, `validation.json`; main/ contains frozen firstpass, smoke/ excluded execution test. Root traces final200. Source snapshots/manifest and analysis_source/analysis_manifest preserve reproducibility. `src/evaluation/summarize_prefix_pipeline.py`: sourcehashes,200×24,49columnCSV,allrule rows,request IDs/tokens,seed-before-follower timing,max16live,FULLgraphs,earlyprefill verified.10related tests passed (pipeline3/prefix3/continuous4). Evidence invalid0,positive nonabsence missing77; binary F1 does not score evidence completeness.

Historical run: `MAX_JOBS=2 uv run --locked python -m nara.experiments.benchmark_prefix_pipeline --output FRESH_DIRECTORY` with frozen reference sources. `src/evaluation/summarize_prefix_pipeline.py` audits the original fixed artifact directory; new default runs produce evaluation via the runner itself. Default submission entrypoints were not changed.
