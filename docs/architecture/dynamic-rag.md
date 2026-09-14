# Dynamic RAG inference

Default experimental workflow: [Prefix pipeline](<../experiments/inference-scheduling/prefix-pipeline.md>), `uv run --locked nara-experiment`. This document describes the shared inference machinery and ungrouped baseline CLI below.

Code: [baseline entry point](<../../src/cli.py>), [predictor](<../../src/inference/predictor.py>), [vLLM adapter](<../../src/inference/engine.py>), [prompt](<../../src/inference/prompt.txt>).
Engine execution/compatibility: [local engine](<local-engine.md>). Shared conversation state, budgets and validation: [judgment conversation](<judgment-conversation.md>).

Dependencies: [retrieval](<legal-retrieval.md>); official [constraints](<../competition/constraints.md>), [submission contract](<../competition/submission.md>).

## Interface and ownership

- `Predictor(model, retriever, item_table, judgment_schema, limits=Limits()).predict(records, item_groups=None)` → input-ordered `Prediction(record_id, judgments | None, error | None, trace)`.
- Groups partition all items exactly once; default one conversation for all 24. `--item-group-size 6` creates four conversations/record.
- Each task owns record, items, messages, retries, seen passages and budgets. Application query IDs: `record-position:group-position:round:query-position`; responses join by ID, independent of batching/order.
- Prompt input allowlist: `id/meta/docs`; excludes dev labels. All groups must succeed; failures never become zero labels.
- Model interface: `max_model_len`, `count_text`, `count_messages`, `generate(list[Turn]) -> {task_id: Reply}`. vLLM uses rendered chat-template token IDs; tests inject a scripted model.

## Protocol and failure handling

Application JSON via XGrammar `anyOf`; schema contains only assigned items:

```json
{"action":"search","queries":["..."]}
{"action":"final","judgments":{"v1":{"위반여부":0,"근거문구":null}}}
```

- Execute queries after generation; append labeled passages as a user message in the same conversation. Final-only turns remove the search schema.
- Defaults/task: 2 search attempts, 4 queries/attempt, 256 chars/query, `top_k=5`. Search is optional; retrieval errors consume an attempt and return an error message to the model.
- Invalid/truncated output: discard invalid text, allow one final-only retry, then fail. `--require-search` instead retries search until the first attempt; final judgment fails if no retrieved passages entered context. Combine with `--search-rounds 1` for exactly one attempt.
- Evidence: schema capped at 500 chars; nonviolations/absence items → null. Unmatched or `=`, `+`, `@`-prefixed evidence → null + trace. Match within one original document only; no metadata, retrieved law or cross-document matches.

## Context budgets

- Retrieved text: 4096 Gemma tokens/round, 8192/task, including JSON labels. Pack whole passages round-robin by query/rank; deduplicate whitespace-normalized text per conversation. Control text counts only toward context.
- Original documents remain intact as plain text blocks. Reserve output budget +128 tokens; optional search also reserves another output budget +128 for its action/control. If search cannot fit, use final-only; if final cannot fit, fail. Source chunking/merging is unimplemented.
- Required search may shrink its action budget to remaining context (minimum 32 tokens), preserving source and final-output budget; fail if it cannot fit.

## Execution

- Load local Sentence Transformers BGE first, then Gemma; keep both resident. BGE: CUDA FP16 by default, `--embed-device cpu` for FP32. Index/search stay in CPU RAM.
- Default 8 active tasks; pooled queries use BGE microbatches of 32. Refill between phases; offline generation and retrieval do not overlap.
- Gemma defaults: context 32768, GPU memory utilization 0.86, prefix caching/CUDA graphs enabled; `--enforce-eager` for diagnostics. Auto quantization preserves checkpoint settings, otherwise selects `int8_per_channel_weight_only`; NVFP4 uses Cutlass MoE.
- Thinking off by default; output budget 2048, or 4096 with `--thinking`; override via `--output-tokens`. Thinking budget: `min(1024, output/2)`, search-only `min(256, output/4)`. Adapter separates answer; traces store thinking counts/budgets, not successfully parsed thinking text.
- Entry point honors `PPS_*` paths; input `.jsonl`/`.jsonl.gz`, default `test.jsonl.gz` then `test.jsonl`. Use a fresh output directory; existing `submission.csv` is refused.
- Writes `trace.jsonl` and `report.json` for prediction failures; atomically writes `submission.csv` only if all records succeed. Package the installed `nara` package including `inference/prompt.txt`, plus `model/legal_index/` assets.

Checks, measurements and remaining validation: [experiments](<../maintenance/local-validation.md>).
