# Competition constraints

Source: [규칙](https://dacon.io/competitions/official/236754/overview/rules), sections 1–5. Verified: 2026-09-10.

## Model use and independent prediction

- Every evaluated notice requires at least one successful fixed-LLM call: the prompt must contain that notice's content and receive a normal response. Unrelated or omitted calls do not satisfy this rule.
- Preprocessing, retrieval, prompting, and rule-based output correction are allowed.
- No fixed-LLM fine-tuning, including LoRA/QLoRA. No submission/loading of model weights or adapters; no participant-trained classifier, regressor, or additional embedding weights for violation decisions. `model/` is for static assets such as retrieval indexes. Organizer-provided model loading: [submission](<submission.md#models-and-runtime>).
- Predict each hidden notice independently. Splitting and combining documents within one notice is allowed; using other hidden notices' information, predictions, or statistics is forbidden.
- No hidden-test training, tuning, pseudo-labeling, or updates to models/rules.

## Data and labeling

| Allowed | Boundary |
|---|---|
| Supplied notices, dev labels, 항목표, 법령패키지 | May support development, validation, retrieval, and postprocessing; weight restrictions above still apply |
| Self-labeling supplied unlabeled notices | Manual, rules, or models; may support validation, retrieval examples, and rule tuning |
| External LLMs, including commercial APIs | Label generation only; input only competition-provided materials; no web search or external-document retrieval |
| Open-source libraries via pip | No bundled external data assets |
| Participant-created labels/processed data | Sharing and reuse through this competition's fully public 코드 공유 board; no private inter-team sharing |

- No external notice text, metadata, labels, answer information, or legal data in development/inference/submissions, including via APIs, crawling, packages, or static assets.
- Do not restore anonymized identifiers by linking, retrieving, or comparing public originals.
- No external LLM/API calls in submitted inference code.
- Legal authority is the supplied 법령패키지 snapshot, including 중소벤처기업부 고시 제2025-96호 (2025. 8. 29.). Subsequent legal amendments do not change scoring. Personal legal study is allowed; integrated legal materials must come from the supplied snapshot.

## Reproducibility and second stage

- Reproduce results using only competition-provided and submitted materials; failure can cancel an award.
- Preserve labeling code, prompts, and procedures. For external-LLM labels, submit generation code, prompts, model/version records, and generated labels; API nondeterminism in rerun outputs is accepted.
- Document provenance for all models, tools, and materials used.
- Second-stage package: score-reproduction code and execution instructions (including labeling artifacts), provenance, and team members' 성명/생년월일/성별/현재 소속. Submit to `dacon@dacon.io` using the organizer's later instructions/templates. Dates and unresolved details: [sources](<sources.md>).

## Participation and conduct

- Individual or team participation; maximum five members; no duplicate individual/multiple-team registration.
- Evaluation-data exfiltration attempts cause immediate disqualification. DACON's separate misconduct policy also applies; policy link and verification scope: [sources](<sources.md>).
- Organizer questions: use a 토크 comment with `[DACON 답변 요청]`; official answers cover competition operations and data issues.
