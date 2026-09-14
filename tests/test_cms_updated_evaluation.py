import csv
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments.legacy_CMS_updated_cards_v19_v24_dev200_20260913.code import evaluate_cms_updated_cards as evaluation


def schema(item):
    return {
        "type": "object", "properties": {
            item: {"type": "object", "properties": {
                "위반여부": {"type": "integer", "enum": [0, 1]},
                "근거문구": {"type": ["string", "null"]},
            }, "required": ["위반여부", "근거문구"], "additionalProperties": False},
        }, "required": [item], "additionalProperties": False,
    }


class CmsUpdatedEvaluationTests(unittest.TestCase):
    def test_invalid_output_is_not_zero_and_valid_v20_requires_null_evidence(self):
        valid = {"status": "completed", "reply": {"text": '{"v20":{"위반여부":0,"근거문구":null}}',
                 "finish_reason": "stop"}, "raw": {"text": '{"v20":{"위반여부":0,"근거문구":null}}',
                 "finish_reason": "stop"}}
        ok, reason, value = evaluation._parse_prediction(valid, schema("v20"))
        self.assertTrue(ok)
        evidence = evaluation._evidence_observations(
            "v20", value, {"docs": [{"text": "원문"}]}, [], None)
        self.assertTrue(evidence["evidence_semantic_valid"])

        invalid = dict(valid)
        invalid["reply"] = {"text": "not json", "finish_reason": "stop"}
        invalid["raw"] = {"text": "not json", "finish_reason": "stop"}
        ok, _, value = evaluation._parse_prediction(invalid, schema("v20"))
        self.assertFalse(ok)
        score = evaluation._classification([
            {"output_valid": True, "gold": 0, "prediction": 0},
            {"output_valid": False, "gold": 0, "prediction": None},
        ])
        self.assertEqual((score["valid"], score["invalid"], score["tn"]), (1, 1, 1))
        self.assertIsNone(value)

    def test_noncontiguous_quote_is_invalid_even_if_fragments_exist(self):
        value = {"v19": {"위반여부": 1, "근거문구": "앞문구뒷문구"}}
        result = evaluation._evidence_observations(
            "v19", value, {"docs": [{"text": "앞문구 ... 뒷문구"}]},
            ["앞문구", "뒷문구"], None)
        self.assertFalse(result["evidence_semantic_valid"])
        self.assertFalse(result["evidence_original_substring"])
        self.assertFalse(result["evidence_selected_candidate_substring"])

    def test_positive_quote_can_be_original_but_outside_selected_candidates(self):
        value = {"v21": {"위반여부": 1, "근거문구": "정확한 원문"}}
        result = evaluation._evidence_observations(
            "v21", value, {"docs": [{"text": "여기에 정확한 원문이 있다"}]},
            ["다른 후보"], "reference")
        self.assertTrue(result["evidence_semantic_valid"])
        self.assertTrue(result["evidence_original_substring"])
        self.assertFalse(result["evidence_selected_candidate_substring"])
        self.assertFalse(result["reference_evidence_exact_match"])

    def test_negative_nonnull_and_v20_nonnull_are_separate_semantic_failures(self):
        for item, reason in (("v19", "negative_evidence_must_be_null"),
                             ("v20", "v20_evidence_must_be_null")):
            value = {item: {"위반여부": 0, "근거문구": "원문"}}
            result = evaluation._evidence_observations(
                item, value, {"docs": [{"text": "원문"}]}, ["원문"], None)
            self.assertFalse(result["evidence_semantic_valid"])
            self.assertEqual(result["evidence_invalid_reason"], reason)

    def test_schema_rejects_extra_key_and_length_finish(self):
        text = '{"v22":{"위반여부":1,"근거문구":"원문","추가":1}}'
        row = {"status": "completed", "reply": {"text": text, "finish_reason": "stop"},
               "raw": {"text": text, "finish_reason": "stop"}}
        self.assertFalse(evaluation._parse_prediction(row, schema("v22"))[0])
        text = '{"v22":{"위반여부":1,"근거문구":"원문"}}'
        row = {"status": "completed", "reply": {"text": text, "finish_reason": "length"},
               "raw": {"text": text, "finish_reason": "length"}}
        self.assertFalse(evaluation._parse_prediction(row, schema("v22"))[0])

    def test_notice_hash_is_checked_before_notice_parsing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dev.jsonl"
            path.write_text("not json\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "SHA256 differs from manifest"):
                evaluation._read_notices(path, set(), "0" * 64)


    def test_manifest_artifact_and_run_summary_hash_guards(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            (run / "source").mkdir()
            (run / "inputs.jsonl").write_text("", encoding="utf-8")
            (run / "predictions.jsonl").write_text("", encoding="utf-8")
            (run / "source/candidates.jsonl").write_text("", encoding="utf-8")
            (run / "schemas.json").write_text(
                json.dumps({item: evaluation._expected_schema(item) for item in evaluation.ITEMS}),
                encoding="utf-8")
            (run / "predictions_frozen.json").write_text(json.dumps({
                "sha256": evaluation._sha256(run / "predictions.jsonl"), "rows": 0}),
                encoding="utf-8")
            manifest = {"artifact_sha256": {name: evaluation._sha256(run / name) for name in (
                "inputs.jsonl", "schemas.json", "source/candidates.jsonl")}}
            (run / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            (run / "run_summary.json").write_text(
                json.dumps({"manifest_sha256": "0" * 64}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "manifest SHA256 mismatch"):
                evaluation._preflight(run, expected_requests=0)
            (run / "run_summary.json").write_text(json.dumps({
                "manifest_sha256": evaluation._sha256(run / "manifest.json")}), encoding="utf-8")
            (run / "source/candidates.jsonl").write_text("\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "artifact hash mismatch"):
                evaluation._preflight(run, expected_requests=0)


    def test_frozen_hash_guard_runs_before_any_label_read(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            (run / "source").mkdir()
            for name in ("inputs.jsonl", "schemas.json", "manifest.json", "source/candidates.jsonl",
                         "run_summary.json"):
                (run / name).write_text("{}\n", encoding="utf-8")
            (run / "predictions.jsonl").write_text("{}\n", encoding="utf-8")
            (run / "predictions_frozen.json").write_text(
                json.dumps({"sha256": "0" * 64, "rows": 1200}), encoding="utf-8")
            with patch.object(evaluation, "_read_labels") as read_labels:
                with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
                    evaluation.evaluate(run, run / "labels.csv", run / "notices.jsonl")
                read_labels.assert_not_called()

    def test_predictions_csv_leaves_invalid_cells_blank(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            (run / "source").mkdir()
            cases = []
            for item in evaluation.ITEMS:
                cases.append({"id": "R", "item": item, "output_valid": item != "v23",
                              "prediction": 1 if item != "v23" else None})
            evaluation._write_outputs(run, cases, {"ok": True})
            with (run / "predictions.csv").open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(list(rows[0]), ["id", *evaluation.ITEMS])
            self.assertEqual(rows[0]["v22"], "1")
            self.assertEqual(rows[0]["v23"], "")


if __name__ == "__main__":
    unittest.main()
