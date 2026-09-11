# Compressed-criteria dev200 experiment

Completed 2026-09-11, RTX5090. Owning artifacts: `analysis/compact200/comparison.json`, `.md`, `validation.json`. Full200 in all6 runs after bounded recovery. No source clipping. `user/` unchanged.

| Configuration | Macro F1 | Micro F1 | inference seconds incl repair | projected1853 minutes incl one load |
|---|---:|---:|---:|---:|
| groups7 OFF | .22154488 | .27777778 |1259.2011|194.9|
| groups9 OFF | .22647273 | .26000000 |1433.3239|221.8|
| groups12 OFF | .26420552 | .25000000 |1847.0477|285.7|
| ungrouped ON | .22328178 | .25000000 |792.6790|122.9|
| groups12 OFF H6 | .28444815 | .26407767 |1819.6749|281.5|
| ungrouped ON H6 | .25524869 | .32812500 |717.3477|111.2|

Selection frozen pre-results: maximum Macro F1; within .01 prefer faster. Winner groups12 OFF. Grouped ON remains user-declared unusable; never reran. Group OFF strategies also exceed2h by local linear extrapolation. Only ungrouped ON H6 falls below2h locally; L40S unmeasured, not a deadline guarantee. Projections exclude offline dev prep/common warmup; include measured retries+repairs.

Prompt: `nara/compact_criteria.json`, English concise criteria from preserved detailed `nara/legal_criteria.json`. Full24 system1383 tokens; largest input30232. Every candidate/group/record fits32768 with output2048+128 reserve. Full source/meta identical via allowlist. Original32 Korean detailed-criteria experiments are not controlled comparators (different sample/prompt).

Runner: `scripts/benchmark_compact200.py --prepare-only`, `--stage baseline`, `--stage hypothesis` via `uv run --locked python`. Stage hypothesis requires complete grouped evaluations. One thinking-capable resident engine per stage, toggle template/sampling OFF/ON; reset prefix cache per configuration. Batch8, ON budget1024, output2048, optional RAG. Actual searches0 in all6; OFF thinking tokens0; ON thinking verified. All models/index local.

First pass failures: groups7 PPS-DEV-063 (length), groups12 PPS-DEV-120 (invalidJSON), ungrouped ON103/147/153 (output failures). `scripts/recover_compact200.py` reruns all groups of failed notices only, same source/criteria/output/thinking budget, final-only, evidence max80, existing1retry. Repair7=8.5312s,12=2.3585s; ON standard44.3340s stillfailed147. `scripts/recover_compact_extended.py` recovered147 in15.3478s with output4096, thinking1024, context<=32768. H6 runs both200 normal after ordinary retries, no separate repair. Preserve `first_pass/`, `before_extended_recovery/`, actual prompts/schemas/traces. Reports include extra repair process loading separately; inference comparison includes all attempted inference costs.

H6: `nara/hypothesis6.py` frozen before labels scored; `rule_freeze.json` hash850ebdceff80371dc8bd4859813e86e017552941b44dfdb4773b672576c925ba. Remove v2/v3 from model table/prompt/schema, keep12 groups (first becomesv1/v4); ungrouped becomes22 model+2rule. Merge only with normal model predictions. v2 known national/local law threshold230m and estimate<threshold; explicit monetary experience lower bound in eligibility section; local small negotiated special-technology exception. v3 amount>allocated budget, unlike baseline estimated-price denominator. Unknown extraction→0 with diagnostics. No colleague code/numerical results provided; this is independent heuristic implementation.

Rule scores: v2 TP5 FP3 FN2 F1.666667; v3 TP6 FP0 FN2 F1.857143. False negatives053/062 had explicit source eligibility missed by section extraction; v2 FP099/165 form wording leaked into eligibility; FP059 disagrees with label. No-section13/200; candidates16/200. Unsupported word numerals/ratios/complex alternatives; v3 amount-only. Rules NOT tuned after scoring. These extraction errors limit inference about colleague hypothesis quality.

H6 deltas: groups12 +.02024262 Macro F1, time .98518x; ungrouped +.03196690, time .90496x. Diagnostic replace-v2/v3-only on archived baseline: Macro .28007854/.24401786 (direct gains .01587302/.02073607). Remaining22 changed224/138 bits. Critical: unchanged11 groups (20features) had identical prompts/schemas but195/4000 bits changed across runs. Cause not isolated; single-pass full rerun delta is not solely causal rule effect. See `unchanged_groups_audit.json` and `per_item_changes.csv`.

Validation:35 pre-run unit tests; `scripts/validate_compact200.py` passed all6 complete200 ID/24bit trace/CSV checks, source/frozen-rule hashes, actual context/output budgets, modes, H6 rule identity and prompt/schema isolation. All emitted evidence exact-source valid, but many missing nonabsence positive quotes (see comparison); exact substring is not semantic proof. Evaluation includes FP/FN/evidence errors. `scripts/summarize_compact200.py` produces report and direct-rule counterfactual. No hidden test run or L40S measurement.
