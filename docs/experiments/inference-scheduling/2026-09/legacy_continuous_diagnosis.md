# Why did continuous scheduling change judgments despite matching inputs?

Current judgment: **Controlled diagnosis points to batch-sensitive generation; the specific kernel cause remains unisolated.**

Reason and scope: Observed accuracy differences led to a predefined five-stage diagnostic sweep. Historical local development evidence; no unseen-data or competition-server generalization is established.

## Run identity and conditions

Run ID: `legacy_continuous_diagnosis`. Historical start time: **unknown**. The available metadata does not establish an orchestration start; initialization/log/preparation timestamps were not substituted. Execution month: September 2026, supported by the original project records and original run names.

Planned/recorded conditions: recorded execution. Preserve condition-specific manifests, input snapshots, traces, and budgets; do not infer identical conditions from the folder name.

## Actions, observations, and judgment history

The original execution and analysis artifacts below retain their original bytes. The migration changes their location and introduces explicit run identity; it is not a rerun, re-score, or adoption decision.

Controlled diagnosis points to batch-sensitive generation; the specific kernel cause remains unisolated.

Historical comparison and interpretation documents are linked from the area index. Their original bytes are also retained in the migration document archive. Current judgment above governs reuse; historical measurements alone do not override a later withdrawal or narrowed scope.

## Run-specific interpretation

Consult the condition-level observations and retained original interpretation linked below. Missing execution settings are not reconstructed from present defaults.

## Evidence and reproducibility

[Retained execution directory](<../../../../experiments/legacy_continuous_diagnosis>) · [Execution metadata and original-file hashes](<../../../../experiments/legacy_continuous_diagnosis/run.json>)

Source snapshots and original manifests retain historical paths. Do not rewrite their hashes or commands. New code and instructions use the migration mapping; old commands need not execute unchanged. Locally excluded data/model assets require separately restored matching content in another checkout. Exact GPU reproducibility has not been verified by this migration.

Essential evidence is retained here, not solely in temporary work or Git-excluded outputs. The migration inventory identifies every original location and checksum. Task verification and temporary paths are listed in the metadata.

## Retained artifacts

- [plan.json](<../../../../experiments/legacy_continuous_diagnosis/plan.json>): original execution or analysis evidence.
- [validation.json](<../../../../experiments/legacy_continuous_diagnosis/validation.json>): original execution or analysis evidence.

## Predecessor

[legacy_continuous_full200](<legacy_continuous_full200.md>): Observed accuracy differences led to a predefined five-stage diagnostic sweep.

## Follow-ups

- [legacy_prefill_decode_probe](<legacy_prefill_decode_probe.md>): Earlier diagnosis motivated a new same24 barrier/continuous comparison; engine submission timing and internal batching remain confounders.

## Unverified conditions

No new model inference, server run, holdout evaluation, or throughput measurement was performed during relocation. Missing historical timestamps and absent external inputs remain explicit limitations.

- [Original detailed observation: continuous_diagnosis/report.md](<../../../../experiments/legacy_continuous_diagnosis/retained_documents/docs/reports/analysis/continuous_diagnosis/report.md>): immutable original-language evidence; current judgment is above.

## Historical conditions, observations, and decisions

The following retained interpretation records the historical execution and decisions. Commands in it describe that time; current execution instructions are in [operations](../../../operations.md).

### Continuous scheduling accuracy diagnosis

Artifact base: `analysis/continuous_diagnosis/`; unqualified JSON/CSV/log/source paths below use this base. Detailed Markdown reports: [index](<../../README.md>).

Status: complete; no inference task pending. Report `docs/experiments/inference-scheduling/2026-09/legacy_continuous_diagnosis.md`, summary.json, historical_flips.csv, divergences.json, input_audit.json, validation.json. Diagnostic scripts/source snapshots retained in source/; logs engine.log.

Original200 six-feature comparison:26/1200 label flips across24notices;17 correct→wrong,9 wrong→correct, net8 moreerrors. Only41 positive labels. TP18→15,FP15→20; Macro .500577→.391453,Micro .486486→.394737. v1 TP4→2 among7positives drives large macro change. Paired notice bootstrap5000replicates fixed-output new−old95CI Macro[-.22964,.00675],Micro[-.21377,.02983]; not inference-repeat uncertainty.

Full200 CPU audit: old/new prompt messages, ordered schemas, actual tokenizer IDs identical; historical input lengths match; old/new final outputs replay through original postprocessing identically; historical logged engine config strings identical; original core/compact prompt/data snapshots unchanged. No RAG, retries, context/output failures in these two six-feature200 traces. Previous200 did not store rawthinking/token IDs, so cannot recover their first divergent token.

GPU controls: first24 original input-order notices (not label-selected), same engine/context32768/step8192/maxseq8/ON1024/output2048/temp0/seed0. Prefix reset per stage; other warm state persists. Five stages: old_barrier1,old_barrier2,new_barrier,new_continuous1,new_continuous2. Captured actual returned prompt tokens to independently mapID, raw thinking/token IDs, API effective sampling. All120 route/parse/params checks passed.

Results: old repeat0token/label changes; oldAPI→newAPI withbarrier0changes; newbarrier→continuous16/24 raw sequences changed (first8unchanged),12answers changed,8/144bits changed. All16 first diverge inside thinking at0-based token3–21. Continuous repeats0changes. Six-feature24 Macro/Micro barrier .577778/.714286 vscontinuous .511111/.625; these are diagnostics, not full200 replacement. Current instrumented oldbarrier differs from historical first24 by8labels, so separate-engine/warm/instrumentation/internal scheduling effects also exist. Do not attribute all historical26flips solely to refill.

Inference: evidence points to batch-sensitive engine generation, not application response routing/postprocessing; this controlled run is repeat-stable within a schedule. Newprefill/decode mix changes numerical execution and can change greedytop1 early, then thinking autoregression amplifies differences. Exact GPUkernel cause (NVFP4/MoE/attention) unisolated; no logit margin or kernel-specific ablation. Do not assert quantization is proved sole cause or random runs always vary.

Official docs https://docs.vllm.ai/en/stable/usage/reproducibility/ : default reproducibility not guaranteed; offline multiprocessing0 fixes scheduling or batch invariance reduces schedule sensitivity. Observed engine multiprocessingTrue,batch_invariantFalse. Gemma4 NVFP4 batch-invariant compatibility/cost not tested; no production settings changed. Fixed-schedule reproducibility differs from invariance across scheduling. Future comparisons should log rawtokens, actual routing and repeat/control schedules. Existing1.8% timing delta is single-run evidence, not sufficient reason to accept unstable quality.


## Recorded condition evidence

These links identify exact original settings rather than substituting current defaults. Missing values remain unknown.

No standalone execution-settings manifest is available for this record. Retained code, results, and original observation documents define the recoverable scope; no defaults were invented.

- [source](<../../../../experiments/legacy_continuous_diagnosis/source>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

- [code](<../../../../experiments/legacy_continuous_diagnosis/code>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

- [retained_documents](<../../../../experiments/legacy_continuous_diagnosis/retained_documents>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

Migration verification: [check report](<../../../maintenance/structure-migration-verification.md>). Retained migration temporary path: [tmp/structure-migration-20260913](<../../../../tmp/structure-migration-20260913>). This is migration work, not a claim about original execution temporary paths. Essential original evidence is retained under the run directory.
