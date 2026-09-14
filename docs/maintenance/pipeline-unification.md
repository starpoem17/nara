# Single-pipeline integration verification

Status: implementation and required integration verification complete on 2026-09-14. User request: promote the existing experimental/evaluation inference pipeline and retire the dual command/driver structure. [ADR0002](../adr/0002-single-inference-command.md) owns the adopted scope and tradeoffs.

## Source and preservation

Baseline revision: `ceb9751c28dc749f5928bb37555cdb6913607535`. The affected source files were clean before this task. Source selection is the maintained `src/experiments/pipeline.py` at that revision, backed by the scheduling adoption and later rule/budget decisions linked in the ADR. This is integration of that exact maintained implementation, not a replay of the historical output2048 experiment.

Pre-existing changes to feature-exclusivity experiment indexes, reports, `analysis/`, and three new experiment directories were left intact. Historical experiment directories and snapshots were not edited. [Task work](../../tmp/pipeline-unification/) retains the four original driver/config files, test logs and smoke console output; do not delete it without user instruction.

## Changes and checks

- One installed prediction command, `nara`, and one maintained execution module, `src/inference/pipeline.py`.
- Explicit input/asset paths, arbitrary nonempty input size, optional labels/evaluation and paired comparison, fresh optional output export with provenance.
- Adopted prompt order, model/engine policy, rule ownership, recovery behavior and stage cache resets preserved.
- Original full suite: 139 tests passed. Updated full suite: 146 tests passed, including single-command integration, three-record recovery, external input retention, empty input rejection, optional evaluation/export, actual custom-path scoring/comparison and engine cleanup on failed recovery.
- Locked offline environment sync succeeded and refreshed installed entrypoints.
- [Final installed-command GPU smoke](checks/20260914_160718_pipeline-unification-final-smoke.md) passed with exit0 and no remaining engine process. All captured source hashes match final maintained code.
- Preparation covered200 notices /2400 group inputs; maximum input29310 tokens fits the32768 context including output512 and128 reserve. GPU smoke covered8 notices /96 requests with zero failures, all request limits512, and FULL graph execution. Cached input1263136 /1388264 tokens (90.99%). This is a small smoke observation, not a maximum-cache or throughput claim.
- [Initial smoke](checks/20260914_160139_pipeline-unification-smoke.md) completed inference but exposed two existing-driver shutdown defects: returning a `Run` object through the console entrypoint, and leaving an engine worker after completion. The task retained evidence and terminated only its own lingering processes. The final code returns0 and explicitly closes the engine on all execution exits.
- [Intermediate preparation](checks/20260914_160432_pipeline-unification-preparation.md) confirmed the exit-code fix before GPU cleanup was added. Final smoke supersedes it for the final source verification.
- `git diff --check` passed. Only the `nara` prediction entrypoint remains installed; module invocation exposes the same options.

[Retained integration evidence](evidence/pipeline-unification/README.md) includes before/after logs, tested files, original driver bytes, console output and GPU summaries. Exact final source/input/assets and condition artifacts are in the final smoke run. No essential verification relies solely on temporary files.

No full200 GPU generation, score comparison, throughput benchmark or holdout validation has been performed as part of this integration.
