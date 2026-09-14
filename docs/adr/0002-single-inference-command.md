# ADR0002: one maintained inference pipeline and command

Status: adopted by the user on 2026-09-14; implementation and verification are recorded in [the integration check](../maintenance/pipeline-unification.md).

## Decision and source

The user requested promotion of the existing experimental/evaluation pipeline and retirement of the two execution paths. `nara` (also `python -m nara`) now invokes `src/inference/pipeline.py` for every prediction. `nara-experiment` and `src/experiments/run_experiment.py` are removed, as is the old baseline implementation in `src/cli.py`. There is no compatibility command redirecting to a second driver.

The integrated implementation is `src/experiments/pipeline.py` from revision `ceb9751c28dc749f5928bb37555cdb6913607535`, with no pre-existing uncommitted changes to that file. Its scheduling adoption comes from [legacy_prefix_pipeline200](../experiments/inference-scheduling/2026-09/legacy_prefix_pipeline200.md); [current adoption](../experiments/inference-scheduling/prefix-pipeline.md) explicitly distinguishes the later 512-token budget and [briefing rule](../experiments/rule-evaluation/briefing-rule.md) from historical output2048 measurements. The original run directories and retained source snapshots remain unchanged. This integration does not adopt the concurrent feature-exclusivity experiments.

## Interface and behavior

The CLI selects input/asset paths and group conditions, captures provenance, invokes the one pipeline, optionally evaluates completed predictions when `--labels` is supplied, and optionally copies final artifacts into a fresh `--output-dir` with a provenance link. Labels do not enter inference. Default input remains `test.jsonl.gz`, falling back to `test.jsonl` under `--data-dir`; dev evaluation is explicit.

The adopted policy stays output512 per model call, thinking OFF, twelve groups with v2/v3/v22 handled by rules, context32768, sixteen engine slots, step8192, shared-prefix caching, bounded notice admission, and the existing recovery policy. `groups21` remains an explicit grouping condition using the same pipeline. Preparation and first-eight smoke checks use that pipeline too. The 200-record restriction is removed; records must be nonempty. No legacy tuning flag silently selects the old baseline. The CLI returns a successful exit code rather than a `Run` object, and the pipeline explicitly closes the engine on success or failure; both issues were exposed by actual command verification.

`src/experiments/recording.py` and `config.py` remain reusable maintained code, not separate inference drivers. Existing predictor, conversation, engine and recovery modules are internal building blocks. Run-specific hypothesis code/evidence stays outside `src/`; unrelated historical helper relocation is not part of this integration.

## Consequences

Normal execution and evaluation cannot choose different inference implementations through their command names. Fixed policy settings have one production execution site. Experiment identity is a recording concern (`--experiment`), not a model mode. Routine executions use retained maintenance records; hypotheses use registered experiment runs and follow-up relationships. Without `--output-dir`, results remain in the printed run directory.

The old command and old CLI tuning interface are intentionally retired. Existing Python helpers used by retained experiment tests are preserved where necessary; this is not a promise that historical GPU scripts execute unchanged. Evaluation and comparison now accept explicit input/label paths and the supplied item table. Evidence capture supports inputs outside the repository. GPU smoke verification does not establish full200 accuracy, throughput, or holdout performance.
