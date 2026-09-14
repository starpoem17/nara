# Failed-notice recovery

Implementation: `src/inference/recovery.py`; default adapter: `src/experiments/pipeline.py`. Engine execution remains in [local engine](<local-engine.md>); judgment validation remains in [dynamic RAG](<dynamic-rag.md>).

## Interface and policy

`recover_notices(records, initial, rerun_notices=..., retry_group=..., replay_group=..., rule_judgments=...)` owns recovery selection, successful-group reuse, trace merging and accounting. Execution adapters return `Attempt(trace, seconds, requests, lifecycle, scheduler)` containing only that execution's results/evidence.

1. Keep initially successful notices unchanged. If none failed, invoke no recovery adapter.
2. Rerun failed notices once with the existing whole-notice policy. Default: twelve OFF groups, engine16, unchanged prompt/budget/search/internal-retry policy; reset cache before this stage.
3. For notices still failing, replay successful groups through `Predictor.replay_judgments(record, task_trace)`; retry each remaining group once with the original group prompt/budgets. Default adapter creates a fresh stream on the same resident engine without clearing its cache.
4. Apply rule judgments after successful isolated repair. Any exhausted group keeps the notice failed with `judgments=None`; no zero filling.

Initial and retry trace inputs remain unchanged. The result trace preserves initial record/group order and accumulates all attempt events/search rounds/retrieval tokens. Match retries by record ID and ordered item-group identity, not positional `zip`; tuple/list representations normalize to the same identity. Reject mismatched records/groups and incomplete isolated/replayed judgments explicitly.

## Validation ownership

`Predictor.replay_judgments` delegates to the shared [judgment conversation](<judgment-conversation.md>) to validate the saved successful final response against the group's schema, applies the same evidence/required-search checks as inference, and requires the resulting final-validation event to match the saved event. No inference is performed and the saved trace is not mutated.

The historical replay helper is retained under the corresponding run's code directory and exercised by regression tests. Historical direct commands are disabled; maintained callers use the recovery interface above.

## Cost and evidence

`RecoveryResult.prediction_seconds` includes initial execution, the whole-notice retry duration, and the full isolated-recovery interval per failed notice (replay, generation, merging and rule application). Isolated `Attempt.seconds` is a diagnostic subinterval and is not summed again. Model loading, warmup, smoke and artifact writing remain outside prediction time as before.

`requests`, `lifecycle`, `scheduler` aggregate every attempt exactly once; recovery scheduler rows retain the existing `stage='recovery'` annotation. The default runner also saves `recovery_attempts.jsonl` with each retry attempt's original trace, timing and evidence, linking isolated request IDs to their notice/groups even after final trace replacement. Main/recovery stage files, main admission records and CSV failure rules remain unchanged. The new module is included in source manifests/snapshots.

## Verification (2026-09-11)

80 automated tests passed, including success/no-op, same-policy recovery, successful-group reuse, isolated success/failure, input immutability, record/group identity, search/token/event totals, timing without double counting, invalid replay rejection and the default runner's complete output/evidence flow.

Saved GPU run `experiments/legacy_engine_refactor/after`: all200 notices/2400 groups replay to identical judgments and evidence through the new validation interface. A simulation removes final events from the first group of two real notices; reversed retry ordering still repairs exactly those two groups and restores the saved judgments while preserving successful notices/attempts. No new GPU inference or time/F1 measurement was performed for this logic-only refactor.

Evidence: [retained recovery audit](../maintenance/evidence/recovery_refactor/validation.json). Historical audit code is retained alongside that evidence. Current CPU checks use `uv run --locked python -m unittest discover -s tests`; new preparation uses `uv run --locked nara-experiment --prepare-only`. [Operations](../operations.md) owns the current saved-output replay command.
