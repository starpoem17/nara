# Local inference engine

Implementation: `src/inference/engine.py`. Default caller: `src/inference/pipeline.py` via `src/cli.py`. Scheduling remains in `src/inference/prefix_pipeline.py`; conversation/retrieval/validation remain in `src/inference/predictor.py` and `src/inference/continuous.py`.

## Interface

- `TokenCounter(model_dir, thinking=False, max_model_len=32768)` loads only the local tokenizer. `render_messages`, `count_messages`, `count_text` use the same implementation as generation. Default preflight no longer constructs an uninitialized GPU model.
- `VLLMModel` retains existing constructor arguments and `generate(turns) -> {task_id: Reply}`. Optional `max_num_batched_tokens`, `enable_chunked_prefill`, `collect_scheduler_stats` configure default experiments explicitly. Unspecified options are omitted, preserving old scripts that inject these keywords themselves.
- `model.stream()` creates a new sequential stage with `submit`, `poll`, `abort`, `rows`, `lifecycle`. One stream is active on an engine at a time. `poll` can return several completions in completion order, joined by task ID. A retry may reuse a task ID; physical request IDs remain unique across stages.
- `thinking` changes future requests. Rendered prompt tokens and thinking budgets are fixed at submission; changing another request's mode does not change their decoding or reported budget.
- `close()` explicitly shuts down the engine worker; the sole pipeline uses it on both success and failure so the command can exit.
- `reset_prefix_cache()` returns engine reset success; the caller resets only between drained stages. `engine_info()` records effective scheduling, graph and cache settings.
- `with model.observe_scheduler() as rows` observes raw steps and restores the original engine callback even on exceptions. Construct with `collect_scheduler_stats=True` for scheduler/graph evidence. Snapshot rows before clearing for a new stage. Warmup remains outside the observation scope in the default runner.

## Compatibility and failure behavior

`from nara.inference.continuous import StreamingModel` remains a compatibility export. `StreamingModel(base)`, raw `.llm` access and `_tokens` remain available for historical scripts; default execution uses the engine interface. Old `VLLMModel.__new__` token counters still render without GPU initialization. Historical source-hash checks intentionally reject modified sources; use their archived versions for exact old experiments.

`stream.serial` overrides may advance the shared engine counter, as used by old recovery scripts; moving backward now fails rather than reusing a physical ID. New default stages use the automatic counter. Offline generation retains input-order routing and observes legacy sampling overrides (e.g. `TimedLLM` setting a thinking budget to zero).

Missing/nonmonotonic request metrics raise explicitly. Pending requests remain available for cancellation if conversion/metrics validation fails. Predictors already abort outstanding work on exceptions. Request/lifecycle field names and time definitions are unchanged.

Failed-notice recovery selection, replay and cross-attempt accounting are owned by the [recovery module](<recovery.md>).

## Validation

`tests/test_vllm_model.py` crosses the production engine module using a deterministic raw-engine adapter: rendering/sampling parity, mixed modes and reordered completions, repeated task IDs, legacy imports/options/observers, cancellation, metrics and observation lifecycle. `tests/test_experiment_engine.py` exercises the default runner's same-policy recovery success, isolated recovery success and explicit final failure, retaining all request/scheduler attempts. Existing scheduling tests remain in place.

Real graph execution, cache reuse and throughput require GPU evidence; see [engine refactor experiment](<../experiments/architecture-validation/engine-refactor.md>). No prompt, item grouping, output/search/retry budget, rule or notice admission policy changed in this refactor.
