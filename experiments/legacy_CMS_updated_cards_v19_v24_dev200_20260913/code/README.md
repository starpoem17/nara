# Retained hypothesis code

These modules belong to the linked historical run. Helper imports were updated for regression checks; direct historical execution is disabled because it would overwrite retained evidence or recreate old paths. New experiments must use a fresh `Run` and explicitly record adopted hypothesis code.

Original pre-migration bytes are retained in [original-source.tar](../../../docs/maintenance/evidence/structure-migration/original-source.tar); they are migration-baseline code, not a claim that every file was the version executed historically. Existing `source/` snapshots and manifests remain authoritative for historical execution.

See [operations](../../../docs/operations.md) for new execution and saved-output replay.
