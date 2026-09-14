"""jsonl 레코드를 건별 markdown 파일로 펼친다.

사용법:
    python3 src/tools/jsonl_to_md.py data/dev.jsonl data/dev_md --labels data/dev_labels.csv
    python3 src/tools/jsonl_to_md.py data/train_unlabeled.jsonl data/train_md

라벨 csv가 없으면 라벨 표의 위반·근거 칸을 비워 둔다.
"""
import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ITEMS = json.loads((ROOT / "data" / "항목표.json").read_text(encoding="utf-8"))
ABSENT = set(ITEMS["부재탐지항목"])
NAMES = {k: v["항목명"] for k, v in ITEMS["항목"].items()}


def cell(s):
    """표 칸에 넣을 문자열: 줄바꿈과 | 를 이스케이프한다."""
    return str(s).replace("|", "\\|").replace("\n", "<br>")


def fence(text):
    """본문에 ``` 가 들어 있어도 깨지지 않도록 더 긴 펜스를 고른다."""
    n = 3
    while "`" * n in text:
        n += 1
    return "`" * n


def render(rec, label):
    out = [f"# {rec['id']}", "", "## 라벨", "",
           "| 항목 | 항목명 | 위반 | 근거 문구 |", "|---|---|---|---|"]
    for i in range(1, 25):
        k = f"v{i}"
        v = label.get(k, "") if label else ""
        e = "(부재탐지)" if k in ABSENT else (label.get(f"e{i}", "") if label else "")
        out.append(f"| {k} | {NAMES[k]} | {v} | {cell(e)} |")

    out += ["", "## 메타", "", "| 필드 | 값 |", "|---|---|"]
    for k, v in rec["meta"].items():
        out.append(f"| {k} | {'null' if v is None else cell(v)} |")
    dropped = ", ".join(f"{t} {n}건" for t, n in rec["dropped_doc_counts"].items()) or "없음"
    comp = ", ".join(f"{k}={'예' if v else '아니오'}" for k, v in rec["input_completeness"].items())
    out += ["", f"제외된 문서: {dropped}  ", f"입력 완전성: {comp}"]

    for d in rec["docs"]:
        f = fence(d["text"])
        out += ["", f"## {d['doc_id']} · {d['type']} ({len(d['text']):,}자)", "",
                f"{f}text", d["text"], f]
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jsonl")
    ap.add_argument("outdir")
    ap.add_argument("--labels")
    a = ap.parse_args()

    labels = {}
    if a.labels:
        with open(a.labels, encoding="utf-8", newline="") as f:
            labels = {r["id"]: r for r in csv.DictReader(f)}

    outdir = Path(a.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(a.jsonl, encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            (outdir / f"{rec['id']}.md").write_text(render(rec, labels.get(rec["id"])), encoding="utf-8")
            n += 1
    print(f"{n} files -> {outdir}")


if __name__ == "__main__":
    main()
