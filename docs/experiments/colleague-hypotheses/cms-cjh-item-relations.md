# CMS/CJH item relations for redesign

Status: read-only source analysis, 2026-09-13. No new inference, prompt, repair rule or evaluator implemented. Scope is the selected CJH v10–v18 cards and CMS v19–v24 정리본; no KHJ/local decision prompts or dev labels/predictions were consulted. All 15 cards were read. This is a condition-comparison catalog, not a new hypothesis or an executable constraint system.

## Grouping decided by KHJ

Group v15/v16 in one request and v17/v18 in one request. Other items retain independent requests. CJH groups: [v10], [v11], [v12], [v13], [v14], [v15,v16], [v17,v18]. CMS groups: [v19], [v20], [v21], [v22], [v23], [v24]. At dev200 this means 1,400 CJH and 1,200 CMS requests if all notices are run once. Full input/response/reference/budget design remains unresolved; grouping approval alone is not final run approval. Joint generation does not guarantee consistent outputs.

## How to read the relations

A pair here concerns both violation values being 1. A 0 has multiple possible reasons (out of scope, satisfied condition, exemption), so a 1/0 pair is not automatically inconsistent. Necessary-condition conflicts assume the same actual purchase object/lot, qualification scope, relevant time and factual inputs. The cards do not provide an explicit multi-product/multi-lot aggregation rule; do not turn object-level exclusions into unconditional notice-level corrections. If responses concern different objects or rely on incompatible intermediate facts, record the scope/fact issue rather than silently choose a winning answer.

CJH calls for competitive/general classification before direct-production and company-size decisions in every card. P below denotes the same meta 입찰추정가격; T denotes the applicable threshold for the same notice date, contract law and contract object. Different P or T choices are themselves a shared-fact inconsistency requiring inspection.

Source paths below are relative to this document. Source citations state author text; relation classifications beyond explicit pair instructions are this audit's conditional deductions and must not be inserted into the model as additional rules.

## Complete CJH pair catalog

| Class | All pairs | Basis / limits |
|---|---|---|
| E: explicit pair exclusivity | 15/16; 17/18 | Original v15:44 and v16:44; v17:43 and v18:44 explicitly describe exclusive decisions. Both 0 is possible. |
| B: opposite product branches | 10/12, 10/14, 10/15, 10/16, 10/17, 10/18; 11/12, 11/14, 11/15, 11/16, 11/17, 11/18; 13/12, 13/14, 13/15, 13/16, 13/17, 13/18 | v10/v11/v13 require competitive products; v12/v14/v15/v16/v17/v18 require general products. Same-object and same classification scope required. 10/12 also opposes absence/presence of a direct-production qualification. |
| A: disjoint amounts | 14/15, 14/16 | P >= T versus P < T. Same applicable T required. |
| A: disjoint amounts | 15/17, 15/18, 16/17, 16/18 | P >= 100,000,000 versus P < 100,000,000. |
| S: restriction present versus absent | 14/18 | v14 requires a SME participation restriction; v18 requires no company-size restriction. Does not need an assumption that T >= 100,000,000. |
| Q: threshold-dependent | 14/17 | Amounts exclude each other if T >= 100,000,000. The selected cards do not numerically establish every applicable T. If T < 100,000,000, the two amount conditions can overlap. Do not assert an unconditional amount exclusion without the applicable source. |
| Q: category-reading-dependent | 11/13 | v11 requires absence of a SME restriction; v13 requires a small/micro-enterprise restriction. They conflict if the latter is recognized as a SME participation restriction for v11. Unlike 15/16 and 17/18, the cards do not explicitly give this pair's mapping; do not silently add one. |
| C: simultaneous violations can fit the stated conditions | 10/11 | Competitive product, no direct-production qualification, no SME participation restriction. |
| C: simultaneous violations can fit the stated conditions | 10/13 | Competitive product, no direct-production qualification, small/micro-enterprise restriction without the author-stated permission grounds. |
| C: simultaneous violations can fit the stated conditions | 12/14, 12/15, 12/16, 12/17, 12/18 | General product with a direct-production qualification can also have a separate company-size violation for the applicable amount band. v12 and v16/v18 are compatible because a direct-production requirement is not itself a company-size restriction in these cards. |

Count check: E2 + B18 + A6 + S1 + Q2 + C7 = 36, all unordered pairs among CJH's nine items. E/B/A/S are conditional on shared scope/facts as stated above; this count is not a notice-level automatic invalidation rule.

| Item | v11 | v12 | v13 | v14 | v15 | v16 | v17 | v18 |
|---|---|---|---|---|---|---|---|---|
| v10 | C | B | C | B | B | B | B | B |
| v11 | — | B | Q | B | B | B | B | B |
| v12 | — | — | B | C | C | C | C | C |
| v13 | — | — | — | B | B | B | B | B |
| v14 | — | — | — | — | A | A | Q | S |
| v15 | — | — | — | — | — | E | A | A |
| v16 | — | — | — | — | — | — | A | A |
| v17 | — | — | — | — | — | — | — | E |

Original sources: [v10 necessary conditions](../../user/CJH/판정카드(10~18)/v10.md#L10), [v11](../../user/CJH/판정카드(10~18)/v11.md#L10), [v12](../../user/CJH/판정카드(10~18)/v12.md#L10), [v13](../../user/CJH/판정카드(10~18)/v13.md#L10), [v14](../../user/CJH/판정카드(10~18)/v14.md#L10), [v15 explicit pair](../../user/CJH/판정카드(10~18)/v15.md#L44), [v16](../../user/CJH/판정카드(10~18)/v16.md#L44), [v17 explicit pair](../../user/CJH/판정카드(10~18)/v17.md#L43), [v18](../../user/CJH/판정카드(10~18)/v18.md#L44).

## CMS pairs and cross-author pairs

No fixed simultaneous-1 prohibition was established from the selected CMS cards for any of their 15 pairs, or from CMS/CJH cards for the 54 cross-author pairs. This is an absence of a justified binary constraint, not proof that every conceivable factual explanation is compatible. Together with the 36 CJH pairs this covers all 105 unordered pairs in the 15-item source scope. Items v1–v9 are outside this audit.

- CMS v22/v23 share negotiation/briefing facts, but judge different violations: forced attendance versus insufficient interval. All four binary combinations can fit the cards. Examples: forced attendance with sufficient intervals gives 1/0; voluntary attendance with insufficient intervals under local negotiation gives 0/1; forced attendance with insufficient intervals gives 1/1; no briefing gives 0/0. See CMS:179–190, 219, 234–246.
- CMS v19 concerns manufacturer/supplier/support assurance obligations; CJH v10/v12 concern direct-production certificates. Do not equate the documents and create an exclusion.
- CMS v20 concerns SW participation-regime disclosure, while CJH's size items concern actual participation restrictions under their stated classification/amount conditions. No fixed binary mapping follows. Missing disclosure is not automatically the same fact as missing every company-size qualification.
- CMS v21 and v23 share contract-law information; CMS v22/v23 share award method and briefing occurrence. Conflicting interpretations of those facts can occur even when final bits are not logically exclusive.
- CMS v24 compares specified text/meta attributes; another item finding a violation does not imply v24=1. Joint contracting, dates and clause-reason fields are explicitly excluded from v24 comparison (CMS:333), so a v21 or v23 issue does not establish v24.
- CMS v24:333 prioritizes notice-text values for other items' legal application while retaining original meta for comparison. CJH repeatedly specifies meta 입찰추정가격, especially v14:44. Preserve each author's source conditions; do not import CMS's precedence sentence into CJH inputs or silently reconcile the authors' conventions. CMS v20's VAT-inclusive project amount and CJH's estimated price also describe different attributes, not necessarily contradictory values.

Shared-fact discrepancies (product identity, product classification and special conditions, company-size category, qualifying-document presence/scope, P/T, applicable law, award method, briefing type/occurrence, or attachment availability) require examining actual outputs. Binary values alone cannot identify their cause. Do not add an intermediate-state output requirement or a new adjudication model without agreeing that design separately.

## Dev-specific notes in the selected CMS source

File: `user/CMS/판정카드v19_v24/판정카드_v19-v24_정리본.md`, v24 [주의], final three paragraphs.

| Line | ID | What the source says |
|---|---|---|
| 335 | PPS-DEV-062 | Describes an organizer-confirmed budget-axis violation as an official exception; states that VAT conversion is arithmetically consistent, the general principle does not reproduce it, and it must not generalize to other cases. This audit reports the author's statement, not independent verification of organizer confirmation. |
| 337 | PPS-DEV-071 | Gives notice/meta regional-restriction values and calls the regional-restriction axis a violation. |
| 339 | PPS-DEV-049 | Explicitly says to preserve the official label v24=1 while stating that the current material does not reproduce the discrepancy and evidence is unconfirmed. |

These are case-specific answers/discussion, not general anonymous examples. The selected CJH v10–v18 cards contain no dev-ID/official-label notes found by full reading and targeted search. The user/ original remains unchanged. KHJ subsequently instructed excluding precisely these three paragraphs from the experiment input, while preserving the preceding general [주의] paragraph at line 333 and all other card text. This source exception is settled and must be documented in the eventual experiment report; no modified input copy or new inference has yet been produced.

## Run navigation

[September run reports](2026-09/README.md) own each execution's current and historical judgments; this document is question-level context.
