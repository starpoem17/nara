# How do prefill/decode controls and barrier scheduling affect execution?

Current judgment: **Same24 scheduling comparison; batch-sensitive output differences observed without isolated kernel attribution.**

Reason and scope: Earlier diagnosis motivated a new same24 barrier/continuous comparison; engine submission timing and internal batching remain confounders. Historical local development evidence; no unseen-data or competition-server generalization is established.

## Current interpretation and material history

Barrier versus continuous produced24/24 raw differences and6/144 label flips;63.952s versus60.612s. API timing/internal prefill batching confound exclusive attribution to completion waiting. The resulting first four divergent cases motivated a separate token-phase probe. Fallback16 is maintenance verification, not a new full200 score.

## Run identity and conditions

Run ID: `legacy_prefill_decode_probe`. Historical start time: **unknown**. The available metadata does not establish an orchestration start; initialization/log/preparation timestamps were not substituted. Execution month: September 2026, supported by the original project records and original run names.

Planned/recorded conditions: recorded execution. Preserve condition-specific manifests, input snapshots, traces, and budgets; do not infer identical conditions from the folder name.

## Actions, observations, and judgment history

The original execution and analysis artifacts below retain their original bytes. The migration changes their location and introduces explicit run identity; it is not a rerun, re-score, or adoption decision.

Same24 scheduling comparison; batch-sensitive output differences observed without isolated kernel attribution.

Historical comparison and interpretation documents are linked from the area index. Their original bytes are also retained in the migration document archive. Current judgment above governs reuse; historical measurements alone do not override a later withdrawal or narrowed scope.

## Run-specific interpretation

Consult the condition-level observations and retained original interpretation linked below. Missing execution settings are not reconstructed from present defaults.

## Evidence and reproducibility

[Retained execution directory](<../../../../experiments/legacy_prefill_decode_probe>) · [Execution metadata and original-file hashes](<../../../../experiments/legacy_prefill_decode_probe/run.json>)

Source snapshots and original manifests retain historical paths. Do not rewrite their hashes or commands. New code and instructions use the migration mapping; old commands need not execute unchanged. Locally excluded data/model assets require separately restored matching content in another checkout. Exact GPU reproducibility has not been verified by this migration.

Essential evidence is retained here, not solely in temporary work or Git-excluded outputs. The migration inventory identifies every original location and checksum. Task verification and temporary paths are listed in the metadata.

## Retained artifacts

- [plan.json](<../../../../experiments/legacy_prefill_decode_probe/plan.json>): original execution or analysis evidence.
- [validation.json](<../../../../experiments/legacy_prefill_decode_probe/validation.json>): original execution or analysis evidence.

## Predecessor

[legacy_continuous_diagnosis](<legacy_continuous_diagnosis.md>): Earlier diagnosis motivated a new same24 barrier/continuous comparison; engine submission timing and internal batching remain confounders.

## Follow-ups

- [legacy_prefill_decode_tokens](<legacy_prefill_decode_tokens.md>): Stage1 output divergence selected the first four cases by input order; stage2 appended common generated prefixes and used unconstrained token probes with prefill/decode controls.

## Unverified conditions

No new model inference, server run, holdout evaluation, or throughput measurement was performed during relocation. Missing historical timestamps and absent external inputs remain explicit limitations.

## Recorded condition evidence

These links identify exact original settings rather than substituting current defaults. Missing values remain unknown.

- [plan.json](<../../../../experiments/legacy_prefill_decode_probe/plan.json>). `{"limits": "No layer/kernel probes; token probes use unconstrained decoding without thinking budget so no forced token masks obscure scores; not a label-quality evaluation"}`

- [source](<../../../../experiments/legacy_prefill_decode_probe/source>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

Migration verification: [check report](<../../../maintenance/structure-migration-verification.md>). Retained migration temporary path: [tmp/structure-migration-20260913](<../../../../tmp/structure-migration-20260913>). This is migration work, not a claim about original execution temporary paths. Essential original evidence is retained under the run directory.
