# Evaluation

Source: [평가](https://dacon.io/competitions/official/236754/overview/evaluation), sections 1–2. Verified: 2026-09-10.

## Leaderboard

- `score = mean(F1_positive(item_i), i=1..24)`; positive class = violation (`1`). All items have positive examples in the evaluation set.
- Only `v1`–`v24` affect this score. All 1,853 test notices contribute to Public Score; Private Score is Public Score at competition end.
- Top 15 teams by Private Score advance. Final evaluation combines leaderboard performance (80%) and evidence quality (20%), plus reproducibility and rule checks. Private rank is not final award rank.

## Evidence

- `e1`–`e24` are preserved for second-stage review, even though leaderboard scoring ignores them.
- Review targets ground-truth positive items. Evidence must be an exact substring of the supplied notice/attachment body text. Metadata values are not eligible source text. Generated, edited, or summarized evidence fails automatic validation.
- Quote only the relevant violation span; quality depends on agreement with reference evidence.
- Absence-detection items `10,11,16,18,20` are excluded from qualitative evidence evaluation, but remain in binary scoring.

Reproducibility records and second-stage deliverables: [constraints](<constraints.md#reproducibility-and-second-stage>).
