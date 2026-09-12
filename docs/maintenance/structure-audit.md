# Structure audit — 2026-09-11

Scope agreed with user: restore root README to original three lines; relocate agent documentation and misplaced scripts; fix links and future report destinations; retain five frozen document copies when discoverable through docs. No inference/GPU experiment requested.

## Findings and disposition

| Finding | Evidence / disposition |
|---|---|
| Root README grew beyond the user's objective | Current additions included commands, implementation routing and recent measurements. Restored exact original first three lines; moved the additional material to [operations](../operations.md), with corrected report destinations. |
| Agent documentation outside `docs/` | Moved root `ENVIRONMENT.md` to [environment](../environment.md); moved 41 active analysis reports and 2 local output evaluations to `docs/reports/`, retaining experiment names and subdirectories. |
| Reports recreated outside `docs/` | Updated 15 report writers to use `scripts/reporting.py`; fixed three summarizers that reopen evaluations. JSON/CSV/log/input paths remain run-relative. The default runner snapshots the report helper with the evaluator. |
| Scripts mixed with analysis artifacts | Moved five active Python files to `scripts/`; updated their bootstrap paths and live documentation references. Frozen script copies and historical command/manifests retain original bytes/paths. See relocation table below. |
| `scripts/` has mixed responsibilities and non-obvious imports | Cataloged all scripts in [project map](../project-structure.md#script-catalog). Current default execution depends on benchmark-named modules, so no speculative subfolder split or deletion. |
| `analysis/` mixes results, report text, prompts and source copies | Active prose moved; [report index](../reports/README.md) joins concise conclusions, detailed reports and artifact folders. Machine evidence and frozen sources retain their paths. |
| Existing documentation index was incomplete as a project map | Existing 22 subject documents were registered, but folder/script roles and some artifact families were not. Added project map, setup/operations routes, report index and this audit. |
| Historical hash checks use current files | Existing benchmark/summarizer/verifier code can reject a changed working tree, including reporting edits. Preserve those checks and old manifests; historical results are not evidence from current sources. Use frozen sources for historical reconstruction, and `run_experiment.py` for a fresh default run. Do not alter hashes to make old checks pass. |
| Potentially misleading extensions | `nara/prompt.txt`, prompt snapshots, JSON criteria and commands/verification text are runtime inputs or evidence. `data/*_md/` holds rendered notices. Imported distribution README and `user/` notes are source/user material. They were not relocated as agent handover documents. |

Policy timing: the current `AGENT.md` explicitly forbids agent documentation outside docs and treats root README as protected. Those additions to `AGENT.md` were already uncommitted at audit start; older committed text was less explicit. This audit establishes current placement mismatches, not which actor violated which historical instruction. README expansion exists both in commit history and the initial working-tree diff.

## Active script relocation

| Previous path | Current path |
|---|---|
| `analysis/summarize_gemma4_experiments.py` | `scripts/summarize_gemma4_experiments.py` |
| `analysis/merge_thinking_recovery.py` | `scripts/merge_thinking_recovery.py` |
| `analysis/engine_refactor200/verify.py` | `scripts/verify_engine_refactor.py` |
| `analysis/engine_refactor200/request_parity.py` | `scripts/check_engine_request_parity.py` |
| `analysis/recovery_refactor/verify_saved.py` | `scripts/verify_recovery_saved.py` |

Old paths inside archived source/command/hash records remain historical identifiers. They are not the current entry points; do not update historical manifests during ordinary documentation maintenance.

## Frozen document exceptions

User approved retaining these five copies at original paths. They are immutable experimental evidence, not active documentation. Read the current summary first; consult a copy only to reconstruct that experiment's recorded state.

| Frozen copy under `analysis/` | Hash record in the same experiment folder | Current summary |
|---|---|---|
| `continuous200/analysis_source/docs/experiments/continuous-prefill.md` | `analysis_manifest.json` | [Continuous](../experiments/continuous-prefill.md) |
| `continuous_diagnosis/source/docs/experiments/continuous-diagnosis.md` | `analysis_manifest.json` | [Diagnosis](../experiments/continuous-diagnosis.md) |
| `prefill_decode_probe/source/docs/experiments/prefill-decode-fallback.md` | `source_manifest.json` | [Phase probes](../experiments/prefill-decode-fallback.md) |
| `prefix200_batch11/analysis_source/docs/experiments/prefix-cache.md` | `analysis_manifest.json` | [Prefix](../experiments/prefix-cache.md) |
| `prefix_pipeline200/analysis_source/docs/experiments/prefix-pipeline.md` | `analysis_manifest.json` | [Pipeline](../experiments/prefix-pipeline.md) |

## Maintenance rules

1. Root README remains the user's objective; never add agent instructions there. Put new knowledge in its owning docs summary and register it in `docs/README.md`.
2. New Markdown reports use `nara.evaluation.reporting.write_report(former_artifact_path, text)`. The caller supplies its run-relative path; the helper writes `docs/reports/<repository-relative-artifact-path>`, rebases Markdown links, and adds the artifact directory. `report_path(...)` locates a report for a subsequent read/edit. JSON/CSV remain beside the run.
3. Examples: `analysis/on0_200/comparison.md` → `docs/reports/analysis/on0_200/comparison.md`; `output/experiments/RUN/evaluation.md` → `docs/reports/output/experiments/RUN/evaluation.md`. Absolute run paths outside this checkout mirror their absolute path below `docs/reports/external/` to avoid same-basename collisions.
4. Reports are detailed evidence. Keep only decisions, result limits and routing in `docs/experiments/`. Add a family to [report index](../reports/README.md) when retaining new results; do not duplicate every metric in the top-level index.
5. Keep live code under `src/` by role: shared records at the package root, inference and retrieval functions below their role folders, and thin commands under `experiments/`, `evaluation/`, and `tools/`. Check imports, source-copy lists, CLI bootstrap paths and saved hashes before moving code.
6. Preserve frozen `source/`, `analysis_source/`, `original/` and their manifests. Historical snapshot code predates the report-location rule; running it may recreate old-location reports. Use an isolated reconstruction and place new agent documentation under docs; do not promote snapshots to live tools.
7. `src/tools/jsonl_to_md.py` renders source records, not handover notes. Its explicit data output path remains supported. Preserve `user/`, original distribution data and model/index assets.
8. Share raw model responses, execution JSONL and logs under `analysis/` as experiment evidence. Keep Python caches and repeated `source/data/dev.jsonl` input snapshots ignored; root datasets, models and indexes still require local setup. `output/` run artifacts remain local even when a report links to them.

9. For future experiments testing a colleague’s hypothesis, name the `analysis/` run directory `<INITIALS>_<experiment_name>[_<date>]`, with uppercase initials first (user decision, 2026-09-12). Example: `LJM_static_law_v2_v8_20260912`. Match the mirrored report directory and update navigation/replay paths. Do not bulk-rename unrelated historical experiments or rewrite frozen source/log evidence.

## Original audit validation

- Root README matches the initial first three lines byte-for-byte.
- All 71 Markdown files under `docs/` are reachable from `docs/README.md`; 435 local links resolve in this checkout. Every active script is in the catalog.
- 83 CPU unit tests passed, including report routing, artifact/document links, frozen-source links and external-run path separation.
- Re-evaluated saved dev200 predictions in a temporary folder: aggregate scores, all per-item values and evidence counts matched the archived evaluation. Comparing the copy with the original produced zero score delta / changed judgments. JSON/CSV stayed with artifacts; both evaluation and comparison Markdown appeared only under docs.
- 733 pre-existing protected user/code/artifact files matched their pre-change hashes. This includes `AGENT.md`, `user/`, `nara/`, prior tests and retained analysis evidence. All five frozen document copies also match their recorded experiment hashes. Existing uncommitted work was preserved.
- Python syntax and `git diff --check` passed. No GPU inference, model download or new accuracy/runtime experiment was performed.

## Unified source-layout validation — 2026-09-12

- The full CPU suite passes: 99 tests.
- Default dev200 preparation passes for all inputs; maximum initial input is 29,310 tokens.
- Re-evaluating the saved dev200 output matches all 28 non-hash evaluation fields and changes zero judgments.
- The built wheel includes runtime prompt and criteria assets. The source relocation preserves the prior Git history and merge compatibility.

Inventory counts describe this audit's working tree, including pre-existing uncommitted work. Links to ignored local evidence may require restoring the corresponding artifacts in another checkout.
