"""Real GPU checks: bounded searches, grouping, long source, and thinking."""
import argparse
from dataclasses import asdict
import copy
import json
from pathlib import Path
import time

from nara.records import read_records, write_submission
from nara.inference.predictor import Limits, Predictor, Turn


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="tmp/local-checks/dynamic_rag_check")
    parser.add_argument("--enforce-eager", action="store_true")
    args = parser.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    from nara.retrieval.search import BGEEncoder, LegalRetriever
    from nara.inference.engine import VLLMModel
    started = time.monotonic()
    encoder = BGEEncoder("models/bge-m3", device="cuda")
    retriever = LegalRetriever("model/legal_index", encoder)
    model = VLLMModel("models/gemma-4-26B-A4B-it-NVFP4", enforce_eager=args.enforce_eager)
    table = json.loads(Path("data/항목표.json").read_text())["항목"]
    schema = json.loads(Path("data/정답스키마_디코딩.json").read_text())["properties"]["판정"]
    records = read_records("data/dev.jsonl")
    report = {"load_seconds": time.monotonic() - started, "checks": []}

    def run(name, selected, items, *, groups=None, expected_rounds=None, limits=None):
        predictor = Predictor(model, retriever, items, schema, limits=limits)
        result = predictor.predict(selected, item_groups=groups)
        (out / f"{name}.json").write_text(json.dumps([asdict(r) for r in result], ensure_ascii=False))
        assert all(r.error is None for r in result), [r.error for r in result]
        if expected_rounds is not None:
            assert all(r.trace[0]["search_rounds"] == expected_rounds for r in result)
            assert all(any(e["passage_ids"] for e in r.trace[0]["events"] if e["event"] == "search")
                       for r in result), "No real retrieved material reached the conversation"
        write_submission(result, out / f"{name}.csv")
        checks = {"name": name, "passed": True, **predictor.metrics,
                  "search_rounds": [t["search_rounds"] for r in result for t in r.trace],
                  "input_tokens": sum(e.get("input_tokens", 0) for r in result for t in r.trace for e in t["events"]),
                  "output_tokens": sum(e.get("output_tokens", 0) for r in result for t in r.trace for e in t["events"])}
        report["checks"].append(checks)
        (out / "report.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(checks), flush=True)
        return result

    # Test-only item note forces both search branches; production has optional search.
    probe_table = copy.deepcopy(table)
    probe_table["v1"]["비고"] += (
        " 이 실행은 검색 연결 동작 점검이다. 반드시 첫 응답은 국가계약법 참가자격 제한에 대한 "
        "검색 요청으로 작성하라. 첫 검색 결과를 받은 후에는 반드시 지방계약법 참가자격 제한으로 "
        "검색어를 보완해 두 번째 검색을 요청하라. 두 번째 결과를 받은 후에만 최종 판단하라."
    )
    run("two_search_rounds", records[:2], probe_table, expected_rounds=2)
    # Exercise the public grouping argument with the actual model and output assembly.
    keys = list(table)
    run("groups_of_six", records[:1], table,
        groups=[keys[i:i + 6] for i in range(0, 24, 6)], limits=Limits(search_rounds=0))
    longest = max(records, key=lambda r: model.count_messages(
        Predictor(model, retriever, table, schema)._messages(r, tuple(table))))
    run("longest_source", [longest], table)

    # Same engine, actual thinking chat template and reasoning-aware JSON constraints.
    model.thinking = True
    messages = [{"role": "user", "content": '2+3을 계산하고 {"answer":5} 형식으로 답하라.'}]
    simple_schema = {"type": "object", "properties": {"answer": {"type": "integer"}},
                     "required": ["answer"], "additionalProperties": False}
    response = model.generate([Turn("thinking", messages, simple_schema, 512)])["thinking"]
    assert response.finish_reason == "stop" and json.loads(response.text) == {"answer": 5}, response
    report["checks"].append({"name": "thinking_json", "passed": True,
                             "output_tokens": response.output_tokens})
    print(json.dumps(report["checks"][-1]), flush=True)
    report["total_seconds"] = time.monotonic() - started
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
