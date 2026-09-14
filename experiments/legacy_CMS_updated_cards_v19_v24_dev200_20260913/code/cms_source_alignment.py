"""Audit the immutable CMS candidate artifact against the original dev records."""

if __name__ == "__main__":
    raise SystemExit("Archived code: create a fresh registered run; see docs/operations.md.")


import argparse
import bisect
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import subprocess
import unicodedata


ROOT = Path(__file__).resolve().parents[3]
COMMIT = "615e649e80794556f9ae2d889da99d5c41a8cba4"
ITEMS = tuple(f"v{i}" for i in range(19, 25))
DEFAULT_OUTPUT = (
    ROOT / "analysis/CMS_updated_cards_v19_v24_dev200_20260913/source_alignment.json"
)
CANDIDATE_HASH = "80259ee689e0b03888311d3a7fcb19cafff161be9408423317f15151f0f33c1b"
CARD_HASH = "68f0a760c779897dd2bce9c3874ea80dd7a5788605d913e60b3403b4449e45bc"
SOURCE_NAMES = {
    "candidates": "candidates.jsonl",
    "cards": "판정카드_v19-v24_토큰수_제한.md",
    "extraction": "원문_META_추출규칙_v19-v24.md",
}


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def _git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def _authored_sources():
    paths = _git(
        "ls-tree", "-r", "--name-only", "-z", COMMIT, "--", "user/CMS"
    ).decode().split("\0")
    sources = {}
    for key, name in SOURCE_NAMES.items():
        matches = [
            path
            for path in paths
            if unicodedata.normalize("NFC", path).endswith("/" + name)
        ]
        if len(matches) != 1:
            raise ValueError(f"Expected exactly one CMS source named {name}: {matches}")
        path = matches[0]
        sources[key] = (path, _git("show", f"{COMMIT}:{path}"))
    return sources


def _jsonl(data):
    return [json.loads(line) for line in data.splitlines() if line]


def _same_json(left, right):
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return list(left) == list(right) and all(
            _same_json(left[key], right[key]) for key in left
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            _same_json(a, b) for a, b in zip(left, right)
        )
    return left == right


def _line_bounds(text):
    lines = text.splitlines(keepends=True) or [""]
    starts = []
    ends = []
    position = 0
    for line in lines:
        starts.append(position)
        position += len(line)
        ends.append(position)
    return starts, ends


def _git_blob_sha1(data):
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()


def _fatal(issues, code, **details):
    issues.append({"severity": "fatal", "code": code, **details})


def _warning(issues, code, **details):
    issues.append({"severity": "warning", "code": code, **details})


def _audit(candidates_data, dev_data, sources):
    candidates = _jsonl(candidates_data)
    dev_records = _jsonl(dev_data)
    issues = []
    counts = Counter()
    per_item = defaultdict(Counter)
    meta_key_shapes = defaultdict(Counter)

    candidate_ids = [row.get("id") for row in candidates]
    dev_ids = [row.get("id") for row in dev_records]
    duplicate_candidate_ids = sorted(
        key for key, count in Counter(candidate_ids).items() if count > 1
    )
    duplicate_dev_ids = sorted(key for key, count in Counter(dev_ids).items() if count > 1)
    dev_by_id = {row["id"]: row for row in dev_records}
    missing_ids = sorted(set(dev_ids) - set(candidate_ids))
    extra_ids = sorted(set(candidate_ids) - set(dev_ids))
    if len(candidates) != 200:
        _fatal(issues, "candidate_record_count_mismatch", expected=200, actual=len(candidates))
    if len(dev_records) != 200:
        _fatal(issues, "dev_record_count_mismatch", expected=200, actual=len(dev_records))
    if duplicate_candidate_ids:
        _fatal(issues, "duplicate_candidate_ids", ids=duplicate_candidate_ids)
    if duplicate_dev_ids:
        _fatal(issues, "duplicate_dev_ids", ids=duplicate_dev_ids)
    if missing_ids or extra_ids:
        _fatal(issues, "record_id_set_mismatch", missing_ids=missing_ids, extra_ids=extra_ids)
    if candidate_ids != dev_ids:
        _fatal(issues, "record_order_mismatch")

    for candidate in candidates:
        record_id = candidate.get("id")
        dev = dev_by_id.get(record_id)
        if dev is None:
            continue
        item_keys = tuple(candidate.get("items", {}))
        if item_keys != ITEMS:
            _fatal(
                issues,
                "item_key_order_or_coverage_mismatch",
                id=record_id,
                expected=list(ITEMS),
                actual=list(item_keys),
            )
        docs = {doc["doc_id"]: doc for doc in dev["docs"]}
        if len(docs) != len(dev["docs"]):
            _fatal(issues, "duplicate_dev_doc_id", id=record_id)

        for item in ITEMS:
            value = candidate.get("items", {}).get(item)
            if value is None:
                continue
            counts["item_sets_checked"] += 1
            per_item[item]["sets"] += 1
            meta_key_shapes[item][tuple(value.get("meta", {}))] += 1

            completeness = value.get("input_completeness")
            counts["input_completeness_objects_checked"] += 1
            if isinstance(completeness, dict):
                counts["input_completeness_values_checked"] += len(completeness)
            if not _same_json(completeness, dev.get("input_completeness")):
                _fatal(
                    issues,
                    "input_completeness_mismatch",
                    id=record_id,
                    item=item,
                    expected=dev.get("input_completeness"),
                    actual=completeness,
                )

            dropped = value.get("dropped_doc_counts")
            counts["dropped_doc_counts_objects_checked"] += 1
            if isinstance(dropped, dict):
                counts["dropped_doc_count_values_checked"] += len(dropped)
            if not _same_json(dropped, dev.get("dropped_doc_counts")):
                _fatal(
                    issues,
                    "dropped_doc_counts_mismatch",
                    id=record_id,
                    item=item,
                    expected=dev.get("dropped_doc_counts"),
                    actual=dropped,
                )

            meta = value.get("meta", {})
            for key, selected in meta.items():
                counts["selected_meta_values_checked"] += 1
                if key not in dev.get("meta", {}):
                    _fatal(
                        issues,
                        "selected_meta_key_missing_in_dev",
                        id=record_id,
                        item=item,
                        key=key,
                    )
                elif not _same_json(selected, dev["meta"][key]):
                    _fatal(
                        issues,
                        "selected_meta_value_or_type_mismatch",
                        id=record_id,
                        item=item,
                        key=key,
                        expected=dev["meta"][key],
                        actual=selected,
                    )

            segments = value.get("segments", [])
            per_item[item]["segments"] += len(segments)
            per_item[item]["empty_sets"] += not segments
            per_item[item]["budget_truncated_sets"] += bool(
                value.get("budget_truncated")
            )
            declared_chars = value.get("candidate_chars")
            actual_chars = sum(len(segment.get("text", "")) for segment in segments)
            per_item[item]["candidate_chars"] += declared_chars or 0
            if declared_chars != actual_chars:
                _fatal(
                    issues,
                    "candidate_chars_mismatch",
                    id=record_id,
                    item=item,
                    expected=actual_chars,
                    actual=declared_chars,
                )

            for segment_index, segment in enumerate(segments):
                counts["segments_checked"] += 1
                doc_id = segment.get("doc_id")
                doc = docs.get(doc_id)
                if doc is None:
                    _fatal(
                        issues,
                        "segment_doc_id_missing",
                        id=record_id,
                        item=item,
                        segment_index=segment_index,
                        doc_id=doc_id,
                    )
                    continue
                if segment.get("doc_type") != doc.get("type"):
                    _fatal(
                        issues,
                        "doc_type_mismatch",
                        id=record_id,
                        item=item,
                        segment_index=segment_index,
                        expected=doc.get("type"),
                        actual=segment.get("doc_type"),
                    )

                text = doc["text"]
                start = segment.get("start")
                end = segment.get("end")
                valid_chars = (
                    type(start) is int
                    and type(end) is int
                    and 0 <= start <= end <= len(text)
                )
                if not valid_chars:
                    _fatal(
                        issues,
                        "invalid_character_range",
                        id=record_id,
                        item=item,
                        segment_index=segment_index,
                        start=start,
                        end=end,
                        doc_chars=len(text),
                    )
                    continue
                exact_slice = text[start:end] == segment.get("text")
                if exact_slice:
                    counts["exact_character_slices"] += 1
                else:
                    _fatal(
                        issues,
                        "candidate_text_or_character_offset_mismatch",
                        id=record_id,
                        item=item,
                        segment_index=segment_index,
                        start=start,
                        end=end,
                    )

                starts, ends = _line_bounds(text)
                line_start = segment.get("line_start")
                line_end = segment.get("line_end")
                valid_lines = (
                    type(line_start) is int
                    and type(line_end) is int
                    and 1 <= line_start <= line_end <= len(starts)
                )
                if not valid_lines:
                    _fatal(
                        issues,
                        "invalid_line_range",
                        id=record_id,
                        item=item,
                        segment_index=segment_index,
                        line_start=line_start,
                        line_end=line_end,
                        doc_lines=len(starts),
                    )
                    continue
                expected_start = starts[line_start - 1]
                claimed_full_end = ends[line_end - 1]
                if start == expected_start:
                    counts["exact_line_starts"] += 1
                else:
                    _fatal(
                        issues,
                        "line_start_character_mismatch",
                        id=record_id,
                        item=item,
                        segment_index=segment_index,
                        start=start,
                        line_start=line_start,
                        expected_start=expected_start,
                    )
                if end == claimed_full_end:
                    counts["exact_line_ends"] += 1
                    continue

                actual_end_line = (
                    bisect.bisect_left(ends, end) + 1 if end > start else line_start
                )
                is_budget_cut_window = (
                    exact_slice
                    and start == expected_start
                    and end < claimed_full_end
                    and actual_end_line <= line_end
                    and value.get("budget_truncated") is True
                )
                if is_budget_cut_window:
                    counts["preserved_search_window_line_ends"] += 1
                    _warning(
                        issues,
                        "line_window_end_exceeds_candidate_end_after_char_budget_cut",
                        id=record_id,
                        item=item,
                        segment_index=segment_index,
                        doc_id=doc_id,
                        doc_type=segment.get("doc_type"),
                        start=start,
                        end=end,
                        line_start=line_start,
                        line_end=line_end,
                        actual_candidate_end_line=actual_end_line,
                        claimed_line_end_full_char_end=claimed_full_end,
                        unrepresented_window_chars_after_end=claimed_full_end - end,
                        segment_chars=len(segment["text"]),
                        item_candidate_chars=declared_chars,
                        budget_truncated=True,
                    )
                else:
                    _fatal(
                        issues,
                        "unexpected_line_end_character_mismatch",
                        id=record_id,
                        item=item,
                        segment_index=segment_index,
                        end=end,
                        line_end=line_end,
                        expected_full_end=claimed_full_end,
                        actual_candidate_end_line=actual_end_line,
                    )

    candidate_hash = _sha256(candidates_data)
    card_hash = _sha256(sources["cards"][1])
    if candidate_hash != CANDIDATE_HASH:
        _fatal(
            issues,
            "candidate_hash_mismatch",
            expected=CANDIDATE_HASH,
            actual=candidate_hash,
        )
    if card_hash != CARD_HASH:
        _fatal(issues, "card_hash_mismatch", expected=CARD_HASH, actual=card_hash)

    fatal_count = sum(issue["severity"] == "fatal" for issue in issues)
    warning_count = sum(issue["severity"] == "warning" for issue in issues)
    per_item_report = {key: dict(per_item[key]) for key in ITEMS}
    selected_meta_shapes = {
        key: [list(shape) for shape in meta_key_shapes[key]] for key in ITEMS
    }
    exact_meta_shape_counts = {
        key: sum(meta_key_shapes[key].values()) if len(meta_key_shapes[key]) == 1 else 0
        for key in ITEMS
    }
    dev_hash = _sha256(dev_data)
    extraction_hash = _sha256(sources["extraction"][1])
    report = {
        "passed": fatal_count == 0,
        "candidate_sha256": candidate_hash,
        "card_sha256": card_hash,
        "dev_sha256": dev_hash,
        "summary": {
            "status": (
                "pass_with_documented_line_window_distinctions"
                if fatal_count == 0 and warning_count
                else "pass" if fatal_count == 0 else "fail"
            ),
            "fatal_issue_count": fatal_count,
            "warning_issue_count": warning_count,
            "candidate_record_count": len(candidates),
            "item_set_count": counts["item_sets_checked"],
            "segment_count": counts["segments_checked"],
            "candidate_text_char_count": sum(
                item["candidate_chars"] for item in per_item_report.values()
            ),
            "selected_meta_value_count": counts["selected_meta_values_checked"],
            "input_completeness_object_count": counts[
                "input_completeness_objects_checked"
            ],
            "input_completeness_value_count": counts[
                "input_completeness_values_checked"
            ],
            "dropped_doc_counts_object_count": counts[
                "dropped_doc_counts_objects_checked"
            ],
            "dropped_doc_count_value_count": counts[
                "dropped_doc_count_values_checked"
            ],
            "interpretation": (
                "All model-visible candidate text is an exact data/dev.jsonl character "
                "slice at start:end, and every selected META/completeness value matches "
                "the same dev record. For character-budget-cut segments, "
                "line_start:line_end may retain the larger source search-window span "
                "while start:end and text retain only its exact prefix. These are "
                "reported as non-fatal provenance warnings; they do not change or "
                "invalidate the candidate text slice."
            ),
        },
        "sources": {
            "cms_commit": COMMIT,
            "candidate_git_path_nfc_display": unicodedata.normalize(
                "NFC", sources["candidates"][0]
            ),
            "candidate_path_normalization_in_git_tree": "NFD",
            "card_git_path_nfc_display": unicodedata.normalize("NFC", sources["cards"][0]),
            "card_path_normalization_in_git_tree": "NFD directory; NFC filename",
            "extraction_rules_git_path_nfc_display": unicodedata.normalize(
                "NFC", sources["extraction"][0]
            ),
            "extraction_rules_path_normalization_in_git_tree": "NFD",
            "extraction_rules_sha256": extraction_hash,
            "dev_path": "data/dev.jsonl",
            "dev_git_blob_sha1": _git_blob_sha1(dev_data),
            "runner_preserved_source_names": [
                "source/candidates.jsonl",
                "source/cards_original.txt",
                "source/extraction_original.txt",
                *(f"source/cards/{item}.txt" for item in ITEMS),
            ],
        },
        "checks": {
            "candidate_hash": {
                "passed": candidate_hash == CANDIDATE_HASH,
                "expected": CANDIDATE_HASH,
                "actual": candidate_hash,
            },
            "card_hash": {
                "passed": card_hash == CARD_HASH,
                "expected": CARD_HASH,
                "actual": card_hash,
            },
            "record_identity": {
                "passed": not (
                    missing_ids
                    or extra_ids
                    or duplicate_candidate_ids
                    or duplicate_dev_ids
                    or candidate_ids != dev_ids
                    or len(candidates) != 200
                    or len(dev_records) != 200
                ),
                "candidate_records": len(candidates),
                "dev_records": len(dev_records),
                "candidate_unique_ids": len(set(candidate_ids)),
                "dev_unique_ids": len(set(dev_ids)),
                "same_id_set": set(candidate_ids) == set(dev_ids),
                "same_record_order": candidate_ids == dev_ids,
                "missing_ids": missing_ids,
                "extra_ids": extra_ids,
            },
            "item_cardinality": {
                "passed": counts["item_sets_checked"] == 1200
                and not any(
                    issue["code"] == "item_key_order_or_coverage_mismatch"
                    for issue in issues
                ),
                "expected_items_per_record": list(ITEMS),
                "item_sets_checked": counts["item_sets_checked"],
                "records_with_item_key_mismatch": sum(
                    issue["code"] == "item_key_order_or_coverage_mismatch"
                    for issue in issues
                ),
            },
            "candidate_text_and_character_offsets": {
                "passed": counts["exact_character_slices"] == counts["segments_checked"],
                "segments_checked": counts["segments_checked"],
                "exact_text_equals_dev_doc_slice_count": counts[
                    "exact_character_slices"
                ],
                "invalid_character_range_count": sum(
                    issue["code"] == "invalid_character_range" for issue in issues
                ),
                "text_or_character_offset_mismatch_count": sum(
                    issue["code"] == "candidate_text_or_character_offset_mismatch"
                    for issue in issues
                ),
            },
            "document_identity_and_type": {
                "passed": not any(
                    issue["code"] in {"segment_doc_id_missing", "doc_type_mismatch"}
                    for issue in issues
                ),
                "segments_checked": counts["segments_checked"],
                "missing_doc_id_count": sum(
                    issue["code"] == "segment_doc_id_missing" for issue in issues
                ),
                "doc_type_mismatch_count": sum(
                    issue["code"] == "doc_type_mismatch" for issue in issues
                ),
            },
            "line_offsets": {
                "passed": not any(
                    issue["severity"] == "fatal" and "line_" in issue["code"]
                    for issue in issues
                ),
                "segments_checked": counts["segments_checked"],
                "invalid_line_range_count": sum(
                    issue["code"] == "invalid_line_range" for issue in issues
                ),
                "line_start_matches_start_character_count": counts["exact_line_starts"],
                "line_start_mismatch_count": sum(
                    issue["code"] == "line_start_character_mismatch" for issue in issues
                ),
                "line_end_matches_exact_candidate_end_count": counts["exact_line_ends"],
                "preserved_search_window_line_end_after_character_cut_count": counts[
                    "preserved_search_window_line_ends"
                ],
                "unexpected_line_end_mismatch_count": sum(
                    issue["code"] == "unexpected_line_end_character_mismatch"
                    for issue in issues
                ),
                "note": (
                    "Listed warnings have budget_truncated=true, exact "
                    "text==doc.text[start:end], and a line_end that identifies the "
                    "pre-cut search-window end rather than the line containing the "
                    "stored candidate end."
                ),
            },
            "candidate_chars": {
                "passed": not any(
                    issue["code"] == "candidate_chars_mismatch" for issue in issues
                ),
                "item_sets_checked": counts["item_sets_checked"],
                "candidate_chars_equals_sum_of_segment_text_lengths_count": (
                    counts["item_sets_checked"]
                    - sum(issue["code"] == "candidate_chars_mismatch" for issue in issues)
                ),
                "mismatch_count": sum(
                    issue["code"] == "candidate_chars_mismatch" for issue in issues
                ),
            },
            "selected_meta": {
                "passed": not any(
                    issue["code"]
                    in {
                        "selected_meta_key_missing_in_dev",
                        "selected_meta_value_or_type_mismatch",
                    }
                    for issue in issues
                ),
                "values_checked": counts["selected_meta_values_checked"],
                "missing_source_key_count": sum(
                    issue["code"] == "selected_meta_key_missing_in_dev"
                    for issue in issues
                ),
                "value_or_type_mismatch_count": sum(
                    issue["code"] == "selected_meta_value_or_type_mismatch"
                    for issue in issues
                ),
                "key_shapes": {
                    key: shapes[0] if len(shapes) == 1 else shapes
                    for key, shapes in selected_meta_shapes.items()
                },
                "records_per_item_with_exact_key_shape": exact_meta_shape_counts,
            },
            "input_completeness": {
                "passed": not any(
                    issue["code"] == "input_completeness_mismatch" for issue in issues
                ),
                "objects_checked": counts["input_completeness_objects_checked"],
                "values_checked": counts["input_completeness_values_checked"],
                "mismatch_count": sum(
                    issue["code"] == "input_completeness_mismatch" for issue in issues
                ),
            },
            "dropped_doc_counts": {
                "passed": not any(
                    issue["code"] == "dropped_doc_counts_mismatch" for issue in issues
                ),
                "objects_checked": counts["dropped_doc_counts_objects_checked"],
                "source_key_value_pairs_checked": counts[
                    "dropped_doc_count_values_checked"
                ],
                "mismatch_count": sum(
                    issue["code"] == "dropped_doc_counts_mismatch" for issue in issues
                ),
            },
            "per_item": per_item_report,
        },
        "issues": issues,
    }
    return report


def audit_source_alignment(output=DEFAULT_OUTPUT):
    """Write and return a complete CMS source-alignment report."""
    output = Path(output)
    if output.exists() and (output.parent / "predictions_frozen.json").exists():
        raise FileExistsError("Do not overwrite an execution audit after predictions are frozen; choose another output path")
    sources = _authored_sources()
    candidates_data = sources["candidates"][1]
    dev_data = (ROOT / "data/dev.jsonl").read_bytes()
    report = _audit(candidates_data, dev_data, sources)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    report = audit_source_alignment(args.output.resolve())
    print(
        json.dumps(
            {
                "output": str(args.output.resolve()),
                "passed": report["passed"],
                "fatal_issues": report["summary"]["fatal_issue_count"],
                "warnings": report["summary"]["warning_issue_count"],
            },
            ensure_ascii=False,
        )
    )
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    raise SystemExit("Archived experiment: create a new registered run; see docs/operations.md. Historical evidence is read-only.")
    main()
