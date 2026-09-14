# Verify successful installed-command exit after single-pipeline integration and full-source context preparation.

Current judgment: **Preparation and installed-command exit passed.**

Run ID: `20260914_160432_pipeline-unification-preparation`. Planned comparison: groups12.

## Question and conditions

Verify successful installed-command exit after single-pipeline integration and full-source context preparation.

## Judgment history

The run was created with the conditions below; no results have been assessed.

## Limits

Do not infer unseen-data performance or repeatability from one execution.

<!-- execution:start -->
## Execution evidence

Execution status: **complete**. Judgment: **Preparation and installed-command exit passed.**.

[Run directory](<../evidence/20260914_160432_pipeline-unification-preparation>) · [Metadata](<../evidence/20260914_160432_pipeline-unification-preparation/run.json>)

| Condition | Status | Attempts | Settings |
|---|---|---:|---|
| [groups12](<../evidence/20260914_160432_pipeline-unification-preparation/conditions/groups12>) | complete | 1 | `{"grouping": "groups12", "phase": "preparation", "output_tokens": 512, "thinking": false, "seed": 0, "input_path": "/home/hwajoong/projects/nara/data/dev.jsonl", "data_dir": "/home/hwajoong/projects/nara/data", "model_dir": "/home/hwajoong/projects/nara/models/gemma-4-26B-A4B-it-NVFP4", "embed_model": "/home/hwajoong/projects/nara/models/bge-m3", "index": "/home/hwajoong/projects/nara/model/legal_index", "labels": null}` |

Retained task temporary path: `/home/hwajoong/projects/nara/tmp/pipeline-unification`.

Sources recorded; fresh inference reproducibility not verified.
<!-- execution:end -->

<!-- integration-verification:start -->
200 notices / 2400 group inputs fit context; maximum input29310 tokens. The installed command exited0 after the return-value fix. This CPU-only check predates explicit GPU shutdown and does not verify it.

[Integration report](../pipeline-unification.md) owns the full change and check history. [Final smoke](./20260914_160718_pipeline-unification-final-smoke.md) verifies the completed code. Original traces and source snapshots remain retained.
<!-- integration-verification:end -->
