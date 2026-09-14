# WITHDRAWN: CMS/CJH original-card run

Current scope: historical withdrawn design/observations. CJH redesign is cancelled; original CMS evidence was explicitly deleted. No legacy command below is an active execution instruction. [Current study status](cms-cjh-redesign-interview.md) and the linked canonical run reports govern reuse.

Withdrawn by KHJ on 2026-09-13 after completed-run criticism. Generation completed, but this is not accepted as valid substantive hypothesis verification. KHJ later ordered full local deletion of the CMS raw evidence and its dedicated report; that deletion is complete. Do not restore the CMS run or reuse its scores, predictions or experimenter-derived rules. Other historical artifacts are outside this cleanup scope. See [redesign interview](<cms-cjh-redesign-interview.md>). Human-facing [Korean results and interpretation](<cms-cjh-original-summary.md>) owns the outcome and limitations. [Plan](<cms-cjh-original-plan.md>), [Astra review](<cms-cjh-original-plan-review.md>).

Both dev200 suites completed exactly one generation per original card/notice: CMS 1,200 and CJH 1,800. Inputs, source spans, template token IDs, selection provenance and completed runtime evidence were verified before opening labels. The user approved context 36,864 only for this experiment; shared default remains 32,768. No prompt correction, generated-response retry or repaired judgment was used.

The dominant observation was output-schema mismatch. The frozen evaluator accepts a full JSON fence as readable while recording the strict-format violation; it rejects alternative keys/nesting and surrounding commentary. Do not interpret valid-subset F1 as the authors' overall hypothesis accuracy, and do not interpret zero CJH simultaneous positives as exclusivity validation: both-valid pair denominators are zero. CMS v24 contains knowingly preserved dev-answer notes. Static references and product preselection are explicitly experimenter-authored integration conditions.

`experiments/legacy_CJH_original_cards_v10_v18_20260913/code/evaluate_colleague_cards.py` remains the exact pre-inference evaluator. The post-evaluation `experiments/legacy_CJH_original_cards_v10_v18_20260913/code/describe_colleague_outputs.py` inventories raw shapes and adds report caveats without extracting extra judgments or rescoring. `experiments/legacy_CJH_original_cards_v10_v18_20260913/code/audit_colleague_runtime.py` froze raw responses before label access. See the plan for safe reproduction commands and artifact guards.

## Run navigation

[September run reports](2026-09/README.md) own each execution's current and historical judgments; this document is question-level context.
