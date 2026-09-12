# Prediction task

Source: [개요](https://dacon.io/competitions/official/236754/overview/description), sections 설명 / 대회 방식. Verified: 2026-09-10.

- Competition: `236754`, 나라장터 자체입찰 공고 법령 위반사항 모니터링 AI 경진대회.
- Unit: one procurement notice, including 공고문, attached-document text, and 나라장터 registration metadata.
- Output: binary violation decisions and supporting text for each of 24 review items. Exact CSV contract: [submission](submission.md#output).
- Items 1–23 concern legal violations; item 24 checks consistency between document content and registration values. Item definitions and legal references come from the supplied 항목표; do not infer them from item numbers.
- Provided development material: 20,000 unlabeled notices, 200 labeled `dev` examples, and supporting files. No separate labeled training dataset is supplied. Permitted labeling: [constraints](constraints.md#data-and-labeling).
- Deliverable: an inference pipeline executed on hidden evaluation data, using the organizer's fixed LLM. Model and runtime identifiers: [submission](submission.md#models-and-runtime).
- Competition progression: leaderboard selection, then reproducibility and evidence review; final awards go to seven teams. Detailed scoring: [evaluation](evaluation.md).
