# Structure migration verification

Implementation: **complete** in the working tree,2026-09-14 Asia/Seoul. Root implemented the user-authorized migration; the requested `gpt-6-astra` medium supervisor independently reviewed preservation, execution granularity, run judgments, and common recording behavior. Final supervisor review found no additional completion-blocking instruction violation; [its scope is retained](evidence/structure-migration/supervisor-review.json). No commit, publication, GPU experiment, or changed hypothesis adoption was performed.

The original objective and decisions are in the [migration plan](structure-migration-plan.md); [ADR0001](../adr/0001-retained-experiment-runs.md) owns consequential rationale. [Current operations](../operations.md) replaces old commands.

## Implemented structure

- Maintained code lives in `src/`;56 historical hypothesis/analysis modules moved with their evidence, retaining original source bytes separately.
- 48 historical runs now have one owning report each under problem area/month. Planned sweeps keep conditions together;25 predecessor relations are bidirectional. Three original ON/CoD directories were consolidated from matching execution sources and the original comparison, with absent initial orchestration plan disclosed.
- All1,925 original artifacts (582,434,489 bytes) moved to retained run/maintenance/architecture evidence. Start time is unknown where not established; historical IDs use the approved legacy exception, with separate migration time.
- Current execution allocates second-precise Asia/Seoul IDs, records planned conditions and attempts, captures actual source/uncommitted inputs and local asset hashes, and keeps one report. Result-triggered follow-ups get new IDs even for unchanged settings. Standalone preparation/smoke uses maintenance records.
- The retired `analysis/`, `output/`, and `docs/reports/` roots are absent. Old caches were moved to retained task work. Root submission output defaults to `outputs/submission` while preserving the existing environment override and fresh-output check.
- Glossary is in `docs/CONTEXT.md`; area/month indexes, architecture index, ADR and maintenance navigation describe the current layout. Original-language reports are retained as immutable evidence, distinguished from current English agent documentation.

## Passed verification

| Check | Result and evidence |
|---|---|
| Original artifacts | 1,925/1,925 SHA-256 values match; unique destinations. [Machine audit](evidence/structure-migration/verification.json), [mapping](evidence/structure-migration/mapping.json). |
| Protected contents | 27 files match baseline, including all22 user files, root README/AGENT, lock/configuration files. Root input/model files were not edited; their current references were hashed during preparation. |
| Pre-existing source/docs/tests |254 original archive members verified against the baseline, preserving untracked and uncommitted contents. [Original evidence archives](evidence/structure-migration/README.md). |
| CPU regression suite |139 tests pass. [Test log](evidence/structure-migration/final-tests.log), [checked source hashes](evidence/structure-migration/verified-source-hashes.json). Includes failure-state, active-attempt, changed-source, CSV-integrity, report-preservation and original inference/recovery behavior checks. |
| Saved-result replay |28 non-path evaluation fields and prediction CSV match. Input hashes checked; original artifacts unchanged. [Current replay record](checks/20260914_003426_saved-evaluation.md). |
| Actual CPU preparation |Both planned grouping conditions completed on dev200. Max input29,310 tokens(groups12) and29,273(groups21); output512/context32768. [Preparation record](checks/20260914_002652_migrated-preparation.md), [log](evidence/structure-migration/preparation.log). No GPU model loading or inference. |
| Packaging |Offline wheel build passed;42 packaged source/asset files match the current source byte-for-byte. Historical runners are omitted and both current help entrypoints passed. [Package verification](evidence/structure-migration/package-verification.json). Installation in an unrelated checkout was not tested. |
| Run ownership |48 unique reports and25 reciprocal predecessor relations verified. Every report links exact evidence and retained migration task work; each period index links its runs. |

| Navigation |121/121 active Markdown documents reachable from docs/README; zero broken local file links or heading anchors. [Navigation audit](evidence/structure-migration/navigation-verification.json). |
| Change formatting |`git diff --check` passed. |

## Supervisor findings and corrections

Final independent review recomputed all1,925 artifact hashes and25 reciprocal relations, verified root AGENT/README hashes, and inspected corrected execution protection and judgments. It found no additional blocking issue. Root subsequently completed navigation and current-package byte checks.

The supervisor identified incorrect unchanged-prompt wording for compact repair; missing batch11 aborted/corrected recovery, v22 revision and token-probe run boundaries; omitted predecessor links; generic judgments that hid invalid/non-adopted CoD results; and a saved-only comparison misclassified as a separate run. The reports and mappings now record these distinctions with original evidence.

For new execution, review identified failure states recorded as complete, a direct pipeline overwrite path, missing evaluation/CSV hash validation, and overly broad unchanged-condition labels. The implementation now catches comparison failure, requires a matching active empty attempt, checks saved prediction hashes, and separately compares source/input/asset provenance. Regression tests exercise these failures.

## Limits and retained work

No new full200 model generation, GPU smoke, throughput benchmark, server submission, holdout evaluation, or bitwise generation reproduction was performed. Existing engine/prompt/rule semantics are covered by CPU regression and actual tokenizer preparation; those checks do not establish GPU numerical invariance. Missing historical start times, commands, revisions or external inputs were not invented. Models/datasets/indexes remain locally available/excluded assets and need matching restoration in another checkout.

The full baseline inventory, original patch and affected-file backup remain at [tmp/structure-migration-20260913](../../tmp/structure-migration-20260913). Essential original contents and verification evidence were copied to retained locations above. No temporary directory is disposable without explicit user deletion. The earlier Korean planning visualization remains at `/tmp/nara-structure-review-20260913T090444/architecture-review-20260913.html`; its original plan is historical.

## User deliverable

[Korean completion report](../../outputs/structure-migration/completion.md) summarizes the finished migration. Its provenance is this verification record and the linked retained evidence.
