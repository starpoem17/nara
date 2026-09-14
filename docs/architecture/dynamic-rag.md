# Maintained inference and dynamic RAG

The sole maintained entrypoint is `nara` / `python -m nara`. [ADR0002](../adr/0002-single-inference-command.md) records promotion of the adopted prefix pipeline and removal of the baseline CLI. [Operations](../operations.md) owns commands; [integration verification](../maintenance/pipeline-unification.md) owns current evidence.

Code: [CLI](../../src/cli.py), [pipeline](../../src/inference/pipeline.py), [source-first prompt](../../src/inference/prefix_predictor.py), [criteria](../../src/inference/compact_criteria.json), [scheduler](../../src/inference/prefix_pipeline.py). Engine execution: [local engine](local-engine.md). Conversation state: [judgment conversation](judgment-conversation.md). Dependencies: [legal retrieval](legal-retrieval.md), [competition constraints](../competition/constraints.md), [submission contract](../competition/submission.md).

## Interface and ownership

`pipeline.execute(out, grouping="groups12", *, input_path, data_dir, model_dir, embed_model, index, prepare_only=False, smoke_only=False)` executes a declared active `Run` attempt into a fresh directory. The CLI owns input selection, source/input/asset capture, optional evaluation and final export. Settings must match the declared condition. The pipeline owns preparation, loading, warmup, smoke, prediction, rule merge, recovery and complete artifact writing. Input size is any positive number of notices, not dev200 specifically.

Default policy: 512 output tokens per call, thinking OFF, context32768, sixteen active requests, 8192 batched engine tokens, chunked prefill and prefix caching enabled. Twelve model groups cover 21 items; deterministic rules own v2/v3/v22. An explicit groups21 condition uses the same execution path. Model/retrieval stay resident. Admission begins with two notices, allows at most three live notices and 48000 common-prefix tokens, and looks ahead when sixteen follower groups remain.

`PrefixPipelinePredictor` uses shared conversation and retrieval machinery. First complete the seed group for a notice, then release that notice's followers. Prompts are independent: a group's answers are never injected into another group. Original input order is restored in returned predictions. `Predictor`, `ContinuousPredictor` and related helpers remain internal reusable scheduling/conversation building blocks; the retired CLI no longer selects the old baseline predictor.

## Prompt and protocol

System: shared `compact_criteria.json` common instructions. User: notice ID, metadata, all original documents, then selected item criteria and absence-item IDs. Thus the common instructions and complete notice form the identical prefix across the notice's groups. Input allowlist is `id/meta/docs`; labels never enter inference. The original baseline `prompt.txt` is not the maintained command's prompt.

The model returns XGrammar-constrained JSON: either `{"action":"search","queries":[...]}` or `{"action":"final","judgments":{...}}`, containing only assigned items. Each conversation owns its messages, retries, search rounds, seen passages, budgets and validation. Retrieval results are appended to that conversation only. Optional search is capped at two rounds and four queries per round; each query is at most256 characters, top_k=5. Retrieval errors consume an attempt and enter the conversation as an error.

Invalid/truncated output permits one internal final-only retry before failure. Source documents are never truncated. Reserve output512 plus128 tokens; optional search reserves space for both the search action and final answer. Retrieved text is capped at4096 tokens/round and8192/conversation, with whole-passage packing and per-conversation deduplication. Context overflow is explicit failure.

Evidence must match a contiguous span in one original document, at most500 characters. Nonviolations and absence judgments have null evidence; unsafe/unmatched evidence is nulled and recorded. These validation rules are unchanged by pipeline promotion.

## Recovery, artifacts and limits

Reset prefix cache between drained smoke/main/notice-rerun stages, not between item groups. Recovery repeats failed notices once under the same policy, then runs remaining failed groups in isolation; all attempt cost and evidence are retained. See [recovery](recovery.md).

The pipeline records manifests, traces, request timings, lifecycle, scheduler/admission events, deterministic rule results and recovery attempts. Write `submission.csv` only when every notice succeeds. Optional evaluation occurs afterward and requires complete identical IDs; it cannot change the prediction strategy. Output export links back to retained execution provenance.

Routine CPU regression tests cover inference, prefix scheduling, recovery and CLI routing. GPU smoke and remaining verification scope are documented in the integration check. Historical scores do not validate the current512-token/rule policy on unseen data.
