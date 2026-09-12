# Grouping latency benchmark

Measured 2026-09-10. [Human report](../reports/analysis/grouping_time32/comparison.md), [raw measurements](../../analysis/grouping_time32/report.json), [selection and prompts](../../analysis/grouping_time32/manifest.json).

- Original benchmark measured timing without reading labels; a later frozen-prediction evaluation is linked below. RTX 5090, Gemma 4 26B A4B NVFP4, thinking ON (1024 budget), output 2048, context 32768, batch 8, optional RAG (max 2 rounds), one retry. BGE and Gemma co-resident.
- Same 32 notices in original order, sampled at length-stratum midpoints from 179/200 notices that fit every configuration. The 21 excluded long notices and hidden evaluation distribution are not covered.
- Benchmark-only `TimingPredictor` uses one compact protocol plus assigned features and referenced-law aliases. Source documents remain complete; production Predictor defaults were not modified.
- One pass per configuration, one resident engine; prefix cache reset between configurations. Model/search initialization 26.82 s, recorded separately. Latency variation across repeated trials was not measured.

| Groups | Seconds / 32 notices | Relative | Invalid responses | Failed notices | Searches |
|---:|---:|---:|---:|---:|---:|
| 1 | 109.86 | 1.00 | 0 | 0 | 0 |
| 7 | 544.90 | 4.96 | 1 | 0 | 0 |
| 9 | 675.25 | 6.15 | 6 | 1 | 1 |
| 12 | 854.30 | 7.78 | 5 | 0 | 1 |



Nine-group run: PPS-DEV-085, v1–v4 hit the 2048 output cap on both attempts. Its elapsed time includes failed attempts and is not time to complete all normal outputs. No context failures in any measured run. Failed notices were not zero-filled; no submission CSV was written for the incomplete configuration.

Grouped runs repeat thinking and document inputs. Apparent text length savings do not offset repeated generation in this configuration. Projections to 200 notices are simple averages ×200, not full-dev timings. L40S/INT8 submission latency and the 2-hour limit remain unverified; include model initialization in deployment accounting.

Reproduce: `uv run --locked python -m nara.experiments.benchmark_grouping_time --output NEW_PATH`, then `uv run --locked python -m nara.evaluation.summarize_grouping_time --input NEW_PATH`. Initial prompts, selected input, source snapshot and per-task traces are saved under each output directory. Trace/report/CSV IDs and token counts were cross-checked; [validation](../../analysis/grouping_time32/validation.json).

The earlier dev200 thinking result used a different prompt and population; do not interpret this new ungrouped timing as a controlled speedup over that experiment.

## Post-hoc grouping effect

[Effect report](../reports/analysis/grouping_time32/effect.md), [machine-readable scores](../../analysis/grouping_time32/effect.json), [per-item results](../../analysis/grouping_time32/effect_per_item.csv).

- Evaluated frozen traces against dev labels after the timing run; no new inference or prompt tuning. Main comparison uses the same 31 notices successful in all four configurations (28 positive labels, 5 items with no positives); nine-group failure PPS-DEV-085 excluded from every main score. Zero-denominator F1=0; all 24 items included.
- Macro F1, 1/7/9/12 groups: .2431/.2590/.3287/.3597. Twelve groups improves TP 7→15 and FN 21→13, but FP 12→31; whole-notice exact matches fall 13→10. Seven/nine groups' micro F1 falls despite macro F1 increasing. Small selected sample; no generalization or evidence-quality claim.
- Official test count 1,853 confirmed on evaluation page on 2026-09-10. Local average ×1,853 plus model initialization: 1.77/8.77/10.87/13.75 h; extrapolations, not L40S measurements. The previous 200-notice projection alone was insufficient for submission-time planning. Fixed multi-call grouping shows macro-score gains here but substantial runtime cost; do not treat the present grouped configurations as ready for the 2-hour limit.
- Reproduce evaluation: `uv run --locked python -m nara.evaluation.evaluate_grouping_effect`, then regenerate timing summary. Raw benchmark report and traces remain unchanged.
