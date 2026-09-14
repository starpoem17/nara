Artifacts: [run directory](<../../../../../output/experiments/v9-cod-fewshot5-v3-20260912>). Unlinked artifact names below are relative to that directory.

# CoD few-shot random-five style probe

Success: 1/5. Prediction seconds: 6.581.

First attempt: nonempty native thinking, both item labels, every nonempty line begins v9:/v19: and contains <=5 whitespace words; natural end before256; valid JSON, no retry/length stop. Five of five required.

Few-shot placement/prompt and batch5 differ from archived batch16. Five fixed random records assess format, not generalization.

PPS-DEV-16 — 0 body tokens, success=False

```text

```

PPS-DEV-175 — 254 body tokens, success=False

```text
*   Item v9: Check for unjustified brand/model/spec restrictions on the equipment (살수차/16톤).
    *   Item v19: Check if manufacturer/supplier assurance is required before the bid deadline.

    *   Subject: 공공기관 여름철 폭염대응 도로 살수차 임차용역 (Public agency summer heat response road water sprayer rental service).
    *   Equipment: 살수차(16톤) 3대 (3 units of 16-ton water sprayers).
    *   Specifications (from [과업지시서:D1] and [별지2]):
        *   Water tank capacity: 15,000L or more.
        *   Engine: 4-cylinder 4-cycle (diesel) or more, output 150PS/2,000rpm or more.
        *   Sprayer: Front (400L/min, 20 deg), Side (400L/min, 10bar, 5m).
        *   Vehicle: 5th grade exclusion, DPF attached, no illegal modification.
    *
```

PPS-DEV-111 — 55 body tokens, success=True

```text
v9: Excavation service (investigation).
v9: No specific brand/model mentioned.
v9: No restriction on products.
v9: No violation.
v19: No manufacturer assurance requirement.
v19: No violation.
```

PPS-DEV-055 — 254 body tokens, success=False

```text
- v9: Check for unjustified brand/model/spec restrictions.
- v19: Check for unlawful manufacturer/supplier assurance requirements (pre-bid issuance).

- Document: [공고문:D0]
- Content:
    - "공기업 해운부문 외부사업 운영 지원 및 감축사업 활성화 용역(제한경쟁·1억원미만)"
    - "계약방법: 제한경쟁"
    - "입찰방법: 제한경쟁(총액), 협상에 의한 계약"
    - "수 량: 1식(과업지시서 참조)"
    - "납품기한: 계약체결일로부터 2026.11.30.까지"
    - "하도급: 본 사업은 하도급을 불허합니다."
    - "입찰보증금: ... (생략) ... 입찰보증금의 납부는 면제하되, 입찰보증금 지급각서를 제출하여야 합니다."
    - "제출서류: ... (생략) ..."
    - "입찰참가자격: ... (생략
```

PPS-DEV-31 — 106 body tokens, success=False

```text
v9: Target: artificial turf removal/recycling.
v9: Requires specific equipment (specialized separation equipment).
v9: Equipment ownership/lease requirement.
v9: No specific brand/model restriction.
v9: No violation.
v19: Safety/health evaluation mentioned.
v19: Safety/health evaluation follows award.
v19: Evaluation occurs after award.
v19: No pre-bid assurance requirement.
v19: No violation.
```
