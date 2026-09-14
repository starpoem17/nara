Artifacts: [run directory](<../../../../../output/experiments/v9-cod-comparison-20260912>). Unlinked artifact names below are relative to that directory.

# Thinking behavior and interpretation

First responses: ON 200/200 at256 budget-counted tokens (254 body +2 channel-label tokens). CoD 182/200 at256,17 empty-body channels,1 unframed repetitive response ending at total512. No nonempty CoD draft ended below the budget. The17 empty-body first responses all have gold v9=0/v19=0; observed after evaluation, not a routing rule.

CoD mean232.30 body tokens excludes the unframed response (n199); median/p95/max254. ON mean/median/p95/max254 (n200). The apparent reduction is skipping thinking for some records, not compression into short drafts. Every nonempty framed thinking response in both arms consumes254 body tokens. The runtime parser reports thought for an empty channel; token-ID-based analysis corrects this artifact. Budget-boundary classification is inferred from exact spans and engine source, not a captured forced-end flag.

Both modes mostly restate task, metadata and document inventories in prose/bullets. Korean present in179/182 nonempty CoD first outputs. Line-word mean10.61 ON vs11.17 CoD; five-or-fewer-word line share40.18% vs35.43%. Format proxies only: escaped newlines normalized and list prefixes removed; not semantic step segmentation.

ON1 length stop vs CoD6. All resolved;200 final records each, no searches. CoD required one outer same-budget rerun for152 after normal retries; ON required none. Total inference including retries/recovery210.68s ON vs220.64s CoD (+4.73%). Both new modes include raw-output capture overhead. Archived OFF152.52s had no raw-output observer.

CoD vs ON v9 removes4 FP/adds3 FP (TP unchanged5); v19 recovers2 TP (033,036), adds4 FP/removes2 FP. Both ON modes return0 for051, whose supplied documents did not support the gold positive. On023, standard ON cites the DJI battery for v9; CoD cites supplier-assurance requirements for both v9/v19. CoD positive evidence missing13/18 v9 and6/13 v19 vs ON6/19 and3/9. Exact substring checks pass for saved quotes, but this does not establish semantic relevance.

Conclusion: this zero-shot CoD instruction did not establish draft-style reasoning or justify cutting thinking to64/128. A lower cap would truncate the observed thinking of182/200 first CoD responses; accuracy at that cap is unmeasured. No lower-budget runs were performed. A follow-up could test a neutral synthetic draft example for style adherence before reducing budgets; do not use dev labels as demonstrations.

Paper: [Chain of Draft](https://arxiv.org/html/2502.18600v2). New ON arms differ only by42-token system suffix; matched source/data/schema/model/limits and batches16. ON then CoD once each, cache reset, identical warmup. Not a causal/holdout claim.

Actual Gemma thinking excerpts, PPS-DEV-01:

on: The user wants me to audit a specific item (or items) based on the provided law snapshot and documents.

cod: The user wants me to audit a specific set of items (v9 and v19) based on the provided documents.
