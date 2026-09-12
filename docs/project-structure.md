# Project map

Start at [docs/README](README.md). Read one relevant summary, then its named code or report. Commands below run from the repository root. Detailed commands: [operations](operations.md); setup: [environment](environment.md).

## Folder roles

| Location | Ownership / contents | Navigation rule |
|---|---|---|
| `AGENT.md`, `README.md` | Project instructions; user's three-line objective | Do not append agent notes. User explicitly authorized the README restoration. |
| `docs/` | Agent navigation, implementation decisions, conclusions and generated reports | `competition/` = requirements; `architecture/` = implementation; `experiments/` = concise conclusions; `reports/` = detailed evidence. |
| `src/` | Complete installed `nara` package: shared records plus `inference/`, `retrieval/`, `rules/`, `experiments/`, `evaluation/`, and `tools/` | [Code routing below](#code-routing). There is no nested `src/nara/` or live `scripts/` tree. |
| `tests/` | CPU tests with small fixtures/injected models | `uv run --locked python -m unittest discover -s tests -v`. |
| `analysis/` | Experiment JSON/CSV, prompts, manifests, raw model responses, execution records and frozen sources; repeated input snapshots remain local | [Report and artifact index](reports/README.md). Five frozen document copies remain by user agreement. |
| `output/` | Local run artifacts; default `output/experiments/<timestamp>/` | Ignored by Git. Markdown evaluations now mirror the run path under `docs/reports/output/`. |
| `data/` | Local JSONL/labels, rendered notice data, original distribution README, schema and legal references | Search exact IDs/files. Rendered notice Markdown is data, not agent notes. Only the two schema JSON files and legal package are tracked. |
| `models/` | Local model checkpoints | Ignored; distinct from singular `model/`. |
| `model/` | Generated legal retrieval index | Ignored; index contract: [legal retrieval](architecture/legal-retrieval.md). |
| `open/`, root ZIPs | Original distribution / colleague submission inputs | Ignored; preserve source material. |
| `user/` | User-owned hypotheses and notes | Read-only for agents. Never move or edit. |
| `.venv/`, `__pycache__/` | Local dependencies and Python caches | Ignored; exclude from exploration. |
| `pyproject.toml`, `uv.lock`, `.python-version`, `.gitignore` | Environment and tracked/local separation | [Environment](environment.md). |

## Code routing

| Change / question | Read first | Live files |
|---|---|---|
| CLI interface and shared records | [Domain glossary](architecture/domain.md) | `src/cli.py`, `src/records.py::{read_records, write_submission, prediction_payload}` |
| Default dev200 run | [Prefix pipeline](experiments/prefix-pipeline.md) | `src/experiments/run_experiment.py` → `benchmark_prefix_pipeline.py` → `src/inference/prefix_pipeline.py` |
| Default prompt / item criteria | [Compact200](experiments/compact200.md) | `src/inference/compact_criteria.json`, `compact_predictor.py`, `prefix_predictor.py` |
| Twelve groups / rule overrides | [Compact200](experiments/compact200.md) | `src/experiments/config.py::PLANS`, `configuration`, `src/rules/qualification.py`, `briefing.py` |
| RAG baseline / submission CLI | [Dynamic RAG](architecture/dynamic-rag.md) | `src/cli.py`, `src/inference/predictor.py`, `prompt.txt`, `legal_criteria.json` |
| Conversation budgets / retries / search-result packing / judgment validation | [Judgment conversation](architecture/judgment-conversation.md) | `src/inference/conversation.py` |
| GPU engine / cache / request accounting | [Local engine](architecture/local-engine.md) | `src/inference/engine.py` |
| Retrieval / index construction | [Legal retrieval](architecture/legal-retrieval.md) | `src/retrieval/search.py`, `index.py` |
| Recovery / preserved successful work | [Recovery](architecture/recovery.md) | `src/inference/recovery.py` |
| Mixed thinking / scheduling comparisons | [Hybrid five](experiments/hybrid-five.md) | `src/inference/hybrid_experiment.py`, `batch_barrier.py`, `continuous.py` |
| Report location / links | [Maintenance rules](maintenance/structure-audit.md#maintenance-rules) | `src/evaluation/reporting.py`; `evaluate_dev.py`, `summarize_*.py` |

The physical `src/` tree is installed as package `nara`: for example, `src/evaluation/evaluate_dev.py` runs as `python -m nara.evaluation.evaluate_dev`. Commands depend on shared records and inference functions; shared modules do not import CLI or experiment entry points. This one-way dependency keeps commands thin and lets tests call the same functions directly.

The default runner takes `MODEL`, `PLANS`, and `configuration` from `src/experiments/config.py`, and serializes predictions through `src/records.py::prediction_payload`. Its source snapshot includes `config.py`, `records.py`, `runtime.py`, and `paths.py`. `src/inference/prompt.txt` controls the RAG CLI; changing it does not change the default compact prompt.

## Script catalog

Run the submission CLI with `uv run --locked nara` and the default experiment with `uv run --locked nara-experiment`. Other modules use `uv run --locked python -m nara.tools.NAME`, `nara.experiments.NAME`, or `nara.evaluation.NAME` according to their role.

Run individual modules only after reading their `main`/argument parsing and owning experiment note. Some historical experiments hard-code `analysis/` output directories, overwrite summaries, or enforce frozen source hashes. A catalog entry is not an instruction to rerun it.

| Purpose | Files | Read |
|---|---|---|
| Default current experiment | `run_experiment.py` | [Prefix pipeline](experiments/prefix-pipeline.md) |
| Current scoring / comparison / report storage | `evaluate_dev.py`, `compare_dev_runs.py`, `reporting.py` | [Operations](operations.md), [maintenance](maintenance/structure-audit.md#maintenance-rules) |
| Data preparation / inspection | `jsonl_to_md.py`, `measure_token_lengths.py` | [Folder roles](#folder-roles) |
| Model, RAG, legal criteria checks / render | `check_gemma_inference.py`, `check_dynamic_rag.py`, `check_legal_retrieval.py`, `check_legal_criteria.py`, `render_legal_criteria.py` | [Environment](environment.md), [validation](experiments/local-validation.md), [criteria](architecture/legal-criteria.md) |
| Grouping comparison | `benchmark_grouping_time.py`, `summarize_grouping_time.py`, `evaluate_grouping_effect.py` | [Grouping](experiments/grouping-time.md) |
| Compact criteria / H6 | `benchmark_compact200.py`, `summarize_compact200.py`, `validate_compact200.py`, `recover_compact200.py`, `recover_compact_extended.py` | [Compact200](experiments/compact200.md) |
| Prefix / batch11 | `benchmark_prefix200.py`, `summarize_prefix200.py`, `summarize_prefix_batch11.py`, `recover_prefix_batch11.py` | [Prefix cache](experiments/prefix-cache.md) |
| Cross-notice pipeline / historical reference | `benchmark_prefix_pipeline.py`, `summarize_prefix_pipeline.py` | [Prefix pipeline](experiments/prefix-pipeline.md) |
| Hybrid five / barrier / phase probes | `benchmark_hybrid200.py`, `benchmark_hybrid_batch_controls.py`, `summarize_hybrid200.py`, `recover_hybrid200.py`, `run_batch_fallback.py`, `probe_prefill_decode.py`, `summarize_prefill_decode.py` | [Hybrid](experiments/hybrid-five.md), [phase probes](experiments/prefill-decode-fallback.md) |
| Continuous prefill / diagnosis | `benchmark_continuous.py`, `run_continuous_study.py`, `summarize_continuous.py`, `recover_continuous.py`, `diagnose_continuous.py`, `summarize_continuous_diagnosis.py` | [Continuous](experiments/continuous-prefill.md), [diagnosis](experiments/continuous-diagnosis.md) |
| Instant OFF / ON0 | `benchmark_on0.py`, `summarize_on0.py` | [ON0](experiments/instant-on0.md) |
| Colleague submission | `benchmark_colleague200.py`, `summarize_colleague200.py` | [Colleague](experiments/colleague-submission.md) |
| Early RAG comparison / one-record recovery | `summarize_gemma4_experiments.py`, `merge_thinking_recovery.py` | [Validation](experiments/local-validation.md) |
| Engine / recovery saved-run verification | `verify_engine_refactor.py`, `check_engine_request_parity.py`, `verify_recovery_saved.py` | [Engine refactor](experiments/engine-refactor.md), [recovery](architecture/recovery.md) |

## Targeted searches

- Find an implementation: `rg -n 'SYMBOL' src tests`.
- Find a decision: `rg -n 'TERM' docs/architecture docs/experiments`.
- Find a detailed report: consult [report index](reports/README.md), then search only that family.
- Find frozen evidence: inspect the chosen `analysis/<family>/manifest.json` or `analysis_manifest.json`, then the named `source/` or `analysis_source/` file. These copies are not live edit targets.
- Avoid repository-wide recursive reads: notice expansions alone contain 20,210 Markdown records; source snapshots repeat implementations.

Audit findings, relocation map and preservation policy: [structure audit](maintenance/structure-audit.md).
