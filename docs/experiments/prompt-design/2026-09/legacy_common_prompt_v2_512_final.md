# How does common prompt v2 compare under matched dev200/output512 conditions?

Current judgment: **Not adopted under the Macro-F1 priority: candidate recall/per-item F1 losses outweigh fewer false positives.**

Reason and scope: The failed launcher led to a final corrected execution. Historical local development evidence; no unseen-data or competition-server generalization is established.

## Current interpretation and material history

Paired comparison uses only198 notices completed by both arms; no zero filling of the original two failures. MacroF1 .28785730→.23955716; candidate full200 is separately scored .23636771. Fixed original→candidate order and one pass limit causality/repeatability. Saved error review is not additional inference.

## Run identity and conditions

Run ID: `legacy_common_prompt_v2_512_final`. Historical start time: **unknown**. The available metadata does not establish an orchestration start; initialization/log/preparation timestamps were not substituted. Execution month: September 2026, supported by the original project records and original run names.

Planned/recorded conditions: recorded execution. Preserve condition-specific manifests, input snapshots, traces, and budgets; do not infer identical conditions from the folder name.

## Actions, observations, and judgment history

The original execution and analysis artifacts below retain their original bytes. The migration changes their location and introduces explicit run identity; it is not a rerun, re-score, or adoption decision.

Not adopted under the Macro-F1 priority: candidate recall/per-item F1 losses outweigh fewer false positives.

Historical comparison and interpretation documents are linked from the area index. Their original bytes are also retained in the migration document archive. Current judgment above governs reuse; historical measurements alone do not override a later withdrawal or narrowed scope.

## Run-specific interpretation

Consult the condition-level observations and retained original interpretation linked below. Missing execution settings are not reconstructed from present defaults.

## Evidence and reproducibility

[Retained execution directory](<../../../../experiments/legacy_common_prompt_v2_512_final>) · [Execution metadata and original-file hashes](<../../../../experiments/legacy_common_prompt_v2_512_final/run.json>)

Source snapshots and original manifests retain historical paths. Do not rewrite their hashes or commands. New code and instructions use the migration mapping; old commands need not execute unchanged. Locally excluded data/model assets require separately restored matching content in another checkout. Exact GPU reproducibility has not been verified by this migration.

Essential evidence is retained here, not solely in temporary work or Git-excluded outputs. The migration inventory identifies every original location and checksum. Task verification and temporary paths are listed in the metadata.

## Retained artifacts

- [candidate/evaluation.json](<../../../../experiments/legacy_common_prompt_v2_512_final/candidate/evaluation.json>): original execution or analysis evidence.
- [candidate/manifest.json](<../../../../experiments/legacy_common_prompt_v2_512_final/candidate/manifest.json>): original execution or analysis evidence.
- [candidate/report.json](<../../../../experiments/legacy_common_prompt_v2_512_final/candidate/report.json>): original execution or analysis evidence.
- [candidate/submission.csv](<../../../../experiments/legacy_common_prompt_v2_512_final/candidate/submission.csv>): original execution or analysis evidence.
- [candidate/trace.jsonl](<../../../../experiments/legacy_common_prompt_v2_512_final/candidate/trace.jsonl>): original execution or analysis evidence.
- [comparison.json](<../../../../experiments/legacy_common_prompt_v2_512_final/comparison.json>): original execution or analysis evidence.
- [original/manifest.json](<../../../../experiments/legacy_common_prompt_v2_512_final/original/manifest.json>): original execution or analysis evidence.
- [original/report.json](<../../../../experiments/legacy_common_prompt_v2_512_final/original/report.json>): original execution or analysis evidence.
- [original/trace.jsonl](<../../../../experiments/legacy_common_prompt_v2_512_final/original/trace.jsonl>): original execution or analysis evidence.
- [plan.json](<../../../../experiments/legacy_common_prompt_v2_512_final/plan.json>): original execution or analysis evidence.
- [validation.json](<../../../../experiments/legacy_common_prompt_v2_512_final/validation.json>): original execution or analysis evidence.

## Recorded evaluation values

These are values read from retained evaluations, not newly computed results.

| Evidence | Macro F1 | Micro F1 |
|---|---:|---:|
| [candidate](<../../../../experiments/legacy_common_prompt_v2_512_final/candidate/evaluation.json>) | 0.2363677100190258 | 0.2783882783882784 |

## Predecessor

[legacy_common_prompt_v2_512_run](<legacy_common_prompt_v2_512_run.md>): The failed launcher led to a final corrected execution.

## Unverified conditions

No new model inference, server run, holdout evaluation, or throughput measurement was performed during relocation. Missing historical timestamps and absent external inputs remain explicit limitations.

- [Original detailed observation: candidate/evaluation.md](<../../../../experiments/legacy_common_prompt_v2_512_final/retained_documents/docs/reports/analysis/common_prompt_v2_512_final/candidate/evaluation.md>): immutable original-language evidence; current judgment is above.

- [Original detailed observation: common_prompt_v2_512_final/comparison.md](<../../../../experiments/legacy_common_prompt_v2_512_final/retained_documents/docs/reports/analysis/common_prompt_v2_512_final/comparison.md>): immutable original-language evidence; current judgment is above.

- [Original detailed observation: error_review/case_review.md](<../../../../experiments/legacy_common_prompt_v2_512_final/retained_documents/docs/reports/analysis/common_prompt_v2_512_final/error_review/case_review.md>): immutable original-language evidence; current judgment is above.

- [Original detailed observation: error_review/report.md](<../../../../experiments/legacy_common_prompt_v2_512_final/retained_documents/docs/reports/analysis/common_prompt_v2_512_final/error_review/report.md>): immutable original-language evidence; current judgment is above.

## Historical conditions, observations, and decisions

The following retained interpretation records the historical execution and decisions. Commands in it describe that time; current execution instructions are in [operations](../../../operations.md).

### Common prompt v2: matched dev200, output512

Completed2026-09-11. [Detailed comparison](<legacy_common_prompt_v2_512_final.md>). Artifacts: `analysis/common_prompt_v2_512_final/`; candidate source: `experiments/legacy_common_prompt_v2_512_final/support/prompt_candidates/common_v2.txt`.

User-authorized comparison: original and candidate once each, current Gemma4 NVFP4/RTX5090, thinkingOFF, sequential notices with first1 then11 groups, maxseq11, context32768, output512, optional RAG2x4, normal1retry, no extra recovery. This explicitly uses the agreed sequential12-group schedule, not the newer default cross-notice pipeline16. v2/v3 use identical current H6 code/results. Common system only differs (197 vs393tokens); all2400 initial input lengths +196; group/user/schema/source/index hashes matched. Runtime prompt remains unchanged.

Original: attempted200, completed198, failed066(v24)/075(v10..13), both length after normal retry. Candidate: completed200, no finalfailures. Inference452.329s→436.926s (-3.405%), load27.299s→27.158s; warmup/preflight excluded. Both0search. Invalidresponses5→4; length-terminated3→4 (candidate all recovered normally). Candidate full200 Macro .23636771, Micro .27838828, FP82/FN115. Original full200 score unavailable; no zero filling.

Paired complete198 ONLY: Macro .28785730→.23955716 (-.04830014), Micro .27918782→.28358209, FP189→80, FN95→112. LLM22 Macro .22614736→.17345630; H6v2/v3 identical. 214changedbits:153fixed/61regressed. v1 F1 .5→0, v20 .4444→0, v8 .3529→0. Candidate emits fewer positives; lower FP does not offset per-item recall/F1 losses. Single pass, fixed original→candidate order; no repeat/generalization or specific-clause causal claim. Macro-priority criterion does not support adopting v2.

Runner: `experiments/legacy_prefix200/code/benchmark_prefix200.py --batch-size 11 --output-tokens 512 --common-prompt PATH --output FRESH`. Defaults unchanged; optional common replacement survives phase splitting via a local predictor subclass, without mutating CRITERIA. Explicit prompt/budget runs skip historical H6 hash pin and use new parent plan/source hashes. `plan.json` has exact commands/environment, launcher snapshot, sources, prompt hashes. Both prior initialization-only failed attempts remain preserved (`analysis/common_prompt_v2_512/`, `analysis/common_prompt_v2_512_run/`): old H6 hash assertion, then missing virtualenv bin on PATH/ninja. Neither produced notice predictions. Final launcher prepends .venv/bin; no package changes. Final inference process durations496.965s/481.924s include preflight/init/evaluation/exit; do not equate measured inference totals with entire task walltime.

Audit: `experiments/legacy_common_prompt_v2_512_final/code/summarize_common_prompt.py --run-dir analysis/common_prompt_v2_512_final`; sources frozen in analysis_source. Checks actual caps512/thinking0/context/search limits, all200 IDs/12groups, first1→11, common-only changes, identical H6 results, cache/trace totals; candidate full score crosschecked with standard evaluator. 28 related unit tests passed. `comparison.json`, `validation.json`, `changed_judgments.csv`; raw traces local. No additional inference or candidate editing authorized/executed after results.

#### Saved-output error review (2026-09-12)

[Source comparison](<legacy_common_prompt_v2_512_final.md>), [case notes](<legacy_common_prompt_v2_512_final.md>); artifacts `analysis/common_prompt_v2_512_final/error_review/`. No new inference/prompt/label changes. Paired198: newFN24 (21notices), resolvedFN7 (5), resolvedFP146 (87), newFP37 (33). PersistentFN88/FP43. All31 FN transitions and86 non-amount FP fixes reviewed; remaining60 FP fixes outside frozen v14–18 amount bands using meta estimated price. Preserve applicability/scope/timing gains; recover explicit mandatory eligibility and clarify meta/document roles. Adjudicate 042v4 amount-rule mismatch, 09/050v9 equivalents, 044v18 existing certificate, and source/label tensions in057v8/050v24/182v14 before treating every label transition as semantic improvement. All31 candidate relevant groups single normal response; no relevant length stops/search in either arm; original049v1 had malformed JSON then normal retry. Relevant output max190, so no evidence of512 truncation causing these lost detections. Binary preserved when invalid quotes dropped. Full214 CSV/JSONL, exact source excerpts and input hashes; offline rebuild via artifact build.py.


## Recorded condition evidence

These links identify exact original settings rather than substituting current defaults. Missing values remain unknown.

- [candidate/manifest.json](<../../../../experiments/legacy_common_prompt_v2_512_final/candidate/manifest.json>). `{"groups": [["v1", "v4"], ["v5", "v6", "v7"], ["v8"], ["v9", "v19"], ["v10", "v11", "v12", "v13"], ["v14"], ["v15", "v16"], ["v17", "v18"], ["v20"], ["v21"], ["v22", "v23"], ["v24"]], "limits": {"batch_size": 11, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 512, "retries": 1, "require_search": false, "instant_output_tokens": null}}`

- [candidate/report.json](<../../../../experiments/legacy_common_prompt_v2_512_final/candidate/report.json>). `{"options": {"model_dir": "models/gemma-4-26B-A4B-it-NVFP4", "max_model_len": 32768, "thinking": false, "item_group_size": 4}, "limits": {"batch_size": 11, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 512, "retries": 1, "require_search": false, "instant_output_tokens": null}, "groups": [["v1", "v4"], ["v5", "v6", "v7"], ["v8"], ["v9", "v19"], ["v10", "v11", "v12", "v13"], ["v14"], ["v15", "v16"], ["v17", "v18"], ["v20"], ["v21"], ["v22", "v23"], ["v24"]]}`

- [original/manifest.json](<../../../../experiments/legacy_common_prompt_v2_512_final/original/manifest.json>). `{"groups": [["v1", "v4"], ["v5", "v6", "v7"], ["v8"], ["v9", "v19"], ["v10", "v11", "v12", "v13"], ["v14"], ["v15", "v16"], ["v17", "v18"], ["v20"], ["v21"], ["v22", "v23"], ["v24"]], "limits": {"batch_size": 11, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 512, "retries": 1, "require_search": false, "instant_output_tokens": null}}`

- [original/report.json](<../../../../experiments/legacy_common_prompt_v2_512_final/original/report.json>). `{"options": {"model_dir": "models/gemma-4-26B-A4B-it-NVFP4", "max_model_len": 32768, "thinking": false, "item_group_size": 4}, "limits": {"batch_size": 11, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 512, "retries": 1, "require_search": false, "instant_output_tokens": null}, "groups": [["v1", "v4"], ["v5", "v6", "v7"], ["v8"], ["v9", "v19"], ["v10", "v11", "v12", "v13"], ["v14"], ["v15", "v16"], ["v17", "v18"], ["v20"], ["v21"], ["v22", "v23"], ["v24"]]}`

- [plan.json](<../../../../experiments/legacy_common_prompt_v2_512_final/plan.json>). `{"model": "models/gemma-4-26B-A4B-it-NVFP4", "groups": "groups12; v2/v3 use unchanged H6 rules"}`

- [source](<../../../../experiments/legacy_common_prompt_v2_512_final/source>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

- [analysis_source](<../../../../experiments/legacy_common_prompt_v2_512_final/analysis_source>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

- [code](<../../../../experiments/legacy_common_prompt_v2_512_final/code>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

- [retained_documents](<../../../../experiments/legacy_common_prompt_v2_512_final/retained_documents>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

Migration verification: [check report](<../../../maintenance/structure-migration-verification.md>). Retained migration temporary path: [tmp/structure-migration-20260913](<../../../../tmp/structure-migration-20260913>). This is migration work, not a claim about original execution temporary paths. Essential original evidence is retained under the run directory.
