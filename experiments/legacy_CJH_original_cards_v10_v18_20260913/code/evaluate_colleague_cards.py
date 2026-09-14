"""Evaluate complete CMS/CJH original-card runs after frozen-artifact verification."""
from __future__ import annotations

if __name__ == "__main__":
    raise SystemExit("Archived code: create a fresh registered run; see docs/operations.md.")


import argparse
from collections import Counter
import csv
from dataclasses import dataclass
import html
import json
from pathlib import Path
import re
from statistics import mean

from nara.evaluation.reporting import write_report


ROOT = Path(__file__).resolve().parents[3] if Path(__file__).parent.name == "evaluation" else Path(__file__).resolve().parents[3]
from experiments.legacy_CJH_original_cards_v10_v18_20260913.code.colleague_cards import FEATURES, PARSING, RUNS, dump, read_jsonl, sha


LABEL_COLUMNS = ["id", *(f"v{i}" for i in range(1, 25))]
OPTIONAL_LABEL_COLUMNS = {f"e{i}" for i in range(1, 25)}
ABSENCE_FEATURES = {"v10", "v11", "v16", "v18", "v20"}
FENCE = re.compile(r"\A```(?:json)?[ \t]*\r?\n([\s\S]*?)\r?\n```[ \t]*\Z", re.IGNORECASE)


@dataclass(frozen=True)
class ParsedResponse:
    valid: bool
    strict_format: bool
    format_violation: str | None
    invalid_reason: str | None
    violation: int | None
    evidence: str | None


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key: {key}")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError(f"non-JSON numeric constant: {value}")


def _invalid(reason, *, strict=True, format_violation=None):
    return ParsedResponse(False, strict, format_violation, reason, None, None)


def parse_response(text, finish_reason="stop"):
    """Parse one raw response without repair, cleanup, or judgment substitution."""
    if not isinstance(text, str):
        return _invalid("response_text_not_string")
    if finish_reason != "stop":
        return _invalid("non_stop_finish")
    envelope = text.strip()
    match = FENCE.fullmatch(envelope)
    if match:
        payload = match.group(1)
        strict = False
        format_violation = "complete_code_fence"
    else:
        payload = envelope
        strict = True
        format_violation = None
    try:
        value = json.loads(payload, object_pairs_hook=_unique_object, parse_constant=_reject_constant)
    except (json.JSONDecodeError, ValueError) as exc:
        return _invalid("invalid_json:" + str(exc), strict=strict, format_violation=format_violation)
    if type(value) is not dict:
        return _invalid("top_level_not_object", strict=strict, format_violation=format_violation)
    if set(value) != {"위반여부", "근거문구"} or len(value) != 2:
        return _invalid("wrong_keys", strict=strict, format_violation=format_violation)
    violation, evidence = value["위반여부"], value["근거문구"]
    if type(violation) is not int or violation not in (0, 1):
        return _invalid("invalid_violation_type", strict=strict, format_violation=format_violation)
    if evidence is not None and type(evidence) is not str:
        return _invalid("invalid_evidence_type", strict=strict, format_violation=format_violation)
    return ParsedResponse(True, strict, format_violation, None, violation, evidence)


def _safe_div(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def _score_feature(rows):
    tp = fp = fn = tn = invalid_pos = invalid_neg = 0
    for row in rows:
        if not row["valid"]:
            if row["gold"]:
                invalid_pos += 1
            else:
                invalid_neg += 1
        elif row["gold"] and row["prediction"]:
            tp += 1
        elif not row["gold"] and row["prediction"]:
            fp += 1
        elif row["gold"] and not row["prediction"]:
            fn += 1
        else:
            tn += 1
    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)
    f1 = _safe_div(2 * tp, 2 * tp + fp + fn)
    lower = _safe_div(2 * tp, 2 * tp + fp + fn + invalid_pos + invalid_neg)
    upper_tp = tp + invalid_pos
    upper = _safe_div(2 * upper_tp, 2 * upper_tp + fp + fn)
    return {
        "records": len(rows), "valid": tp + fp + fn + tn, "invalid": invalid_pos + invalid_neg,
        "gold_positive": tp + fn + invalid_pos, "predicted_positive": tp + fp,
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "invalid_gold_positive": invalid_pos, "invalid_gold_negative": invalid_neg,
        "precision": precision, "recall": recall, "f1_valid_only": f1,
        "f1_all_records_lower": lower, "f1_all_records_upper": upper,
    }


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _verify_hashes(base, hashes, label):
    for relative, expected in hashes.items():
        path = base / relative
        _require(path.is_file(), f"{label}: missing hashed file {path}")
        _require(sha(path) == expected, f"{label}: hash mismatch {path}")


def _verify_lifecycle(rows, expected_tasks):
    active = set()
    seen_submit, seen_complete = set(), set()
    peak = 0
    for event in rows:
        task = event.get("task_id")
        request_id = event.get("request_id")
        _require(task in expected_tasks, f"lifecycle: unknown task {task}")
        if event.get("event") == "submit":
            _require(request_id not in active and task not in seen_submit, f"lifecycle: duplicate submit {task}")
            active.add(request_id)
            seen_submit.add(task)
            peak = max(peak, len(active))
        elif event.get("event") == "complete":
            _require(request_id in active and task not in seen_complete, f"lifecycle: unmatched complete {task}")
            active.remove(request_id)
            seen_complete.add(task)
        else:
            raise ValueError(f"lifecycle: unexpected event {event.get('event')}")
        _require(len(active) <= 16, "lifecycle: more than 16 active requests")
    _require(not active, "lifecycle: unfinished active requests")
    _require(seen_submit == seen_complete == expected_tasks, "lifecycle: incomplete task coverage")
    return peak


def _preflight_suite(author, out):
    """Verify one suite completely. This function never opens the label file."""
    out = Path(out)
    required = [out / "manifest.json", out / "runtime.json", out / "request_timings.jsonl", out / "lifecycle.jsonl", out / "admissions.jsonl"]
    _require(all(path.is_file() for path in required), f"{author}: incomplete run artifacts")
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    features = FEATURES[author]
    expected_count = 200 * len(features)
    _require(manifest.get("author") == author, f"{author}: manifest author mismatch")
    _require(manifest.get("features") == features, f"{author}: manifest feature mismatch")
    _require(manifest.get("records") == 200 and manifest.get("requests") == expected_count,
             f"{author}: manifest denominator mismatch")
    _require(manifest.get("ready") is True, f"{author}: manifest is not ready")
    _require(bool(manifest.get("input_hashes")), f"{author}: missing input hashes")
    _require(bool(manifest.get("artifact_hashes")), f"{author}: missing artifact hashes")
    _verify_hashes(ROOT, manifest["input_hashes"], f"{author} input")
    _verify_hashes(out, manifest["artifact_hashes"], f"{author} artifact")

    requests, responses, record_ids = {}, {}, None
    for feature in features:
        request_path = out / "requests" / f"{feature}.jsonl.gz"
        response_path = out / "responses" / f"{feature}.jsonl"
        _require(request_path.is_file() and response_path.is_file(), f"{author}/{feature}: missing request or response")
        request_rows, response_rows = read_jsonl(request_path), read_jsonl(response_path)
        _require(len(request_rows) == len(response_rows) == 200, f"{author}/{feature}: expected 200 rows")
        ids = [row.get("id") for row in request_rows]
        _require(len(set(ids)) == 200, f"{author}/{feature}: duplicate request IDs")
        if record_ids is None:
            record_ids = ids
        _require(ids == record_ids, f"{author}/{feature}: request order differs")
        response_ids = [row.get("id") for row in response_rows]
        _require(len(set(response_ids)) == 200 and set(response_ids) == set(ids),
                 f"{author}/{feature}: response ID coverage differs")
        response_by_id = {row["id"]: row for row in response_rows}
        for request in request_rows:
            response = response_by_id[request["id"]]
            task_id = f"{request['id']}:{feature}"
            _require(request.get("feature") == feature and request.get("task_id") == task_id,
                     f"{author}/{feature}: malformed frozen request")
            _require(response.get("feature") == feature and response.get("task_id") == task_id,
                     f"{author}/{feature}: malformed response identity")
            _require(response.get("prompt_sha256") == request.get("prompt_sha256"),
                     f"{author}/{feature}: runtime prompt hash differs for {request['id']}")
            requests[task_id], responses[task_id] = request, response
    _require(len(requests) == len(responses) == expected_count, f"{author}: incomplete task set")

    runtime = json.loads((out / "runtime.json").read_text(encoding="utf-8"))
    _require(runtime.get("requests") == expected_count and runtime.get("retries") == 0,
             f"{author}: runtime request/retry mismatch")
    timings = read_jsonl(out / "request_timings.jsonl")
    _require(len(timings) == expected_count, f"{author}: request timing count mismatch")
    timing_tasks = [row.get("task_id") for row in timings]
    _require(len(set(timing_tasks)) == expected_count and set(timing_tasks) == set(requests),
             f"{author}: request timing task mismatch")
    lifecycle = read_jsonl(out / "lifecycle.jsonl")
    peak = _verify_lifecycle(lifecycle, set(requests))
    admissions = read_jsonl(out / "admissions.jsonl")
    admitted = [row.get("id") for row in admissions if row.get("event") == "admit"]
    completed_records = [row.get("id") for row in admissions if row.get("event") == "record_complete"]
    _require(len(admitted) == len(set(admitted)) == 200 and set(admitted) == set(record_ids),
             f"{author}: admission coverage mismatch")
    _require(len(completed_records) == 200 and set(completed_records) == set(record_ids),
             f"{author}: record completion coverage mismatch")
    return {
        "author": author, "out": out, "manifest": manifest, "runtime": runtime,
        "requests": requests, "responses": responses, "record_ids": record_ids,
        "timings": timings, "lifecycle": lifecycle, "admissions": admissions, "peak_inflight": peak,
        "response_sha256": {f: sha(out / "responses" / f"{f}.jsonl") for f in features},
    }


def _read_labels(path, expected_ids):
    with Path(path).open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames
        _require(fields is not None and len(fields) == len(set(fields)) and fields[0] == "id",
                 "labels: missing, duplicate, or misplaced id column")
        _require(set(LABEL_COLUMNS).issubset(fields), f"labels: required columns missing from {LABEL_COLUMNS}")
        _require(set(fields) - set(LABEL_COLUMNS) <= OPTIONAL_LABEL_COLUMNS,
                 "labels: unexpected columns outside optional e1..e24")
        rows = list(reader)
    ids = [row["id"] for row in rows]
    _require(len(rows) == len(set(ids)) == 200, "labels: expected 200 unique IDs")
    _require(set(ids) == set(expected_ids), "labels: ID set differs from frozen requests")
    _require(all(row[feature] in ("0", "1") for row in rows for feature in LABEL_COLUMNS[1:]),
             "labels: nonbinary or missing value")
    return {row["id"]: row for row in rows}


def _read_notices(path, expected_ids):
    rows = read_jsonl(path)
    ids = [row.get("id") for row in rows]
    _require(ids == expected_ids and len(set(ids)) == 200, "notices: ID order differs from frozen requests")
    return {row["id"]: row for row in rows}


def _evidence_in_notice(evidence, record):
    return any(evidence in doc["text"] for doc in record["docs"])


def _evaluate_suite(bundle, labels, notices):
    author, out = bundle["author"], bundle["out"]
    result_rows, by_feature = [], {}
    for feature in FEATURES[author]:
        rows = []
        for record_id in bundle["record_ids"]:
            response = bundle["responses"][f"{record_id}:{feature}"]
            parsed = parse_response(response.get("text"), response.get("finish_reason"))
            gold = int(labels[record_id][feature])
            evidence = parsed.evidence if parsed.valid else None
            empty = evidence is None or evidence == ""
            in_source = None if empty or not parsed.valid else _evidence_in_notice(evidence, notices[record_id])
            row = {
                "author": author, "id": record_id, "feature": feature, "gold": gold,
                "valid": parsed.valid, "strict_format": parsed.strict_format,
                "format_violation": parsed.format_violation, "invalid_reason": parsed.invalid_reason,
                "prediction": parsed.violation, "evidence": evidence,
                "evidence_json": json.dumps(evidence, ensure_ascii=False),
                "evidence_empty": empty if parsed.valid else None,
                "evidence_substring": in_source,
                "absence_evidence_nonempty": bool(parsed.valid and feature in ABSENCE_FEATURES and not empty),
                "positive_nonabsence_missing": bool(parsed.valid and parsed.violation == 1
                                                     and feature not in ABSENCE_FEATURES and empty),
                "positive_nonabsence_not_substring": bool(parsed.valid and parsed.violation == 1
                                                           and feature not in ABSENCE_FEATURES and not empty and not in_source),
                "normal_nonempty": bool(parsed.valid and parsed.violation == 0 and not empty),
                "finish_reason": response.get("finish_reason"), "stop_reason": response.get("stop_reason"),
                "output_tokens": response.get("output_tokens"), "raw_response": response.get("text"),
            }
            row["error_type"] = ("invalid" if not row["valid"] else
                                 "fp" if row["prediction"] == 1 and gold == 0 else
                                 "fn" if row["prediction"] == 0 and gold == 1 else None)
            rows.append(row)
            result_rows.append(row)
        by_feature[feature] = {**_score_feature(rows), "feature": feature,
            "strict_format_violations": sum(r["format_violation"] is not None for r in rows),
            "evidence": {
                "absence_nonempty": sum(r["absence_evidence_nonempty"] for r in rows),
                "positive_nonabsence_missing": sum(r["positive_nonabsence_missing"] for r in rows),
                "positive_nonabsence_not_substring": sum(r["positive_nonabsence_not_substring"] for r in rows),
                "normal_nonempty": sum(r["normal_nonempty"] for r in rows),
            }}
    return result_rows, by_feature


CSV_FIELDS = [
    "author", "id", "feature", "gold", "valid", "strict_format", "format_violation", "invalid_reason", "error_type",
    "prediction", "evidence_json", "evidence_empty", "evidence_substring", "absence_evidence_nonempty",
    "positive_nonabsence_missing", "positive_nonabsence_not_substring", "normal_nonempty",
    "finish_reason", "stop_reason", "output_tokens", "raw_response",
]


def _write_csv(path, rows, fields=CSV_FIELDS):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _runtime_summary(bundle):
    runtime, timings = bundle["runtime"], bundle["timings"]
    inference = runtime["inference_seconds"]
    inputs = sum(row["input_tokens"] for row in timings)
    cached = sum(row["cached_tokens"] for row in timings)
    admissions = bundle["admissions"]
    reasons = Counter(row.get("reason") for row in admissions if row.get("event") == "admit")
    return {
        "first_pass_seconds": inference,
        "model_load_seconds": runtime.get("model_load_seconds"),
        "warmup_seconds": runtime.get("warmup_seconds"),
        "requests": runtime["requests"],
        "requests_per_second": _safe_div(runtime["requests"], inference),
        "input_tokens": inputs,
        "output_tokens": sum(row["output_tokens"] for row in timings),
        "cached_input_tokens": cached,
        "cached_input_fraction": _safe_div(cached, inputs),
        "mean_queue_seconds": mean(row["queue_seconds"] for row in timings),
        "mean_prefill_seconds": mean(row["prefill_seconds"] for row in timings),
        "mean_decode_seconds": mean(row["decode_seconds"] for row in timings),
        "peak_inflight_requests": bundle["peak_inflight"],
        "admission_reasons": dict(reasons),
        "cache_reset_before_suite": runtime.get("cache_reset_before_suite"),
        "retries": runtime.get("retries"),
    }


def _cross_item(rows):
    predictions = {(row["id"], row["feature"]): row["prediction"]
                   for row in rows if row["valid"]}
    result = {}
    for left, right in (("v15", "v16"), ("v17", "v18")):
        ids = sorted(record_id for record_id in {r["id"] for r in rows}
                     if predictions.get((record_id, left)) == predictions.get((record_id, right)) == 1)
        result[f"{left}_{right}_simultaneous_positive"] = {"count": len(ids), "ids": ids}
    return result


def _law_notes(out):
    notes = []
    for path in sorted((out / "law_specs").glob("v*.json"), key=lambda p: int(p.stem[1:])):
        spec = json.loads(path.read_text(encoding="utf-8"))
        notes.extend({"feature": spec["feature"], "note": note} for note in spec.get("selection_notes", []))
    return notes


def _md(value):
    if value is None:
        return ""
    return html.escape(str(value), quote=False).replace("|", "&#124;").replace("\r\n", "<br>").replace("\n", "<br>")


def _report(author, out, evaluation, rows, cases, errors, bundle):
    runtime = evaluation["runtime"]
    invalid_reasons = Counter(row["invalid_reason"] for row in rows if not row["valid"])
    finish_reasons = Counter(str(row["finish_reason"]) for row in rows)
    text = [f"# {author} 원문 판정카드 dev200 평가", "",
        "이 결과는 제공된 dev 라벨에 대한 단일 로컬 관찰이다. 저자의 검색 구현을 독립적으로 검증하거나 새로운 법적 판단 기준을 확립한 결과가 아니다.", "",
        "## 항목별 결과", "",
        "| 항목 | F1(유효 응답) | TP | FP | FN | TN | 유효 | 무효 | 전체 F1 하한–상한 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|" ]
    for feature in FEATURES[author]:
        score = evaluation["per_feature"][feature]
        text.append(f"| {feature} | {score['f1_valid_only']:.6f} | {score['tp']} | {score['fp']} | "
                    f"{score['fn']} | {score['tn']} | {score['valid']} | {score['invalid']} | "
                    f"{score['f1_all_records_lower']:.6f}–{score['f1_all_records_upper']:.6f} |")
    text += ["", "유효 응답만 TP/FP/FN/TN과 기본 F1에 포함했다. 무효 응답은 정상 0으로 바꾸지 않았다. "
             "전체 200건 F1 하한은 `2TP/(2TP+FP+FN+invalid_pos+invalid_neg)`, 상한은 "
             "`2(TP+invalid_pos)/(2(TP+invalid_pos)+FP+FN)`이며 분모가 0이면 0이다.", "",
        "## 원응답과 근거 진단", "",
        f"- 종료 사유: `{json.dumps(dict(finish_reasons), ensure_ascii=False)}`.",
        f"- 무효 사유: `{json.dumps(dict(invalid_reasons), ensure_ascii=False)}`.",
        f"- 완결 코드펜스 형식 위반: {sum(r['format_violation'] is not None for r in rows)}건. payload는 수리하거나 정리하지 않고 그대로 판독했다.",
        f"- 부재탐지 항목(v10·v11·v16·v18·v20)의 비어 있지 않은 근거: {sum(r['absence_evidence_nonempty'] for r in rows)}건.",
        f"- 비부재 양성의 근거 누락: {sum(r['positive_nonabsence_missing'] for r in rows)}건; 비어 있지 않지만 공고 원문 substring이 아닌 근거: {sum(r['positive_nonabsence_not_substring'] for r in rows)}건.",
        f"- 정상 판정의 비어 있지 않은 근거: {sum(r['normal_nonempty'] for r in rows)}건. 모두 진단값이며 이진 판정과 원근거를 바꾸지 않았다.", "",
        "## 실행 조건과 관찰", "",
        f"- thinking OFF, 출력 512토큰, 문맥 {bundle['manifest']['max_model_len']:,}토큰. 이번 실험에만 문맥 확대를 승인했으며 기본 파이프라인·제출 서버의 32,768 한도는 유지한다.",
        "- 원문을 모두 붙인 사전 검사에서 3,000개 중 107개가 종전 한도를 넘었다. 최대 입력+출력은 35,897토큰이었으며 공고·카드·법령을 줄이지 않고 문맥만 확대했다.",
        "- 단일 로컬 실행 결과이며 제출 서버에서의 동일 실행·속도·정확도를 보장하는 결과가 아니다.",
        f"- 최초 추론 {runtime['first_pass_seconds']:.3f}초, {runtime['requests']}요청, {runtime['requests_per_second']:.3f}요청/초. 재시도 {runtime['retries']}회.",
        f"- 모델 로드 {runtime['model_load_seconds']:.3f}초, 예열 {runtime['warmup_seconds']:.3f}초. 로드·예열은 최초 추론 시간과 분리했다.",
        f"- 입력 {runtime['input_tokens']:,}토큰, 출력 {runtime['output_tokens']:,}토큰, 캐시 입력 {runtime['cached_input_tokens']:,}토큰({runtime['cached_input_fraction']:.2%}).",
        f"- 실제 동시 요청 최대 {runtime['peak_inflight_requests']}; 공고 입장 사유 {json.dumps(runtime['admission_reasons'], ensure_ascii=False)}. 평균 queue/prefill/decode {runtime['mean_queue_seconds']:.4f}/{runtime['mean_prefill_seconds']:.4f}/{runtime['mean_decode_seconds']:.4f}초.", ""]
    if author == "CJH":
        cross = evaluation["cross_item"]
        text += ["## 교차 항목 관찰", "",
            f"- v15·v16 동시 양성 {cross['v15_v16_simultaneous_positive']['count']}건: {_md(', '.join(cross['v15_v16_simultaneous_positive']['ids']))}",
            f"- v17·v18 동시 양성 {cross['v17_v18_simultaneous_positive']['count']}건: {_md(', '.join(cross['v17_v18_simultaneous_positive']['ids']))}",
            "- 위 결과는 서로 독립인 원응답의 관찰이며 판정을 결합하거나 수정하지 않았다.", "",
            "경쟁제품 후보선정은 CJH가 작성한 판정 규칙이 아니라 이번 실험의 통합 조건이다. 10자리 코드 일치, 2자 이상 세부품명 literal 일치, 전체 공고문 chunk와 meta 질의의 BGE 상위 5개를 합치고 특이사항 원문을 전달했다. 이 선택은 관련 행을 누락하거나 무관한 행을 과다 포함할 수 있다.", ""]
    else:
        text += ["## CMS v24 공개", "",
            "승인된 CMS v24 원문에는 PPS-DEV-062·071·049의 dev 정답 정보와 재현 여부 메모가 포함되어 있다. 이를 삭제하지 않고 전달했으므로 v24 결과는 독립 검증으로 해석할 수 없다.", ""]
    notes = evaluation["law_reference_notes"]
    text += ["## 고정 참고자료와 범위", "",
        "법령은 feature별 organizer-package 원문 span으로 고정했고 선택된 문구를 새 규칙으로 요약하거나 응답에 맞춰 바꾸지 않았다."]
    if notes:
        text.extend(f"- {row['feature']}: {row['note']}" for row in notes)
    else:
        text.append("- law spec에 별도 범위 메모가 없다.")
    text += ["", "## 전체 양성·무효 사례", "",
        "정답 양성, 유효 예측 양성 또는 무효인 모든 사례다. 원응답과 근거는 저장값 그대로 표시한다.", "",
        "| ID | 항목 | 정답 | 예측 | 상태 | 근거 | 원응답 |",
        "|---|---|---:|---:|---|---|---|"]
    for row in cases:
        status = "유효" if row["valid"] else "무효: " + str(row["invalid_reason"])
        text.append(f"| {_md(row['id'])} | {row['feature']} | {row['gold']} | {_md(row['prediction'])} | "
                    f"{_md(status)} | {_md(row['evidence_json'])} | {_md(row['raw_response'])} |")
    text += ["", "## 산출물과 재현", "",
        f"- 원본 공고와 정답 라벨은 저장소 외부에서 별도 준비해야 한다. [manifest](manifest.json), [실행정보](runtime.json), [평가 JSON](evaluation.json)",
        f"- [전체 오류 CSV](errors.csv), [전체 양성·무효 사례 CSV](cases.csv), [요청 timing](request_timings.jsonl), [lifecycle](lifecycle.jsonl)",
        f"- 요청 원문 압축파일: {', '.join(f'[requests/{feature}](requests/{feature}.jsonl.gz)' for feature in FEATURES[author])}",
        f"- 원응답: {', '.join(f'[responses/{feature}](responses/{feature}.jsonl)' for feature in FEATURES[author])}",
        f"- 법령: [렌더링 원문](laws.json), [span provenance](law_provenance.json), "
        f"{', '.join(f'[law_specs/{feature}](law_specs/{feature}.json)' for feature in FEATURES[author])}"]
    if author == "CJH":
        text.append("- 후보선정: [protocol](selection_protocol.json), [선정 행·원문·근거](product_candidates.jsonl.gz)")
    text += ["", "```bash", "uv run --locked python -m experiments.legacy_CJH_original_cards_v10_v18_20260913.code.evaluate_colleague_cards", "```", ""]
    return write_report(out / "report.md", "\n".join(text))


def evaluate(labels_path=None, notices_path=None):
    """Verify both complete runs, then open labels once and emit evaluations/reports."""
    bundles = {author: _preflight_suite(author, RUNS[author]) for author in ("CMS", "CJH")}
    expected_ids = bundles["CMS"]["record_ids"]
    _require(bundles["CJH"]["record_ids"] == expected_ids, "suite notice IDs/orders differ")

    # Keep this label read below every suite/input/artifact/prompt/runtime completeness check.
    labels_path = ROOT / "data/dev_labels.csv" if labels_path is None else Path(labels_path)
    labels = _read_labels(labels_path, expected_ids)
    notices_path = ROOT / "data/dev.jsonl" if notices_path is None else Path(notices_path)
    notices = _read_notices(notices_path, expected_ids)
    outputs = {}
    for author, bundle in bundles.items():
        out = bundle["out"]
        rows, per_feature = _evaluate_suite(bundle, labels, notices)
        for feature in FEATURES[author]:
            _write_csv(out / "per_feature" / f"{feature}.csv", [r for r in rows if r["feature"] == feature])
        errors = [row for row in rows if not row["valid"] or
                  (row["valid"] and row["prediction"] != row["gold"])]
        cases = [row for row in rows if row["gold"] == 1 or not row["valid"] or row["prediction"] == 1]
        _write_csv(out / "errors.csv", errors)
        _write_csv(out / "cases.csv", cases)
        runtime = _runtime_summary(bundle)
        evaluation = {
            "author": author, "records": 200, "features": FEATURES[author],
            "judgments": len(rows), "parsing_protocol": PARSING,
            "per_feature": per_feature,
            "macro_f1_valid_only": mean(score["f1_valid_only"] for score in per_feature.values()),
            "macro_f1_all_records_lower": mean(score["f1_all_records_lower"] for score in per_feature.values()),
            "macro_f1_all_records_upper": mean(score["f1_all_records_upper"] for score in per_feature.values()),
            "totals": _score_feature(rows), "runtime": runtime,
            "cross_item": _cross_item(rows) if author == "CJH" else {},
            "law_reference_notes": _law_notes(out),
            "hashes": {
                "labels": sha(labels_path), "notices": sha(notices_path),
                "responses": bundle["response_sha256"],
                "manifest": sha(out / "manifest.json"), "runtime": sha(out / "runtime.json"),
            },
            "error_rows": len(errors), "case_rows": len(cases),
        }
        dump(out / "evaluation.json", evaluation)
        report = _report(author, out, evaluation, rows, cases, errors, bundle)
        outputs[author] = {"evaluation": out / "evaluation.json", "report": report}
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", type=Path, default=ROOT / "data/dev_labels.csv")
    parser.add_argument("--notices", type=Path, default=ROOT / "data/dev.jsonl")
    args = parser.parse_args()
    outputs = evaluate(args.labels, args.notices)
    print(json.dumps({author: {key: str(value) for key, value in paths.items()}
                      for author, paths in outputs.items()}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    raise SystemExit("Archived experiment: create a new registered run; see docs/operations.md. Historical evidence is read-only.")
    main()
