# CMS updated-card study: KHJ decisions

The [experiment plan](<cms-updated-cards-plan.md>) governs the implementation. This CMS-only record distinguishes author instructions from KHJ's explicit experimental choices.

| Decision | Authorization and scope |
|---|---|
| Author source | CMS commit615e649e80794556f9ae2d889da99d5c41a8cba4; revised standalone v19–v24 cards and uploaded candidates.jsonl |
| Cached extraction | KHJ instructed skipping extraction and using the uploaded JSONL directly. Extraction timing and the complete original-to-prediction pipeline are not validated. |
| Answer memo | KHJ allowed excluding answer memos. Only the revised v24 line containing PPS-DEV-062/049 is removed; other card content is retained. |
| Placeholder representation | KHJ chose plain-text META and original candidates at the author's existing placeholders, rather than JSONL object serialization. |
| Joining pieces | CMS did not specify the model-visible join representation. KHJ chose `추출된 원문 후보는 다음과 같다. '후보1', '후보2', '후보3'`, retaining each piece's exact text and uploaded order. Document identity/positions remain in the artifact without added model-visible headers. The actual prompts must be reported. |
| Empty candidates | CMS did not specify this display wording. KHJ approved `추출된 원문 후보가 없습니다.` for empty segment lists and required disclosure of this user-authorized choice. It describes the candidate list, not a judgment about the original document. |
| Input cap exception | KHJ approved PPS-DEV-189/v24 at2,024 input tokens only,24 above CMS's2,000-token input cap including chat formatting. Preserve candidates/display and disclose the exception. |
| Independence and outputs | Six independent calls per notice, literal item-keyed JSON output, shape enforcement only. No result-driven repairs, retries or invalid-output zero filling. |
| Runtime | Previously agreed local NVFP4 Gemma, thinkingOFF, temperature0, seed0, output512, at most16 requests with completion-driven refill and identical-prefix caching. |
| Interpretation | KHJ accepted that dev/answer-developed cards and candidates do not validate unseen-data generalization, and that skipping extraction does not validate the extractor or total pipeline runtime. |
| Review and start | The [Astra medium review](<cms-updated-cards-astra-fidelity-review.md>) was reported before implementation. After settling the subsequent choices, KHJ explicitly answered `시작` to the implementation-start question. |
| Sharing | KHJ requested GitHub publication so CMS can inspect the actual experiment and prompts. |

No other hypothesis improvement, passage selection, legal supplementation or judgment rule was authorized or introduced. The previous original CMS experiment was withdrawn as hypothesis evidence; its scores are not used as a baseline.

## Run navigation

[September run reports](2026-09/README.md) own each execution's current and historical judgments; this document is question-level context.
