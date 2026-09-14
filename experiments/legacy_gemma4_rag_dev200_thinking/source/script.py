"""Dynamic RAG baseline. Run python script.py --help for local experiments."""
import argparse
from dataclasses import asdict
import csv
import gzip
import json
import logging
import os
from pathlib import Path
import time

# Set before loading BGE/CUDA; vLLM workers must spawn after CUDA initialization.
os.environ.setdefault("VLLM_WORKER_MULTIPROC_METHOD", "spawn")
os.environ.setdefault("OMP_NUM_THREADS", "4")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "4")
os.environ.setdefault("MAX_JOBS", "2")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

from nara.inference import Limits, Predictor


def read_records(path, limit=None):
    opener = gzip.open if str(path).endswith(".gz") else open
    records, seen = [], set()
    with opener(path, "rt", encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            record = json.loads(line)
            if (not isinstance(record.get("id"), str) or not record["id"]
                    or record["id"] in seen or not isinstance(record.get("meta"), dict)
                    or not isinstance(record.get("docs"), list) or not record["docs"]
                    or any(not isinstance(d.get("text"), str)
                           or "type" not in d or "doc_id" not in d for d in record["docs"])
                    or not any(d["type"] == "공고문" for d in record["docs"])):
                raise ValueError("Invalid or duplicate input record")
            seen.add(record["id"])
            records.append(record)
            if limit is not None and len(records) >= limit:
                break
    return records


def write_submission(results, path):
    if any(result.error or result.judgments is None for result in results):
        raise ValueError("Prediction failures: see trace.jsonl; submission was not written")
    items = [f"v{i}" for i in range(1, 25)]
    for result in results:
        if set(result.judgments) != set(items):
            raise ValueError(f"Incomplete judgment: {result.record_id}")
    path = Path(path)
    temporary = path.with_suffix(".csv.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["id"] + items + [f"e{i}" for i in range(1, 25)])
        writer.writeheader()
        for result in results:
            row = {"id": result.record_id}
            for key, value in result.judgments.items():
                row[key] = value["위반여부"]
                row["e" + key[1:]] = value["근거문구"] or ""
            writer.writerow(row)
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default=os.environ.get("PPS_DATA_DIR", "data"))
    parser.add_argument("--input", help="Defaults to test.jsonl.gz, or local test.jsonl")
    parser.add_argument("--output-dir", default=os.environ.get("PPS_OUTPUT_DIR", "output"))
    parser.add_argument("--model-dir", default=os.environ.get(
        "PPS_MODEL_DIR", "models/gemma-4-26B-A4B-it-NVFP4"))
    parser.add_argument("--embed-model", default=os.environ.get("PPS_EMBED_DIR", "models/bge-m3"))
    parser.add_argument("--index", default="model/legal_index")
    parser.add_argument("--embed-device", choices=["cpu", "cuda"], default="cuda")
    parser.add_argument("--embedding-batch-size", type=int, default=32)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--max-model-len", type=int, default=32768)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.86)
    parser.add_argument("--quantization", default="auto")
    parser.add_argument("--enforce-eager", action="store_true")
    parser.add_argument("--thinking", action="store_true")
    parser.add_argument("--output-tokens", type=int, help="2048 by default; 4096 with thinking")
    parser.add_argument("--search-rounds", type=int, default=2)
    parser.add_argument("--require-search", action="store_true",
                        help="Require search before judgment; use --search-rounds 1 for exactly once")
    parser.add_argument("--queries-per-round", type=int, default=4)
    parser.add_argument("--round-tokens", type=int, default=4096)
    parser.add_argument("--total-retrieval-tokens", type=int, default=8192)
    parser.add_argument("--item-group-size", type=int, default=24,
                        help="24 = one conversation; e.g. 6 = four independent conversations")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    if not 1 <= args.item_group_size <= 24 or (args.limit is not None and args.limit < 1):
        parser.error("item-group-size must be 1..24 and limit must be positive")
    logging.basicConfig(level=logging.INFO, format="[rag] %(message)s")
    started = time.monotonic()
    data_dir, output_dir = Path(args.data_dir), Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    # Do not allow an old successful file to masquerade as this run's result.
    if (output_dir / "submission.csv").exists():
        parser.error("output-dir already contains submission.csv; select a fresh output directory")
    input_path = Path(args.input) if args.input else data_dir / "test.jsonl.gz"
    if not args.input and not input_path.exists():
        input_path = data_dir / "test.jsonl"
    records = read_records(input_path, args.limit)
    table = json.loads((data_dir / "항목표.json").read_text())["항목"]
    schema = json.loads((data_dir / "정답스키마_디코딩.json").read_text())["properties"]["판정"]
    limits = Limits(batch_size=args.batch_size, search_rounds=args.search_rounds,
                    require_search=args.require_search,
                    queries_per_round=args.queries_per_round, round_tokens=args.round_tokens,
                    total_retrieval_tokens=args.total_retrieval_tokens,
                    output_tokens=(args.output_tokens if args.output_tokens is not None
                                   else (4096 if args.thinking else 2048)))
    from nara.retrieval import BGEEncoder, LegalRetriever
    from nara.vllm_model import VLLMModel
    encoder = BGEEncoder(args.embed_model, device=args.embed_device,
                         batch_size=args.embedding_batch_size)
    retriever = LegalRetriever(args.index, encoder)
    model = VLLMModel(args.model_dir, max_model_len=args.max_model_len,
                      gpu_memory_utilization=args.gpu_memory_utilization,
                      max_num_seqs=args.batch_size, quantization=args.quantization,
                      thinking=args.thinking, enforce_eager=args.enforce_eager)
    loaded = time.monotonic()
    predictor = Predictor(model, retriever, table, schema, limits=limits)
    keys = list(table)
    groups = [keys[i:i + args.item_group_size] for i in range(0, len(keys), args.item_group_size)]
    results = predictor.predict(records, item_groups=groups)
    with (output_dir / "trace.jsonl").open("w") as stream:
        for result in results:
            stream.write(json.dumps(asdict(result), ensure_ascii=False) + "\n")
    import torch
    report = {"records": len(results), "failed": sum(bool(r.error) for r in results),
              "load_seconds": loaded - started, "total_seconds": time.monotonic() - started,
              "gpu": torch.cuda.get_device_name(0), "options": vars(args),
              "limits": asdict(limits), **predictor.metrics}
    events = [event for result in results for task in result.trace for event in task["events"]]
    report["input_tokens"] = sum(event.get("input_tokens", 0) for event in events)
    report["output_tokens"] = sum(event.get("output_tokens", 0) for event in events)
    report["search_rounds"] = sum(event["event"] == "search" for event in events)
    report["search_queries"] = sum(len(event["queries"]) for event in events if event["event"] == "search")
    # predictor total excludes initialization; retain both quantities.
    report["prediction_seconds"] = predictor.metrics["total_seconds"]
    report["total_seconds"] = time.monotonic() - started
    (output_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False), flush=True)
    write_submission(results, output_dir / "submission.csv")


if __name__ == "__main__":
    main()
