# Verify the integrated command, unchanged inference policy and explicit engine cleanup after the first smoke exposed shutdown issues.

Current judgment: **Final integration smoke passed; no accuracy adoption claim.**

Run ID: `20260914_160718_pipeline-unification-final-smoke`. Planned comparison: groups12.

## Question and conditions

Verify the integrated command, unchanged inference policy and explicit engine cleanup after the first smoke exposed shutdown issues.

## Judgment history

The run was created with the conditions below; no results have been assessed.

## Limits

Do not infer unseen-data performance or repeatability from one execution.

<!-- execution:start -->
## Execution evidence

Execution status: **complete**. Judgment: **Final integration smoke passed; no accuracy adoption claim.**.

[Run directory](<../evidence/20260914_160718_pipeline-unification-final-smoke>) · [Metadata](<../evidence/20260914_160718_pipeline-unification-final-smoke/run.json>)

| Condition | Status | Attempts | Settings |
|---|---|---:|---|
| [groups12](<../evidence/20260914_160718_pipeline-unification-final-smoke/conditions/groups12>) | complete | 1 | `{"grouping": "groups12", "phase": "smoke", "output_tokens": 512, "thinking": false, "seed": 0, "input_path": "/home/hwajoong/projects/nara/data/dev.jsonl", "data_dir": "/home/hwajoong/projects/nara/data", "model_dir": "/home/hwajoong/projects/nara/models/gemma-4-26B-A4B-it-NVFP4", "embed_model": "/home/hwajoong/projects/nara/models/bge-m3", "index": "/home/hwajoong/projects/nara/model/legal_index", "labels": null}` |

Retained task temporary path: `/home/hwajoong/projects/nara/tmp/pipeline-unification`.

Sources recorded; fresh inference reproducibility not verified.
<!-- execution:end -->

<!-- integration-verification:start -->
Final source hashes match maintained code. Installed command exited0; worker cleanup completed and no engine process remained. Full input preparation:200 notices,12 groups, maximum29310 tokens. Smoke:8 notices,96 requests,zero failures,all request limits512,FULL graph observed,cached fraction0.909867. No full200 generation, scoring or holdout validation.

[Integration report](../pipeline-unification.md) owns the full change and check history. [Final smoke](./20260914_160718_pipeline-unification-final-smoke.md) verifies the completed code. Original traces and source snapshots remain retained.
<!-- integration-verification:end -->
