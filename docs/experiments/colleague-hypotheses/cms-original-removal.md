# Withdrawn CMS run: local removal

KHJ explicitly requested complete disposal of the obsolete local CMS experiment on2026-09-13, superseding the previous raw-audit retention instruction.

Deleted the entire `analysis/CMS_original_cards_v19_v24_20260913/` tree (61 files,55,746,956 bytes) and its dedicated `docs/reports/analysis/CMS_original_cards_v19_v24_20260913/` report tree (1 file,292,970 bytes). This includes cached original inputs, responses, source snapshots, metrics, logs and the withdrawal marker. Removed the obsolete CMS entry from the report index and its navigation links from the historical summary. Do not regenerate or restore this withdrawn run as an experiment or baseline.

The current `analysis/CMS_updated_cards_v19_v24_dev200_20260913/` publication-manifest hashes were checked before and after deletion and are unchanged. The publication worktree already contained neither obsolete directory. Original `user/CMS` materials and other experiments were untouched. Historical Git commits and design/reviewer notes were not rewritten; only the obsolete working-tree experiment payload and its dedicated report were removed.

## Run navigation

[September run reports](2026-09/README.md) own each execution's current and historical judgments; this document is question-level context.
