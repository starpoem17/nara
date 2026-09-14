# ADR0001: Retained runs, question navigation, and maintained source boundary

Status: adopted and implemented2026-09-14. Verification status is separate in [migration verification](../maintenance/structure-migration-verification.md). No replacement ADR.

The user changed AGENT.md and requested full layout migration, including historical experiments. Mixed hypothesis runners in `src/`, evidence split across `analysis/` and `output/`, and separate summary/generated reports obscured current judgments and execution ownership.

The user confirmed: migrate past evidence in stages; preserve original bytes/hashes and withdrawal history; one planned question/condition sweep is one run; use `legacy_<old-name>` when actual historical start cannot be established; do not preserve old commands. AGENT.md additionally requires a new ID for every result-triggered experimental execution, even under unchanged conditions.

Decision: keep reusable recording/execution/evaluation in `src/`, place hypothesis code and retained artifacts in `experiments/<run-id>/`, and give each run one owning report under question area/month. Keep cross-run conclusions at area level, architecture rationale here, and routine checks in maintenance. Local temporary work and final deliverables are both retained but have different ownership. User-owned files remain untouched.

This removes historical command/import compatibility maintenance. Original execution snapshots stay byte-identical; migration-time helper imports may change in explicitly labeled historical code. Future hypothesis work starts a fresh registered run and records selected source/inputs. Missing metadata is disclosed, never fabricated. Old result-driven repairs are split and linked; saved-only reanalysis is identified without claiming new model generation.

Alternatives rejected: keeping both old/new executable paths would retain duplicate maintenance; changing original manifests or fabricating timestamps would undermine evidence; placing all checks in experiments would obscure hypothesis conclusions. The original directory compatibility contract is superseded only for this authorized migration.

Source plan and confirmed decisions: [migration plan](../maintenance/structure-migration-plan.md). Source inventories and original content: [migration evidence](../maintenance/evidence/structure-migration/README.md).
