#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""나라장터 자체입찰 공고 법령 위반사항 모니터링 AI 경진대회 베이스라인.

평가 서버는 이 파일을 `python script.py`로 그대로 실행합니다.
  입력   ./data/test.jsonl.gz (+ 항목표.json · 정답스키마_디코딩.json)
  출력   ./output/submission.csv  (열 = id, v1..v24, e1..e24)
         v = 위반 여부 0/1, e = 근거 문구(원문 부분문자열, 비위반은 빈칸)
  경로   PPS_DATA_DIR · PPS_OUTPUT_DIR · PPS_MODEL_DIR 환경변수 우선

전체 흐름
  데이터 로드 → 프롬프트 구성 → vLLM 배치 추론 → JSON 파싱
  → 근거 문구 검증 → submission.csv 저장 → 형식 검증

로컬 실행
  python script.py --mock          # 모델 없이 입력·출력 흐름 확인
  python script.py --limit 10      # 앞 10건 실행
"""
from __future__ import annotations

# ===== 1. 상수·경로 =====
import argparse
import csv
import gzip
import glob
import io
import json
import os
import re
import sys
import time
import unicodedata
from collections import Counter
from typing import Any, Dict, Iterator, List, Optional, Tuple

DATA_DIR = os.environ.get("PPS_DATA_DIR", "./data")
OUTPUT_DIR = os.environ.get("PPS_OUTPUT_DIR", "./output")
MODEL_DIR = os.environ.get("PPS_MODEL_DIR", "/opt/models/gemma-4-26B-A4B-it")

ITEMS = [f"v{i}" for i in range(1, 25)]
EVID = [f"e{i}" for i in range(1, 25)]
COLUMNS = ["id"] + ITEMS + EVID
ABSENCE = ["v10", "v11", "v16", "v18", "v20"]          # 부재탐지 항목: 근거 문구 빈칸

DOC_ORDER = ["공고문", "규격서", "과업지시서", "제안요청서", "예외공표서", "기타"]
META_FIELDS = [
    "적용계약법", "업무구분", "계약방법", "낙찰방법", "낙찰하한율",
    "배정예산금액", "입찰추정가격", "소관구분", "공동도급구성방식", "정보화사업여부",
    "세부품명번호목록", "제한지역코드목록", "지역제한여부", "면허업종제한목록", "업종제한여부",
    "조항호내용", "공고게시일자", "개찰예정일자", "긴급공고여부", "입찰방법", "조달방식",
]

SEED = 20260826
MAX_MODEL_LEN = 16384                   # 베이스라인 모델 컨텍스트 길이
MAX_TOKENS = 1536                       # 구조화 출력 토큰 예산
PROMPT_BUDGET = MAX_MODEL_LEN - MAX_TOKENS
EVIDENCE_MAX = 500                      # 근거 문구 셀 글자 수 상한
QUANT = "int8_per_channel_weight_only"  # 평가 서버 양자화 설정

# 모든 문서를 무작정 앞부분부터 자르지 않고, 자격·실적·지역·중소기업·설명회 등
# 24개 항목 판정에 자주 쓰이는 문단을 우선 포함하기 위한 일반 검색어입니다.
CONTEXT_TERMS = (
    "참가자격", "입찰참가", "참여자격", "실적", "수행실적", "단일건", "최근",
    "본점", "주된 영업소", "소재지", "지역", "제조사", "모델명", "제품명",
    "직접생산", "중소기업", "소기업", "소상공인", "경쟁제품", "세부품명",
    "공급", "기술지원", "확약서", "소프트웨어", "공동수급", "공동이행",
    "분담이행", "설명회", "현장설명", "사업설명", "공고기간", "예산", "금액",
)

# dev 200건에서 만든 few-shot 사례집은 제출 ZIP의 model/casebook.json에 둡니다.
# 평가 서버의 data/에 dev 파일이 없더라도 제출 코드가 동일하게 동작하도록 정적 자산으로 포함합니다.
CASEBOOK_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model", "casebook.json")
CASEBOOK_TERMS = {
    "v1": ("기관", "대학", "공공기관", "참여 가능"),
    "v2": ("실적", "최근", "단일", "수행실적"),
    "v3": ("실적", "단일", "억원", "만원"),
    "v4": ("실적", "국가기관", "공공기관"),
    "v5": ("본점", "주된 영업소", "소재지", "지역"),
    "v6": ("본점", "소재지", "시·군·구"),
    "v7": ("광역시", "특별자치도", "소재지"),
    "v8": ("실적", "본점", "소재지"),
    "v9": ("제조사", "모델명", "제품명", "시리즈"),
    "v10": ("직접생산", "경쟁제품", "세부품명"),
    "v11": ("경쟁제품", "중소기업", "소기업", "소상공인"),
    "v12": ("직접생산", "직접생산확인"),
    "v13": ("중소기업", "소기업", "소상공인", "확인서"),
    "v14": ("중소기업", "소기업", "소상공인", "확인서"),
    "v15": ("소기업", "소상공인", "확인서"),
    "v16": ("중소기업", "소기업", "소상공인"),
    "v17": ("중소기업", "소기업", "소상공인"),
    "v18": ("소기업", "소상공인"),
    "v19": ("공급", "기술지원", "확약서"),
    "v20": ("소프트웨어", "SW", "사업금액"),
    "v21": ("공동수급", "공동이행", "분담이행", "지분"),
    "v22": ("설명회", "현장설명회", "참석"),
    "v23": ("설명회", "공고기간", "협상"),
    "v24": ("금액", "계약방법", "지역", "업종"),
}
_CASEBOOK_CACHE: Optional[Dict[str, Any]] = None
_LAW_INDEX_CACHE: Optional[Any] = None
_LAW_INDEX_ATTEMPTED = False


def log(msg: str) -> None:
    print(f"[baseline] {msg}", file=sys.stderr, flush=True)


# ===== 2. 데이터 로더 =====
def _open(path: str):
    if str(path).endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8")
    return io.open(path, "r", encoding="utf-8")


def validate_record(rec: Any) -> None:
    """레코드 1건의 최소 스키마 검사 (id · docs(공고문 1개 이상) · meta)"""
    if not isinstance(rec, dict):
        raise ValueError(f"레코드가 object가 아니다: {type(rec).__name__}")
    for k in ("id", "docs", "meta"):
        if k not in rec:
            raise ValueError(f"필수 키 없음: {k}")
    if not isinstance(rec["id"], str) or not rec["id"]:
        raise ValueError("id가 비어 있다")
    docs = rec["docs"]
    if not isinstance(docs, list) or not docs:
        raise ValueError(f"docs가 비어 있다 (id={rec['id']})")
    for d in docs:
        if not isinstance(d, dict) or not all(k in d for k in ("doc_id", "type", "text")):
            raise ValueError(f"docs 원소 형식 오류 (id={rec['id']})")
        if not isinstance(d["text"], str):
            raise ValueError(f"docs.text가 문자열이 아니다 (id={rec['id']})")
    if not any(d["type"] == "공고문" for d in docs):
        raise ValueError(f"공고문이 없다 (id={rec['id']})")
    if not isinstance(rec["meta"], dict):
        raise ValueError(f"meta가 object가 아니다 (id={rec['id']})")


def normalize(rec: Dict[str, Any]) -> Dict[str, Any]:
    """NFC 정규화 — macOS에서 만든 파일은 한글이 NFD로 저장될 수 있어 문자열 비교가 어긋날 수 있습니다."""
    for d in rec.get("docs", []):
        d["text"] = unicodedata.normalize("NFC", d["text"])
        if isinstance(d.get("type"), str):
            d["type"] = unicodedata.normalize("NFC", d["type"])
    return rec


def iter_records(path: str, limit: Optional[int] = None) -> Iterator[Dict[str, Any]]:
    n = 0
    with _open(path) as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"{path}:{lineno} JSON 파싱 실패: {e}") from e
            validate_record(rec)
            yield normalize(rec)
            n += 1
            if limit and n >= limit:
                return


def full_text(rec: Dict[str, Any]) -> str:
    """근거문구 대조용 원문 (프롬프트에 넣은 것과 같은 텍스트 · NFC)"""
    return "\n".join(d["text"] for d in rec["docs"])


def build_context(rec: Dict[str, Any], max_chars: int = 12000) -> str:
    """문서 머리말과 판정 관련 문단을 우선하여 프롬프트용 텍스트를 구성합니다.

    기존 방식처럼 공고문 앞부분만 남기면 첨부문서의 참가자격·규격·설명회 조건을
    놓치기 쉽습니다. 따라서 각 문서의 앞부분을 조금씩 포함한 뒤, 관련 검색어가
    들어간 문단을 문서 순서대로 추가합니다. 근거 대조는 원문 전체를 대상으로 하므로
    프롬프트에 들어간 문단을 정규화하거나 요약하지 않습니다.
    """
    order = {t: i for i, t in enumerate(DOC_ORDER)}
    pool = sorted(rec["docs"], key=lambda d: (order.get(d["type"], len(DOC_ORDER)), d["doc_id"]))

    chunks, used, dropped, truncated = [], 0, Counter(), False
    selected = set()

    def add_chunk(d: Dict[str, Any], body: str, marker: str = "") -> bool:
        nonlocal used, truncated
        head = f"[{d['type']}:{d['doc_id']}{marker}]\n"
        remaining = max_chars - used
        if remaining <= len(head):
            return False
        if len(head) + len(body) > remaining:
            body = body[: max(0, remaining - len(head))]
            truncated = True
        if not body:
            return False
        chunks.append(head + body)
        used += len(head) + len(body)
        return True

    # 문서별 앞부분은 제목·사업명·문서 구조 파악용으로 짧게 보존합니다.
    for d in pool:
        if used >= max_chars:
            dropped[d["type"]] += 1
            continue
        add_chunk(d, d["text"][:1200], "·앞부분")

    # 관련 문단을 추가합니다. 동일 문단이 이미 앞부분에 포함된 경우는 생략합니다.
    for d in pool:
        paragraphs = re.split(r"\n\s*\n", d["text"])
        for pidx, paragraph in enumerate(paragraphs):
            if not paragraph.strip() or len(paragraph) < 10:
                continue
            if not any(term in paragraph for term in CONTEXT_TERMS):
                continue
            if paragraph in d["text"][:1200]:
                continue
            key = (d["doc_id"], pidx)
            if key in selected:
                continue
            selected.add(key)
            if used >= max_chars:
                dropped[d["type"]] += 1
                break
            add_chunk(d, paragraph, f"·관련문단{pidx + 1}")

    if not chunks:
        dropped[pool[0]["type"]] += 1

    for t, n in (rec.get("dropped_doc_counts") or {}).items():
        dropped[t] += n

    text = "\n\n".join(chunks)
    if truncated:
        text += "\n\n[절단] 공고문 뒷부분이 길이 예산으로 잘렸다"
    if dropped:
        text += "\n\n[미수록 문서] " + ", ".join(f"{t} {n}건" for t, n in sorted(dropped.items()))
    return text


def format_meta(rec: Dict[str, Any]) -> str:
    """나라장터 메타를 한 줄짜리 목록으로. 값이 없는 필드는 '미기재'로 표시합니다."""
    m = rec.get("meta", {})
    lines = []
    for k in META_FIELDS:
        if k in m:
            v = m[k]
            lines.append(f"- {k}: {'미기재' if v is None else v}")
    return "\n".join(lines)


def load_casebook() -> Dict[str, Any]:
    """제출물에 포함한 dev 기반 정적 사례집을 선택적으로 읽습니다."""
    global _CASEBOOK_CACHE
    if _CASEBOOK_CACHE is None:
        if not os.path.exists(CASEBOOK_PATH):
            _CASEBOOK_CACHE = {}
        else:
            with io.open(CASEBOOK_PATH, encoding="utf-8") as f:
                _CASEBOOK_CACHE = json.load(f)
    return _CASEBOOK_CACHE


def build_casebook_context(rec: Dict[str, Any], max_chars: int = 4500) -> str:
    """현재 공고와 관련성이 높은 dev 양성·음성 사례를 짧게 few-shot으로 제공합니다."""
    book = load_casebook().get("items", {})
    if not book:
        return ""
    current = format_meta(rec) + "\n" + full_text(rec)
    ranked = []
    for v in ITEMS:
        terms = CASEBOOK_TERMS.get(v, ())
        score = sum(1 for term in terms if term in current)
        if score:
            ranked.append((score, v))
    ranked.sort(key=lambda x: (-x[0], int(x[1][1:])))

    blocks, used = [], 0
    for _, v in ranked[:8]:
        item = book.get(v, {})
        pos = (item.get("positive") or [])[:1]
        neg = (item.get("negative") or [])[:1]
        for label, examples in ((1, pos), (0, neg)):
            if not examples:
                continue
            ex = examples[0]
            snippet = str(ex.get("snippet") or "").replace("\r", "").replace("\n", " ").strip()
            snippet = snippet[:240]
            meta = ex.get("meta") or {}
            info = ", ".join(str(meta.get(k)) for k in ("법령", "업무", "계약방법", "추정가격") if meta.get(k) not in (None, ""))
            line = f"- {v} {'위반' if label else '정상'} 예시"
            if info:
                line += f" ({info})"
            line += f": {snippet or '(문구 없음)'}"
            if used + len(line) + 1 > max_chars:
                return "[dev 정답 사례 참고 — 근거는 현재 공고에서 다시 찾을 것]\n" + "\n".join(blocks)
            blocks.append(line)
            used += len(line) + 1
    return ("[dev 정답 사례 참고 — 근거는 현재 공고에서 다시 찾을 것]\n" + "\n".join(blocks)) if blocks else ""


def _law_tokenize(text: str) -> List[str]:
    """법령 BM25 검색용 간단한 토큰화. 원문 인용에는 사용하지 않습니다."""
    words = re.findall(r"[가-힣]{2,}|[A-Za-z]{2,}|\d{2,}", text or "")
    out: List[str] = []
    for word in words:
        out.append(word)
        if len(word) > 2:
            out.extend(word[i:i + 2] for i in range(len(word) - 1))
    return out


def _load_law_articles(data_dir: str) -> List[Tuple[str, str]]:
    articles: List[Tuple[str, str]] = []
    pattern = re.compile(r"^제\s?\d+조(?:의\s?\d+)?\s*\(", re.M)
    law_dir = os.path.join(data_dir, "법령패키지", "법령")
    for p in sorted(glob.glob(os.path.join(law_dir, "*.txt"))):
        law = unicodedata.normalize("NFC", os.path.splitext(os.path.basename(p))[0])
        with io.open(p, encoding="utf-8") as f:
            text = unicodedata.normalize("NFC", f.read())
        cuts = [m.start() for m in pattern.finditer(text)]
        if not cuts:
            articles.append((law, text.strip()))
            continue
        for i, start in enumerate(cuts):
            end = cuts[i + 1] if i + 1 < len(cuts) else len(text)
            body = text[start:end].strip()
            if body:
                articles.append((law, body))
    return articles


class LawBM25Index:
    """배포된 법령 패키지의 조문을 검색하는 정적 RAG 색인."""

    def __init__(self, data_dir: str):
        from rank_bm25 import BM25Okapi
        self.articles = _load_law_articles(data_dir)
        self.bm25 = BM25Okapi([_law_tokenize(body) for _, body in self.articles])

    def search(self, query: str, top_k: int = 6, max_chars: int = 5000) -> str:
        if not self.articles:
            return ""
        scores = self.bm25.get_scores(_law_tokenize(query))
        order = sorted(range(len(scores)), key=lambda i: -scores[i])[:top_k]
        chunks, used = [], 0
        for i in order:
            law, body = self.articles[i]
            block = f"[{law}]\n{body}"
            if used + len(block) > max_chars:
                block = block[:max(0, max_chars - used)]
            if not block:
                break
            chunks.append(block)
            used += len(block)
        return "\n\n".join(chunks)


def configure_law_index(data_dir: str, enabled: bool = True) -> None:
    """법령 색인을 한 번만 준비합니다. 패키지가 없으면 RAG 없이 계속 실행합니다."""
    global _LAW_INDEX_CACHE, _LAW_INDEX_ATTEMPTED
    if _LAW_INDEX_ATTEMPTED or not enabled:
        return
    _LAW_INDEX_ATTEMPTED = True
    try:
        _LAW_INDEX_CACHE = LawBM25Index(data_dir)
        log(f"법령 RAG 색인 {_LAW_INDEX_CACHE and len(_LAW_INDEX_CACHE.articles)}개 조문")
    except Exception as e:
        _LAW_INDEX_CACHE = None
        log(f"법령 RAG 비활성화 — {type(e).__name__}: {str(e)[:120]}")


def build_legal_context(rec: Dict[str, Any], max_chars: int = 5000) -> str:
    if _LAW_INDEX_CACHE is None:
        return ""
    meta_query = format_meta(rec)
    doc_query = "\n".join(d["text"][:1800] for d in rec.get("docs", []))
    query = f"{meta_query}\n{doc_query}"
    return _LAW_INDEX_CACHE.search(query, top_k=6, max_chars=max_chars)


# ===== 3. 항목표·디코딩 스키마 =====
# data/에 항목표.json·정답스키마_디코딩.json이 동봉됩니다.
# 항목명·근거조문·비고는 항목표.json 에 있으니 여기에 사본을 두지 않습니다.


def item_table(data_dir: str = DATA_DIR) -> Dict[str, Dict[str, Any]]:
    p = os.path.join(data_dir, "항목표.json")
    if not os.path.exists(p):
        raise FileNotFoundError(f"{p} 가 없습니다 — data/ 를 그대로 둔 채 실행하세요.")
    return json.load(io.open(p, encoding="utf-8"))["항목"]


def decode_schema(data_dir: str = DATA_DIR) -> Dict[str, Any]:
    """베이스라인의 구조화 출력에 사용할 JSON Schema를 불러옵니다."""
    p = os.path.join(data_dir, "정답스키마_디코딩.json")
    if os.path.exists(p):
        s = json.load(io.open(p, encoding="utf-8"))
        return s["properties"]["판정"] if "판정" in s.get("properties", {}) else s
    props = {}
    for v in ITEMS:
        props[v] = {
            "type": "object", "additionalProperties": False,
            "required": ["위반여부", "근거문구"],
            "properties": {
                "위반여부": {"type": "integer", "enum": [0, 1]},
                "근거문구": {"type": "null"} if v in ABSENCE else {"type": ["string", "null"]},
            },
        }
    return {"type": "object", "additionalProperties": False, "required": list(ITEMS), "properties": props}


# ===== 4. 프롬프트 구성 =====
# 베이스라인 프롬프트는 출력 형식과 항목 목록을 구성합니다.
SYSTEM_HEAD = """당신은 공공 입찰공고의 법령 위반 여부를 점검한다.
공고문과 첨부 문서, 그리고 나라장터 입력 메타를 함께 읽고 아래 24개 항목 각각에 대해
위반 여부(1/0)와 근거 문구를 판정한다.

지켜야 할 것
1. 24개 항목 전부에 답한다. 판단이 어려운 항목도 비워 두지 말고 0으로 낸다.
2. 근거 문구는 반드시 **주어진 문서에 그대로 있는 문장**을 옮긴다. 요약하거나 고쳐 쓰지 않는다.
   원문에 없는 문구는 근거로 인정되지 않는다. 500자를 넘기지 않는다.
3. 아래 '근거 없음' 표시가 붙은 항목은 **있어야 할 문구가 없는 것**이 위반이다.
   인용할 원문이 존재하지 않으므로 근거 문구를 null로 둔다.
4. 먼저 적용계약법·업무구분·금액·계약방법·문서 완전성을 확인한다. 적용 대상이 아니면 0이다.
5. 공고문뿐 아니라 규격서·과업지시서·제안요청서의 조건도 함께 본다.
6. 첨부문서가 누락되었거나 문서에 표시된 [미수록 문서] 때문에 판단할 수 없으면,
   단순히 문구가 없다는 이유로 부재탐지 항목을 1로 만들지 않는다.
7. v2/v3/v4, v5/v6/v7/v8, v13~v18은 금액·지역·품목 조건을 비교하여 각각 독립적으로 판단한다.
8. 위반이 확실한 일반 항목만 1로 하고, 위반 근거가 문서에 없으면 0으로 둔다.
9. 검색된 법령 조문과 dev 사례는 판정 참고용이다. 근거문구는 반드시 현재 공고의 문서에서만 인용한다.
10. dev 사례의 표현을 현재 공고에 억지로 적용하지 말고, 현재 공고의 사실·meta·적용 법령을 우선한다.

판정할 24개 항목"""

SYSTEM_TAIL = """
출력은 JSON 하나로만 낸다. 키는 v1~v24, 각 값은 {"위반여부": 0 또는 1, "근거문구": 문자열 또는 null}이다.
설명이나 머리말을 덧붙이지 않는다."""

OPERATIONAL_GUIDE = """

판정 실무 가이드
1. 먼저 적용계약법, 업무구분, 입찰추정가격·배정예산금액, 계약방법, 세부품명번호, 문서 완전성을 확인한다.
   적용 대상이 아닌 항목은 0이다. 법령 조문 번호가 공고문에 적혀 있다는 사실만으로 위반으로 판단하지 않는다.
2. 금액 구간은 항목표와 검색된 법령 패키지의 기준을 사용한다. 숫자만 보고 국가·지방 기준을 섞지 않는다.
3. 한 문장이 여러 조건을 포함하면 해당하는 항목을 각각 독립적으로 판정하되, 같은 문장을 근거로 재사용할 수 있다.
4. 일반 위반 항목은 현재 공고 문서에서 위반 조건을 직접 확인할 수 있을 때만 1이다.
5. 부재탐지 항목(v10·v11·v16·v18·v20)은 적용 대상이고 필요한 문서가 관측된 경우에만 필수 문구의 부재를 판단한다.

항목별 구분 기준
- v1: 특정 기관 유형만 참가하도록 자격을 제한하는지 확인한다. 일반적인 법정 자격 안내는 v1이 아니다.
- v2: 고시금액 미만 공고에서 과거 실적을 참가자격으로 요구하는지 확인한다.
- v3: 요구한 단일 실적 금액이 사업금액 이상인지 확인한다. 단순 실적 요구와 구분한다.
- v4: 고시금액 이상에서 특정 기관이 발주한 실적 또는 지나치게 특정된 실적을 요구하는지 확인한다.
- v5: 고시금액 이상 공고에서 참가자의 영업소·본점을 특정 지역으로 제한하는지 확인한다.
- v6: 고시금액 미만 지역제한의 지역 단위가 시·군·구 기준에 맞는지 확인한다.
- v7: 고시금액 미만 지역제한에서 인접 광역단위 등으로 제한 범위를 부당하게 넓혔는지 확인한다.
- v8: 실적제한과 지역제한이 동시에 참가자격으로 부과되는지 확인한다.
- v9: 규격서·과업지시서에 제조사·모델명·제품 시리즈를 필수 규격처럼 명시했는지 확인한다. 동등품 허용 여부도 본다.
- v10: 세부품명번호가 경쟁제품인 경우 직접생산 관련 필수 참가조건의 부재를 확인한다. 근거문구는 null이다.
- v11: 세부품명번호가 경쟁제품인 경우 중소기업 참가조건의 부재를 확인한다. 근거문구는 null이다.
- v12: 경쟁제품이 아닌 일반제품에 직접생산확인 등 제조자 제한을 부과하는지 확인한다.
- v13: 경쟁제품 공고에서 소기업·소상공인 등으로 참가자를 제한하는지 확인한다.
- v14: 고시금액 이상 일반물품을 중소기업으로 제한하는지 확인한다.
- v15: 1억원 이상 고시금액 미만 구간에서 소기업·소상공인 제한을 두는지 확인한다. 판로지원 예외를 확인한다.
- v16: v15 조건에서 중소기업 제한 문구가 없는지 확인한다. 근거문구는 null이다.
- v17: 1억원 미만 일반물품에서 중소기업 제한을 두는지 확인한다.
- v18: 1억원 미만 일반물품에서 소기업 제한 문구가 없는지 확인한다. 근거문구는 null이다.
- v19: 물품공급·기술지원 확약서를 입찰 전에 보유·제출하도록 요구하는지 확인한다. 계약 시 제출만 요구하는 경우와 구분한다.
- v20: 정보화·소프트웨어 사업에서 사업금액 기준 중소 소프트웨어사업자 참여 제한 문구가 부재한지 확인한다. 근거문구는 null이다.
- v21: 공동수급을 허용하는 경우 구성원의 최소 지분율 등 공동계약 제한조건이 기준에 맞는지 확인한다.
- v22: 협상에 의한 계약에서 설명회·현장설명회 불참을 입찰 또는 제안서 제출 자격의 제한조건으로 삼는지 확인한다.
- v23: 지방계약법의 협상계약에서 설명회 일정과 공고기간이 관련 기준을 충족하는지 확인한다.
- v24: 공고문과 meta의 예산·추정가격·계약방법·지역제한·업종제한 등 동일 의미의 값을 비교한다.

혼동하기 쉬운 조합
- v2·v3·v4는 모두 실적과 관련될 수 있으므로 금액 구간, 실적 금액, 발주기관 특정 여부를 함께 비교한다.
- v5·v6·v7·v8은 지역의 범위와 실적제한의 동시 존재를 각각 확인한다.
- v10·v11·v16·v18·v20은 문서가 빠진 것과 실제 필수 문구가 없는 것을 구분한다.
- 검색된 법령 조문은 판단 기준이고, e열 근거는 현재 공고문·첨부문서의 연속된 원문 부분문자열만 사용한다.
"""


def build_system_prompt(tbl: Dict[str, Dict[str, Any]]) -> str:
    lines = []
    for v in ITEMS:
        it = tbl[v]
        tag = "  [근거 없음 — null]" if it["부재탐지"] else ""
        note = f" ({it['비고']})" if it.get("비고") else ""
        lines.append(f"- {v}: {it['항목명']}{note}{tag}")
    return SYSTEM_HEAD + "\n" + "\n".join(lines) + OPERATIONAL_GUIDE + "\n" + SYSTEM_TAIL


def build_user_prompt(rec: Dict[str, Any], max_chars: int) -> str:
    casebook = build_casebook_context(rec)
    legal = build_legal_context(rec)
    legal_block = f"[검색된 법령 조문 — 판정 참고용]\n{legal}\n\n" if legal else ""
    return (
        f"[공고 ID] {rec['id']}\n\n"
        f"[나라장터 입력 메타]\n{format_meta(rec)}\n\n"
        f"{legal_block}"
        f"{casebook + chr(10) + chr(10) if casebook else ''}"
        f"[문서]\n{build_context(rec, max_chars=max_chars)}\n"
    )


def build_messages(rec: Dict[str, Any], system_prompt: str, max_chars: int) -> List[Dict[str, str]]:
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": build_user_prompt(rec, max_chars)},
    ]


# ===== 5. 모델 러너 (vLLM offline / mock) =====
class VLLMRunner:
    """평가 서버의 모델을 vLLM offline API로 실행합니다."""

    def __init__(self, schema: Dict[str, Any], model_dir: str = MODEL_DIR, quant: Optional[str] = QUANT,
                 max_tokens: int = MAX_TOKENS, seed: int = SEED, gpu_mem: float = 0.92, tp: int = 1):
        t0 = time.time()
        import vllm                                    # --mock 실행 시 vllm이 없어도 되도록 지연 import
        from vllm import LLM, SamplingParams
        from vllm.sampling_params import StructuredOutputsParams

        log(f"vllm {vllm.__version__} · 모델 {model_dir} · quant={quant} · max_model_len={MAX_MODEL_LEN}")
        kw = dict(model=model_dir, tokenizer=model_dir, max_model_len=MAX_MODEL_LEN,
                  gpu_memory_utilization=gpu_mem, seed=seed, tensor_parallel_size=tp, dtype="auto")
        if quant:
            kw["quantization"] = quant
        self.llm = LLM(**kw)
        self.tok = self.llm.get_tokenizer()
        self.sp = SamplingParams(
            temperature=0.0, max_tokens=max_tokens, seed=seed,
            structured_outputs=StructuredOutputsParams(json=schema, disable_any_whitespace=True),
        )
        self.load_seconds = time.time() - t0

    def count_tokens(self, messages: List[Dict[str, str]]) -> int:
        try:
            ids = self.tok.apply_chat_template(messages, add_generation_prompt=True, tokenize=True)
            if hasattr(ids, "keys") and "input_ids" in ids:   # transformers 버전에 따라 dict가 반환되는 경우
                ids = ids["input_ids"]
            return len(ids)
        except Exception:
            return len(self.tok.encode("\n".join(m["content"] for m in messages)))

    def chat(self, batch: List[List[Dict[str, str]]]) -> List[str]:
        outs = self.llm.chat(batch, sampling_params=self.sp, use_tqdm=False)
        return [o.outputs[0].text if o.outputs else "" for o in outs]


class MockRunner:
    """모델 없이 입력·출력 및 제출 형식을 확인합니다."""
    load_seconds = 0.0

    def __init__(self, schema: Dict[str, Any], **_):
        pass

    def count_tokens(self, messages: List[Dict[str, str]]) -> int:
        return sum(len(m["content"]) for m in messages) // 2     # Mock 실행용 간이 추정치

    def _one(self, _messages: List[Dict[str, str]]) -> str:
        out = {v: {"위반여부": 0, "근거문구": None} for v in ITEMS}
        return json.dumps(out, ensure_ascii=False)

    def chat(self, batch: List[List[Dict[str, str]]]) -> List[str]:
        return [self._one(m) for m in batch]


def fit_to_budget(rec: Dict[str, Any], system_prompt: str, runner, max_chars: int,
                  budget: int = PROMPT_BUDGET) -> Tuple[List[Dict[str, str]], int, int]:
    """설정된 토큰 예산에 맞게 문서 글자 수를 조정합니다."""
    while True:
        msgs = build_messages(rec, system_prompt, max_chars)
        n = runner.count_tokens(msgs)
        if n <= budget or max_chars <= 2000:
            return msgs, n, max_chars
        max_chars = int(max_chars * min(0.85, budget / n * 0.95))


def run_chunk(runner, batch: List[List[Dict[str, str]]]) -> List[str]:
    """배치 실패 시 건별로 재시도하고, 처리하지 못한 건은 빈 출력으로 반환합니다."""
    try:
        return runner.chat(batch)
    except Exception as e:
        log(f"  ! 청크({len(batch)}건) 실패 → 건 단위 재시도: {type(e).__name__}: {str(e)[:160]}")
    outs = []
    for m in batch:
        try:
            outs.append(runner.chat([m])[0])
        except Exception as e:
            log(f"  ! 건 단위 실패 → 빈 출력: {type(e).__name__}: {str(e)[:160]}")
            outs.append("")
    return outs


# ===== 6. 파싱·후처리 =====
FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.S)


def extract_json(text: str) -> Optional[Any]:
    text = (text or "").strip()
    if not text:
        return None
    for cand in (text, *(m.group(1) for m in FENCE.finditer(text))):
        try:
            return json.loads(cand)
        except json.JSONDecodeError:
            pass
    i, j = text.find("{"), text.rfind("}")
    if i >= 0 and j > i:
        try:
            return json.loads(text[i:j + 1])
        except json.JSONDecodeError:
            return None
    return None


def parse_judgment(text: str) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    """모델 출력을 24항목 판정으로 정리합니다. 빠진 항목은 0/None으로 채우고 결손 목록을 함께 반환합니다."""
    obj = extract_json(text)
    if isinstance(obj, dict) and isinstance(obj.get("판정"), dict):
        obj = obj["판정"]
    out, missing = {}, []
    for v in ITEMS:
        raw = obj.get(v) if isinstance(obj, dict) else None
        if not isinstance(raw, dict):
            missing.append(v)
            out[v] = {"위반여부": 0, "근거문구": None}
            continue
        hit = raw.get("위반여부", raw.get("violation", 0))
        if isinstance(hit, bool):
            hit = int(hit)
        if isinstance(hit, str):
            hit = 1 if hit.strip() in ("1", "위반", "true", "True") else 0
        if hit not in (0, 1):
            hit = 1 if hit else 0
        ev = raw.get("근거문구", raw.get("evidence"))
        if ev is not None and not isinstance(ev, str):
            ev = str(ev)
        out[v] = {"위반여부": int(hit), "근거문구": ev}
    return out, missing


def clean_evidence(ev: Optional[str], src: str) -> str:
    """근거문구 셀 규약: NFC · 앞뒤 공백 제거 · 500자 상한 · 수식 접두(=,+,@)면 빈칸 ·
    원문 부분문자열이 아니면 빈칸(원문에 없는 근거는 채점에서 인정되지 않습니다)."""
    if not ev:
        return ""
    ev = unicodedata.normalize("NFC", ev).replace("\r", "").strip()
    if not ev or ev[0] in "=+@":
        return ""
    ev = ev[:EVIDENCE_MAX]
    return ev if ev in src else ""


def postprocess(judgment: Dict[str, Dict[str, Any]], rec: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """후처리: ① 부재탐지 5항목 근거 빈칸 고정 ② 위반이 아니면 근거 빈칸 ③ 근거문구 원문 대조(NFC)"""
    src = unicodedata.normalize("NFC", full_text(rec))
    out = {}
    for v in ITEMS:
        cell = dict(judgment.get(v, {"위반여부": 0, "근거문구": None}))
        hit = 1 if cell.get("위반여부") == 1 else 0
        ev = "" if (hit == 0 or v in ABSENCE) else clean_evidence(cell.get("근거문구"), src)
        out[v] = {"위반여부": hit, "근거문구": ev}
    return out


def to_row(rec_id: str, judgment: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    row = {"id": rec_id}
    for i, v in enumerate(ITEMS, 1):
        row[v] = judgment[v]["위반여부"]
        row[f"e{i}"] = judgment[v]["근거문구"]
    return row


def empty_row(rec_id: str) -> Dict[str, Any]:
    return to_row(rec_id, {v: {"위반여부": 0, "근거문구": ""} for v in ITEMS})


# ===== 7. submission.csv 저장·자가검증 =====
def write_csv(rows: List[Dict[str, Any]], path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with io.open(path, "w", encoding="utf-8", newline="") as f:   # UTF-8(BOM 없음) · RFC4180 quoting
        w = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: unicodedata.normalize("NFC", str(r[k])) for k in COLUMNS})


def validate_csv(path: str, expected_ids: List[str]) -> List[str]:
    """자가검증: 열 49 · 행 수 = 입력 건수 · id 유일·일치 · v 0/1 · e 500자 이하 · 부재탐지 e 빈칸"""
    errs: List[str] = []
    with io.open(path, "r", encoding="utf-8", newline="") as f:
        rd = csv.reader(f)
        header = next(rd, None)
        rows = list(rd)
    if header != COLUMNS:
        errs.append(f"헤더 불일치: {len(header or [])}열 (기대 {len(COLUMNS)})")
        return errs
    if len(rows) != len(expected_ids):
        errs.append(f"행 수 {len(rows)} ≠ 입력 {len(expected_ids)}")
    ids = [r[0] for r in rows]
    if len(set(ids)) != len(ids):
        errs.append("id 중복")
    if set(ids) != set(expected_ids):
        errs.append(f"id 집합 불일치 (누락 {len(set(expected_ids) - set(ids))})")
    absence_idx = {COLUMNS.index("e" + v[1:]) for v in ABSENCE}
    for r in rows:
        if len(r) != len(COLUMNS):
            errs.append(f"{r[0]}: 열 수 {len(r)}")
            continue
        if any(x not in ("0", "1") for x in r[1:25]):
            errs.append(f"{r[0]}: 위반여부에 0/1 아닌 값")
        if any(len(x) > EVIDENCE_MAX for x in r[25:]):
            errs.append(f"{r[0]}: 근거문구 {EVIDENCE_MAX}자 초과")
        if any(r[j] for j in absence_idx):
            errs.append(f"{r[0]}: 부재탐지 항목에 근거문구")
        if any(x.startswith(("=", "+", "@")) for x in r[25:]):
            errs.append(f"{r[0]}: 수식 접두 근거문구")
    return errs


# ===== 8. 실행 =====
def run(input_path: str, out_path: str, runner_cls, limit: Optional[int], chunk: int,
        max_chars: int, data_dir: str, **runner_kw) -> Dict[str, Any]:
    t_all = time.time()
    recs = list(iter_records(input_path, limit=limit))
    log(f"입력 {len(recs)}건 ← {input_path}")
    if not recs:
        write_csv([], out_path)
        return {"건수": 0}

    tbl, schema = item_table(data_dir), decode_schema(data_dir)
    system_prompt = build_system_prompt(tbl)
    runner = runner_cls(schema, **runner_kw)
    log(f"모델 로드 {runner.load_seconds:.1f}s")

    # 실제 제출에서는 배포된 법령 패키지로 RAG를 준비합니다. mock 모드에서는
    # 외부 패키지 없이도 입출력 검증이 되도록 색인을 만들지 않습니다.
    configure_law_index(data_dir, enabled=runner_cls is not MockRunner)

    # 전건 메시지 구성(길이 예산 맞춤)
    msgs_all, shrunk, ntok = [], 0, []
    for rec in recs:
        m, n, mc = fit_to_budget(rec, system_prompt, runner, max_chars)
        msgs_all.append(m)
        ntok.append(n)
        shrunk += int(mc < max_chars)
    log(f"프롬프트 토큰 중앙값 {sorted(ntok)[len(ntok) // 2]:,} · 최대 {max(ntok):,} · 예산 축소 {shrunk}건")

    # 배치 추론
    t_inf = time.time()
    texts: List[str] = []
    for s in range(0, len(msgs_all), chunk):
        texts.extend(run_chunk(runner, msgs_all[s:s + chunk]))
        log(f"  {min(s + chunk, len(msgs_all))}/{len(msgs_all)}건 … {time.time() - t_inf:.0f}s")
    inf_seconds = time.time() - t_inf

    # 파싱·후처리 → 행
    rows, invalid, filled, ev_kept, ev_dropped = [], 0, 0, 0, 0
    for rec, text in zip(recs, texts):
        try:
            parsed, missing = parse_judgment(text)
            invalid += int(len(missing) == 24)
            filled += len(missing)
            before = sum(1 for v in ITEMS if parsed[v]["근거문구"] and parsed[v]["위반여부"] == 1 and v not in ABSENCE)
            final = postprocess(parsed, rec)
            kept = sum(1 for v in ITEMS if final[v]["근거문구"])
            ev_kept += kept
            ev_dropped += before - kept
            rows.append(to_row(rec["id"], final))
        except Exception as e:                           # 한 건의 실패가 전체 실행을 막지 않도록
            log(f"  ! {rec['id']} 후처리 실패 → 전항목 0: {type(e).__name__}: {e}")
            rows.append(empty_row(rec["id"]))
    assert len(rows) == len(recs)

    write_csv(rows, out_path)
    errs = validate_csv(out_path, [r["id"] for r in recs])
    report = {
        "건수": len(recs), "모델로드_s": round(runner.load_seconds, 1), "추론_s": round(inf_seconds, 1),
        "건당_s": round(inf_seconds / len(recs), 2), "전체_s": round(time.time() - t_all, 1),
        "유효JSON": len(recs) - invalid, "메운_항목수": filled,
        "근거_유지": ev_kept, "근거_원문불일치_폐기": ev_dropped,
        "출력": out_path, "자가검증": "PASS" if not errs else errs,
    }
    log(json.dumps(report, ensure_ascii=False))
    if invalid:
        log("[주의] 유효 JSON이 아닌 출력이 있습니다. 구조화 출력 설정과 JSON Schema를 확인하세요.")
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description="24개 항목의 법령 위반 여부 판정 베이스라인")
    ap.add_argument("--data-dir", default=DATA_DIR)
    ap.add_argument("--output-dir", default=OUTPUT_DIR)
    ap.add_argument("--input", default=None, help="기본 = <data-dir>/test.jsonl.gz")
    ap.add_argument("--model-dir", default=MODEL_DIR, help="로컬에서는 HF ID(google/gemma-4-26B-A4B-it)도 가능")
    ap.add_argument("--quantization", default=os.environ.get("PPS_QUANT", QUANT),
                    help="채점 서버 = int8_per_channel_weight_only · 'none'이면 미양자화")
    ap.add_argument("--gpu-mem", type=float, default=0.92)
    ap.add_argument("--tp", type=int, default=1)
    ap.add_argument("--chunk", type=int, default=128, help="LLM.chat 한 번에 넘길 건수")
    ap.add_argument("--max-chars", type=int, default=12000, help="문서 문맥의 초기 글자 상한(토큰 예산에 맞춰 자동 조정)")
    ap.add_argument("--max-tokens", type=int, default=MAX_TOKENS)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--mock", action="store_true", help="모델 없이 흐름만 확인")
    a = ap.parse_args()

    input_path = a.input or os.path.join(a.data_dir, "test.jsonl.gz")
    out_path = os.path.join(a.output_dir, "submission.csv")
    quant = None if str(a.quantization).lower() in ("none", "") else a.quantization
    runner_kw = {} if a.mock else dict(model_dir=a.model_dir, quant=quant, max_tokens=a.max_tokens,
                                       seed=SEED, gpu_mem=a.gpu_mem, tp=a.tp)
    report = run(input_path, out_path, MockRunner if a.mock else VLLMRunner,
                 limit=a.limit, chunk=a.chunk, max_chars=a.max_chars, data_dir=a.data_dir, **runner_kw)
    return 0 if report.get("자가검증") in ("PASS", None) else 1


if __name__ == "__main__":
    sys.exit(main())
