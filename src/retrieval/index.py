"""Build and query a local legal index: python -m nara.retrieval.index --help."""
import argparse
from bisect import bisect_left
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import time
from xml.etree import ElementTree as ET
import zipfile
import csv

import numpy as np

from .search import BGEEncoder, BGE_REVISION, LegalRetriever, file_sha256, normalized


@dataclass(frozen=True)
class SourceText:
    source: str
    locator: str
    title: str
    text: str


def _tag(element):
    return element.tag.rsplit("}", 1)[-1]


def _xml_text(element, *, skip_tables=False):
    tag = _tag(element)
    if skip_tables and tag == "tbl":
        return ""
    if tag == "t":
        return "".join(element.itertext())
    if tag == "lineBreak":
        return "\n"
    if tag == "tab":
        return "\t"
    text = "".join(_xml_text(child, skip_tables=skip_tables) for child in element)
    return text + ("\n" if tag == "p" else "")


def _table_rows(table):
    """Expand merged cells so every product retains its parent classification."""
    grid, header_rows = {}, set()
    for row in table:
        if _tag(row) != "tr":
            continue
        for cell in row:
            if _tag(cell) != "tc":
                continue
            address = next(e for e in cell if _tag(e) == "cellAddr")
            span = next(e for e in cell if _tag(e) == "cellSpan")
            x, y = int(address.attrib["colAddr"]), int(address.attrib["rowAddr"])
            width, height = int(span.attrib["colSpan"]), int(span.attrib["rowSpan"])
            value = " ".join(_xml_text(cell).split())
            if cell.attrib.get("header") == "1":
                header_rows.add(y)
            for dy in range(height):
                for dx in range(width):
                    grid[y + dy, x + dx] = value
    if not grid:
        return []
    columns = max(x for _, x in grid) + 1
    labels = []
    for x in range(columns):
        parts = dict.fromkeys(grid.get((y, x), "") for y in sorted(header_rows))
        labels.append(" / ".join(p for p in parts if p) or f"열{x + 1}")
    rows = []
    for y in sorted({y for y, _ in grid} - header_rows):
        fields = [f"{labels[x]}: {grid[y, x]}" for x in range(columns)
                  if grid.get((y, x), "").strip()]
        if fields:
            rows.append((y + 1, "\n".join(fields)))
    return rows


def read_sources(corpus_dir):
    corpus_dir = Path(corpus_dir)
    documents, sources = [], []
    files = sorted(p for p in corpus_dir.rglob("*") if p.is_file())
    if not files:
        raise ValueError("The legal corpus is empty")
    for path in files:
        source = path.relative_to(corpus_dir).as_posix()
        title = path.stem
        sources.append({"path": source, "sha256": file_sha256(path),
                        "bytes": path.stat().st_size})
        if path.suffix == ".txt":
            documents.append(SourceText(source, "text", title, path.read_text(encoding="utf-8-sig")))
        elif path.suffix == ".csv":
            with path.open(encoding="utf-8-sig", newline="") as stream:
                for row_num, row in enumerate(csv.DictReader(stream), 2):
                    if None in row or any(value is None for value in row.values()):
                        raise ValueError(f"Malformed CSV row: {source}:{row_num}")
                    text = "\n".join(f"{key}: {value}" for key, value in row.items() if value.strip())
                    if text:
                        documents.append(SourceText(source, f"row:{row_num}", title, text))
        elif path.suffix == ".hwpx":
            with zipfile.ZipFile(path) as archive:
                sections = sorted(
                    name for name in archive.namelist()
                    if re.fullmatch(r"Contents/section\d+\.xml", name)
                )
                if not sections:
                    raise ValueError(f"No HWPX text sections: {source}")
                for name in sections:
                    root = ET.fromstring(archive.read(name))
                    body = _xml_text(root, skip_tables=True)
                    if body.strip():
                        documents.append(SourceText(source, name, title, body))
                    for table_num, table in enumerate(
                        (e for e in root.iter() if _tag(e) == "tbl"), 1
                    ):
                        for row_num, text in _table_rows(table):
                            locator = f"{name}/table:{table_num}/row:{row_num}"
                            documents.append(SourceText(source, locator, title, text))
        else:
            raise ValueError(f"Unsupported legal source format: {source}")
    if (not documents or any(not d.text.strip() for d in documents)
            or {d.source for d in documents} != {s["path"] for s in sources}):
        raise ValueError("A legal source contains no extractable text")
    return documents, sources


HEADING = re.compile(r"(?m)^(제\s*\d+(?:조(?:의\s*\d+)?|장|절|관)(?:\([^)\n]*\))?)")


def passages_for(document, tokenizer, *, chunk_tokens=512, overlap_tokens=64):
    if not 0 <= overlap_tokens < chunk_tokens:
        raise ValueError("Require 0 <= overlap_tokens < chunk_tokens")
    matches = list(HEADING.finditer(document.text))
    sections = [(0, "")]
    sections.extend((m.start(), m.group(1)) for m in matches if m.start() != 0)
    if matches and matches[0].start() == 0:
        sections[0] = (0, matches[0].group(1))
    for i, (section_start, section) in enumerate(sections):
        section_end = sections[i + 1][0] if i + 1 < len(sections) else len(document.text)
        text = document.text[section_start:section_end]
        if not text.strip():
            continue
        prefix = document.title + ("\n" + section if section else "") + "\n"
        prefix_tokens = len(tokenizer(prefix, add_special_tokens=True)["input_ids"])
        available = chunk_tokens - prefix_tokens - 8
        if available <= overlap_tokens + 1:
            raise ValueError(f"Chunk budget too small for source title: {document.title}")
        offsets = tokenizer(
            text, add_special_tokens=False, return_offsets_mapping=True,
            truncation=False, verbose=False,
        )["offset_mapping"]
        if not offsets:
            raise ValueError(f"No tokens for source: {document.source}")
        starts = [start for start, _ in offsets]
        begin = 0
        while begin < len(offsets):
            stop = min(len(offsets), begin + available)
            lo = 0 if begin == 0 else offsets[begin][0]
            hi = len(text) if stop == len(offsets) else offsets[stop][0]
            if stop < len(offsets):
                newline = text.rfind("\n", lo + (hi - lo) // 2, hi)
                if newline >= 0:
                    cut = newline + 1
                    cut_stop = bisect_left(starts, cut)
                    if cut_stop > begin + overlap_tokens:
                        stop, hi = cut_stop, cut
            while len(tokenizer(prefix + text[lo:hi], add_special_tokens=True)["input_ids"]) > chunk_tokens:
                stop -= 1
                if stop <= begin + overlap_tokens:
                    raise ValueError("Cannot split text within the requested token budget")
                hi = offsets[stop][0]
            identity = f"{document.source}\0{document.locator}\0{section_start + lo}\0{section_start + hi}"
            yield {
                "id": hashlib.sha256(identity.encode()).hexdigest()[:24],
                "source": document.source, "locator": document.locator,
                "title": document.title, "section": section,
                "char_start": section_start + lo, "char_end": section_start + hi,
                "text": text[lo:hi], "embedding_text": prefix + text[lo:hi],
            }
            if stop == len(offsets):
                break
            begin = max(begin + 1, stop - overlap_tokens)


def build_index(corpus_dir, output_dir, encoder, *, chunk_tokens=512, overlap_tokens=64):
    started = time.monotonic()
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise FileExistsError(f"Index already exists; choose a new output directory: {output_dir}")
    documents, sources = read_sources(corpus_dir)
    passages = [p for d in documents for p in passages_for(
        d, encoder.tokenizer, chunk_tokens=chunk_tokens, overlap_tokens=overlap_tokens,
    )]
    print(f"Extracted {len(documents)} text entries, {len(passages)} passages from {len(sources)} files.",
          flush=True)
    vectors = normalized(encoder.encode([p["embedding_text"] for p in passages]))
    if vectors.shape != (len(passages), encoder.signature["dimension"]):
        raise ValueError("Corpus encoder returned an unexpected shape")
    manifest = {
        "format_version": 1, "encoder": encoder.signature,
        "chunking": {"tokens": chunk_tokens, "overlap_tokens": overlap_tokens,
                     "method": "section-paragraph-token-v1"},
        "sources": sources, "source_text_count": len(documents),
        "passage_count": len(passages), "dimension": vectors.shape[1],
        "vector_bytes": vectors.nbytes,
        "passages_by_source": dict(Counter(p["source"] for p in passages)),
        "duplicate_text_count": len(passages) - len({" ".join(p["text"].split()) for p in passages}),
    }
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".legal-index-", dir=output_dir.parent) as staging:
        staging = Path(staging)
        (staging / "passages.jsonl").write_text(
            "".join(json.dumps(p, ensure_ascii=False) + "\n" for p in passages), encoding="utf-8",
        )
        np.save(staging / "embeddings.npy", vectors, allow_pickle=False)
        manifest["artifacts"] = {
            name: file_sha256(staging / name) for name in ("passages.jsonl", "embeddings.npy")
        }
        manifest["build_seconds"] = round(time.monotonic() - started, 3)
        (staging / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
        )
        # Validate the complete artifact through the same interface used by inference.
        LegalRetriever(staging, encoder)
        if output_dir.exists():
            raise FileExistsError(output_dir)
        staging.rename(output_dir)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "search"))
    parser.add_argument("--index", default="model/legal_index")
    parser.add_argument("--corpus", default="data/법령패키지")
    parser.add_argument("--embed-model", default=os.environ.get("PPS_EMBED_DIR", "models/bge-m3"))
    parser.add_argument("--revision", default=BGE_REVISION)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--chunk-tokens", type=int, default=512)
    parser.add_argument("--overlap-tokens", type=int, default=64)
    parser.add_argument("--query", action="append")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    if args.action == "build" and Path(args.index).exists():
        parser.error("Index already exists; choose a new --index path")
    if args.action == "search" and not args.query:
        parser.error("search requires at least one --query")
    started = time.monotonic()
    encoder = BGEEncoder(args.embed_model, device=args.device,
                         batch_size=args.batch_size, revision=args.revision)
    load_seconds = time.monotonic() - started
    if args.action == "build":
        manifest = build_index(args.corpus, args.index, encoder,
                               chunk_tokens=args.chunk_tokens, overlap_tokens=args.overlap_tokens)
        result = {"index": args.index, "passages": manifest["passage_count"],
                  "vector_mib": round(manifest["vector_bytes"] / 1024**2, 2)}
    else:
        retriever = LegalRetriever(args.index, encoder)
        result = {
            key: [hit.to_dict() for hit in hits]
            for key, hits in retriever.search(
                {str(i): query for i, query in enumerate(args.query)}, top_k=args.top_k,
            ).items()
        }
    print(json.dumps({"result": result, "model_load_seconds": round(load_seconds, 3),
                      "total_seconds": round(time.monotonic() - started, 3)},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
