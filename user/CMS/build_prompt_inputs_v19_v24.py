#!/usr/bin/env python3
"""dev/test JSONL에서 v19~v24별 최소 meta와 관련 원문 구간을 추출한다."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ITEMS = tuple(f"v{i}" for i in range(19, 25))
MAX_CANDIDATE_CHARS = 1800

META_FIELDS = {
    "v19": ("적용계약법", "업무구분", "계약방법"),
    "v20": ("적용계약법", "업무구분", "계약방법", "낙찰방법", "정보화사업여부",
             "배정예산금액", "입찰추정가격"),
    "v21": ("적용계약법", "업무구분", "계약방법", "공동도급구성방식"),
    "v22": ("적용계약법", "계약방법", "낙찰방법"),
    "v23": ("적용계약법", "계약방법", "낙찰방법", "입찰추정가격", "배정예산금액",
             "공고게시일자", "긴급공고여부"),
    "v24": ("배정예산금액", "입찰추정가격", "계약방법", "낙찰방법",
             "지역제한여부", "제한지역코드목록", "업종제한여부", "면허업종제한목록"),
}

# 첫 묶음은 핵심 신호라 높은 점수를 받고, 뒤 묶음은 문맥 보강용이다.
PATTERNS = {
    "v19": (
        r"물품공급|공급[·ㆍ ]?(?:및[·ㆍ ]?)?기술지원|기술지원|공급\s*증명|확약서|정품인증|A/S",
        r"제조사|공급사|입찰.*마감|제안서.*마감|보유|발급|제출|낙찰|계약",
    ),
    "v20": (
        r"소프트웨어|SW사업|정보시스템|컴퓨터관련서비스|업종코드\s*:?\s*1468|대기업.*참여|중견기업",
        r"사업금액|추정가격|부가가치세|유지관리|구축|운영|참여제한|예외사업|제48조|별표\s*1",
    ),
    "v21": (
        r"공동수급|공동도급|공동이행|분담이행|혼합방식|최소\s*지분|최소\s*출자",
        r"구성원|지분율|출자비율|참여비율|대표사|지역업체|공동수급협정",
    ),
    "v22": (
        r"현장설명|사업설명|제안요청서?\s*설명|과업설명|설명회.*(?:참석|불참)|(?:참석|불참).*설명회",
        r"참가자격|제출\s*자격|제안서.*접수|입찰.*(?:허용|불허|제외)|미참석|미접수|PT|발표",
    ),
    "v23": (
        r"현장설명|사업설명|제안요청서?\s*설명|과업설명|설명회|제안서.*(?:접수|제출).*마감",
        r"공고기간|공고일|입찰공고|접수마감|제출마감|추정가격|사업금액|기초금액|긴급|재공고|개찰",
    ),
    "v24": (
        r"예산액|사업금액|용역금액|기초금액|추정가격|입찰방법|계약방법|계약방식|제한경쟁|일반경쟁",
        r"본점\s*소재지|사업장.*소재지|지역제한|업종코드|면허|등록한\s*자|등록한\s*업체|여행업|행사대행업|식품판매업",
    ),
}

WINDOWS = {"v19": 2, "v20": 2, "v21": 2, "v22": 2, "v23": 3, "v24": 2}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/dev.jsonl"))
    parser.add_argument("--output", type=Path,
                        default=Path("output/prompt-inputs-v19-v24-20260913/candidates.jsonl"))
    parser.add_argument("--max-candidate-chars", type=int, default=MAX_CANDIDATE_CHARS)
    return parser.parse_args()


def line_records(text: str) -> list[dict]:
    records, start = [], 0
    for number, raw in enumerate(text.splitlines(keepends=True), 1):
        end = start + len(raw)
        records.append({"number": number, "start": start, "end": end,
                        "text": raw.rstrip("\r\n")})
        start = end
    if not records and not text:
        return []
    if text and (not records or records[-1]["end"] < len(text)):
        records.append({"number": len(records) + 1, "start": start, "end": len(text),
                        "text": text[start:]})
    return records


def merge_ranges(indices: set[int], size: int, window: int) -> list[tuple[int, int]]:
    expanded: set[int] = set()
    for index in indices:
        expanded.update(range(max(0, index - window), min(size, index + window + 1)))
    ranges: list[list[int]] = []
    for index in sorted(expanded):
        if not ranges or index > ranges[-1][1] + 1:
            ranges.append([index, index])
        else:
            ranges[-1][1] = index
    return [(start, end) for start, end in ranges]


def extract_segments(record: dict, item: str, max_chars: int) -> tuple[list[dict], bool]:
    primary, secondary = (re.compile(p, re.I) for p in PATTERNS[item])
    ranked = []
    for doc_order, doc in enumerate(record["docs"]):
        lines = line_records(doc["text"])
        # 보조 문맥어만으로 후보가 범람하지 않게 한다. 날짜·금액과 네 대조축을
        # 각각 모아야 하는 v23·v24만 두 패턴을 모두 독립 시드로 사용한다.
        hits = {i for i, line in enumerate(lines) if primary.search(line["text"]) or
                (item in {"v23", "v24"} and secondary.search(line["text"]))}
        for start_i, end_i in merge_ranges(hits, len(lines), WINDOWS[item]):
            start, end = lines[start_i]["start"], lines[end_i]["end"]
            raw = doc["text"][start:end]
            if not raw.strip():
                continue
            primary_hits = len(primary.findall(raw))
            secondary_hits = len(secondary.findall(raw))
            score = primary_hits * 10 + secondary_hits * 2
            ranked.append((score, -doc_order, -start, {
                "doc_id": doc["doc_id"], "doc_type": doc["type"],
                "start": start, "end": end, "line_start": lines[start_i]["number"],
                "line_end": lines[end_i]["number"], "text": raw,
            }))

    selected, used = [], 0
    for _, _, _, segment in sorted(ranked, reverse=True):
        available = max_chars - used
        if available <= 0:
            break
        if len(segment["text"]) > available:
            if not selected:  # 매우 긴 한 줄도 입력 예산 안에서 원문 부분문자열로 보존
                segment = dict(segment)
                segment["text"] = segment["text"][:available]
                segment["end"] = segment["start"] + available
                selected.append(segment)
                used = max_chars
            continue
        selected.append(segment)
        used += len(segment["text"])
    selected.sort(key=lambda x: (x["doc_id"], x["start"]))
    return selected, len(selected) < len(ranked)


def compact_meta(record: dict, item: str) -> dict:
    meta = record.get("meta", {})
    return {field: meta.get(field) for field in META_FIELDS[item]}


def main() -> int:
    args = parse_args()
    if args.max_candidate_chars < 1:
        raise ValueError("--max-candidate-chars는 1 이상이어야 합니다")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with args.input.open(encoding="utf-8") as source, args.output.open("w", encoding="utf-8") as target:
        for line in source:
            if not line.strip():
                continue
            record = json.loads(line)
            items = {}
            for item in ITEMS:
                segments, budget_truncated = extract_segments(record, item, args.max_candidate_chars)
                items[item] = {
                    "meta": compact_meta(record, item),
                    "input_completeness": record.get("input_completeness", {}),
                    "dropped_doc_counts": record.get("dropped_doc_counts", {}),
                    "segments": segments,
                    "candidate_chars": sum(len(segment["text"]) for segment in segments),
                    "budget_truncated": budget_truncated,
                }
            target.write(json.dumps({"id": record["id"], "items": items}, ensure_ascii=False) + "\n")
            count += 1
    print(f"저장: {args.output} ({count}건 × {len(ITEMS)}항목)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
