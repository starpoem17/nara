# How do 1/7/9/12 item groups affect latency on the selected notices?

Current judgment: **Exploratory timing sweep; selected sample and incomplete predictions limit the accuracy comparison.**

Reason and scope: Exploratory timing sweep; selected sample and incomplete predictions limit the accuracy comparison. Historical local development evidence; no unseen-data or competition-server generalization is established.

## Run identity and conditions

Run ID: `legacy_grouping_time32`. Historical start time: **unknown**. The available metadata does not establish an orchestration start; initialization/log/preparation timestamps were not substituted. Execution month: September 2026, supported by the original project records and original run names.

Planned/recorded conditions: recorded execution. Preserve condition-specific manifests, input snapshots, traces, and budgets; do not infer identical conditions from the folder name.

## Actions, observations, and judgment history

The original execution and analysis artifacts below retain their original bytes. The migration changes their location and introduces explicit run identity; it is not a rerun, re-score, or adoption decision.

Exploratory timing sweep; selected sample and incomplete predictions limit the accuracy comparison.

Historical comparison and interpretation documents are linked from the area index. Their original bytes are also retained in the migration document archive. Current judgment above governs reuse; historical measurements alone do not override a later withdrawal or narrowed scope.

## Run-specific interpretation

Consult the condition-level observations and retained original interpretation linked below. Missing execution settings are not reconstructed from present defaults.

## Evidence and reproducibility

[Retained execution directory](<../../../../experiments/legacy_grouping_time32>) · [Execution metadata and original-file hashes](<../../../../experiments/legacy_grouping_time32/run.json>)

Source snapshots and original manifests retain historical paths. Do not rewrite their hashes or commands. New code and instructions use the migration mapping; old commands need not execute unchanged. Locally excluded data/model assets require separately restored matching content in another checkout. Exact GPU reproducibility has not been verified by this migration.

Essential evidence is retained here, not solely in temporary work or Git-excluded outputs. The migration inventory identifies every original location and checksum. Task verification and temporary paths are listed in the metadata.

## Retained artifacts

- [groups12/submission.csv](<../../../../experiments/legacy_grouping_time32/groups12/submission.csv>): original execution or analysis evidence.
- [groups12/trace.jsonl](<../../../../experiments/legacy_grouping_time32/groups12/trace.jsonl>): original execution or analysis evidence.
- [groups7/submission.csv](<../../../../experiments/legacy_grouping_time32/groups7/submission.csv>): original execution or analysis evidence.
- [groups7/trace.jsonl](<../../../../experiments/legacy_grouping_time32/groups7/trace.jsonl>): original execution or analysis evidence.
- [groups9/trace.jsonl](<../../../../experiments/legacy_grouping_time32/groups9/trace.jsonl>): original execution or analysis evidence.
- [manifest.json](<../../../../experiments/legacy_grouping_time32/manifest.json>): original execution or analysis evidence.
- [report.json](<../../../../experiments/legacy_grouping_time32/report.json>): original execution or analysis evidence.
- [ungrouped/submission.csv](<../../../../experiments/legacy_grouping_time32/ungrouped/submission.csv>): original execution or analysis evidence.
- [ungrouped/trace.jsonl](<../../../../experiments/legacy_grouping_time32/ungrouped/trace.jsonl>): original execution or analysis evidence.
- [validation.json](<../../../../experiments/legacy_grouping_time32/validation.json>): original execution or analysis evidence.

## Unverified conditions

No new model inference, server run, holdout evaluation, or throughput measurement was performed during relocation. Missing historical timestamps and absent external inputs remain explicit limitations.

- [Original detailed observation: grouping_time32/comparison.md](<../../../../experiments/legacy_grouping_time32/retained_documents/docs/reports/analysis/grouping_time32/comparison.md>): immutable original-language evidence; current judgment is above.

- [Original detailed observation: grouping_time32/effect.md](<../../../../experiments/legacy_grouping_time32/retained_documents/docs/reports/analysis/grouping_time32/effect.md>): immutable original-language evidence; current judgment is above.

## Historical conditions, observations, and decisions

The following retained interpretation records the historical execution and decisions. Commands in it describe that time; current execution instructions are in [operations](../../../operations.md).

### Grouping latency benchmark

Measured 2026-09-10. [Human report](<legacy_grouping_time32.md>), [raw measurements](<../../../../experiments/legacy_grouping_time32/report.json>), [selection and prompts](<../../../../experiments/legacy_grouping_time32/manifest.json>).

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

Reproduce: `uv run --locked python -m nara.experiments.benchmark_grouping_time --output NEW_PATH`, then `uv run --locked python -m nara.evaluation.summarize_grouping_time --input NEW_PATH`. Initial prompts, selected input, source snapshot and per-task traces are saved under each output directory. Trace/report/CSV IDs and token counts were cross-checked; [validation](<../../../../experiments/legacy_grouping_time32/validation.json>).

The earlier dev200 thinking result used a different prompt and population; do not interpret this new ungrouped timing as a controlled speedup over that experiment.

#### Post-hoc grouping effect

[Effect report](<legacy_grouping_time32.md>), [machine-readable scores](<../../../../experiments/legacy_grouping_time32/effect.json>), [per-item results](<../../../../experiments/legacy_grouping_time32/effect_per_item.csv>).

- Evaluated frozen traces against dev labels after the timing run; no new inference or prompt tuning. Main comparison uses the same 31 notices successful in all four configurations (28 positive labels, 5 items with no positives); nine-group failure PPS-DEV-085 excluded from every main score. Zero-denominator F1=0; all 24 items included.
- Macro F1, 1/7/9/12 groups: .2431/.2590/.3287/.3597. Twelve groups improves TP 7→15 and FN 21→13, but FP 12→31; whole-notice exact matches fall 13→10. Seven/nine groups' micro F1 falls despite macro F1 increasing. Small selected sample; no generalization or evidence-quality claim.
- Official test count 1,853 confirmed on evaluation page on 2026-09-10. Local average ×1,853 plus model initialization: 1.77/8.77/10.87/13.75 h; extrapolations, not L40S measurements. The previous 200-notice projection alone was insufficient for submission-time planning. Fixed multi-call grouping shows macro-score gains here but substantial runtime cost; do not treat the present grouped configurations as ready for the 2-hour limit.
- Reproduce evaluation: `uv run --locked python -m nara.evaluation.evaluate_grouping_effect`, then regenerate timing summary. Raw benchmark report and traces remain unchanged.


## Recorded condition evidence

These links identify exact original settings rather than substituting current defaults. Missing values remain unknown.

- [manifest.json](<../../../../experiments/legacy_grouping_time32/manifest.json>). `{"limits": {"batch_size": 8, "search_rounds": 2, "queries_per_round": 4, "top_k": 5, "round_tokens": 4096, "total_retrieval_tokens": 8192, "output_tokens": 2048, "retries": 1, "require_search": false}}`

- [source](<../../../../experiments/legacy_grouping_time32/source>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

- [code](<../../../../experiments/legacy_grouping_time32/code>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

- [retained_documents](<../../../../experiments/legacy_grouping_time32/retained_documents>): retained source/evidence; execution snapshots and migration-time helpers are distinguished.

Migration verification: [check report](<../../../maintenance/structure-migration-verification.md>). Retained migration temporary path: [tmp/structure-migration-20260913](<../../../../tmp/structure-migration-20260913>). This is migration work, not a claim about original execution temporary paths. Essential original evidence is retained under the run directory.
