# CJH Dev18 notified-amount date audit

Checked 2026-09-13 at KHJ's explicit request to analyze Dev18 labels and determine whether the January 2/8 date difference materially affects this dev200 experiment. This is a source/label audit, not an inference experiment.

## Finding

The identified notified-amount revision does not change the monetary decision boundary. The old and new official texts contain the same 35 amount entries. Their numbered main bodies match after removing whitespace and substituting the minister's name (기획재정부장관 → 재정경제부장관). The organizer-supplied file's main body matches the new official main body. The amendment reason describes government-organization/name changes. This resolves root's specific concern that the January 8 header implies a changed amount for the January 2 notice; it is not a survey of every legislative change in that interval.

## Dev18 evidence

- Notice: PPS-DEV-18, 2026-01-02, 지방계약법, 물품(내자), LPG supply.
- META estimated price: 204,246,000 KRW; VAT-inclusive budget: 224,670,600 KRW.
- Original qualification section 3라 explicitly requires a 소기업 or 소상공인 certificate. Section8가 itself describes the award rule as 추정가격이 고시금액 미만인 물품.
- Official labels: v14=0, v15=1, v16=0; every other CJH item v10–v18 is0. The sole positive across v1–v24 is v15. Its e15 quotes the certificate qualification.
- Under CJH's authored v15 meaning, the positive label is case-level evidence for the 1억원 이상·고시금액 미만 branch and an impermissible small-business-only restriction. It cannot identify the exact historic threshold by itself.
- The independently retrieved old and new WTO goods/services amounts are both230,000,000 KRW. Thus 100,000,000 ≤ 204,246,000 < 230,000,000, with25,754,000 KRW to the upper boundary. This is consistent with the label triplet(0,1,0) under the authored card conditions; it is not an observed model prediction.
- All200 dev dates were checked without consulting their labels for case selection: only Dev18 precedes2026-01-08. Its reference-date issue therefore does not establish a dev200-wide monetary-rule problem.

## Official evidence

- [Old original: notice2024-42, effective2025-01-01](https://www.law.go.kr/LSW/admRulInfoP.do?admRulSeq=2100000251078).
- [New original: notice2026-439, effective2026-01-08](https://www.law.go.kr/LSW/admRulInfoP.do?admRulSeq=2100000272620).
- [New revision reason/document](https://www.law.go.kr/LSW/admRulInfoP.do?admRulSeq=2100000272620&urlMode=admRulRvsInfoR).
- [Exact retrieved text, source URLs/hashes and comparisons](../experiments/cjh-dev18-notified-amount-audit.json). The dynamic content endpoints were read directly because browser-tool opening sometimes returned the surrounding UI or an error. No official-text conflict was silently repaired. The revision payload also includes an inherited2025 commencement clause; no additional applicability interpretation was imposed on the experiment from that clause.

## Experimental boundary

KHJ explicitly authorized analyzing Dev18's label for this question. Record this label exposure; do not claim that all redesign research preceded label access. Only Dev18's label values were selected/analyzed. These observations, label/evidence text, audit deductions and external historical text are documentation, not authorized additions to model prompts. CJH cards, provided data, labels and runtime settings remain unchanged. The earlier proposal to acquire external originals as model inputs remains unapproved; this factual audit removes the reason to make that a prerequisite based solely on the January8 header. It does not imply that differently formatted/differently dated prompts must produce identical model responses. Final experiment design agreement and other unresolved decisions still apply.
