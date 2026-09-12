"""Check source coverage and real retrieval; compare separately loaded GPU/CPU encoders."""
import argparse
import json
from pathlib import Path
import time

import numpy as np
import torch

from nara.retrieval.index import read_sources
from nara.retrieval.search import BGEEncoder, LegalRetriever


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", default="model/legal_index")
    parser.add_argument("--corpus", default="data/법령패키지")
    parser.add_argument("--embed-model", default="models/bge-m3")
    parser.add_argument("--output", default="analysis/legal_retrieval_check.json")
    args = parser.parse_args()
    torch.set_num_threads(4)
    torch.cuda.reset_peak_memory_stats()
    started = time.monotonic()
    encoder = BGEEncoder(args.embed_model, device="cuda")
    retriever = LegalRetriever(args.index, encoder)
    documents, _ = read_sources(args.corpus)
    by_source = {(d.source, d.locator): d for d in documents}
    coverage = {key: bytearray(len(d.text)) for key, d in by_source.items()}
    for passage in retriever.passages:
        key = passage["source"], passage["locator"]
        text = by_source[key].text
        lo, hi = passage["char_start"], passage["char_end"]
        assert text[lo:hi] == passage["text"], passage["id"]
        coverage[key][lo:hi] = b"\1" * (hi - lo)
    missing = sum(
        sum(1 for i, c in enumerate(d.text) if not c.isspace() and not coverage[key][i])
        for key, d in by_source.items()
    )
    assert missing == 0, missing
    lengths = encoder.tokenizer(
        [p["embedding_text"] for p in retriever.passages],
        add_special_tokens=True, return_length=True,
    )["length"]
    limit = retriever.manifest["chunking"]["tokens"]
    assert max(lengths) <= limit, max(lengths)
    queries = {
        "eligibility": "경쟁입찰에 참가하기 위한 자격 요건 허가 인가 면허 사업자등록",
        "software": "중소 소프트웨어사업자 사업 참여 지원 대기업 참여 제한 사업금액 하한",
        "direct_production": "중소기업자간 경쟁제품 직접생산 확인 증명서",
        "product": "1017161101 석회질비료",
    }
    expected_sources = {
        "eligibility": "국가를 당사자로 하는 계약에 관한 법률 시행규칙",
        "software": "중소 소프트웨어사업자의 사업 참여 지원에 관한 지침",
        "direct_production": "중소기업자간 경쟁제품 직접생산 확인기준",
        "product": "중기부고시_경쟁제품_세부품명.csv",
    }

    def measure(searcher, *, cuda):
        if cuda:
            torch.cuda.synchronize()
        before = time.monotonic()
        result = searcher.search(queries, top_k=5)
        if cuda:
            torch.cuda.synchronize()
        return result, round(time.monotonic() - before, 4)

    hits, cold_gpu = measure(retriever, cuda=True)
    gpu_vectors = encoder.encode(list(queries.values()))
    gpu_times = [measure(retriever, cuda=True)[1] for _ in range(3)]
    peak_gpu_mib = torch.cuda.max_memory_allocated() / 1024**2
    # Reload original FP32 weights; upcasting an FP16 model would round the CPU reference.
    cpu_encoder = BGEEncoder(args.embed_model, device="cpu")
    cpu_retriever = LegalRetriever(args.index, cpu_encoder)
    cpu_vectors = cpu_encoder.encode(list(queries.values()))
    cpu_hits, _ = measure(cpu_retriever, cuda=False)
    cpu_times = [measure(cpu_retriever, cuda=False)[1] for _ in range(3)]
    cosines = (gpu_vectors * cpu_vectors).sum(axis=1)
    assert np.all(cosines > 0.995), cosines
    for key, expected in expected_sources.items():
        assert any(expected in h.source for h in hits[key]), key
        assert any(expected in h.source for h in cpu_hits[key]), key
    report = {
        "passages": len(retriever.passages), "source_texts": len(documents),
        "uncovered_non_whitespace_characters": missing,
        "max_passage_tokens": max(lengths), "gpu": torch.cuda.get_device_name(0),
        "cpu_threads": 4, "query_count": len(queries),
        "first_gpu_search_seconds": cold_gpu,
        "warm_gpu_search_seconds": gpu_times, "warm_cpu_search_seconds": cpu_times,
        "gpu_peak_allocated_mib": round(peak_gpu_mib, 2),
        "cpu_gpu_embedding_cosines": [float(x) for x in cosines],
        "cpu_reference": "Separately loaded original FP32 weights",
        "queries": {
            key: {"text": queries[key], "expected_source_found": True,
                  "hits": [h.to_dict() for h in hits[key]],
                  "cpu_top_passage": cpu_hits[key][0].passage_id,
                  "same_top_passage": cpu_hits[key][0].passage_id == hits[key][0].passage_id}
            for key in queries
        },
        "total_seconds": round(time.monotonic() - started, 3),
        "scope": "Source-text coverage and four retrieval smoke queries; not RAG accuracy or co-resident Gemma throughput.",
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key != "queries"},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
