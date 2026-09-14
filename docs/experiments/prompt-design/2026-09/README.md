# prompt-design: September2026

Historical runs, current judgments and material limits. See each report for historical conditions and follow-ups.

- [legacy_gemma4_rag_dev200_v1](legacy_gemma4_rag_dev200_v1.md): Historical exploratory baseline; actual optional searches and development-set limits govern interpretation.
- [legacy_gemma4_rag_dev200_forced1](legacy_gemma4_rag_dev200_forced1.md): The forced-search condition did not improve historical Macro F1; do not extend that conclusion to untested retrieval conditions.
- [legacy_gemma4_rag_dev200_thinking](legacy_gemma4_rag_dev200_thinking.md): Initial run completed 199/200 notices. The later repaired result uses a different output allowance.
- [legacy_common_prompt_v2_512](legacy_common_prompt_v2_512.md): Initialization-only attempt; no notice predictions. Follow-up execution is recorded separately.
- [legacy_common_prompt_v2_512_run](legacy_common_prompt_v2_512_run.md): Failed launcher attempt; no notice predictions. Do not treat it as a completed model comparison.
- [legacy_common_prompt_v2_512_final](legacy_common_prompt_v2_512_final.md): Not adopted under the Macro-F1 priority: candidate recall/per-item F1 losses outweigh fewer false positives.
- [legacy_compact_baseline](legacy_compact_baseline.md): Historical initial four-condition sweep; groups12 OFF selected for the subsequent H6 question. Later repairs are separate runs.
- [legacy_compact_repair](legacy_compact_repair.md): Post-result standard repair; successful predecessor predictions were reused and the remaining ON147 failure led to another run.
- [legacy_compact_extended_repair](legacy_compact_extended_repair.md): Only the remaining ON147 failure was recovered with output4096; merged200 is a mixed-attempt/budget result.
- [legacy_gemma4_thinking_recovery](legacy_gemma4_thinking_recovery.md): The merged200 result is not a uniform-budget execution; only the failed notice was newly inferred.
- [legacy_cod_legal_gemma_20260912](legacy_cod_legal_gemma_20260912.md): INVALID and aborted: partial results excluded after a necessary/sufficient-condition error in the demonstration; superseded by the corrected final legal probe.
- [legacy_cod_legal_gemma_final_20260912](legacy_cod_legal_gemma_final_20260912.md): Corrected small synthetic legal probe; format/completion observations do not establish transfer to long Korean notices.
- [legacy_cod_plain_gemma_20260912](legacy_cod_plain_gemma_20260912.md): Small synthetic format/completion observations only; no transferable dev200 improvement established.
- [legacy_v9_cod_fewshot5_v1_20260912](legacy_v9_cod_fewshot5_v1_20260912.md): Not adopted for lower thinking budgets: format success0/5 in this first fixed-five probe.
- [legacy_v9_cod_fewshot5_v2_20260912](legacy_v9_cod_fewshot5_v2_20260912.md): Not adopted for lower thinking budgets: format success0/5 after the second prompt revision.
- [legacy_v9_cod_fewshot5_v3_20260912](legacy_v9_cod_fewshot5_v3_20260912.md): Partial style inducement only: format success1/5, not reliable enforcement or grounds for lower thinking budgets.
- [legacy_v9_cod_off512_20260912](legacy_v9_cod_off512_20260912.md): Not adopted for v9; unsuitable as a replacement for both items. v19 improvement is not an isolated CoD effect.
- [legacy_v9_group512_20260912](legacy_v9_group512_20260912.md): Historical exploratory observations; consult retained condition results and the linked question-level interpretation before reuse.
- [legacy_v9_on_cod512_20260912](legacy_v9_on_cod512_20260912.md): Not adopted: zero-shot CoD did not establish short-draft reasoning or justify reducing the thinking budget. OFF is an earlier reused comparator.
