# WITHDRAWN: CMS/CJH original-card experiment — historical plan

Historical implementation/command details below describe the recorded study. Current execution uses [operations](../../operations.md); archived entrypoints are disabled and future executions require a fresh run.

Current scope: historical withdrawn design/observations. CJH redesign is cancelled; original CMS evidence was explicitly deleted. No legacy command below is an active execution instruction. [Current study status](cms-cjh-redesign-interview.md) and the linked canonical run reports govern reuse.

Status: superseded by KHJ’s withdrawal and redesign instruction on 2026-09-13. This is a historical decision record, not authorization to repeat or publish the run as valid hypothesis verification. The user previously confirmed execution and GitHub publication on 2026-09-13; requested an Astra medium fidelity review before execution. Both measured suites and frozen evaluation are complete; see [results](<cms-cjh-original-results.md>). The review conditions were closed before measured inference. This is an observation of the supplied hypotheses under explicit integration conditions, not prompt optimization or a claim of independent validation.

## User decisions

- KHJ is the user; CMS and CJH are the hypothesis authors. Preserve their words and criteria; do not improve, merge, reinterpret, or replace them with local prompts, KHJ/LJM hypotheses, heuristic judgments, or existing rule modules. `user/` is read-only.
- CMS: use only `user/CMS/*/판정카드_v19-v24_정리본.md`, including its v24 notes about PPS-DEV-062, PPS-DEV-071 and PPS-DEV-049. The user was informed these notes contain dev-specific answer information and explicitly retained the complete selected source. Do not import the other CMS document's rules or examples.
- CJH: use the complete authored `user/CJH/판정카드(10~18)/v10.md` through `v18.md`.
- One card per independent conversation: CMS v19–v24 = 6 requests/notice; CJH v10–v18 = 9 requests/notice. All 200 dev notices, input order preserved, every item called regardless of candidate/eligibility flags: 1,200 CMS and 1,800 CJH first-pass requests.
- Maximum 16 active requests; refill completed slots without waiting for the entire batch. Reuse the same notice text's prefill cache; never pass one feature's answer into another. Preserve source-first, bounded cross-notice scheduling of the baseline as execution infrastructure only.
- Replace live model RAG with preattached organizer-package original text: laws/threshold notices fixed per item, competitive-product candidate rows and their special notes selected per notice. Final product classification, amount/exception applicability and violation judgments remain with the model.
- The competitive-product selection/delivery mechanism is our experimental choice, not a CMS/CJH-authored instruction. User explicitly requires this distinction in the reports. Explain how selection can omit a relevant row or include irrelevant rows; freeze and publish the actual selected rows and provenance. Do not claim this tests the authors' unspecified retrieval implementation.
- Local Gemma 4 26B A4B NVFP4, thinking OFF, temperature=0, seed=0, context=36864 (experiment-only exception below; originally 32768), output=512, max sequences=16. One measured first pass. No output-driven retry, correction, forced judgment replacement, zero filling or post-result tuning.
- Preserve raw requests/responses and all failures, including format errors, length stops and invalid evidence. Separate reference preparation, model load/warmup and measured inference time. No evidence cleanup in stored predictions.
- The CMS output directory was subsequently deleted at KHJ's request. The other historical output used `analysis/CJH_original_cards_v10_v18_20260913/` directories. Reports mirror these below `docs/reports/analysis/` under repository rules; publish run artifacts, raw outputs, metadata, reproducibility code and report links on GitHub.

## Minimal integration instructions

The only new instruction text proposed and approved is:

> 제공된 공고와 참고자료를 사용해 아래 판정카드의 항목을 판정하세요. 응답은 위반여부(0 또는 1)와 근거문구(문자열 또는 null)를 담은 JSON 하나로 작성하세요.

Use the literal JSON keys `위반여부` and `근거문구`. No added legal advice, decision ordering, CoD, few-shot examples, reasons/explanations field, original-project system prompt, RAG control text, rejection hint or recovery instruction. No guided-decoding grammar was requested; use raw generation to retain observable format behavior. Preserve all card text, even ambiguity or an apparent contradiction; observe the model's response instead of resolving the author's meaning in code.

## Input and preparation contract

- Input allowlist: original notice ID, `meta`, full `docs` text/type/doc_id, `input_completeness` and `dropped_doc_counts` (CMS v20 explicitly refers to attachment completeness). Do not truncate, summarize, normalize or rewrite notice text. Serialize metadata without altering values and place document text verbatim, avoiding unnecessary JSON escapes.
- Input layout: approved neutral instruction, common notice input, then reference materials and the current card. Preserve exact common prefix across a notice's feature requests. Any common competitive-product attachment for CJH can be included before its item-specific suffix; it is reference data, not a precomputed classification.
- Reference selection may read original cards and unlabeled notice content/metadata, organizer `data/법령패키지/`, and the supplied item table as a citation locator only. It must not import any local prompt, interpreted criteria file, old law-selection artifact, previous predictions, errors, scores, or `data/dev_labels.csv`.
- Freeze law source paths/spans, original text and source hashes. Include necessary referenced conditions/exception text rather than restating a rule. Preserve source dates/versions; do not manufacture missing historical thresholds or resolve contradictions with new legal interpretation. Document source coverage limits.
- Freeze the candidate selection procedure before reading labels or generating judgments; retain row numbers, complete row values/special notes, source hash, and the observable input match/retrieval basis. A candidate is not an asserted competitive product. Do not generate eligibility/violation flags as selector output, reject unmatched notices, or suppress any feature call.
- Prepare and count all 3,000 exact rendered requests before GPU inference; snapshot and hash original cards, inputs, references, settings and implementation. Raw source input measured up to 28,866 Gemma tokens before cards/references/template. The entire product CSV is 33,768 tokens/616 rows. Do not silently shorten materials to fit; investigate any overflow before execution and disclose any additional choice that changes supplied content.

## Evaluation and review

- Read labels only after predictions and input/reference hashes are frozen. Evaluate only the colleague's assigned items; do not fill the remaining competition columns or claim a full 24-item submission.
- Preserve strict JSON-format status separately from readable judgments. Reading one complete JSON code fence is permissible as parsing only if declared before inference; no extraction from arbitrary commentary, JSON repair or evidence/judgment replacement. Record stop reason, missing/extra fields, invalid types and truncated responses.
- Report per-item TP/FP/FN/TN, precision/recall/F1, valid/invalid counts, evidence substring/absence-field violations, representative and complete error cases, cross-item contradictions as observations, first-pass duration, throughput, token counts, cache reuse and concurrency/refill evidence. Report evaluation denominators and invalid-positive counts; no invalid output becomes normal=0.
- CMS v24 already contains selected dev answer information; make this visible in the report and case analysis. Do not erase it from the approved source or mistake it for newly supplied label leakage.
- Astra medium reviewer should compare this plan directly with both authors' selected source text and flag concrete contamination, undisclosed integration choices or claims that cannot be made. Review is independent of reference selection and implementation. Necessary fidelity fixes are within authorized scope; changes to agreed content/experimental conditions must be surfaced to KHJ.

## Publication

Git remote: `https://github.com/starpoem17/nara.git`. User authorized publication after experiment. Use a `starpoem/` branch and publish a reviewable commit/PR with report links. Do not change `user/`, root README, existing frozen experiments or unrelated source. Keep shared datasets/model weights local; retain actual model requests as approved experiment evidence, consistent with earlier published runs.

## Approved context exception after exact preflight

On 2026-09-13 KHJ explicitly approved context=36,864 for these two runs only. The exact 3,000-request preflight at the former 32,768 ceiling found 12 CMS and 95 CJH overflows; maximum input+512 was 34,983 CMS / 35,897 CJH. No source/card/reference text was shortened. Preserve the draft preflight evidence. The normal engine and all other pipelines retain 32,768. The experiment subclass alone opts into 36,864, within the local checkpoint's 262,144 native context.

Server context remains 32,768; local environment freedom was verified on official evaluation/rules pages on 2026-09-13. These are local original-hypothesis observations and not a server-compatible submission claim. Sources: https://dacon.io/competitions/official/236754/overview/evaluation and https://dacon.io/competitions/official/236754/overview/rules .

## Frozen implementation and verification entry points

- `experiments/legacy_CJH_original_cards_v10_v18_20260913/code/colleague_cards.py`: `select`, `prepare`, `run`. The run refuses existing responses and verifies both frozen manifests before loading the model. `select`/`prepare` refuse overwriting frozen artifacts. A separate clean experiment checkout is required for a new run; do not remove these published results to reuse their directories.
- `experiments/legacy_CJH_original_cards_v10_v18_20260913/code/verify_colleague_cards.py`: verify every original source span, input field, selected CSV row and actual rendered input token ID. No labels.
- `experiments/legacy_CJH_original_cards_v10_v18_20260913/code/audit_colleague_runtime.py`: verify both completed suites, one request per item/notice, 512 output cap, independent seed/follower ordering, admission limits and completion-driven refill; freeze response hashes before labels. No labels.
- `experiments/legacy_CJH_original_cards_v10_v18_20260913/code/evaluate_colleague_cards.py`: verify both completed suites and input hashes, then read labels and write detailed reports/CSV/JSON. Evaluation is repeatable from these saved responses; it never generates new judgments.

Use `uv run --locked python -m nara.experiments.colleague_cards run` for generation in the separate fresh result checkout; follow with `uv run --locked python -m nara.tools.audit_colleague_runtime` and `uv run --locked python -m nara.evaluation.colleague_cards`. Launcher environment: `OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MAX_JOBS=2`. The first initialization attempt used the virtualenv Python directly but omitted its binary directory from PATH, so FlashInfer could not find the already-installed `ninja`; it generated zero dev requests. Its log and metadata are preserved. Using `uv run --locked` fixed that path without any code, prompt or dependency change.

Post-evaluation descriptive reporting: `uv run --locked python -m nara.evaluation.describe_colleague_outputs` inventories output shapes and annotates report limitations without changing the frozen primary evaluator or rescoring.
