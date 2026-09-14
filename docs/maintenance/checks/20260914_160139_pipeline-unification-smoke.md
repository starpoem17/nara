# Verify the promoted single inference command on current inputs without scoring or changing the adopted policy.

Current judgment: **Inference passed; command shutdown failed and was subsequently repaired.**

Run ID: `20260914_160139_pipeline-unification-smoke`. Planned comparison: groups12.

## Question and conditions

Verify the promoted single inference command on current inputs without scoring or changing the adopted policy.

## Judgment history

The run was created with the conditions below; no results have been assessed.

## Limits

Do not infer unseen-data performance or repeatability from one execution.

<!-- execution:start -->
## Execution evidence

Execution status: **failed**. Judgment: **Inference passed; command shutdown failed and was subsequently repaired.**.

[Run directory](<../evidence/20260914_160139_pipeline-unification-smoke>) · [Metadata](<../evidence/20260914_160139_pipeline-unification-smoke/run.json>)

| Condition | Status | Attempts | Settings |
|---|---|---:|---|
| [groups12](<../evidence/20260914_160139_pipeline-unification-smoke/conditions/groups12>) | complete | 1 | `{"grouping": "groups12", "phase": "smoke", "output_tokens": 512, "thinking": false, "seed": 0, "input_path": "/home/hwajoong/projects/nara/data/dev.jsonl", "data_dir": "/home/hwajoong/projects/nara/data", "model_dir": "/home/hwajoong/projects/nara/models/gemma-4-26B-A4B-it-NVFP4", "embed_model": "/home/hwajoong/projects/nara/models/bge-m3", "index": "/home/hwajoong/projects/nara/model/legal_index", "labels": null}` |

Retained task temporary path: `/home/hwajoong/projects/nara/tmp/pipeline-unification`.

Sources recorded; fresh inference reproducibility not verified.
<!-- execution:end -->

<!-- integration-verification:start -->
Eight notices / 96 requests completed without prediction failures. The console entrypoint returned a Run object and the GPU worker remained after inference. The task terminated its own remaining processes after retaining results. Later source changes return0 and explicitly close the worker; final verification is linked below.

[Integration report](../pipeline-unification.md) owns the full change and check history. [Final smoke](./20260914_160718_pipeline-unification-final-smoke.md) verifies the completed code. Original traces and source snapshots remain retained.
<!-- integration-verification:end -->
