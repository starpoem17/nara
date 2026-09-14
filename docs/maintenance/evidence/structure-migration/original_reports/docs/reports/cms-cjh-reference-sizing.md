# CMS/CJH reference-input sizing — proposal for KHJ review

**Historical sizing; superseded for the current design.** KHJ has adopted CMS's revised standalone cards and pre-extracted candidates, and explicitly rejected using data/항목표.json as a source for CJH reference selection. The mixed organizer-table/card bundles and their totals below are retained as prior measurements, not approved input compositions or current context requirements. Use the [active redesign interview](../experiments/cms-cjh-redesign-interview.md) for current decisions.

Measured 2026-09-13. KHJ requested lengths before deciding the legal-reference composition. No new hypothesis inference, GPU model load, schema/runner implementation, source edit or final input freeze was performed. Full-catalog provision and an experiment-only context/KV extension were already approved; numerical settings and this reference composition remain provisional.

## Main result

With per-group legal references and whole selected author cards, the largest raw-component sum is **65,330 tokens for CMS v21** and **80,183 for CJH v11**, using complete parent articles for citations that mention a specific paragraph. The alternative that retains only explicitly cited paragraphs has the same CMS maximum and a CJH maximum of 79,936.

These are sums of separately tokenized source components, not final chat-template prompt lengths. The counting deliberately excludes a not-yet-agreed instruction wrapper, input schema text/formatting and output reserve. It must not be reported as an executed prompt or demonstrated GPU capacity.

## Counting assumptions made visible

- Tokenizer: local Gemma4 tokenizer.json, with saved 8,192-token truncation disabled, padding disabled, special tokens disabled. No model generation. The detailed record stores tokenizer and input-source hashes.
- All 200 original dev records were measured as json.dumps(record, ensure_ascii=False), retaining every supplied field/document for sizing. Maximum: PPS-DEV-169, **33,633** raw tokens. This serialization is an explicit sizing convention, not a frozen inference format.
- Each call is assumed to contain its author's entire selected card source. CMS removes precisely the three KHJ-specified v24 case paragraphs and preserves other source text: **3,905** tokens. CJH v10–v18 combined: **5,616**.
- CJH includes the full organizer competitive-product CSV, header, all 616 rows/columns and special conditions: **34,386** tokens. The selected CJH v10–v18 cards call for this comparison. The selected CMS v19–v24 cards and their organizer-table references do not call for competitive-product-list comparison; CMS receives no CSV. KHJ correctly challenged the unnecessary CSV-in-CMS alternative, which root withdrew. Recipient scope is settled; the unrelated alternative must not drive the context requirement.
- Each group uses the union of its target items' organizer-table references plus explicit citations in those target cards. Both national/local references are present; no per-notice law-selection decision was made. CJH's explicit SW Act article48 is included in all its groups. Source metadata headers are retained once per file, overlapping source spans are merged, and original text within each span is unchanged. A newline separates spans for the law-bundle count.
- A named law with no unit specified is counted as the whole supplied text file: CMS v20 SW Act; CMS v21 national Joint Contract Operation Guidelines. Specified chapters/sections/tables include their entire designated unit, including the local chapter6 attachments. The v19 local caution item is exactly its cited numbered item within chapter1/section1.
- Two paragraph scopes are calculated. **Literal** retains the specified paragraph and its article heading; **Article** includes the complete containing article. This difference affects CJH v11/v13 (Act7(1)), CJH v14–v18 (Decree2-2(1)), and CMS v22 (deleted paragraphs6/7 of article43). Neither option has been silently selected for the run.

## Per-group lengths

The last column includes the maximum notice + whole author cards + target-group laws + CSV for CJH. It excludes final formatting and output reserve.

| Author | Group | Laws: literal paragraphs | Laws: full parent articles | Maximum raw-component sum: full articles |
|---|---|---:|---:|---:|
| CMS | v19 | 5,759 | 5,759 | 43,297 |
| CMS | v20 | 21,871 | 21,871 | 59,409 |
| CMS | v21 | 27,792 | 27,792 | 65,330 |
| CMS | v22 | 402 | 2,161 | 39,699 |
| CMS | v23 | 4,338 | 4,338 | 41,876 |
| CMS | v24 | 0 | 0 | 37,538 |
| CJH | v10 | 3,182 | 3,182 | 76,817 |
| CJH | v11 | 6,138 | 6,548 | 80,183 |
| CJH | v12 | 5,878 | 5,878 | 79,513 |
| CJH | v13 | 5,250 | 5,660 | 79,295 |
| CJH | v14 | 6,301 | 6,546 | 80,181 |
| CJH | v15/v16 | 6,301 | 6,546 | 80,181 |
| CJH | v17/v18 | 6,301 | 6,546 | 80,181 |

## Reference units behind the table

Names below are shorthand for the exact source paths/line spans and hashes in the [measurement record](../experiments/cms-cjh-reference-sizing.json). This is a source-size inventory, not legal advice or an additional decision rule.

| Group | Counted references |
|---|---|
| CJH v10 | SME Procurement Act9; competitive-product designation notice entire text; SW Act48 |
| CJH v11 | National Decree21; Local Decree20; SME Procurement Act7(1) / whole7; designation notice entire text; SW Act48 |
| CJH v12 | National Decree21; Local Decree20; designation notice entire text (organizer v12 비고 points to the competitive-product notice); SW Act48 |
| CJH v13 | National Decree21; Local Decree20; SME Procurement Act7(1) / whole7; author-cited Act7-2; SW Act48 |
| CJH v14, v15/v16, v17/v18 | National Decree21; Local Decree20; SME Procurement Decree2-2(1) / whole2-2, whole2-3; SW Act48 |
| CMS v19 | National Decree12, Rules17, Government Procurement Guidelines5-3; Local Decree13, Rules17, Local Procurement Guidelines chapter1/section1/item7 |
| CMS v20 | SW Act entire supplied file; SME SW participation guidelines article2 and annex1 |
| CMS v21 | Joint Contract Operation Guidelines entire supplied file; Local Procurement Guidelines chapter6 entire text including chapter contents and attachments |
| CMS v22 | National Decree43(6) and Local Decree43(7) deletion markers / respective whole43 articles |
| CMS v23 | Local Decree35; Local Award Guidelines chapter7/section3 |
| CMS v24 | None specified by the organizer table |

## Alternative: common author-wide legal bundle

This is a separate measured option, not an instruction to merge prediction groups. It gives every group all selected legal references for that author, retaining whole original cards. Overlapping source spans are included once.

| Author | Laws: full parent articles | Maximum raw-component sum |
|---|---:|---:|
| CMS | 61,110 | 98,648 |
| CJH | 9,637 | 83,272 |

The main design proposal has so far been item/group-specific law attachment. The author-wide legal bundle above is a separate sizing option only; it does not add a competitive-product CSV to CMS.

## Items not silently filled in

1. The sole supplied notified-amount document is **1,402** raw tokens, measured separately. It has not been folded into the main totals as if it established the correct threshold for every notice date, contract law and object. If attached in full, its source-token contribution is 1,402 (plus final formatting); current/historical applicability still needs checking.
2. Literal citations do not include every recursively referenced statute/annex. For example, CMS discusses annual-average handling for maintenance, while the organizer's v20 reference specifically names guideline article2 and annex1; guideline article3 is outside that literal scope. This sizing does not prove the provided reference set is sufficient to execute every condition in the card.
3. The current v22 source contains deletion markers, not the deleted original attendance provisions. Enlarging the parent article or context does not recover missing text.
4. Statute publication/effective dates are preserved in source headers. No source was presumed historically applicable merely because it was available in the package.
5. Qualitative phrases such as other permitted grounds are not converted into extra experimenter-selected rules or recursively selected source documents.

## Context and verification

For the measured **per-group** composition, **98,304** is a possible context setting with room beyond the measured maximum; this is a sizing candidate only. The **author-wide law** alternative already exceeds 98,304 for CMS before wrapper/output, so **131,072** is a possible sizing candidate for that alternative when CMS has no CSV. Additional sources, final prompt rendering, output reserve and actual GPU fit must be checked before fixing either value. Model config states 262,144 maximum positions; it does not establish GPU KV capacity or sustained 16-request concurrency.

The measurement record was reconstructed from original line spans: **248 span hash/token checks and 30 bundle hash/token checks matched**. No source text was rewritten. Full provided legal-text corpus inventory is also stored there (23 files, 1,209,153 separately counted raw tokens); that whole-corpus inventory is not the proposed input.
