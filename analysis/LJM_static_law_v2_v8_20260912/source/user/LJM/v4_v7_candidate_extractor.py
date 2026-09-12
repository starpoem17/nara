"""v4~v7 후보 추출기.

최종 법령 판정기는 아니다. 공고문에서 후보 근거와 비교에 필요한 값을
추출해 Gemma/RAG 입력 JSON으로 만드는 전처리 모듈이다.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from typing import Any, Iterable


AMOUNT_RE = re.compile(
    r"(?P<num>\d[\d,]*(?:\.\d+)?)\s*(?P<unit>억|천\s*만|백\s*만|만)?\s*원?",
    re.I,
)
EXPERIENCE_RE = re.compile(r"실적|수행실적|이행실적|납품실적|용역실적|수행 경험")
INSTITUTION_RE = re.compile(
    r"국가기관|중앙정부|지방자치단체|지자체|공공기관|공기업|정부투자기관|대학병원|수요기관|특정 기관"
)
REGION_RE = re.compile(
    r"지역제한|지역\s*제한|본사|본점|주된\s*영업소|영업소|사업장\s*소재지|"
    r"지역\s*업체|관내\s*업체|소재지를\s*둔\s*업체|소재하고\s*있는\s*업체|"
    r"\[지역:[^\]]+\]"
)
BASIC_REGION_RE = re.compile(r"단위\s*=\s*기초|시[·ㆍ]?군[·ㆍ]?구|시군구|관내")
BAD_CONTEXT_RE = re.compile(
    r"평가장소|제출처|제출\s*장소|납품장소|발급기관|주소\s*[:：]|"
    r"서식|양식|평가항목|평가요소|배점|평점|정량적\s*평가|계약\s*후|정산|성과보고"
)
QUALIFICATION_RE = re.compile(r"입찰참가자격|입찰\s*참가\s*자격|참가자격|제한경쟁|입찰에\s*참가")
ADJACENT_RE = re.compile(r"인접|인근|접한\s*지역|연접|주변|확대|복수\s*지역")


def parse_amounts(text: str) -> list[dict[str, Any]]:
    result = []
    for m in AMOUNT_RE.finditer(text):
        unit = (m.group("unit") or "").replace(" ", "")
        multiplier = {"억": 100_000_000, "천만": 10_000_000, "백만": 1_000_000, "만": 10_000}.get(unit, 1)
        result.append({"text": m.group(0), "value": int(float(m.group("num").replace(",", "")) * multiplier), "start": m.start()})
    return result


def _lines(text: str) -> list[str]:
    return [x.strip() for x in text.splitlines() if x.strip()]


def _context(lines: list[str], index: int, radius: int = 1) -> str:
    return " ".join(lines[max(0, index - radius): min(len(lines), index + radius + 1)])


def extract_candidates(record: dict[str, Any]) -> dict[str, Any]:
    meta = record.get("meta", {})
    text = "\n".join(d.get("text", "") for d in record.get("docs", []))
    lines = _lines(text)

    experience = []
    institution = []
    regions = []
    for i, line in enumerate(lines):
        ctx = _context(lines, i)
        if BAD_CONTEXT_RE.search(ctx):
            continue
        if EXPERIENCE_RE.search(ctx):
            experience.append({"line": line, "context": ctx, "amounts": parse_amounts(ctx), "qualification": bool(QUALIFICATION_RE.search(ctx))})
        if INSTITUTION_RE.search(ctx):
            institution.append({"line": line, "context": ctx, "qualification": bool(QUALIFICATION_RE.search(ctx))})
        if REGION_RE.search(ctx):
            regions.append({"line": line, "context": ctx, "basic_unit": bool(BASIC_REGION_RE.search(ctx)), "qualification": bool(QUALIFICATION_RE.search(ctx))})

    exp_text = " ".join(x["context"] for x in experience)
    inst_text = " ".join(x["context"] for x in institution)
    region_text = " ".join(x["context"] for x in regions)
    exp_amounts = [a for x in experience for a in x["amounts"]]
    has_qualification = bool(QUALIFICATION_RE.search(text))
    has_region_qualification = any(x["qualification"] for x in regions)
    has_exp_qualification = any(x["qualification"] for x in experience)

    # 후보 추출 단계: 법령 기준금액 비교 전에는 넓게 유지한다.
    candidates = {
        "v4": bool(experience and exp_amounts and institution),
        "v5": bool(regions),
        "v6": bool(regions and any(x["basic_unit"] for x in regions)),
        "v7": bool(regions and (ADJACENT_RE.search(region_text) or len(re.findall(r"\[지역:", region_text)) >= 2)),
    }

    return {
        "id": record.get("id"),
        "meta": meta,
        "candidate_flags": [k for k, v in candidates.items() if v],
        "evidence": {
            "experience": experience[:10],
            "institution": institution[:10],
            "region": regions[:15],
        },
        "extracted": {
            "experience_amounts": exp_amounts[:30],
            "has_qualification_section": has_qualification,
            "has_qualification_experience": has_exp_qualification,
            "has_qualification_region": has_region_qualification,
            "region_text": region_text[:3000],
            "experience_text": exp_text[:3000],
            "institution_text": inst_text[:2000],
        },
    }


def gemma_prompt(item: dict[str, Any], label: str) -> str:
    """Gemma에 전달할 JSON 판정 프롬프트를 생성한다."""
    return f"""당신은 나라장터 입찰공고 법령 위반 판정기다.
항목: {label}
아래 공고 메타데이터와 추출 근거를 사용하라. 평가표, 서식, 주소, 납품장소,
계약 후 조건은 입찰참가자격으로 보지 않는다. 관련 법령·고시금액을 검색한 뒤
적용 법령, 기준금액, 비교값을 명시하고 JSON만 출력하라.

출력 형식:
{{"label":"{label}","violation":0,"law":"","threshold":null,"comparison":"","evidence":"","reason":""}}

입력:
{json.dumps(item, ensure_ascii=False)}
"""


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("json_file", help="단일 JSON record 파일")
    args = parser.parse_args()
    record = json.load(open(args.json_file, encoding="utf-8"))
    result = extract_candidates(record)
    print(json.dumps(result, ensure_ascii=False, indent=2))
