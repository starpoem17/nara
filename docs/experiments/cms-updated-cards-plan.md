# CMS updated-card experiment: confirmed plan

Status: KHJ explicitly approved implementation with ‘시작’ on2026-09-13 after the Astra review, candidate presentation choices, one-case token exception and empty-candidate wording were reported and settled. Proceed with implementation, preflight and the approved one-pass dev200 experiment; the earlier implementation hold is lifted. Preserve the stated hypothesis and authorization limits. The old original CMS results remain withdrawn, not valid comparison scores. The [CMS-only decision record](cms-updated-cards-decisions.md) retains chronological provenance.

## Hypothesis and inputs

- Source: CMS commit615e649e80794556f9ae2d889da99d5c41a8cba4, revised 판정카드_v19-v24_토큰수_제한.md and uploaded candidates.jsonl. Candidate SHA256:80259ee689e0b03888311d3a7fcb19cafff161be9408423317f15151f0f33c1b. Read via git objects; never edit user/.
- Use each of the six authored text blocks as its independent item prompt. Exclude the v24 line containing the PPS-DEV-062/049 official-answer memo under KHJ's explicit permission. Preserve all other criteria, examples, exception/uncertainty instructions and output wording. No imported local prompts, extra judgment rules or supplementary legal summaries.
- Use the uploaded200 records and all1,200 item candidate sets directly. Do not reproduce extraction, rank candidates, resolve historical ties, replace candidates with full notices, or select extra passages from labels. Extraction is skipped and its time is unmeasured.
- Fill the existing META placeholder with original selected field-name/value lines. Preserve null/미입력/해당 없음 and the author-required input_completeness and dropped_doc_counts, rendered as nested plain-text key/value lines. For nonempty candidate lists, fill the original-text placeholder with KHJ's subsequently specified presentation: `추출된 원문 후보는 다음과 같다. ` followed by each exact segment text enclosed in ASCII single quotes, joined by comma-space in uploaded order. This supersedes root's two-newline-only proposal. No JSON/JSONL object serialization is inserted. For an empty uploaded segments list, KHJ explicitly approved the exact placeholder text `추출된 원문 후보가 없습니다.`. This reports an empty candidate list; it does not establish absence in the original documents or prescribe a judgment.
- Candidate doc ID/type/character and line offsets, candidate_chars and budget_truncated remain preserved in the source/audit artifact. The measured prompt does not add these as model-visible headers. The final prepared-input review must show this exact representation; do not silently add provenance headers or delete source text to fit a changed representation.
- One user message with the author's text; chat generation prefix included. No separate system judgment prompt. Under KHJ's quoted-candidate presentation, the measured nonempty inputs include one breach of the author's2,000-token INPUT cap: PPS-DEV-189/v24=2,024 tokens. KHJ explicitly approved this exact24-token exception for PPS-DEV-189/v24 only, preserving all candidate text and the chosen presentation. Every other input remains subject to the2,000-token cap; no broader exception, trimming or deferral is authorized. The previous maximum1,998 applies only to the superseded two-newline presentation. Output budget is separate.

## Inference and output

- Six independent groups [v19]...[v24] for each of200 notices:1,200 first-pass requests. Generated judgments never enter another request.
- Existing agreed runtime: local Gemma4 26B A4B NVFP4; thinkingOFF; temperature0; seed0; output512; at most16 outstanding requests, refilled as completions arrive. Enable automatic prefix caching for identical input prefixes while preserving authored prompt order. Do not claim full-notice cache sharing when item prompts/candidates differ.
- The newly measured maximum input+output reserve is2,536 tokens (including KHJ's approved2,024-token exception for PPS-DEV-189/v24). The ordinary32,768 context setting suffices; the former experiment-only36,864 exception is unnecessary for these inputs. Report actual context/KV allocation, hardware/model precision and runtime observations; do not claim a larger-than-competition allocation if it was not used or evidenced.
- Match structured JSON output to the author-prescribed item-keyed object, e.g. {"v19":{"위반여부":0,"근거문구":null}}. Shape enforcement only; retain model choice of0/1 and authored evidence requirements. Do not inject a top-level 공고ID/판정 wrapper into the cards. Associate outputs with the known request notice/item during aggregation.
- One measured first pass without result-driven retries, repairs, forced judgments or invalid-output zero filling, as previously agreed. Preserve raw output and completion/error status.

## Evaluation and reporting

- Report each item's classification results against dev labels with explicit denominators, plus aggregate results and observed failures. Keep unreadable/missing/aborted outputs distinguishable from valid0/1 judgments.
- Evaluate original-quote continuity/length against the full original source documents separately from classification, preserving returned evidence. Do not treat one exact reference-string match as the only possible valid original quotation, or repair model evidence silently.
- Record model/input preparation/load/inference timing separately. Mandatory disclosure: CMS's candidate extraction was already performed and was not timed; measured latency omits that step and is shorter by that unmeasured work than the complete original-to-extraction-to-inference pipeline. No invented extraction duration or end-to-end total.
- Mandatory report disclosure of the empty-candidate presentation: “CMS는 후보가 0개일 때의 입력 표시 문구를 명시하지 않았다. 본 실험에서는 사용자의 명시적 승인에 따라 해당 입력의 [원문]에 ‘추출된 원문 후보가 없습니다.’를 표시했다. 이는 업로드된 후보 목록이 비어 있음을 나타내는 입력 형식 선택이며, 원문에 관련 내용이 없다는 판정이나 추가 판단 규칙이 아니다.” This applies to438 notice/item inputs; preserve the authored classification and uncertainty rules.
- Mandatory report disclosure of KHJ's narrow token exception: “후보 원문과 사용자 지정 표시 형식을 유지하기 위해 PPS-DEV-189의 v24 입력 한 건에 한해 2,024토큰을 허용했다. 이는 CMS가 정한 채팅 템플릿 포함 입력 상한 2,000토큰을 24토큰 초과하는 사용자 승인 예외다. 다른 입력에 대한 상한 초과는 허용하지 않았다.” Report actual final input counts and retain the actual prompt; do not broaden this permission or present the exception as CMS's original condition.
- Describe CMS's disclosed dev/label-based development provenance and KHJ-authorized answer-memo exclusion. Preserve a pre-inference source/prompt/schema/runtime manifest. No claim of an untouched holdout or universal label-blind redesign preparation.
- New run artifacts: analysis/CMS_updated_cards_v19_v24_dev200_20260913/ (or an unused date-suffixed path if needed); human-readable report under docs/reports/ with links to the artifact. Preserve historical withdrawn artifacts as audit history.
- KHJ wants colleagues to review the eventual result on GitHub. Prepare a concrete CMS-only publication payload after the run; do not publish the withdrawn combined payload as a valid experiment. Any outstanding export-review condition must be resolved against the actual new payload before upload.

## Independent review status

Astra medium completed the [independent source/plan review](../reports/cms-updated-cards-astra-fidelity-review.md) on 2026-09-13: conditionally faithful within the cached-candidate dev200 inference scope. It identifies one consequential presentation issue requiring KHJ's decision: whether to accept current two-newline joining without model-visible source boundaries, or specify an alternative boundary representation. The source requires provenance preservation but does not explicitly require exposing every provenance field to the model; the reviewer therefore does not call the omission a proven source violation. It can nevertheless affect cross-document reasoning and continuous-quotation selection. After the review and explanation, KHJ explicitly specified quoted candidate pieces and required disclosure of the actual input prompt in the experiment report. This is KHJ's experimenter-selected presentation, not a formatting rule authored by CMS. At that discussion point the plan recorded the decision and implementation had not started. Read-only remeasurement found one2,024-token input; KHJ subsequently approved this one case as a disclosed24-token exception to CMS's2,000-token input cap. Any further consequential change needs KHJ's decision. Review limitations and later verification are recorded separately in the review; they do not authorize hypothesis improvements.

KHJ's required report-before-implementation sequence was fulfilled. Source/card/candidate hashes and cardinalities were checked read-only during the review; KHJ subsequently approved implementation with ‘시작’. The historical Astra output remains unchanged.

## Sequence before inference

1. Completed: present the CMS-only plan and the later explicitly approved presentation/token choices.
2. Completed: Astra-medium review and report. KHJ resolved the stated presentation choice and accepted the scope limits; other consequential changes still require approval.
3. Approved by KHJ's ‘시작’: prepare reviewable source copies, exact rendered inputs, matching output schemas and isolated runner. Verify source alignment for all candidates/selected META, exact authorized memo exclusion, no extra judgment instructions, all1,200 rendered-token budgets, no output dependency between calls, and runtime/refill/cache instrumentation.
4. Run the approved experiment only after material review findings and preflight checks are addressed within authorization. Freeze predictions before ordinary evaluation and report the actual behavior without hypothesis edits based on outcomes.


## KHJ follow-up after Astra review

KHJ explicitly accepted both scope limits: this does not validate extraction/full-pipeline runtime, and it does not validate generalization to unseen data. KHJ requested clearer explanations of v20 completeness versus candidate truncation, and model-visible document/segment boundaries. These explanation requests are not implementation approval or approval to change fields/boundaries. The implementation hold still applied at that earlier point; KHJ later approved the completed design.

Read-only clarification facts from the immutable CMS candidate artifact and original dev records (no label lookup): v20 cases with 완전관측=true and budget_truncated=true are PPS-DEV-088 (candidate1787 chars; original23470 chars in3 docs), PPS-DEV-135 (1780;28794 in3 docs), PPS-DEV-171 (1600;44256 in2 docs). The original dev records already have the same complete-observation flags, confirming that these are inherited source-processing flags rather than statements that the model sees all original text. Truncation flags already exist in CMS's uploaded artifact; root did not perform this truncation.

PPS-DEV-088 v20's five preserved segments are D0/공고문 lines46–50, D1/과업지시서21–25 and61–65, D2/규격서11–15 and64–68. The plan reviewed by Astra passed their text in order separated by two newlines, leaving doc/type/line/character metadata in the audit artifact. Thus D1 lines26–60 are omitted without a model-visible gap annotation, and document transitions are not explicitly marked. Plain-text formatting itself does not require omission of these fields. Current META rendering passes complete-observation information; budget_truncated is kept only in the artifact. That reviewed presentation was root's choice, not specified by CMS or implied by the earlier generic plain-text approval. KHJ later specified quoted candidate pieces as recorded below. Truncation does not itself establish that a decisive clause was lost or that any prediction is wrong.


## KHJ candidate-presentation decision and read-only remeasurement

KHJ explicitly took responsibility for the unspecified candidate-joining choice: show `...는 다음과 같다. '후보1', '후보2', '후보3'` and disclose the actual input prompts in the experiment report so CMS can inspect them. Root acknowledged the concrete prefix `추출된 원문 후보는 다음과 같다. ` plus single-quoted original pieces joined by comma-space. Do not add literal candidate numbers, source headers, escaping, strip operations, reordered pieces, or rewritten source text silently. Existing internal newlines remain unchanged. This separates pieces visually without supplying document IDs/positions; do not claim full provenance visibility or guaranteed model recognition of boundaries. Raw provenance remains in the source/audit artifact. The original Astra report is unchanged historical reviewer output, not a new review of this presentation.

Read-only in-memory measurement on2026-09-13 used the same immutable CMS inputs, exact memo-line removal, META rendering, local tokenizer and chat-template settings as the earlier measurement. All1,200 baseline counts reproduced the old per-item minimum/median/maximum exactly, and every old/new chat-template input ID sequence matched an independent untruncated backend encoding. No runner, schema, frozen inputs, inference, source edits or publication were produced.

| Item | Quoted minimum | Median | Maximum | Over2,000 |
|---|---:|---:|---:|---:|
| v19 | 553 | 608 | 1707 | 0 |
| v20 | 620 | 633 | 1755 | 0 |
| v21 | 537 | 669.5 | 1684 | 0 |
| v22 | 515 | 517 | 1403 | 0 |
| v23 | 917 | 1770 | 1936 | 0 |
| v24 | 663 | 1573 | 2024 | 1 |

PPS-DEV-189/v24 contains seven candidate segments and exceeds CMS's authored input cap by24 tokens. The quoted list and candidate originals were preserved for this measurement. KHJ explicitly approved this exact24-token exception for this one notice/item while retaining candidate originals and the specified display format. Disclose it in the experiment report; do not claim universal2,000-token compliance. This does not authorize exceptions for any other input, changes to candidates, implementation or inference.

The first quoted-form sizing used the prefix with an empty suffix for empty lists. KHJ subsequently approved the exact sentence `추출된 원문 후보가 없습니다.` and required disclosure that this is a user-authorized experimenter choice, not a CMS-authored instruction. Empty candidate counts for v19..v24 are96,148,65,129,0,0 (438 total). The table above is now updated to the approved sentence following a new read-only measurement of all1,200 inputs. Actual chat-template input IDs again matched untruncated backend encoding. The438 empty inputs have respective item maxima563,645,547,527; none exceed2,000 tokens. PPS-DEV-189/v24 remains the only exception at2,024. No further cap exception is needed or authorized. KHJ subsequently approved implementation with ‘시작’; this no longer blocks execution.


## Execution status

The approved first pass and evaluation completed on2026-09-13. All1,200 requests completed normally; predictions were frozen before labels were evaluated. See the [run report](../reports/analysis/CMS_updated_cards_v19_v24_dev200_20260913/report.md) and its linked immutable inputs, raw outputs, source alignment, timing and per-case results. No result-driven prompt, candidate, judgment or retry change was made. CMS-only results and reproduction files are packaged for GitHub review.

Implementation modules: `src/experiments/cms_updated_cards.py` (prepare/run), `src/experiments/cms_source_alignment.py` (independent original-source checks), and `src/evaluation/cms_updated_cards.py` (post-freeze evaluation/report). The original execution audit and a later reproduced audit are retained separately; `audit_reproduction.json` records byte-identical restoration of the execution audit after a reproduction overwrote its path. The execution audit hash again matches run_summary; predictions, manifest and run_summary were never changed.
