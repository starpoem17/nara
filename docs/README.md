# Agent documentation

Project objective: achieve a strong result in DACON competition 236754.
Read this index, then only the documents relevant to the current task.

Default experiment: `uv run --locked nara-experiment` — current sources, twelve OFF groups, cross-notice lookahead, engine16. Submission/RAG CLI: `uv run --locked nara`. See [Prefix pipeline](experiments/prefix-pipeline.md).

The physical `src/` directory is installed directly as the `nara` package; there is no `src/nara/` layer.

| Source location | Responsibility / command namespace |
|---|---|
| `src/cli.py`, `__main__.py` | Submission/RAG command: `nara` |
| `src/records.py`, `runtime.py`, `paths.py` | Shared records, runtime helpers, and paths used by commands and role modules |
| `src/inference/` | Prediction conversations, engines, schedulers, prompts, criteria, and recovery |
| `src/retrieval/` | Legal index construction and search |
| `src/rules/` | Deterministic qualification and briefing judgments |
| `src/experiments/` | Experiment entry points: `nara.experiments.NAME`; default command `nara-experiment` |
| `src/evaluation/` | Scoring, comparison, summaries, and report writing: `nara.evaluation.NAME` |
| `src/tools/` | Checks, diagnostics, rendering, and data utilities: `nara.tools.NAME` |

## Project navigation

| Need | Read |
|---|---|
| Find folders, active code or a script; distinguish snapshots | [Project map](project-structure.md) |
| Resolve domain terminology | [Domain glossary](architecture/domain.md) |
| Set up Python/models or check local GPU | [Environment](environment.md) |
| Find complete run/evaluation commands and prompt edit locations | [Operations](operations.md) |
| Locate detailed reports and machine evidence by experiment | [Report index](reports/README.md) |
| Understand document placement, moved files and preserved exceptions | [Structure audit](maintenance/structure-audit.md) |

Read summaries first. Open detailed reports or frozen sources only when the task needs their evidence.

## Routing

| Work | Read |
|---|---|
| Understand the prediction task | [task](competition/task.md) |
| Design data, labeling, retrieval, or inference | [constraints](competition/constraints.md), then [task](competition/task.md) |
| Optimize scores or extract evidence | [evaluation](competition/evaluation.md) |
| Implement, package, or debug submission | [submission](competition/submission.md), then [constraints](competition/constraints.md) |
| Verify freshness, deadlines, or missing details | [sources](competition/sources.md) |

## Implementation and experiments

| Work | Read |
|---|---|
| Build/query legal index; inspect artifact contract | [Legal retrieval](architecture/legal-retrieval.md) |
| Change inference, prompts, grouping, budgets or execution | [Dynamic RAG](architecture/dynamic-rag.md) |
| Understand shared domain records and ownership | [Domain glossary](architecture/domain.md), then [Judgment conversation](architecture/judgment-conversation.md) |
| Change shared conversation state, budgets, validation or replay | [Judgment conversation](architecture/judgment-conversation.md) |
| Change local engine execution, token rendering, cache or telemetry; preserve historical calls | [Local engine](architecture/local-engine.md) |
| Change failed-notice recovery, successful replay or retry cost/evidence aggregation | [Recovery](architecture/recovery.md) |
| Inspect per-feature legal criteria, source provenance and prompt budget | [Legal criteria](architecture/legal-criteria.md) |
| Run checks; inspect measured results and validation gaps | [Local validation](experiments/local-validation.md) |
| Compare ungrouped and 7/9/12-group inference latency | [Grouping time](experiments/grouping-time.md) |
| Full200 compressed-criteria OFF groups and v2/v3 rule experiments | [Compact dev200](experiments/compact200.md) |
| LJM v2–v8 candidates with direct per-feature law and Gemma | [LJM static-law experiment](experiments/ljm-static-law.md) |
| Source-first KV prefix reuse: grouped OFF speed and accuracy | [Prefix cache](experiments/prefix-cache.md) |
| Common prompt v2 vs original, output512, matched dev200 | [Common prompt comparison](experiments/common-prompt-512.md) |
| Default experiments: twelve-group cross-notice engine16; early prefill and FULL graphs | [Prefix pipeline](experiments/prefix-pipeline.md) |
| Engine module refactor: compatibility tests and matched dev200 before/after | [Engine refactor](experiments/engine-refactor.md) |
| Five-group mixed thinking/instant: per-feature effects, prefill/decode, cache and batching controls | [Hybrid five](experiments/hybrid-five.md) |
| Actual instant OFF vs ON0 dev200, output differences and cross-mode cache probes | [Instant ON0](experiments/instant-on0.md) |
| Historical mixed-five comparison: batch8 barrier fallback; prefill/decode cause probes | [Prefill/decode and fallback](experiments/prefill-decode-fallback.md) |
| Completion-driven refill and per-step prefill token budgets | [Continuous prefill](experiments/continuous-prefill.md) |
| Why scheduling changed accuracy; raw-token adapter/repeat controls | [Continuous diagnosis](experiments/continuous-diagnosis.md) |
| Reproduce colleague ZIP and calibrate local time against reported75min server run | [Colleague submission](experiments/colleague-submission.md) |

## Maintenance contract

- `competition/` contains official requirements only. Its source register is `competition/sources.md`.
- Generated Markdown reports belong in `reports/`; experiment artifacts remain in `analysis/` or `output/`. Use `nara.evaluation.reporting`; see [maintenance rules](maintenance/structure-audit.md#maintenance-rules).
- Colleague hypothesis experiments in `analysis/` must use uppercase colleague initials first: `<INITIALS>_<experiment_name>[_<date>]`, e.g. `LJM_static_law_v2_v8_20260912`. Apply this to new runs; preserve historical snapshots. See [maintenance rules](maintenance/structure-audit.md#maintenance-rules).
- Root `README.md` contains only the user’s objective. Agent notes belong here or in the owning document.
- Keep each fact in one owning document; link to it elsewhere. Use stable, descriptive filenames and headings.
- Write concise English; preserve Korean item names, legal titles, filenames, and exact API identifiers.
- Each official-requirements document records its source and verification date. When updating a fact, recheck its source and update that date; unresolved conflicts belong in `sources.md`.
- Distinguish mandatory rules, organizer recommendations, and baseline examples. Never silently promote an example into a requirement.
- Add implementation decisions under `architecture/` and experiment conclusions under `experiments/` only when content exists; register new documents here. Keep proposals and project observations out of official requirements.
- Keep raw datasets, logs, source-page dumps, and repeated background out of this index and requirement summaries.
- `user/` is user-owned; agents may read it but must not edit it.
- These summaries are navigation aids for engineering work. Recheck official pages before submissions and material rule-dependent changes.

Search: `rg -n 'PPS_|evidence|label|independent|deadline' docs/competition`.
