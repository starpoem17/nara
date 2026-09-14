# Current prefix-pipeline adoption

Current conclusion: the user adopted cross-notice twelve-group scheduling. The maintained entrypoint is now `nara`, invoking `src/inference/pipeline.py`; [operations](../../operations.md) owns current commands. Current output512 and the later v22 rule are different conditions from the original output2048 measurement.

The [original pipeline run](2026-09/legacy_prefix_pipeline200.md) owns scheduling observations, adoption history, evidence and limitations. The [planned12-versus21 sweep](2026-09/legacy_groups12_vs21_20260912.md) owns the later matched grouping comparison. Neither is a holdout/server guarantee. [Execution architecture](../../architecture/execution-records.md) identifies maintained source and verification.

On 2026-09-14 the user requested promotion into the sole maintained prediction path and retirement of both command/driver alternatives. [ADR0002](../../adr/0002-single-inference-command.md) records scope and exact integrated revision; [verification](../../maintenance/pipeline-unification.md) distinguishes code integration from GPU/accuracy checks. This extends the entrypoint adoption, not the scope of historical performance measurements.
