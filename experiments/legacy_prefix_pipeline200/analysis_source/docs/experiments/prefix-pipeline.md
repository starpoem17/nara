# Source-first twelve-group pipeline16

Completed2026-09-11. User explicitly authorized cross-notice continuous scheduling again, superseding the earlier mixed-five barrier-only direction for this experiment. Current experiment runner `scripts/benchmark_prefix_pipeline.py`; prediction prompts/groups/model/H6 remain frozen. Do not interpret one batch-dependent F1 fluctuation as structural quality degradation.

## Schedule and scope

`nara/prefix_pipeline.py` subclasses existing ContinuousPredictor for unchanged turn construction, validation/retry/RAG/postprocessing. First2notices admitted together; per-notice first real group completes before11followers. At outstanding follower count≤16, prioritize the next notice's first group at next free slot; never wait for all16 requests. At most3live notices and48000 summed common-source tokens; input order preserved for admission, final output restored to input order. This is a logical source budget, not a physical KV allocation formula. Modes allOFF; maxseq16, step8192, context32768, output2048, graphs FULL_AND_PIECEWISE, same NVFP4/RTX5090. Main/callback trace, engine request times, lifecycle, admissions, per-step scheduler/actualgraph modes captured. No source/text/results shared across notice prompts.

## Results

Full200303.9153s vs sequential1→11 561.6153s (45.89% lower), old1→8→3 600.9577s. Macro .26820460 vs.26766451/.28349273; Micro .26368159 vs.25853659/.27737226. FP196/FN100. Finalfailures0,3invalidresponses repaired by normal retry, no extra recovery, noRAG, nocontextoverflow. Load63.6484s incl engine init/compilation; load+inference367.5637s. Preflight/warmup1.2976s/first8smoke16.6997s excluded. Single historical comparison, simultaneous engine/graph/schedule changes; no isolated-causal speed or F1 claim.

After startup2,195/198next notices started prefill before prior live notices' GPU last token;180had prefill-latency interval overlap with old follower decode;195also reached first token before all prior live work ended. This verifies early admission and engine scheduling, not simultaneous GPUkernel execution. Exceptions028/121: source sum54611/50751 exceeds48000 even with one old notice.137: earlier source-budget block, later submitted before old finish but scheduled18.3ms after; complete-drain latency not entirely eliminated.

Actualgraphs FULL13675steps/NONE943/PIECEWISE0; FULL with16real tokens206steps. Mixed/long-prefill steps can run withoutgraphs. Peak requests16, mean sampled running7.8607; do not imply16always full. PeakKV51.34%,preempted requests0,tokenweighted cache90.81%. Source budget max47226; windowblock64/sourceblock23events. Future capacity tuning could relax conservative admission, but not measured here.

## Artifacts and audit

`analysis/prefix_pipeline200/comparison.md`, `scheduling_summary.json`, `prefill_timeline.json`, `validation.json`; main/ contains frozen firstpass, smoke/ excluded execution test. Root traces final200. Source snapshots/manifest and analysis_source/analysis_manifest preserve reproducibility. `scripts/summarize_prefix_pipeline.py`: sourcehashes,200×24,49columnCSV,allrule rows,request IDs/tokens,seed-before-follower timing,max16live,FULLgraphs,earlyprefill verified.10related tests passed (pipeline3/prefix3/continuous4). Evidence invalid0,positive nonabsence missing77; binary F1 does not score evidence completeness.

Reproduce: `MAX_JOBS=2 uv run --locked python scripts/benchmark_prefix_pipeline.py --output FRESH_DIRECTORY`; summarize fixed artifact directory with `python3 scripts/summarize_prefix_pipeline.py`. Default submission entrypoints were not changed.
