# Project structure

Status: the user-authorized layout migration is implemented; [migration verification](maintenance/structure-migration-verification.md) records the checks actually performed. User-owned files and pre-existing uncommitted work were preserved.

| Location | Responsibility |
|---|---|
| `src/` | Maintained `nara` package, directly installed from this directory; no extra `src/nara/` layer. |
| `src/experiments/` | Reusable grouping configuration, registered sweep execution, provenance and attempt lifecycle. |
| `src/inference/`, `src/retrieval/`, `src/rules/` | Maintained prediction engines/scheduling, legal retrieval, deterministic judgments. |
| `src/evaluation/`, `src/tools/` | Reusable scoring/comparison/report sections, saved-output replay, and current utilities. |
| `experiments/<run-id>/` | `run.json`, original predictions/logs/settings/source snapshots, and run-specific hypothesis `code/`. |
| `docs/experiments/<area>/YYYY-MM/<run-id>.md` | One report owning each run's current and historical judgments, with reciprocal metadata links. |
| `docs/experiments/<area>/*.md` | Question-level conclusions and decisions spanning runs. |
| `docs/architecture/`, `docs/adr/` | Maintained module descriptions and consequential rationale. |
| `docs/maintenance/` | Routine verification reports and retained task evidence. |
| `tmp/<task-id>/` | Isolated task work retained until explicitly deleted by the user. |
| `outputs/` | Final user deliverables, local and retained. |
| `data/`, `models/`, `model/`, `pyproject.toml`, `uv.lock`, `tests/` | Existing data/model/build/test locations remain required by the current project. |
| `user/`, root `README.md`, root `AGENT.md` | User-owned; preserved. |

The retired `analysis/`, `output/`, and `docs/reports/` roots have no current writing role. Original source snapshots, logs, and commands may mention them as historical evidence. Old commands/imports are not supported. Use [operations](operations.md) for current entrypoints.

[Migration inventories](maintenance/evidence/structure-migration/README.md) map every moved artifact, source module, and document; originals are recoverable independently of Git history. Code preserved at migration time is distinguished from actual execution-time snapshots.
