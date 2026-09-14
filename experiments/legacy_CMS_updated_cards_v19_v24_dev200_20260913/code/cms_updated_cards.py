"""Run the explicitly approved CMS cards on their cached dev200 candidates."""

if __name__ == "__main__":
    raise SystemExit("Archived code: create a fresh registered run; see docs/operations.md.")

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import shutil
import statistics
import subprocess
import time
import unicodedata

from nara.inference.conversation import Turn
from nara.inference.engine import VLLMModel


ROOT = Path(__file__).resolve().parents[3]
COMMIT = "615e649e80794556f9ae2d889da99d5c41a8cba4"
ITEMS = tuple(f"v{i}" for i in range(19, 25))
MODEL = ROOT / "models/gemma-4-26B-A4B-it-NVFP4"
DEFAULT_OUT = ROOT / "analysis/CMS_updated_cards_v19_v24_dev200_20260913"
CANDIDATE_HASH = "80259ee689e0b03888311d3a7fcb19cafff161be9408423317f15151f0f33c1b"
CARD_HASH = "68f0a760c779897dd2bce9c3874ea80dd7a5788605d913e60b3403b4449e45bc"
EMPTY = "추출된 원문 후보가 없습니다."
PREFIX = "추출된 원문 후보는 다음과 같다. "


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def write_jsonl(path, rows):
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def _git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def authored_sources():
    paths = _git("ls-tree", "-r", "--name-only", "-z", COMMIT, "--", "user/CMS").decode().split("\0")
    names = {"candidates": "candidates.jsonl",
             "cards": "판정카드_v19-v24_토큰수_제한.md",
             "extraction": "원문_META_추출규칙_v19-v24.md"}
    sources = {}
    for key, name in names.items():
        matches = [p for p in paths if unicodedata.normalize("NFC", p).endswith("/" + name)]
        if len(matches) != 1:
            raise ValueError(f"Expected exactly one CMS source: {name}")
        sources[key] = (matches[0], _git("show", f"{COMMIT}:{matches[0]}"))
    if sha256(sources["candidates"][1]) != CANDIDATE_HASH or sha256(sources["cards"][1]) != CARD_HASH:
        raise ValueError("CMS source hash changed")
    return sources


def card_blocks(source):
    memos = [line for line in source.splitlines() if "PPS-DEV-062" in line and "PPS-DEV-049" in line]
    if len(memos) != 1:
        raise ValueError("The authorized answer-memo line is not unique")
    blocks = re.findall(r"```text\n(.*?)\n```", source, re.S)
    if len(blocks) != 6 or memos[0] not in blocks[-1]:
        raise ValueError("Unexpected CMS card blocks")
    cards = dict(zip(ITEMS, blocks))
    cards["v24"] = cards["v24"].replace(memos[0] + "\n", "")
    for item, card in cards.items():
        if not card.startswith(f"공공 입찰공고의 {item}만 판정하라."):
            raise ValueError(f"Unexpected card identity: {item}")
        if card.count("{META}") != 1 or card.count("{원문후보}") != 1:
            raise ValueError(f"Unexpected placeholders: {item}")
    return cards, {"source_line": source.splitlines().index(memos[0]) + 1,
                   "removed_text": memos[0], "authorization": "KHJ: exclude answer memos only"}


def _scalar(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def _lines(mapping, depth=0):
    result = []
    for key, value in mapping.items():
        prefix = "  " * depth + key + ":"
        if isinstance(value, dict):
            result.append(prefix)
            result.extend(_lines(value, depth + 1))
        else:
            result.append(prefix + " " + _scalar(value))
    return result


def render_card(card, candidates):
    meta = "\n".join(_lines({**candidates["meta"],
        "input_completeness": candidates["input_completeness"],
        "dropped_doc_counts": candidates["dropped_doc_counts"]}))
    texts = [segment["text"] for segment in candidates["segments"]]
    text = PREFIX + ", ".join("'" + piece + "'" for piece in texts) if texts else EMPTY
    # Substitute only the author's placeholders, never interpret candidate text as a template.
    return re.sub(r"\{META\}|\{원문후보\}",
                  lambda match: meta if match[0] == "{META}" else text, card)


def output_schema(item):
    # Only shape/types/binary values; no semantic relationship or evidence repair.
    cell = {"type": "object", "properties": {
        "위반여부": {"type": "integer", "enum": [0, 1]},
        "근거문구": {"type": ["string", "null"]}},
        "required": ["위반여부", "근거문구"], "additionalProperties": False}
    return {"type": "object", "properties": {item: cell},
            "required": [item], "additionalProperties": False}


def token_ids(tokenizer, messages):
    tokenizer.backend_tokenizer.no_truncation()
    tokenizer.backend_tokenizer.no_padding()
    ids = tokenizer.apply_chat_template(messages, tokenize=True, return_dict=False,
        add_generation_prompt=True, enable_thinking=False, truncation=False, padding=False)
    rendered = tokenizer.apply_chat_template(messages, tokenize=False,
        add_generation_prompt=True, enable_thinking=False)
    if ids != tokenizer.backend_tokenizer.encode(rendered, add_special_tokens=False).ids:
        raise ValueError("Chat-template tokens differ from untruncated raw encoding")
    return ids


def check_budget(record_id, item, count):
    limit = 2024 if (record_id, item) == ("PPS-DEV-189", "v24") else 2000
    if count > limit:
        raise ValueError(f"Unapproved input-token overage: {record_id}/{item}={count}>{limit}")


def prepare(out):
    started = time.monotonic()
    out.mkdir(parents=True, exist_ok=True)
    if (out / "manifest.json").exists() or (out / "inputs.jsonl").exists():
        raise FileExistsError("Prepared inputs already exist; never overwrite a frozen experiment")
    source = out / "source"
    source.mkdir(exist_ok=True)
    sources = authored_sources()
    cards, exclusion = card_blocks(sources["cards"][1].decode())
    candidates = [json.loads(line) for line in sources["candidates"][1].decode().splitlines()]
    originals = read_jsonl(ROOT / "data/dev.jsonl")
    if len(candidates) != 200 or len({r["id"] for r in candidates}) != 200:
        raise ValueError("Expected 200 unique CMS candidate records")
    if [r["id"] for r in candidates] != [r["id"] for r in originals]:
        raise ValueError("Candidate notice order/coverage differs from dev200")
    for row in candidates:
        if tuple(row["items"]) != ITEMS:
            raise ValueError("Candidate item ordering/coverage changed")
    names = {"candidates": "candidates.jsonl", "cards": "cards_original.txt",
             "extraction": "extraction_original.txt"}
    for key, (_, data) in sources.items():
        (source / names[key]).write_bytes(data)
    (source / "cards").mkdir(exist_ok=True)
    for key, card in cards.items():
        (source / "cards" / f"{key}.txt").write_text(card)
    dump(source / "memo_exclusion.json", exclusion)
    schemas = {key: output_schema(key) for key in ITEMS}
    dump(out / "schemas.json", schemas)
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(MODEL, local_files_only=True)
    inputs = []
    for row in candidates:
        for item in ITEMS:
            candidate = row["items"][item]
            messages = [{"role": "user", "content": render_card(cards[item], candidate)}]
            ids = token_ids(tokenizer, messages)
            check_budget(row["id"], item, len(ids))
            inputs.append({"id": row["id"], "item": item, "task_id": f"{row['id']}:{item}",
                "messages": messages, "schema": schemas[item], "input_tokens": len(ids),
                "prompt_token_ids": ids, "candidate_count": len(candidate["segments"])})
    write_jsonl(out / "inputs.jsonl", inputs)
    for name in ("src/experiments/cms_updated_cards.py", "src/inference/engine.py",
                 "src/inference/conversation.py", "src/inference/predictor.py", "pyproject.toml", "uv.lock"):
        target = source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    stats = {}
    for item in ITEMS:
        selected = [r for r in inputs if r["item"] == item]
        lengths = [r["input_tokens"] for r in selected]
        stats[item] = {"min": min(lengths), "median": statistics.median(lengths),
                       "max": max(lengths), "empty_candidates": sum(r["candidate_count"] == 0 for r in selected)}
    manifest = {"experiment": out.name, "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": COMMIT, "implementation_head": _git("rev-parse", "HEAD").decode().strip(),
        "sources": {key: {"git_path": p, "sha256": sha256(data)} for key, (p, data) in sources.items()},
        "dev_sha256": sha256((ROOT / "data/dev.jsonl").read_bytes()),
        "expected_requests": 1200, "notice_count": 200, "items": ITEMS,
        "model": str(MODEL.relative_to(ROOT)), "thinking": False, "temperature": 0, "seed": 0,
        "output_tokens": 512, "concurrency": 16, "max_model_len": 32768,
        "max_num_batched_tokens": 8192, "gpu_memory_utilization": 0.86,
        "prefix_caching": True, "request_order": "uploaded notice order, then v19 through v24",
        "warmup": "engine initialization only; no extra inference requests",
        "extraction": {"status": "skipped", "seconds": None},
        "runtime_scope": "cached-candidate input preparation, model load, one-pass inference; no full-pipeline time",
        "interpretation": "dev-developed cards/candidates; no unseen-data generalization validation",
        "format": {"candidate_prefix": PREFIX, "join": ", ", "quote": "'", "empty": EMPTY,
                   "source_headers_visible": False, "budget_truncated_visible": False},
        "authorized_input_exception": {"id": "PPS-DEV-189", "item": "v24", "max_tokens": 2024},
        "input_statistics": stats,
        "artifact_sha256": {str(p.relative_to(out)): sha256(p.read_bytes())
                            for p in sorted(out.rglob("*")) if p.is_file() and p.name != "source_alignment.json"},
        "preparation_seconds": time.monotonic() - started}
    dump(out / "manifest.json", manifest)
    print(json.dumps({"stage": "prepared", "requests": len(inputs), "statistics": stats}), flush=True)
    return manifest


class RecordedCMSModel(VLLMModel):
    """Use the existing engine while preserving its unmodified raw token output."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.raw_outputs = {}

    def render_messages(self, messages):
        return token_ids(self.tokenizer, messages)

    def _reply(self, output, budget):
        completion = output.outputs[0]
        self.raw_outputs[output.request_id] = {
            "text": self.tokenizer.decode(completion.token_ids, skip_special_tokens=False),
            "token_ids": list(completion.token_ids), "finish_reason": completion.finish_reason,
            "stop_reason": completion.stop_reason}
        return super()._reply(output, budget)


def execute_once(stream, inputs, on_result, submitted):
    """Refill up to sixteen independent requests after each engine completion step."""
    queue = iter(inputs)
    active = set()
    exhausted = False
    while active or not exhausted:
        while len(active) < 16 and not exhausted:
            row = next(queue, None)
            if row is None:
                exhausted = True
                break
            stream.submit(Turn(row["task_id"], row["messages"], row["schema"], 512))
            active.add(row["task_id"])
            submitted.add(row["task_id"])
        if not active:
            break
        for task_id, reply in stream.poll():
            active.remove(task_id)
            on_result(task_id, reply)


def run(out):
    manifest = json.loads((out / "manifest.json").read_text())
    if (out / "predictions.jsonl").exists() or (out / "predictions_frozen.json").exists():
        raise FileExistsError("One-pass experiment already started; no result-driven reruns")
    for name, expected in manifest["artifact_sha256"].items():
        if sha256((out / name).read_bytes()) != expected:
            raise ValueError(f"Frozen artifact changed: {name}")
    audit = json.loads((out / "source_alignment.json").read_text())
    if not audit["passed"] or audit["candidate_sha256"] != CANDIDATE_HASH or audit["card_sha256"] != CARD_HASH:
        raise ValueError("Independent source-alignment audit did not pass")
    if audit["dev_sha256"] != manifest["dev_sha256"] or sha256((ROOT / "data/dev.jsonl").read_bytes()) != manifest["dev_sha256"]:
        raise ValueError("Original dev sources changed after source alignment")
    # Refuse silently changed execution code even if prepared prompts still match.
    for name in ("src/experiments/cms_updated_cards.py", "src/inference/engine.py",
                 "src/inference/conversation.py", "src/inference/predictor.py"):
        if (ROOT / name).read_bytes() != (out / "source" / name).read_bytes():
            raise ValueError(f"Execution code changed after input freeze: {name}")
    inputs = read_jsonl(out / "inputs.jsonl")
    by_id = {row["task_id"]: row for row in inputs}
    if len(inputs) != 1200 or len(by_id) != 1200:
        raise ValueError("Frozen request set is incomplete or duplicated")
    started = time.monotonic()
    model = RecordedCMSModel(MODEL, thinking=False, max_model_len=32768,
        max_num_seqs=16, max_num_batched_tokens=8192, enable_chunked_prefill=True,
        collect_scheduler_stats=True, gpu_memory_utilization=0.86)
    import torch
    torch.cuda.synchronize()
    load_seconds = time.monotonic() - started
    check_started = time.monotonic()
    for row in inputs:
        if model.render_messages(row["messages"]) != row["prompt_token_ids"]:
            raise ValueError(f"Engine tokenizer differs from frozen input: {row['task_id']}")
    revalidation_seconds = time.monotonic() - check_started
    cache_reset = model.reset_prefix_cache()
    if not cache_reset:
        raise RuntimeError("Could not establish the agreed empty prefix cache at start")
    engine = model.engine_info()
    cfg = model.llm.llm_engine.vllm_config
    engine.update({"max_model_len": cfg.model_config.max_model_len,
        "enable_prefix_caching": cfg.cache_config.enable_prefix_caching,
        "num_gpu_blocks": cfg.cache_config.num_gpu_blocks,
        "block_size": cfg.cache_config.block_size})
    dump(out / "engine.json", engine)
    stream = model.stream()
    saved, submitted = set(), set()
    error = None
    inference_started = time.monotonic()
    with (out / "predictions.jsonl").open("x", encoding="utf-8") as handle, model.observe_scheduler() as scheduler:
        def record(task_id, reply):
            row = by_id[task_id]
            metrics = next(r for r in reversed(stream.rows) if r["task_id"] == task_id)
            payload = {"id": row["id"], "item": row["item"], "task_id": task_id,
                "status": "completed", "reply": asdict(reply),
                "raw": model.raw_outputs[metrics["request_id"]], "error": None}
            if reply.input_tokens != row["input_tokens"]:
                raise ValueError(f"Engine input length differs: {task_id}")
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
            handle.flush()
            saved.add(task_id)
            if len(saved) % 50 == 0 or len(saved) == len(inputs):
                print(json.dumps({"stage": "inference", "completed": len(saved),
                    "seconds": time.monotonic() - inference_started}), flush=True)
        try:
            execute_once(stream, inputs, record, submitted)
            torch.cuda.synchronize()
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            pending = {turn.task_id: rid for rid, (turn, _) in stream.pending.items()}
            stream.abort()
            for task_id, row in by_id.items():
                if task_id not in saved:
                    handle.write(json.dumps({"id": row["id"], "item": row["item"], "task_id": task_id,
                        "status": "engine_error" if task_id in submitted else "not_submitted",
                        "reply": None, "raw": model.raw_outputs.get(pending.get(task_id)),
                        "error": error}, ensure_ascii=False) + "\n")
        elapsed = time.monotonic() - inference_started
    write_jsonl(out / "request_timings.jsonl", stream.rows)
    write_jsonl(out / "lifecycle.jsonl", stream.lifecycle)
    write_jsonl(out / "scheduler.jsonl", scheduler)
    frozen = {"sha256": sha256((out / "predictions.jsonl").read_bytes()),
        "rows": len(read_jsonl(out / "predictions.jsonl")),
        "frozen_utc": datetime.now(timezone.utc).isoformat(), "evaluation_not_started": True}
    dump(out / "predictions_frozen.json", frozen)
    summary = {"preparation_seconds": manifest["preparation_seconds"],
        "model_load_seconds": load_seconds, "input_revalidation_seconds": revalidation_seconds,
        "inference_seconds": elapsed, "extraction_seconds": None, "extraction_status": "skipped",
        "cache_reset_before_run": cache_reset, "engine": engine,
        "hardware": {"gpu": torch.cuda.get_device_name(0),
            "gpu_total_bytes": torch.cuda.get_device_properties(0).total_memory},
        "versions": {p: importlib.metadata.version(p) for p in ("vllm", "torch", "transformers", "xgrammar")},
        "completed": len(saved), "submitted": len(submitted), "expected_requests": len(inputs),
        "input_tokens": sum(r["input_tokens"] for r in stream.rows),
        "output_tokens": sum(r["output_tokens"] for r in stream.rows),
        "cached_tokens": sum(r["cached_tokens"] for r in stream.rows),
        "max_inflight": max((r["inflight"] for r in stream.lifecycle), default=0),
        "error": error, "prediction_sha256": frozen["sha256"],
        "manifest_sha256": sha256((out / "manifest.json").read_bytes()),
        "source_alignment_sha256": sha256((out / "source_alignment.json").read_bytes())}
    dump(out / "run_summary.json", summary)
    print(json.dumps({"stage": "frozen", **summary}, ensure_ascii=False), flush=True)
    if error:
        raise RuntimeError(error)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "run"))
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    (prepare if args.command == "prepare" else run)(args.output.resolve())


if __name__ == "__main__":
    raise SystemExit("Archived experiment: create a new registered run; see docs/operations.md. Historical evidence is read-only.")
    main()
