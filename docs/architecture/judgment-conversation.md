# Judgment conversation

Implemented 2026-09-11 after the user agreed the responsibility split. Code: `nara/conversation.py`. Domain terms: [glossary](../../CONTEXT.md); execution/protocol context: [dynamic RAG](dynamic-rag.md).

## Ownership

- One `JudgmentConversation` manages one procurement notice and one item group: messages, context/output budgets, search history, retries, response/schema validation, evidence validation and final group judgments.
- Scheduling owns admission, ordering and model/search execution. Offline retrieval remains pooled; continuous/prefix execution searches on each completion. Conversation state is private; scheduling reads outcomes and combines groups into input-ordered notice results. Failures never become zero labels.
- Engine exceptions retain existing behavior: offline generation exceptions become error replies processed by retry rules; continuous/prefix execution aborts outstanding requests and propagates exceptions. Returned error replies follow the shared conversation retry rules.
- Retrieval execution errors become search-failure results in both paths. Preserve the older distinction for malformed retrieval material: offline packing errors propagate; streaming packing validation errors use conversation retry handling.
- [Recovery](recovery.md) retains selection, policy, timing and attempt accounting. Its saved successful responses use the same final judgment validation as inference.

## Interface

`Predictor.conversation(task_id, record, items)` constructs a conversation using the existing prompt, schema, limits and injected token-counting model.

- `next_turn()` returns the generation request or `None` when complete/failed. Messages in a returned request are detached from mutable conversation history.
- `accept_reply(turn, reply)` validates the response and returns an ID-keyed query map when search is needed, otherwise `None`. The conversation owns search-round advancement and query identity.
- Execute queries with the existing retrieval adapter, possibly pooling several conversations, then call `accept_search(hits, error=None)`. The conversation packs/deduplicates its own passages and updates budgets, control messages and trace. It rejects generating another turn while search results are pending.
- `done`, `error`, `judgments` and `snapshot()` expose outcomes. Judgment and trace snapshots are detached; callers do not edit retry counts, message history or retrieval budgets.
- `reject(error)` applies the existing invalid-result retry policy for streaming retrieval-material errors. `Predictor.replay_judgments` constructs a fresh conversation and delegates saved-response validation without token counting or generation.

The model is injected for token counting and current thinking mode; model execution and retrieval never run inside the conversation module. Existing production and test adapters supply these dependencies.

## Compatibility

`nara/inference.py` reexports `Limits`, `Turn`, `Reply`, `compact` and `_Task`. `Predictor._schema`, `_finish` and `ContinuousPredictor._turn` retain the live historical diagnostic call shapes. Only compatibility adapters access legacy task state; current offline, continuous, barrier and prefix scheduling use conversation objects.

Prompt construction, group validation, scheduling policies, task/query identities, trace fields and per-mode limits remain unchanged. Current manifests/source snapshots include `nara/conversation.py`. Frozen `analysis/**/source` trees are untouched; exact historical runs still require their archived sources.

## Validation

Evidence: [validation JSON](../../analysis/conversation_refactor/validation.json).

- 94 CPU tests passed in the full working tree; the isolated commit tree passed 83 tests (other uncommitted tests excluded). Coverage includes 11 new behavioral tests with cases across offline, continuous, barrier and prefix execution: required search under tight context, retrieval failures/empty results/wrong IDs, passage budgets/deduplication, malformed/truncated replies, returned errors, group isolation, engine exceptions, legacy calls and detached snapshots.
- Existing scheduler, engine, recovery and runner tests passed. The runner test verifies that the new module's saved bytes match its manifest hash.
- A separate before/after execution comparison matched predictions, full trace, generation requests, query maps and batch counts for 28 scripted scenarios. Comparison used the three pre-change modules from the recorded Git revision in a separate import tree.
- Saved run `output/experiments/engine-refactor-after-20260911`: 200 notices / 2400 groups replay to identical judgments and evidence; source traces remain unchanged. This comparison covers conversation-owned items, excluding the separate v2/v3 rule outputs.
- Current `--prepare-only` completed for 200 notices / 2400 groups; maximum input 29252 tokens. Input lengths, common-prefix counts and groups match the saved run; all snapshots match the manifest and current sources.

Re-run CPU checks: `uv run --locked python -m unittest discover -s tests`. Re-run current-input preparation: `uv run --locked python scripts/run_experiment.py --prepare-only --output-dir FRESH_DIRECTORY`.

No new GPU inference, throughput measurement or F1 evaluation was performed.
