# Execution records and report ownership

Implemented2026-09-14 in the migrated working tree. [Decision](../adr/0001-retained-experiment-runs.md) and [verification](../maintenance/structure-migration-verification.md) own rationale and checked scope.

`Run` hides identity, directory allocation, frozen source/input capture, condition attempts, metadata, reciprocal follow-up links, and documentation navigation. Its callers provide the question and material conditions. This boundary replaces repeated historical directory/report logic while retaining the existing predictor/engine interfaces.

`Run.create` allocates a fresh start-time ID. `capture` snapshots source contents and an actual uncommitted patch before attempts. `reference` records byte hashes of locally retained large assets without duplicating checkpoints. `capture_input` records later evaluation inputs. `compare_provenance` scopes declared-settings equality separately from retained content differences; absent evidence is not equality. `condition` creates a fresh planned attempt and retains failures. The pipeline requires a matching active attempt and refuses a nonempty directory. Historical migrated evidence is read-only.

`pipeline.execute` retains current grouping/preparation/prediction/recovery behavior. `run_experiment.main` declares the sweep, snapshots inputs/source/assets, invokes conditions, and performs paired comparison when applicable. Routine standalone preparation/smoke checks have maintenance records. GPU behavior is unchanged by this migration; source/output512 defaults are derived from the adopted prefix pipeline and later briefing-rule changes, not inferred from historical output2048 scores.

`evaluate_dev` validates complete IDs and trace/CSV judgments and emits metrics. `compare_dev_runs` verifies evaluation/prediction hashes and computes paired differences. `reporting.write_report` inserts one generated section per condition artifact into the owning run report while preserving its judgment history. Saved-output verification copies evidence into a new maintenance record. There is no maintained old-path lookup layer.

Dependencies: existing `nara` package mapping, local development inputs, schemas, model/index assets, installed environment. Checks: `tests/test_run_recording.py`, `test_reporting.py`, `test_experiment_engine.py`, `test_experiment_preflight.py`; actual CPU replay is in the migration verification report. Remaining limits: no new GPU/holdout/server run; missing historical starts and external assets remain explicitly limited.
