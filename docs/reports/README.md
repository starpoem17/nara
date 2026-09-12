# Reports and artifact index

Read the concise owner first. Detailed reports live here; JSON/CSV/prompts, raw model responses, execution logs and frozen source remain in the linked `analysis/` folder. Repeated `source/data/dev.jsonl` snapshots and root datasets remain local. Historical reports retain their recorded commands and source paths; use the [project map](../project-structure.md) for current source locations. `docs/reports/output/` remains readable when its linked local `output/` artifacts are absent. Old `analysis/X/Y.md` maps to `docs/reports/analysis/X/Y.md`; old `output/X/Y.md` maps to `docs/reports/output/X/Y.md`. Unlinked artifact names inside a report refer to its artifact folder, identified at the top.

[Project map](../project-structure.md) · [Script catalog](../project-structure.md#script-catalog) · [Preserved snapshots](../maintenance/structure-audit.md#frozen-document-exceptions)

## Analysis families

| Artifact folder | Concise owner / scope | Detailed reports |
|---|---|---|
| [LJM_static_law_v2_v8_20260912](../../analysis/LJM_static_law_v2_v8_20260912/) | [summary](../experiments/ljm-static-law.md) | [report](analysis/LJM_static_law_v2_v8_20260912/report.md) · [case review](analysis/LJM_static_law_v2_v8_20260912/case_review.md) |
| [colleague200](../../analysis/colleague200/) | [summary](../experiments/colleague-submission.md) | [comparison](analysis/colleague200/comparison.md) |
| [cod_legal_gemma](../../analysis/cod_legal_gemma/) | Fictional legal CoD probe inputs and case results. | [current report](output/experiments/cod-legal-gemma-final-20260912/report.md) |
| [cod_plain_gemma](../../analysis/cod_plain_gemma/) | Verbatim generic Gemma CoD probe configuration. | [current report](output/experiments/cod-plain-gemma-20260912/report.md) |
| [common_prompt_v2_512](../../analysis/common_prompt_v2_512/) | Preserved initialization-only attempt; no notice predictions. | [final experiment summary](../experiments/common-prompt-512.md) |
| [common_prompt_v2_512_run](../../analysis/common_prompt_v2_512_run/) | Preserved failed launcher attempt; no notice predictions. | [final experiment summary](../experiments/common-prompt-512.md) |
| [common_prompt_v2_512_final](../../analysis/common_prompt_v2_512_final/) | [summary](../experiments/common-prompt-512.md) | [comparison](analysis/common_prompt_v2_512_final/comparison.md) · [candidate evaluation](analysis/common_prompt_v2_512_final/candidate/evaluation.md) · [error/source review](analysis/common_prompt_v2_512_final/error_review/report.md) |
| [v9_cod_fewshot5](../../analysis/v9_cod_fewshot5/) | Fixed-five CoD prompt variants. | [current comparison](output/experiments/v9-cod-fewshot5-v3-20260912/comparison.md) |
| [compact200](../../analysis/compact200/) | [summary](../experiments/compact200.md) | [comparison](analysis/compact200/comparison.md) · [groups12_off/evaluation](analysis/compact200/groups12_off/evaluation.md) · [groups12_off_h6/evaluation](analysis/compact200/groups12_off_h6/evaluation.md) · [groups7_off/evaluation](analysis/compact200/groups7_off/evaluation.md) · [groups9_off/evaluation](analysis/compact200/groups9_off/evaluation.md) · [ungrouped_on/evaluation](analysis/compact200/ungrouped_on/evaluation.md) · [ungrouped_on_h6/evaluation](analysis/compact200/ungrouped_on_h6/evaluation.md) |
| [continuous200](../../analysis/continuous200/) | [summary](../experiments/continuous-prefill.md) | [comparison](analysis/continuous200/comparison.md) · [mixed_continuous_8192/evaluation](analysis/continuous200/mixed_continuous_8192/evaluation.md) |
| [continuous_diagnosis](../../analysis/continuous_diagnosis/) | [summary](../experiments/continuous-diagnosis.md) | [report](analysis/continuous_diagnosis/report.md) |
| [dynamic_rag_check](../../analysis/dynamic_rag_check/) | [summary](../experiments/local-validation.md) | Structured artifacts only; inspect folder. |
| [engine_refactor200](../../analysis/engine_refactor200/) | [summary](../experiments/engine-refactor.md) | Structured artifacts only; inspect folder. |
| [gemma4_rag_dev200_forced1](../../analysis/gemma4_rag_dev200_forced1/) | [summary](../experiments/local-validation.md) | [comparison](analysis/gemma4_rag_dev200_forced1/comparison.md) · [evaluation](analysis/gemma4_rag_dev200_forced1/evaluation.md) · [interpretation](analysis/gemma4_rag_dev200_forced1/interpretation.md) |
| [gemma4_rag_dev200_thinking](../../analysis/gemma4_rag_dev200_thinking/) | [summary](../experiments/local-validation.md) | Structured artifacts only; inspect folder. |
| [gemma4_rag_dev200_thinking_recovered](../../analysis/gemma4_rag_dev200_thinking_recovered/) | [summary](../experiments/local-validation.md) | [comparison](analysis/gemma4_rag_dev200_thinking_recovered/comparison.md) · [evaluation](analysis/gemma4_rag_dev200_thinking_recovered/evaluation.md) |
| [gemma4_rag_dev200_v1](../../analysis/gemma4_rag_dev200_v1/) | [summary](../experiments/local-validation.md) | [evaluation](analysis/gemma4_rag_dev200_v1/evaluation.md) · [interpretation](analysis/gemma4_rag_dev200_v1/interpretation.md) |
| [gemma4_rag_forced1_preflight](../../analysis/gemma4_rag_forced1_preflight/) | [summary](../experiments/local-validation.md) | Structured artifacts only; inspect folder. |
| [gemma4_thinking_preflight](../../analysis/gemma4_thinking_preflight/) | [summary](../experiments/local-validation.md) | Structured artifacts only; inspect folder. |
| [gemma4_thinking_recovery](../../analysis/gemma4_thinking_recovery/) | [summary](../experiments/local-validation.md) | Structured artifacts only; inspect folder. |
| [grouping_time32](../../analysis/grouping_time32/) | [summary](../experiments/grouping-time.md) | [comparison](analysis/grouping_time32/comparison.md) · [effect](analysis/grouping_time32/effect.md) |
| [hybrid200](../../analysis/hybrid200/) | [summary](../experiments/hybrid-five.md) | [comparison](analysis/hybrid200/comparison.md) · [composite_six_off/evaluation](analysis/hybrid200/composite_six_off/evaluation.md) · [composite_six_on1024_batch8/evaluation](analysis/hybrid200/composite_six_on1024_batch8/evaluation.md) · [composite_six_on256/evaluation](analysis/hybrid200/composite_six_on256/evaluation.md) · [followup_analysis](analysis/hybrid200/followup_analysis.md) · [main/evaluation](analysis/hybrid200/main/evaluation.md) · [optimized/evaluation](analysis/hybrid200/optimized/evaluation.md) · [optimized_off/evaluation](analysis/hybrid200/optimized_off/evaluation.md) |
| [on0_200](../../analysis/on0_200/) | [summary](../experiments/instant-on0.md) | [comparison](analysis/on0_200/comparison.md) |
| [prefill_decode_probe](../../analysis/prefill_decode_probe/) | [summary](../experiments/prefill-decode-fallback.md) | [report](analysis/prefill_decode_probe/report.md) |
| [prefix200](../../analysis/prefix200/) | [summary](../experiments/prefix-cache.md) | [comparison](analysis/prefix200/comparison.md) · [evaluation](analysis/prefix200/evaluation.md) |
| [prefix200_batch11](../../analysis/prefix200_batch11/) | [summary](../experiments/prefix-cache.md) | [comparison](analysis/prefix200_batch11/comparison.md) · [evaluation](analysis/prefix200_batch11/evaluation.md) |
| [prefix_pipeline200](../../analysis/prefix_pipeline200/) | [summary](../experiments/prefix-pipeline.md) | [comparison](analysis/prefix_pipeline200/comparison.md) · [evaluation](analysis/prefix_pipeline200/evaluation.md) |
| [prompt_candidates](../../analysis/prompt_candidates/) | Candidate criteria JSON; no measured experiment summary. | Structured artifacts only; inspect folder. |
| [rag_dev32](../../analysis/rag_dev32/) | [summary](../experiments/local-validation.md) | Structured artifacts only; inspect folder. |
| [rag_smoke](../../analysis/rag_smoke/) | [summary](../experiments/local-validation.md) | Structured artifacts only; inspect folder. |
| [recovery_refactor](../../analysis/recovery_refactor/) | [summary](../architecture/recovery.md) | Structured artifacts only; inspect folder. |
| [rule_ab200](../../analysis/rule_ab200/) | First rule-only dev200 report. | [report](analysis/rule_ab200/report.md) |
| [rule_ab200_revised](../../analysis/rule_ab200_revised/) | Revised rule-only dev200 report; dev-informed changes. | [report](analysis/rule_ab200_revised/report.md) |
| [rule_difference_audit](../../analysis/rule_difference_audit/) | Rule difference audit JSON. | Structured artifacts only; inspect folder. |
| [rule_robustness_review](../../analysis/rule_robustness_review/) | Wording robustness review; not a new GPU run. | [review](analysis/rule_robustness_review/review.md) |

| [v22_rule200](../../analysis/v22_rule200/) | v22 initial and dev-informed revised rules versus saved full200 runs and latest paired198. | [comparison](analysis/v22_rule200/comparison.md) |

## Standalone analysis reports

- [Detailed legal criteria](analysis/feature_legal_criteria_v1.md); owner: [criteria](../architecture/legal-criteria.md); artifacts: `analysis/legal_criteria_v1_context.json`, `analysis/legal_criteria_v1_system_prompt.txt`.
- [Early Gemma RAG comparison](analysis/gemma4_experiments_summary.md); owner: [validation](../experiments/local-validation.md); machine summary: `analysis/gemma4_experiments_summary.json`.
- Local smoke/retrieval/token checks: inspect named JSON/CSV in [analysis root](../../analysis/) after reading [validation](../experiments/local-validation.md) or [environment](../environment.md).

## Current-run evaluations

Default artifacts: `output/experiments/<timestamp>/`; corresponding reports: `docs/reports/output/experiments/<timestamp>/`. These are current-source runs, distinct from frozen analysis experiments.

| Run | Evaluation | Artifacts |
|---|---|---|
| engine-refactor-after-20260911 | [evaluation](output/experiments/engine-refactor-after-20260911/evaluation.md) | [run](../../output/experiments/engine-refactor-after-20260911/) |
| engine-refactor-before-20260911 | [evaluation](output/experiments/engine-refactor-before-20260911/evaluation.md) | [run](../../output/experiments/engine-refactor-before-20260911/) |

New families must be registered here; avoid adding all detailed reports to `docs/README.md`. Do not infer completeness from a folder name: check its report/validation JSON. A source snapshot is evidence, not the live implementation.

- [v9/v19 isolated dev200, output512](output/experiments/v9-group512-20260912/comparison.md): English v9 candidate vs archived pipeline; v9 F1 rises but recovered positive has unrelated evidence; v19 regresses.

- [v9/v19 Thinking ON vs CoD ON](output/experiments/v9-cod-comparison-20260912/comparison.md) · [thinking analysis](output/experiments/v9-cod-comparison-20260912/interpretation.md): total512/thinking256; most CoD thinking remains budget-bound, no short-draft behavior.

- [CoD few-shot fixed random five](output/experiments/v9-cod-fewshot5-v3-20260912/comparison.md): three attempts; final strict1/5, another terse output exceeds word limit; no reliable enforcement or budget reduction.

- [Verbatim CoD generic Gemma probe](output/experiments/cod-plain-gemma-20260912/report.md): arithmetic5 x zero/eight-shot x ON/OFF; OFF terse correct responses, ON repetitive thinking exhausts512 without final.

- [Fictional legal CoD probe](output/experiments/cod-legal-gemma-final-20260912/report.md):6 English legal cases x0/4-shot xON/OFF; OFF4shot6/6 short correct, ON all unclosed thought at512.

- [OFF CoD dev200 comparison](output/experiments/v9-cod-off512-20260912/all_comparison.md) · [interpretation](output/experiments/v9-cod-off512-20260912/interpretation.md): original parser vs gold-blind first-valid fencedJSON replay separated; replay v9 F1.3077/v19 .6667, short notes18/200; not a joint replacement.

- [12 vs 21 singleton groups](output/experiments/groups12_vs21_20260912/comparison.md): matched current dev200, one pass each; [12 evaluation](output/experiments/groups12_vs21_20260912/groups12/evaluation.md) · [21 evaluation](output/experiments/groups12_vs21_20260912/groups21/evaluation.md). Owner: [prefix pipeline](../experiments/prefix-pipeline.md).
