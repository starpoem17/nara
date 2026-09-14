# Operations

Run commands from the project root using the existing locked environment. No historical GPU execution is promised to run unchanged.

## Submission and retrieval

`uv run --locked nara --help` documents the maintained submission/retrieval interface. Submission outputs are user deliverables: choose an explicit fresh location under `outputs/`. The structure migration did not change inference semantics or competition configuration.

## One planned experimental sweep

```bash
uv run --locked nara-experiment --summary grouping-comparison --question "How do12 and21 groups compare?" --grouping groups12 groups21
```

This creates one timestamped run, two declared conditions, separate attempt directories, and one report under the inference-scheduling area/month. Source contents, uncommitted patch, input hashes, locally retained model/index references, environment, command, settings, status, and results are recorded. Label capture happens in evaluation after predictions. Existing defaults remain output512/OFF/current rules/engine16. A single condition uses `--grouping groups12`.

A result-triggered extra execution always gets a new ID. Supply `--predecessor PRIOR_RUN_ID --reason "Observed issue and purpose of this follow-up"`, even for unchanged settings. The recorder links both reports and compares declared settings and retained source/input/asset evidence. Missing historical provenance stays explicitly unverified. Predeclared internal prediction retries and recovery remain within the condition and retain attempt events; arbitrary extra runs do not.

`--prepare-only` performs tokenizer/context preparation without GPU model loading. `--smoke-only` includes GPU smoke inference. Standalone preparation/smoke is recorded under `docs/maintenance/checks/`; use `--experiment` only when it investigates a stated experimental question. Full200 execution includes preparation, smoke, timed inference, planned recovery, evaluation, and paired comparison when two groupings are declared. Execution completion does not mark an approach adopted: assess and update the owning report with reasons, scope and history.

## Saved-result verification

```bash
uv run --locked python -m nara.tools.replay_evaluation --artifacts experiments/legacy_prefix_pipeline200
```

The command validates recorded input hashes, copies the saved predictions/trace/settings into a fresh retained maintenance record, re-evaluates on CPU, and compares all non-path evaluation fields. It preserves original evidence. It requires the original input/label bytes locally. It does not reproduce GPU generation, timing, or missing historical environments.

`nara.evaluation.evaluate_dev` and `compare_dev_runs` operate on registered current artifacts. Comparisons verify label/input and prediction hashes. Archived hypothesis modules under each run's `code/` expose tested helpers but disable their old direct entrypoints. To extend a hypothesis, create a new `Run`, capture the chosen source/input/assets before execution, and write into a declared active attempt; review the previous run's judgment first.

## Verification and retained work

```bash
uv run --locked python -m unittest discover -s tests
```

Current standalone diagnostic tools accept explicit output paths; use a fresh `tmp/<task-id>/` scope and promote essential check evidence into `docs/maintenance/evidence/` before relying on it. Temporary work and final outputs are retained until the user explicitly requests deletion. See [migration verification](maintenance/structure-migration-verification.md) for passed and unperformed checks.
