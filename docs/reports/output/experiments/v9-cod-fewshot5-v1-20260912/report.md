Artifacts: [run directory](<../../../../../output/experiments/v9-cod-fewshot5-v1-20260912>). Unlinked artifact names below are relative to that directory.

# CoD few-shot random-five style probe

Success: 0/5. Prediction seconds: 6.733.

First attempt: nonempty native thinking, both item labels, every nonempty line begins v9:/v19: and contains <=5 whitespace words; natural end before256; valid JSON, no retry/length stop. Five of five required.

Few-shot placement/prompt and batch5 differ from archived batch16. Five fixed random records assess format, not generalization.

PPS-DEV-16 — 254 body tokens, success=False

```text
*   Target: [v9] Unjustified brand/model/spec restrictions on purchased goods/components.
    *   Target: [v19] Manufacturer/supplier assurance required at bid/proposal or issuance before bid unlawful.

    *   Item: 2026학년도 [수요기관(초등학교)] 통학차량 임차용역 (School bus rental service).
    *   Scope: 2 vehicles (45-seater 1, 25-seater 1).
    *   Vehicle requirement: "차량은 계약 종료일 기준으로 차령이 9년 이내(2018.3.1.이후 출고된 차량)" (Vehicle age within 9 years by contract end date).
    *   Compliance requirement: "본 입찰에 의해 계약자로 선정된 자는 ... '어린이 통학버스' 요건을 갖추어 [기관(경찰기관)]에 「어린이 통학버스」로 신고를 하여야 하며, 그 비용은 계약자로 선정된 자가 부담 함." (The selected contractor must report as an "Children's School Bus" to the police station... at their own expense
```

PPS-DEV-175 — 0 body tokens, success=False

```text

```

PPS-DEV-111 — 254 body tokens, success=False

```text
The user wants me to audit a specific notice (PPS-DEV-111) for violations related to two specific rules:
1.  `v9`: Unjustified brand/model/spec restrictions on purchased goods/components.
2.  `v19`: Unlawful requirement for manufacturer/supplier assurance at bid/proposal or issuance before bid.

**Notice Analysis:**
- **Project Name:** [수요기관(기초자치단체)|지역=r1] 고분군1 26·27호분 발굴 조사 용역 (Excavation investigation of ancient burial mounds 1 26/27).
- **Type:** General Service (용역).
- **Budget/Price:** 200,000,000 KRW (Estimated price 181,818,182 KRW).
- **Law:** 지방계약법 (Local Government Contract Act).
- **Location Restriction:** 경상남도 (Gyeongsangnam-do).
- **Qualification:** 매장유산 조사기관(육상발굴조사) (Buried Heritage Investigation Agency - Land Excavation).

**Item v9
```

PPS-DEV-055 — 254 body tokens, success=False

```text
*   Goal: Audit the provided notice for two specific violations:
        *   `v9`: Unjustified brand/model/spec restrictions on goods/components.
        *   `v19`: Unlawful requirement for manufacturer/supplier assurance (issuance before bid/proposal).
    *   Input: A notice for a service contract (용역) regarding "공기업 해운부문 외부사업 운영 지원 및 감축사업 활성화 용역".
    *   Constraints: Use only the provided text. Check applicability. `v9` is about product/spec restrictions. `v19` is about timing of assurance.

    *   `v9` (Unjustified restrictions):
        *   The contract is for a "용역" (Service/Consulting/Support), not a physical product/component purchase.
        *   The scope is "공기업 해운부문 외부사업 운영 지원 및 감축사업 활성화 용역".
        *   The "수량" is "1식(과업지시서 참조)".
        *   The notice does not mention any specific brand, model, or component restrictions for a product. It's a service contract.
```

PPS-DEV-31 — 254 body tokens, success=False

```text
*   Goal: Audit the provided notice for unjustified brand/model/spec restrictions (v9) and unlawful manufacturer/supplier assurance requirements (v19).
    *   Law: 지방계약법 (Local Government Contract Act).
    *   v9 (Unjustified restriction): Check if specific brands/models/specs are mandated without justification.
    *   v19 (Assurance requirement): Check if manufacturer/supplier assurance is required *at the time of bidding* or *before the bid deadline*.

    *   Notice ID: PPS-DEV-31
    *   Subject: 인조잔디 분리회수 및 재활용 처리 1식 (Artificial turf separation and recycling treatment).
    *   Budget: 316,073,000 KRW.
    *   Location: 충청북도 (Chungcheongbuk-do).
    *   Contract Method: 제한경쟁 (Limited competition).
    *   Qualification (Part 3):
        *   (다) Requires registration in 조경식재·시설물공사업 (4993) [주력분야: 조경시설물설치공사].
```
