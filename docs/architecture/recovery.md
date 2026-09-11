# Failed-notice recovery

Implementation: `nara/recovery.py`; default adapter: `scripts/benchmark_prefix_pipeline.py`. Engine execution remains in [local engine](local-engine.md); judgment validation remains in [dynamic RAG](dynamic-rag.md).

## Interface and policy

`recover_notices(records, initial, rerun_notices=..., retry_group=..., replay_group=..., rule_judgments=...)` owns recovery selection, successful-group reuse, trace merging and accounting. Execution adapters return `Attempt(trace, seconds, requests, lifecycle, scheduler)` containing only that execution's results/evidence.

1. Keep initially successful notices unchanged. If none failed, invoke no recovery adapter.
2. Rerun failed notices once with the existing whole-notice policy. Default: twelve OFF groups, engine16, unchanged prompt/budget/search/internal-retry policy; reset cache before this stage.
3. For notices still failing, replay successful groups through `Predictor.replay_judgments(record, task_trace)`; retry each remaining group once with the original group prompt/budgets. Default adapter creates a fresh stream on the same resident engine without clearing its cache.
4. Apply rule judgments after successful isolated repair. Any exhausted group keeps the notice failed with `judgments=None`; no zero filling.

Initial and retry trace inputs remain unchanged. The result trace preserves initial record/group order and accumulates all attempt events/search rounds/retrieval tokens. Match retries by record ID and ordered item-group identity, not positional `zip`; tuple/list representations normalize to the same identity. Reject mismatched records/groups and incomplete isolated/replayed judgments explicitly.

## Validation ownership

`Predictor.replay_judgments` delegates to the shared [judgment conversation](judgment-conversation.md) to validate the saved successful final response against the group's schema, applies the same evidence/required-search checks as inference, and requires the resulting final-validation event to match the saved event. No inference is performed and the saved trace is not mutated.

Historical `scripts.recover_hybrid200.replay(record, task, predictor)` remains a compatibility adapter; its callers no longer construct private task state or call `_finish` themselves. Historical standalone execution/recovery policies and archived source files are otherwise retained.

## Cost and evidence

`RecoveryResult.prediction_seconds` includes initial execution, the whole-notice retry duration, and the full isolated-recovery interval per failed notice (replay, generation, merging and rule application). Isolated `Attempt.seconds` is a diagnostic subinterval and is not summed again. Model loading, warmup, smoke and artifact writing remain outside prediction time as before.

`requests`, `lifecycle`, `scheduler` aggregate every attempt exactly once; recovery scheduler rows retain the existing `stage='recovery'` annotation. The default runner also saves `recovery_attempts.jsonl` with each retry attempt's original trace, timing and evidence, linking isolated request IDs to their notice/groups even after final trace replacement. Main/recovery stage files, main admission records and CSV failure rules remain unchanged. The new module is included in source manifests/snapshots.

## Verification (2026-09-11)

80 automated tests passed, including success/no-op, same-policy recovery, successful-group reuse, isolated success/failure, input immutability, record/group identity, search/token/event totals, timing without double counting, invalid replay rejection and the default runner's complete output/evidence flow.

Saved GPU run `output/experiments/engine-refactor-after-20260911`: all200 notices/2400 groups replay to identical judgments and evidence through the new validation interface. A simulation removes final events from the first group of two real notices; reversed retry ordering still repairs exactly those two groups and restores the saved judgments while preserving successful notices/attempts. No new GPU inference or time/F1 measurement was performed for this logic-only refactor.

Evidence: `analysis/recovery_refactor/validation.json`. Reproduce with:

```bash
uv run --locked python -m unittest discover -s tests
uv run --locked python analysis/recovery_refactor/verify_saved.py output/experiments/engine-refactor-after-20260911
uv run --locked python scripts/run_experiment.py --prepare-only --output-dir FRESH_DIRECTORY
```
