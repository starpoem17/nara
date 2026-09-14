# Can the corrected launcher execute the common-prompt comparison?

Current judgment: **Failed launcher attempt; no notice predictions. Do not treat it as a completed model comparison.**

Reason and scope: Initialization failure led to a corrected launcher attempt. Historical local development evidence; no unseen-data or competition-server generalization is established.

## Run identity and conditions

Run ID: `legacy_common_prompt_v2_512_run`. Historical start time: **unknown**. The available metadata does not establish an orchestration start; initialization/log/preparation timestamps were not substituted. Execution month: September 2026, supported by the original project records and original run names.

Planned/recorded conditions: recorded execution. Preserve condition-specific manifests, input snapshots, traces, and budgets; do not infer identical conditions from the folder name.

## Actions, observations, and judgment history

The original execution and analysis artifacts below retain their original bytes. The migration changes their location and introduces explicit run identity; it is not a rerun, re-score, or adoption decision.

Failed launcher attempt; no notice predictions. Do not treat it as a completed model comparison.

Historical comparison and interpretation documents are linked from the area index. Their original bytes are also retained in the migration document archive. Current judgment above governs reuse; historical measurements alone do not override a later withdrawal or narrowed scope.

## Run-specific interpretation

Consult the condition-level observations and retained original interpretation linked below. Missing execution settings are not reconstructed from present defaults.

## Evidence and reproducibility

[Retained execution directory](<../../../../experiments/legacy_common_prompt_v2_512_run>) · [Execution metadata and original-file hashes](<../../../../experiments/legacy_common_prompt_v2_512_run/run.json>)

Source snapshots and original manifests retain historical paths. Do not rewrite their hashes or commands. New code and instructions use the migration mapping; old commands need not execute unchanged. Locally excluded data/model assets require separately restored matching content in another checkout. Exact GPU reproducibility has not been verified by this migration.

Essential evidence is retained here, not solely in temporary work or Git-excluded outputs. The migration inventory identifies every original location and checksum. Task verification and temporary paths are listed in the metadata.

## Retained artifacts

- [candidate/manifest.json](<../../../../experiments/legacy_common_prompt_v2_512_run/candidate/manifest.json>): original execution or analysis evidence.
- [original/manifest.json](<../../../../experiments/legacy_common_prompt_v2_512_run/original/manifest.json>): original execution or analysis evidence.
- [plan.json](<../../../../experiments/legacy_common_prompt_v2_512_run/plan.json>): original execution or analysis evidence.

## Predecessor

[legacy_common_prompt_v2_512](<legacy_common_prompt_v2_512.md>): Initialization failure led to a corrected launcher attempt.

## Follow-ups

- [legacy_common_prompt_v2_512_final](<legacy_common_prompt_v2_512_final.md>): The failed launcher led to a final corrected execution.

## Unverified conditions

No new model inference, server run, holdout evaluation, or throughput measurement was performed during relocation. Missing historical timestamps and absent external inputs remain explicit limitations.

## Recorded condition evidence

These links identify exact original settings rather than substituting current defaults. Missing values remain unknown.

- [candidate/manifest.json](<../../../../experiments/legacy_common_prompt_v2_512_run/candidate/manifest.json>). `{"groups": [["v1", "v4"], ["v5", "v6", "v7"], ["v8"], ["v9", "v19"], ["v10", "v11", "v12", "v13"], ["v14"], ["v15", "v16"], ["v17", "v18"], ["v20"], ["v21"], ["v22", "v23"], ["v24"]], "limits": {"batch_size": 11, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 512, "retries": 1, "require_search": false, "instant_output_tokens": null}}`

- [original/manifest.json](<../../../../experiments/legacy_common_prompt_v2_512_run/original/manifest.json>). `{"groups": [["v1", "v4"], ["v5", "v6", "v7"], ["v8"], ["v9", "v19"], ["v10", "v11", "v12", "v13"], ["v14"], ["v15", "v16"], ["v17", "v18"], ["v20"], ["v21"], ["v22", "v23"], ["v24"]], "limits": {"batch_size": 11, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 512, "retries": 1, "require_search": false, "instant_output_tokens": null}}`

- [plan.json](<../../../../experiments/legacy_common_prompt_v2_512_run/plan.json>). `{"model": "models/gemma-4-26B-A4B-it-NVFP4", "groups": "groups12; v2/v3 use unchanged H6 rules"}`

- [source](<../../../../experiments/legacy_common_prompt_v2_512_run/source>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

Migration verification: [check report](<../../../maintenance/structure-migration-verification.md>). Retained migration temporary path: [tmp/structure-migration-20260913](<../../../../tmp/structure-migration-20260913>). This is migration work, not a claim about original execution temporary paths. Essential original evidence is retained under the run directory.
