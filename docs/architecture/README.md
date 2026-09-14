# Architecture

Status: maintained interfaces and source locations updated2026-09-14 against the migrated working tree based on revision `a74048d42d2d8e24a16473eeb056ea3a15264a3b`. That revision alone does not contain the uncommitted migration; [verification and retained change evidence](../maintenance/structure-migration-verification.md) identify checked contents.

| Responsibility | Source | Interface, dependencies and checks |
|---|---|---|
| Sweep execution and evidence | `src/experiments/recording.py`, `run_experiment.py`, `pipeline.py`, `config.py` | [Execution records](execution-records.md); calls maintained inference/retrieval/evaluation, tests in `test_run_recording`, `test_experiment_engine`, `test_reporting`. |
| Submission and RAG | `src/cli.py`, `src/records.py`, `src/runtime.py`, `src/inference/predictor.py` | [Dynamic RAG](dynamic-rag.md); input/output contract and retrieval limits. |
| Conversation state | `src/inference/conversation.py` | [Judgment conversation](judgment-conversation.md); schemas, budgets, validation and replay. |
| Local engine | `src/inference/engine.py` | [Local engine](local-engine.md); token rendering, scheduler observations, caching and GPU adapter. |
| Failed-notice recovery | `src/inference/recovery.py` | [Recovery](recovery.md); successful replay and explicit attempt accounting. |
| Legal retrieval | `src/retrieval/` | [Legal retrieval](legal-retrieval.md); corpus/index/search contracts. |
| Criteria and deterministic rules | `src/inference/*criteria.json`, `src/rules/` | [Legal criteria](legal-criteria.md); source scope and rule tests; [briefing-rule adoption](../experiments/rule-evaluation/briefing-rule.md). |

- [Glossary](../CONTEXT.md): shared domain language.
- [Migration decision](../adr/0001-retained-experiment-runs.md): source/evidence separation and no historical command compatibility.
- [Legal-criteria evidence](evidence/README.md): retained original criteria diagnostics and renderer source.
