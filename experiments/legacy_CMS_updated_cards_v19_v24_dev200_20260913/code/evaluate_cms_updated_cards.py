"""Evaluate the frozen CMS updated-card dev200 run without repairing predictions."""
from __future__ import annotations

if __name__ == "__main__":
    raise SystemExit("Archived code: create a fresh registered run; see docs/operations.md.")


import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
from statistics import mean

import jsonschema

from nara.evaluation.reporting import write_report


ROOT = Path(__file__).resolve().parents[3]
ITEMS = tuple(f"v{i}" for i in range(19, 25))
EXPECTED_RECORDS = 200
EXPECTED_REQUESTS = EXPECTED_RECORDS * len(ITEMS)
STOP_FINISH_REASONS = {"stop"}


def _expected_schema(item: str) -> dict:
    cell = {"type": "object", "properties": {
        "위반여부": {"type": "integer", "enum": [0, 1]},
        "근거문구": {"type": ["string", "null"]}},
        "required": ["위반여부", "근거문구"], "additionalProperties": False}
    return {"type": "object", "properties": {item: cell},
            "required": [item], "additionalProperties": False}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            _require(type(value) is dict, f"{path}:{line_number}: row is not an object")
            rows.append(value)
    return rows


def _unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate key: {key}")
        value[key] = item
    return value


def _reject_constant(value):
    raise ValueError(f"non-JSON numeric constant: {value}")


def _load_prediction(text):
    return json.loads(text, object_pairs_hook=_unique_object, parse_constant=_reject_constant)


def _preflight(run_dir: Path, expected_requests: int = EXPECTED_REQUESTS) -> dict:
    """Verify the frozen prediction bytes and complete request identity before labels."""
    required = ["inputs.jsonl", "schemas.json", "predictions.jsonl",
                "predictions_frozen.json", "manifest.json", "source/candidates.jsonl"]
    for name in required:
        _require((run_dir / name).is_file(), f"missing run artifact: {name}")

    frozen = json.loads((run_dir / "predictions_frozen.json").read_text(encoding="utf-8"))
    expected_hash = frozen.get("sha256")
    _require(isinstance(expected_hash, str) and len(expected_hash) == 64,
             "predictions_frozen.json: missing SHA256")
    actual_hash = _sha256(run_dir / "predictions.jsonl")
    _require(actual_hash == expected_hash, "predictions.jsonl: frozen SHA256 mismatch")
    _require(frozen.get("rows") == expected_requests,
             f"predictions_frozen.json: expected rows={expected_requests}")

    inputs = _read_jsonl(run_dir / "inputs.jsonl")
    predictions = _read_jsonl(run_dir / "predictions.jsonl")
    _require(len(inputs) == expected_requests, f"inputs.jsonl: expected {expected_requests} rows")
    _require(len(predictions) == expected_requests,
             f"predictions.jsonl: expected {expected_requests} rows")
    input_tasks = [row.get("task_id") for row in inputs]
    prediction_tasks = [row.get("task_id") for row in predictions]
    _require(len(set(input_tasks)) == expected_requests and None not in input_tasks,
             "inputs.jsonl: duplicate or missing task_id")
    _require(len(set(prediction_tasks)) == expected_requests and None not in prediction_tasks,
             "predictions.jsonl: duplicate or missing task_id")
    _require(set(input_tasks) == set(prediction_tasks),
             "predictions.jsonl: task coverage differs from inputs.jsonl")
    inputs_by_task = {row["task_id"]: row for row in inputs}
    predictions_by_task = {row["task_id"]: row for row in predictions}
    for task_id, request in inputs_by_task.items():
        prediction = predictions_by_task[task_id]
        for key in ("id", "item", "task_id"):
            _require(prediction.get(key) == request.get(key),
                     f"{task_id}: prediction {key} differs from frozen input")
        _require(request.get("item") in ITEMS, f"{task_id}: item outside v19..v24")

    schemas = json.loads((run_dir / "schemas.json").read_text(encoding="utf-8"))
    _require(type(schemas) is dict and set(schemas) == set(ITEMS),
             "schemas.json: expected exactly v19..v24")
    for item, schema in schemas.items():
        jsonschema.Draft202012Validator.check_schema(schema)
        _require(schema == _expected_schema(item), f"schemas.json: unexpected schema for {item}")
    for task_id, request in inputs_by_task.items():
        _require(request.get("schema") == schemas[request["item"]],
                 f"{task_id}: embedded schema differs from schemas.json")

    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    artifact_hashes = manifest.get("artifact_sha256", {})
    for name in ("inputs.jsonl", "schemas.json", "source/candidates.jsonl"):
        _require(artifact_hashes.get(name) == _sha256(run_dir / name),
                 f"manifest artifact hash mismatch: {name}")
    candidates = _read_jsonl(run_dir / "source/candidates.jsonl")
    run_summary_path = run_dir / "run_summary.json"
    _require(run_summary_path.is_file(), "missing run artifact: run_summary.json")
    run_summary = json.loads(run_summary_path.read_text(encoding="utf-8"))
    _require(run_summary.get("manifest_sha256") == _sha256(run_dir / "manifest.json"),
             "run_summary.json: manifest SHA256 mismatch")
    return {
        "inputs": inputs_by_task, "predictions": predictions_by_task,
        "schemas": schemas, "candidates": candidates, "manifest": manifest,
        "run_summary": run_summary, "prediction_sha256": actual_hash,
    }


def _read_labels(path: Path, expected_ids: set[str]) -> dict[str, dict]:
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames or []
        _require("id" in fields and all(item in fields for item in ITEMS),
                 "labels: id and v19..v24 columns are required")
        rows = list(reader)
    ids = [row["id"] for row in rows]
    _require(len(rows) == EXPECTED_RECORDS and len(set(ids)) == EXPECTED_RECORDS,
             "labels: expected 200 unique IDs")
    _require(set(ids) == expected_ids, "labels: ID set differs from frozen inputs")
    _require(all(row[item] in ("0", "1") for row in rows for item in ITEMS),
             "labels: v19..v24 must be binary")
    return {row["id"]: row for row in rows}


def _read_notices(path: Path, expected_ids: set[str], expected_hash: str) -> dict[str, dict]:
    _require(_sha256(path) == expected_hash, "notices: SHA256 differs from manifest")
    rows = _read_jsonl(path)
    ids = [row.get("id") for row in rows]
    _require(len(rows) == EXPECTED_RECORDS and len(set(ids)) == EXPECTED_RECORDS,
             "notices: expected 200 unique IDs")
    _require(set(ids) == expected_ids, "notices: ID set differs from frozen inputs")
    for row in rows:
        _require(type(row.get("docs")) is list, f"notices: {row.get('id')} has no docs")
    return {row["id"]: row for row in rows}


def _candidate_items(rows: list[dict], expected_ids: set[str]) -> dict[tuple[str, str], list[str]]:
    """Return selected segment texts from the preserved CMS source copy."""
    _require(len(rows) == EXPECTED_RECORDS, "candidates: expected 200 rows")
    found = {}
    for row in rows:
        record_id = row.get("id")
        _require(record_id in expected_ids, f"candidates: unexpected ID {record_id}")
        _require(set(row) == {"id", "items"} and type(row["items"]) is dict,
                 f"candidates: malformed row for {record_id}")
        _require(tuple(row["items"]) == ITEMS, f"candidates: item order/coverage changed for {record_id}")
        for item in ITEMS:
            payload = row["items"].get(item)
            _require(type(payload) is dict, f"candidates: missing {record_id}/{item}")
            segments = payload.get("segments")
            _require(type(segments) is list, f"candidates: malformed segments for {record_id}/{item}")
            texts = []
            for segment in segments:
                _require(type(segment) is dict and type(segment.get("text")) is str,
                         f"candidates: malformed segment for {record_id}/{item}")
                texts.append(segment["text"])
            found[(record_id, item)] = texts
    _require(len(found) == EXPECTED_REQUESTS, "candidates: incomplete item coverage")
    return found


def _parse_prediction(row: dict, schema: dict) -> tuple[bool, str | None, dict | None]:
    if row.get("status") != "completed":
        return False, "status:" + str(row.get("status")), None
    reply, raw = row.get("reply"), row.get("raw")
    if type(reply) is not dict or type(raw) is not dict:
        return False, "completed_without_reply_or_raw", None
    reply_finish, raw_finish = reply.get("finish_reason"), raw.get("finish_reason")
    if reply_finish not in STOP_FINISH_REASONS or raw_finish not in STOP_FINISH_REASONS:
        return False, f"non_normal_finish:{reply_finish}/{raw_finish}", None
    text = reply.get("text")
    if type(text) is not str:
        return False, "reply_text_not_string", None
    try:
        value = _load_prediction(text)
    except (json.JSONDecodeError, ValueError) as exc:
        return False, "invalid_json:" + str(exc), None
    try:
        jsonschema.validate(value, schema)
    except jsonschema.ValidationError as exc:
        return False, "schema_validation:" + exc.message, None
    return True, None, value


def _evidence_observations(item: str, value: dict, notice: dict,
                           candidate_texts: list[str], reference: str | None) -> dict:
    violation, evidence = value[item]["위반여부"], value[item]["근거문구"]
    source_match = (type(evidence) is str and bool(evidence)
                    and any(evidence in doc.get("text", "") for doc in notice["docs"]))
    candidate_match = (type(evidence) is str and bool(evidence)
                       and any(evidence in text for text in candidate_texts))
    if item == "v20":
        semantic_valid = evidence is None
        reason = None if semantic_valid else "v20_evidence_must_be_null"
    elif violation == 0:
        semantic_valid = evidence is None
        reason = None if semantic_valid else "negative_evidence_must_be_null"
    else:
        semantic_valid = (type(evidence) is str and 0 < len(evidence) <= 500 and source_match)
        reason = (None if semantic_valid else "positive_evidence_required" if not isinstance(evidence, str) or not evidence
                  else "evidence_over_500_chars" if len(evidence) > 500
                  else "evidence_not_contiguous_original_substring")
    return {
        "evidence_semantic_valid": semantic_valid,
        "evidence_invalid_reason": reason,
        "evidence_original_substring": source_match,
        "evidence_selected_candidate_substring": candidate_match,
        "evidence_length": len(evidence) if isinstance(evidence, str) else None,
        "reference_evidence_exact_match": (evidence == reference) if reference is not None else None,
    }


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _classification(rows: list[dict]) -> dict:
    valid = [row for row in rows if row["output_valid"]]
    tp = sum(row["gold"] == row["prediction"] == 1 for row in valid)
    fp = sum(row["gold"] == 0 and row["prediction"] == 1 for row in valid)
    fn = sum(row["gold"] == 1 and row["prediction"] == 0 for row in valid)
    tn = sum(row["gold"] == row["prediction"] == 0 for row in valid)
    f1_denominator = 2 * tp + fp + fn
    return {
        "expected": len(rows), "valid": len(valid), "invalid": len(rows) - len(valid),
        "gold_positive_valid": tp + fn, "predicted_positive_valid": tp + fp,
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "positive_f1_valid_only": _ratio(2 * tp, f1_denominator),
        "positive_f1_defined": bool(f1_denominator),
        "positive_f1_undefined_reason": None if f1_denominator else "2TP+FP+FN is zero",
        "accuracy_valid_only": _ratio(tp + tn, len(valid)),
        "accuracy_defined": bool(valid),
        "accuracy_undefined_reason": None if valid else "no valid outputs",
    }


def _evaluate(bundle: dict, labels: dict[str, dict], notices: dict[str, dict],
              labels_hash: str, notices_hash: str) -> tuple[list[dict], dict]:
    expected_ids = set(labels)
    candidate_text = _candidate_items(bundle["candidates"], expected_ids)
    cases = []
    invalid_reasons = Counter()
    for task_id, request in bundle["inputs"].items():
        prediction_row = bundle["predictions"][task_id]
        record_id, item = request["id"], request["item"]
        valid, invalid_reason, value = _parse_prediction(prediction_row, bundle["schemas"][item])
        gold = int(labels[record_id][item])
        case = {
            "id": record_id, "item": item, "task_id": task_id,
            "status": prediction_row.get("status"), "output_valid": valid,
            "invalid_reason": invalid_reason, "gold": gold,
            "prediction": value[item]["위반여부"] if valid else None,
            "evidence": value[item]["근거문구"] if valid else None,
            "finish_reason": ((prediction_row.get("reply") or {}).get("finish_reason")
                              if type(prediction_row.get("reply")) is dict else None),
            "reply": prediction_row.get("reply"), "raw": prediction_row.get("raw"),
            "error": prediction_row.get("error"),
        }
        if valid:
            reference = labels[record_id].get("e" + item[1:])
            case.update(_evidence_observations(item, value, notices[record_id],
                                               candidate_text[(record_id, item)], reference))
        else:
            invalid_reasons[invalid_reason] += 1
            case.update({
                "evidence_semantic_valid": None, "evidence_invalid_reason": None,
                "evidence_original_substring": None,
                "evidence_selected_candidate_substring": None,
                "evidence_length": None, "reference_evidence_exact_match": None,
            })
        cases.append(case)

    per_item = {item: _classification([row for row in cases if row["item"] == item]) for item in ITEMS}
    defined_f1 = [row["positive_f1_valid_only"] for row in per_item.values()
                  if row["positive_f1_defined"]]
    totals = _classification(cases)
    valid = [row for row in cases if row["output_valid"]]
    micro_denominator = 2 * totals["tp"] + totals["fp"] + totals["fn"]
    evidence_valid = [row for row in valid if row["evidence_semantic_valid"]]
    metrics = {
        "scope": {"records": EXPECTED_RECORDS, "items": list(ITEMS),
                  "expected_requests": EXPECTED_REQUESTS},
        "classification_protocol": "valid outputs only; invalid outputs are neither repaired nor filled with zero",
        "per_item": per_item,
        "aggregate": {
            "macro_positive_f1_valid_only": mean(defined_f1) if defined_f1 else None,
            "macro_items_defined": len(defined_f1),
            "macro_items_undefined": [item for item, row in per_item.items()
                                      if not row["positive_f1_defined"]],
            "micro_positive_f1_valid_only": _ratio(2 * totals["tp"], micro_denominator),
            "micro_positive_f1_defined": bool(micro_denominator),
            "micro_positive_f1_undefined_reason": None if micro_denominator else "2TP+FP+FN is zero",
            "accuracy_valid_only": totals["accuracy_valid_only"],
            "valid": totals["valid"], "invalid": totals["invalid"],
            "expected": EXPECTED_REQUESTS,
            "tp": totals["tp"], "fp": totals["fp"], "fn": totals["fn"], "tn": totals["tn"],
            "gold_positive_valid": totals["gold_positive_valid"],
            "predicted_positive_valid": totals["predicted_positive_valid"],
        },
        "failures": {"by_reason": dict(invalid_reasons),
                     "by_status": dict(Counter(str(row["status"]) for row in cases if not row["output_valid"]))},
        "evidence": {
            "evaluated_valid_outputs": len(valid),
            "semantic_valid": len(evidence_valid),
            "semantic_invalid": len(valid) - len(evidence_valid),
            "original_substring": sum(row["evidence_original_substring"] is True for row in valid),
            "selected_candidate_substring": sum(row["evidence_selected_candidate_substring"] is True for row in valid),
            "reference_exact_match": sum(row["reference_evidence_exact_match"] is True for row in valid),
            "invalid_reasons": dict(Counter(row["evidence_invalid_reason"] for row in valid
                                              if row["evidence_invalid_reason"])),
        },
        "prediction_sha256": bundle["prediction_sha256"],
        "evaluated_data_sha256": {"labels": labels_hash, "notices": notices_hash},
        "runtime": {key: bundle["run_summary"].get(key) for key in (
            "preparation_seconds", "model_load_seconds", "inference_seconds",
            "cache_reset_before_run", "engine", "hardware", "completed",
            "expected_requests", "cached_tokens", "input_tokens", "output_tokens")},
    }
    return cases, metrics


def _write_outputs(run_dir: Path, cases: list[dict], metrics: dict) -> None:
    (run_dir / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (run_dir / "evaluation_cases.jsonl").open("w", encoding="utf-8") as stream:
        for row in cases:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    by_id = {}
    for row in cases:
        by_id.setdefault(row["id"], {})[row["item"]] = row["prediction"] if row["output_valid"] else ""
    with (run_dir / "predictions.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["id", *ITEMS])
        writer.writeheader()
        for record_id in sorted(by_id):
            writer.writerow({"id": record_id, **by_id[record_id]})


def _fmt(value) -> str:
    return "미정의" if value is None else f"{value:.6f}"


def _report(run_dir: Path, bundle: dict, metrics: dict) -> Path:
    per_item, aggregate = metrics["per_item"], metrics["aggregate"]
    runtime = metrics["runtime"]
    manifest = bundle["manifest"]
    run_summary = bundle["run_summary"]
    valid_count = aggregate["valid"]
    macro_f1 = aggregate["macro_positive_f1_valid_only"]
    inference_seconds = runtime["inference_seconds"]
    evidence_reasons = metrics["evidence"]["invalid_reasons"]
    cached_fraction = runtime["cached_tokens"] / runtime["input_tokens"]
    v20_fp, v24_fp = per_item["v20"]["fp"], per_item["v24"]["fp"]
    v22_f1 = per_item["v22"]["positive_f1_valid_only"]
    quote_failures = evidence_reasons.get("evidence_not_contiguous_original_substring", 0)
    negative_evidence = evidence_reasons.get("negative_evidence_must_be_null", 0)
    concurrency = manifest["concurrency"]
    output_budget = manifest["output_tokens"]
    temperature, seed = manifest["temperature"], manifest["seed"]
    revalidation_seconds = run_summary["input_revalidation_seconds"]
    evidence_failures = metrics["evidence"]["semantic_invalid"]
    first_input = next(row for row in bundle["inputs"].values() if row.get("candidate_count", 0) > 0)
    actual_prompt = first_input["messages"][0]["content"]
    links = [f"[{item}](source/cards/{item}.txt)" for item in ITEMS]
    lines = [
        "# CMS 수정 판정카드 v19–v24 dev200 평가", "",
        "이 보고서는 CMS가 수정한 여섯 판정카드를 제공된 dev 200건에서 한 번 실행한 관찰이다. "
        "dev 정답을 활용해 개발된 방법이므로 보지 않은 데이터에 대한 일반화는 검증하지 않았다.", "",
        "## 결과 요약", "",
        f"- 구조 유효 출력 {valid_count:,}/1,200개; v19–v24 여섯 항목 macro 양성 F1 **{macro_f1:.6f}**.",
        f"- 추론 {inference_seconds:.2f}초. 후보 extraction은 생략되어 미측정이며 전체 runtime은 산출하지 않았다.",
        f"- 항목별 관찰: v20 FP {v20_fp}건, v24 FP {v24_fp}건, v22 양성 F1 {v22_f1:.0f}.",
        "- v20의 빈 후보 입력 148건은 정답이 모두 0이었고 그중 50건이 양성으로 예측됐다. 사례 목록과 다른 기술 통계는 [observations.json](observations.json)에 있다. 이 입력 표현 선택의 효과를 분리한 대조 실험은 하지 않았다.",
        "- 항목별 F1과 macro 값은 독립적인 scikit-learn 계산과 일치했다: [metric_crosscheck.json](metric_crosscheck.json).",
        f"- 근거 의미 제약 실패 {evidence_failures}개: 원문 연속 substring 불일치 {quote_failures}개, 음성 판정인데 근거가 null이 아닌 경우 {negative_evidence}개.", "",
        "## 실제 입력과 출력", "",
        f"- 전체 1,200개 실제 프롬프트와 토큰 수: [inputs.jsonl](inputs.jsonl)",
        f"- 여섯 판정카드 source: {', '.join(links)}",
        "- 출력은 요청 항목 하나만 담는 singleton JSON이다. 예: `{\"v19\":{\"위반여부\":0,\"근거문구\":null}}`. 강제한 여섯 구조는 [schemas.json](schemas.json)에 있다.",
        f"- 실행 설정: 최대 동시 요청 {concurrency}개를 완료되는 대로 refill, 출력 예산 {output_budget}토큰, thinking OFF, temperature {temperature}, seed {seed}.",
        "- 각 요청은 사용자 메시지 하나와 chat generation prefix로 구성했다. 별도 system 판단 프롬프트는 없었다.",
        "- CMS가 여러 후보 조각의 연결 표현을 명시하지 않은 부분은 KHJ가 선택했다. 모델에 후보 원문을 작은따옴표로 감싸 업로드 순서대로 표시했다. 문서 ID·종류·문자/행 위치는 모델에게 표시하지 않았고 source/candidates.jsonl에만 보존했다.",
        "", f"실제 입력 전체 예시({first_input['task_id']}, {first_input['input_tokens']}토큰):", "",
        "````text", actual_prompt, "````", "",
        "짧은 exact-format 예시:", "",
        "```text", "[원문]", "추출된 원문 후보가 없습니다.", "```", "",
        "CMS는 후보가 0개일 때의 입력 표시 문구를 명시하지 않았다. 본 실험에서는 사용자의 명시적 승인에 따라 해당 입력의 [원문]에 ‘추출된 원문 후보가 없습니다.’를 표시했다. 이는 업로드된 후보 목록이 비어 있음을 나타내는 입력 형식 선택이며, 원문에 관련 내용이 없다는 판정이나 추가 판단 규칙이 아니다. 이 입력은 438개였다.", "",
        "후보 원문과 사용자 지정 표시 형식을 유지하기 위해 PPS-DEV-189의 v24 입력 한 건에 한해 2,024토큰을 허용했다. 이는 CMS가 정한 채팅 템플릿 포함 입력 상한 2,000토큰을 24토큰 초과하는 사용자 승인 예외다. 다른 입력에 대한 상한 초과는 허용하지 않았다.", "",
        "## 분류 결과", "",
        "TP/FP/FN/TN, 양성 F1과 정확도는 JSON 파싱과 schema 검증을 통과한 유효 출력만 대상으로 계산했다. 무효·미제출·엔진 오류·길이 종료 출력은 0으로 채우거나 수리하지 않았다. 각 항목의 기대 분모는 200건이다.", "",
        "| 항목 | 유효/200 | 무효 | TP | FP | FN | TN | 양성 F1(유효만) | 정확도(유효만) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for item in ITEMS:
        row = per_item[item]
        lines.append(f"| {item} | {row['valid']}/200 | {row['invalid']} | {row['tp']} | {row['fp']} | "
                     f"{row['fn']} | {row['tn']} | {_fmt(row['positive_f1_valid_only'])} | "
                     f"{_fmt(row['accuracy_valid_only'])} |")
    undefined = ", ".join(aggregate["macro_items_undefined"]) or "없음"
    lines += ["",
        f"- 여섯 항목 macro 양성 F1(정의된 항목 평균): **{_fmt(aggregate['macro_positive_f1_valid_only'])}**; 정의 {aggregate['macro_items_defined']}/6, 미정의 항목 {undefined}.",
        "- 이 값은 v19–v24 여섯 항목의 dev 관찰이며, 전체 v1–v24를 사용하는 대회 평가 점수가 아니다.",
        f"- Micro 양성 F1(유효 출력만): **{_fmt(aggregate['micro_positive_f1_valid_only'])}**; 판정 정확도(유효 출력만): **{_fmt(aggregate['accuracy_valid_only'])}**.",
        f"- 전체 기대 1,200개 중 유효 {aggregate['valid']}개, 무효 {aggregate['invalid']}개. 무효 사유: `{json.dumps(metrics['failures'], ensure_ascii=False)}`.",
        "- 양성 F1에서 `2TP+FP+FN=0`이면 값을 0으로 바꾸지 않고 미정의로 기록했다. 정확도는 유효 출력이 0개면 미정의다.", "",
        "## 근거 관찰", "",
        f"- 구조상 유효한 출력 {metrics['evidence']['evaluated_valid_outputs']}개 중 의미 제약 통과 {metrics['evidence']['semantic_valid']}개, 실패 {metrics['evidence']['semantic_invalid']}개.",
        f"- 연속 원문 substring {metrics['evidence']['original_substring']}개; 선택 후보 내부 substring {metrics['evidence']['selected_candidate_substring']}개.",
        f"- reference 근거 문자열과 exact match {metrics['evidence']['reference_exact_match']}개. 이 값은 관찰값이며, 다른 연속 원문 인용을 오답으로 정하지 않는다.",
        "- v20 근거는 항상 null이어야 한다. v19·v21·v22·v23·v24는 판정 0이면 null, 판정 1이면 비어 있지 않은 500자 이하의 한 문서 연속 원문이어야 한다. 이 의미 검사는 구조 유효성과 별도로 기록했다.", "",
        "## 실행 범위", "",
        f"- 입력 준비 {runtime['preparation_seconds']:.2f}초, 모델 로드 {runtime['model_load_seconds']:.2f}초, engine 입력 재검증 {revalidation_seconds:.2f}초, 추론 {runtime['inference_seconds']:.2f}초. cache reset before run: {runtime['cache_reset_before_run']}.",
        f"- 하드웨어 `{runtime['hardware']['gpu']}`; 최대 문맥 {runtime['engine']['max_model_len']:,}토큰; 완료 {runtime['completed']:,}/{runtime['expected_requests']:,} 요청.",
        f"- 입력 {runtime['input_tokens']:,}토큰 중 cached {runtime['cached_tokens']:,}토큰({cached_fraction:.2%}), 출력 {runtime['output_tokens']:,}토큰. 실제 cache reuse 관찰이며 비캐시 대조가 없어 속도 향상 배수는 산출하지 않았다.",
        "- 로컬 Gemma 4 26B A4B NVFP4 관찰이며 하드웨어와 정밀도가 다른 환경 또는 제출 환경의 정확도·속도를 보장하지 않는다.",
        "- CMS가 만든 candidates.jsonl을 그대로 사용해 extraction을 생략했다. extraction 시간은 미측정이며, 원문 입력부터 extraction·추론까지의 전체 runtime은 검증하거나 산출하지 않았다.",
        "- [source_alignment.json](source_alignment.json) 독립 점검은 200공고·1,200항목·2,879후보가 원문 문자 범위와 일치함을 확인했다. budget_truncated=true인 20개 후보(v21 2개, v23 18개)는 저장 line_end가 1,800자 절단 전 검색창 끝줄을 가리키지만 start:end와 실제 text는 정확히 일치했다. line 위치는 모델 입력에 없으며 원본 audit 값을 수정하지 않았다.",
        "- v20의 완전관측=true이면서 budget_truncated=true인 입력은 PPS-DEV-088, PPS-DEV-135, PPS-DEV-171 세 건이다. 완전관측은 원본 문서 처리 상태이며 모델이 원문 전체를 보았다는 뜻이 아니다.",
        "- v24 source에서 PPS-DEV-062/049 정답 메모 한 줄만 사용자 승인에 따라 삭제했다. 다른 판정 기준·예시·예외·불확실성 문구는 유지했다.",
        "- predictions.jsonl raw 응답은 SHA256으로 동결한 뒤 평가했다. 재시도·결과 기반 repair·판정 대체는 하지 않았다.", "",
        "## 산출물", "",
        "- [metrics.json](metrics.json): 분모, 혼동행렬, F1, 정확도, 근거 관찰과 runtime.",
        "- [evaluation_cases.jsonl](evaluation_cases.jsonl): 1,200개별 구조·분류·근거 결과와 보존 raw.",
        "- [predictions.csv](predictions.csv): ID와 v19–v24 여섯 판정만 포함하며 무효 출력은 빈칸이다.",
        "- [predictions_frozen.json](predictions_frozen.json): 평가 전에 확인한 원응답 해시와 행 수.", "",
        "```bash",
        "uv run --locked python -m experiments.legacy_CMS_updated_cards_v19_v24_dev200_20260913.code.cms_updated_cards prepare --output analysis/CMS_updated_cards_v19_v24_dev200_20260913_NEW",
        "uv run --locked python -m experiments.legacy_CMS_updated_cards_v19_v24_dev200_20260913.code.cms_source_alignment --output analysis/CMS_updated_cards_v19_v24_dev200_20260913_NEW/source_alignment.json",
        "uv run --locked python -m experiments.legacy_CMS_updated_cards_v19_v24_dev200_20260913.code.cms_updated_cards run --output analysis/CMS_updated_cards_v19_v24_dev200_20260913_NEW",
        "uv run --locked python -m experiments.legacy_CMS_updated_cards_v19_v24_dev200_20260913.code.evaluate_cms_updated_cards --run-dir analysis/CMS_updated_cards_v19_v24_dev200_20260913_NEW",
        "```", "",
    ]
    return write_report(run_dir / "report.md", "\n".join(lines))


def evaluate(run_dir: Path, labels_path: Path | None = None,
             notices_path: Path | None = None) -> dict:
    run_dir = Path(run_dir)
    bundle = _preflight(run_dir)
    expected_ids = {row["id"] for row in bundle["inputs"].values()}
    _require(len(expected_ids) == EXPECTED_RECORDS, "inputs.jsonl: expected 200 notice IDs")
    # Deliberately below all frozen hash/count/schema/request checks.
    labels_path = Path(labels_path or ROOT / "data/dev_labels.csv")
    notices_path = Path(notices_path or ROOT / "data/dev.jsonl")
    labels = _read_labels(labels_path, expected_ids)
    notices = _read_notices(notices_path, expected_ids, bundle["manifest"]["dev_sha256"])
    cases, metrics = _evaluate(bundle, labels, notices, _sha256(labels_path), _sha256(notices_path))
    _write_outputs(run_dir, cases, metrics)
    report_path = _report(run_dir, bundle, metrics)
    return {"metrics": run_dir / "metrics.json", "cases": run_dir / "evaluation_cases.jsonl",
            "predictions": run_dir / "predictions.csv", "report": report_path}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--labels", type=Path, default=ROOT / "data/dev_labels.csv")
    parser.add_argument("--notices", type=Path, default=ROOT / "data/dev.jsonl")
    args = parser.parse_args()
    outputs = evaluate(args.run_dir, args.labels, args.notices)
    print(json.dumps({key: str(value) for key, value in outputs.items()}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    raise SystemExit("Archived experiment: create a new registered run; see docs/operations.md. Historical evidence is read-only.")
    main()
