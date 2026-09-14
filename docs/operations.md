# Operations

Run commands from the project root using the locked environment. `nara` is the only maintained prediction command; `python -m nara` uses the same CLI. [ADR0002](adr/0002-single-inference-command.md) records retirement of `nara-experiment` and the old baseline driver.

## Prediction and optional evaluation

```bash
uv run --locked nara --input data/test.jsonl --output-dir outputs/submission
uv run --locked nara --input data/dev.jsonl --labels data/dev_labels.csv --output-dir outputs/dev-evaluation
```

Use a fresh output directory. Without `--input`, the command reads `test.jsonl.gz`, then `test.jsonl`, under `--data-dir` (default `data`). Any nonempty number of notices is accepted; evaluation requires identical input/label/prediction IDs. `--labels` only evaluates after prediction completes; no labels enter the model. The model, embedding, index and data paths remain configurable. `PPS_DATA_DIR`, `PPS_MODEL_DIR`, `PPS_EMBED_DIR` and `PPS_OUTPUT_DIR` are honored.

Every invocation uses the same maintained pipeline: Gemma4 NVFP4, output512 per call, thinking OFF, context32768, twelve groups, v2/v3/v22 rules, sixteen engine slots, common-prefix caching and bounded cross-notice scheduling. The legacy baseline tuning flags are removed; see `uv run --locked nara --help` for the supported interface.

Provenance, input snapshots, model/index references, traces and results are retained under a timestamped routine maintenance record by default. `--output-dir` copies final files and writes `provenance.json` pointing to the retained run/report. Without it, use the artifact directory printed in the report. A failed judgment never becomes a zero prediction or a partial submission.

## Preparation and smoke checks

```bash
uv run --locked nara --input data/dev.jsonl --prepare-only --summary input-preparation
uv run --locked nara --input data/dev.jsonl --smoke-only --summary engine-smoke
```

Preparation checks every full input and group against the 32K context using the local tokenizer. Smoke adds GPU inference on the first eight notices (or all notices if fewer). Full execution includes preparation, smoke excluded from main timing, prediction and planned recovery. `--prepare-only` and `--smoke-only` are mutually exclusive and cannot be combined with `--labels`.

## Planned hypothesis experiments

```bash
uv run --locked nara --input data/dev.jsonl --labels data/dev_labels.csv --experiment --summary grouping-comparison --question "How do twelve and twenty-one groups compare?" --grouping groups12 groups21
```

`--experiment` changes recording ownership, not inference. One sweep gets one timestamped experiment run/report, declared conditions and separate attempts. Two evaluated groupings also receive a paired comparison. Execution success does not establish adoption. Review the owning report's judgment before reusing an approach.

A result-triggered extra execution always gets a new ID: supply `--experiment --predecessor PRIOR_RUN_ID --reason "Observed issue and follow-up purpose"`. Planned internal retries/recovery remain within a condition. Run-specific experimental code belongs in `experiments/<run-id>/`; reusable execution/recording code remains in `src/`.

## Saved-result verification

```bash
uv run --locked python -m nara.tools.replay_evaluation --artifacts experiments/legacy_prefix_pipeline200
uv run --locked python -m unittest discover -s tests
```

Saved-result replay checks recorded hashes, copies evidence into a fresh maintenance record and re-evaluates on CPU without changing original artifacts. It does not reproduce GPU generation/timing or missing historical environments. Evaluation/comparison modules remain reusable utilities, not separate inference pipelines. Historical direct GPU commands are not supported unchanged.

Temporary work under `tmp/<task-id>/` and final outputs are retained until explicit deletion instructions. [Integration verification](maintenance/pipeline-unification.md) records current checks and limitations.
