# Structure migration plan

Status: implementation authorized2026-09-13 and implemented2026-09-14; final verification is recorded separately in [migration verification](structure-migration-verification.md). The user explicitly instructed “개편 시작” and requested an Astra medium sub-agent to supervise compliance with AGENT.md. Root implements; migration_supervisor performs independent read-only milestone reviews. No GPU experiment or publication is authorized by this migration.

Authority: [AGENT.md](<../../AGENT.md>), sections 6–9. Navigation: [maintenance index](<README.md>). The [previous audit](<structure-audit.md>) describes the earlier layout and preservation decisions; conflicting placement rules are historical inputs, not the target contract.

## Confirmed user decisions

1. Migrate historical experiments in stages. Preserve original evidence, hashes, withdrawals, and decision history; do not invent missing facts.
2. A sweep addressing the same question under one comparison plan receives one run ID and one run report. Preserve each condition's inputs, settings, results, and execution status within that run. Any additional experimental execution triggered by observed results receives a new ID, even under unchanged conditions, and links to its predecessor in both directions with the reason and condition comparison. This incorporates the latest AGENT.md clarification at implementation start. Document the granularity in each applicable experiment-area index. The earlier agent recommendation of one ID per condition was not adopted.
3. If the actual start time cannot be recovered, use a historical exception ID such as `legacy_<previous-name>`. Record the unknown start time and migration time separately. This exception does not apply to new runs. Preparation completion, file modification, and migration timestamps are not automatically run start times.
4. Supporting old experiment commands without modification is unnecessary. Prioritize maintainability for future experiments. Do not add compatibility entry points, import aliases, or directory aliases solely for historical commands. Preserve original command text as evidence and provide new-location mappings and reconstruction instructions.

The user authorized one Astra medium compliance supervisor; other implementation sub-agents have not been requested. Existing adopted prediction behavior remains the verification baseline; restructuring does not authorize adoption of withdrawn hypotheses or changes to prompts, judgment semantics, scoring, or runtime budgets.

## Verified baseline and limits

Checked source revision: `a74048d42d2d8e24a16473eeb056ea3a15264a3b`, with the pre-existing working-tree changes described below.

The inspected pre-plan tree contains 92 Python source files, 24 test files, and 127 Markdown documents under `docs/`. The existing CPU suite passed: 126 tests. Counts include pre-existing untracked work.

- The default runner writes to `output/experiments/`; [reporting](<../../src/evaluation/reporting.py>) maps reports into `docs/reports/`. Fifty-one source files contain old artifact/report paths. Twenty-seven source/test files import reporting.
- `src/experiments/` contains both the adopted default runner and hypothesis-specific code. Some evaluation and verification modules import experiment-specific settings and helpers. Relocate dependency groups rather than selecting files only by directory name.
- The experiment and architecture README indexes and `docs/CONTEXT.md` are absent. At baseline, root `CONTEXT.md` overlapped with `docs/architecture/domain.md`. Missing empty output or ADR directories alone are not defects.
- A simple Markdown traversal reached 121 of 127 documents. After file-line suffix normalization, two missing links point to deliberately deleted CMS responses. Do not restore them. This was not a full Markdown syntax or anchor audit.
- Excluding Python caches, `analysis/` and `output/` contain 1,925 files totaling approximately 582 MB. These counts exclude root datasets and model assets. A directory is not automatically one run.
- Most of 48 inspected manifest-like files lack a run start time. Inspect other logs before assigning historical IDs.
- Two tracked documentation files and additional untracked code, tests, reports, and artifacts were already changed. The original change list was unchanged after CPU tests. Capture content hashes and excluded artifacts before migration.

At planning time, no complete historical hash audit or migration trial had been performed. See the final verification record for work completed since then. CPU success is not proof of historical GPU reproducibility.

## Adopted design

### Maintained Modules and future experiments

Keep maintained prediction, retrieval, rules, common evaluation, and shared execution support in `src/`. Preserve existing build, package, and test arrangements where they still serve these responsibilities. The adopted default pipeline is maintained code; do not archive it merely because its filename contains `benchmark`.

Store hypothesis-specific execution, evaluation, and verification code under its retained `experiments/<run-id>/`. Move coupled code together and adjust real callers. Keep frozen original snapshots byte-for-byte. Distinguish revised reconstruction code from code actually used in historical execution.

Extend existing JSON metadata and reporting support into a common run-recording Module. Its Interface should give experiment code its workspace and record conditions, attempts, evidence, and results without duplicating ID, path, preservation, and report-link rules. Design the smallest concrete Interface during implementation; no generic plugin framework is proposed. New experiments should add hypothesis-specific code and planned conditions while reusing maintained Modules and common recording support.

Current maintained command names can remain where useful, but historical compatibility must not dictate the design. Audit existing relocation helpers before removing them: some also serve provenance verification. Preserve necessary evidence lookup through current reconstruction instructions and code.

### Target locations

```text
src/                                  maintained Modules and shared run support
tests/                                behavioral checks
experiments/<run-id>/                  run-specific code, metadata, evidence
docs/README.md                        brief constraints, timezone, area links
docs/CONTEXT.md                        glossary only
docs/architecture/README.md            responsibility, source, Interface, checks
docs/adr/README.md                     consequential decisions, as needed
docs/experiments/README.md
docs/experiments/<area>/README.md      scope, run granularity, period links
docs/experiments/<area>/synthesis.md   conclusions spanning runs, as needed
docs/experiments/<area>/YYYY-MM/README.md
docs/experiments/<area>/YYYY-MM/<run-id>.md
docs/maintenance/                     migration mapping and verification
tmp/<task-id>/                        retained task-specific temporary work
outputs/                             final user deliverables, Git-excluded
```

Proposed routine default: `Asia/Seoul`, consistent with the project environment and local records. Convert verified timestamps explicitly. A new sweep's start is its orchestration start, including preparation; separately record preparation completion and measured-inference start. Historical start-time interpretation must follow actual evidence. Use collision suffixes, and retain a sweep's ID for its planned retry attempts.

Use a verifiable execution month for historical report placement. If even the month is unknown, record an unresolved placement exception before moving that run; do not silently use the migration month.

Each run report owns its current and historical judgments, scope, reasons, evidence, and follow-up links. Reports and metadata link reciprocally. Execution status and adoption/withdrawal status remain distinct. Preserve deleted-evidence notices and frozen document exceptions. Multiple runs answering one question link through a synthesis when needed.

Record actual source contents, revision, uncommitted changes, commands/configuration, inputs or immutable retrievable references, environment, and results. Extend recording to prevent new provenance gaps; do not claim to reconstruct absent historical evidence. Essential evidence cannot depend solely on temporary files or `outputs/`.

Move Git exclusion rules with affected paths: retain experiment logs, preserve the established exclusion of repeated local dataset copies, and exclude `outputs/`. Document excluded-input access limits and check what another checkout could actually retrieve.

Protect `user/`, root `README.md`, original distribution inputs, model assets, and unrelated work. Do not edit the user's AGENT.md to remove mismatches. Record approved historical exceptions in affected documentation. Change tooling/configuration locations only when required by the responsibility split.

## Execution stages and gates

| Stage | Work | Gate |
|---|---|---|
| Baseline | Inventory tracked, untracked, and excluded files; capture hashes and current changes. | Complete preservation inventory and identifiable migration batches. |
| Mapping | Classify questions, sweeps, conditions, and follow-ups; recover timestamps; design the common recording Interface and code split. | Concrete old-to-new mapping, explicit exceptions, behavior-based checks. |
| New recording | Update maintained runner, metadata, reporting, and ignore rules. | CPU checks for identities, retries, failures, collisions, snapshots, reciprocal links; no new old-layout output. |
| Pilot | Move one simple completed case and one comparison/withdrawal case with dependent code and docs. | Original hashes match; saved predictions re-evaluate identically; decision history and tested reconstruction remain usable. |
| Remaining areas | Migrate disjoint experiment groups; update callers, source-copy lists, tests, indexes, report writers together. | Each batch passes affected checks before integration and can be reversed independently. |
| Completion | Audit active references, index reachability, report uniqueness, metadata links, evidence, status scopes, packaging, commands. | Full CPU suite passes; protected content and evidence preserved; remaining reproduction limits explicit. |

Do not bulk-replace paths inside frozen manifests, logs, or snapshots. Their old path text is historical evidence. Current executable references follow the new design, and old commands need not execute unchanged. Preserve relevant behavioral test coverage.

Use saved-result replay, CPU tests, and appropriate package/preparation checks before considering GPU reruns. If an unavoidable change affects model requests or scheduling, identify the additional validation needed and do not claim unmeasured equivalence.

## Optional future delegation

Only after explicit user authorization:

- Agent A: assigned areas' document navigation and current/historical judgment, withdrawal, replacement records.
- Agent B: assigned runs' artifacts, sweep reconstruction, timestamps, hashes, evidence-access limits.
- Agent C: assigned experiment code dependencies and relocation with affected tests.
- Root: user decisions, common Interface and metadata rules, shared runner/reporting, global indexes, packaging/ignore rules, integration, verification.

Read-only investigations can run in parallel. Actual moves follow the common contract and pilot. Assign disjoint experiment groups with ownership across code, reports, and evidence; shared indexes and recording Modules have one editor.

## Retained planning artifacts and implementation authorization

The Korean user-facing visual review remains at `/tmp/nara-structure-review-20260913T090444/architecture-review-20260913.html`; retain it until explicit deletion instructions. This Markdown document is the durable record of confirmed policy and the proposed execution plan.

The user confirmed shared understanding and explicitly started implementation. Baseline inventory, original uncommitted patch, and complete affected-file backup are retained at `tmp/structure-migration-20260913/baseline.json`, `baseline.diff`, and `baseline.tar`. Implementation is complete; the linked verification record reports each gate and explicit remaining reproduction limits. These task files must be retained until explicit deletion instructions.
