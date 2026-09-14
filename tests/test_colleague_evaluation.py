import unittest
from experiments.legacy_CJH_original_cards_v10_v18_20260913.code import evaluate_colleague_cards as evaluation


class EvaluationTests(unittest.TestCase):
    def test_bare_json_is_strict_and_preserves_evidence(self):
        result = evaluation.parse_response('{"위반여부":1,"근거문구":"  원문  "}')
        assert result.valid and result.strict_format and result.format_violation is None
        assert result.violation == 1 and result.evidence == "  원문  "


    def test_one_complete_json_fence_is_readable_but_format_violation(self):
        result = evaluation.parse_response('```json\n{"위반여부":0,"근거문구":null}\n```')
        assert result.valid and not result.strict_format
        assert result.format_violation == "complete_code_fence" and result.violation == 0


    def test_no_surrounding_commentary_repair_or_non_stop_acceptance(self):
        samples = [
            ('답: {"위반여부":1,"근거문구":null}', "stop"),
            ('{"위반여부":1,"근거문구":null} trailing', "stop"),
            ('{"위반여부":1,"근거문구":null}', "length"),
        ]
        assert all(not evaluation.parse_response(text, finish).valid for text, finish in samples)


    def test_duplicate_nan_bool_extra_and_wrong_evidence_are_invalid(self):
        samples = [
            '{"위반여부":1,"위반여부":0,"근거문구":null}',
            '{"위반여부":NaN,"근거문구":null}',
            '{"위반여부":true,"근거문구":null}',
            '{"위반여부":1,"근거문구":null,"이유":"x"}',
            '{"위반여부":1,"근거문구":3}',
        ]
        assert all(not evaluation.parse_response(text).valid for text in samples)


    def test_valid_only_confusion_and_all_record_bounds(self):
        rows = [
            {"valid": True, "gold": 1, "prediction": 1},
            {"valid": True, "gold": 0, "prediction": 1},
            {"valid": True, "gold": 1, "prediction": 0},
            {"valid": True, "gold": 0, "prediction": 0},
            {"valid": False, "gold": 1, "prediction": None},
            {"valid": False, "gold": 0, "prediction": None},
        ]
        score = evaluation._score_feature(rows)
        assert (score["tp"], score["fp"], score["fn"], score["tn"]) == (1, 1, 1, 1)
        assert (score["invalid_gold_positive"], score["invalid_gold_negative"]) == (1, 1)
        assert score["f1_valid_only"] == 0.5
        assert score["f1_all_records_lower"] == 1 / 3
        assert score["f1_all_records_upper"] == 2 / 3


    def test_zero_denominators_are_zero(self):
        score = evaluation._score_feature([])
        assert score["precision"] == score["recall"] == score["f1_valid_only"] == 0
        assert score["f1_all_records_lower"] == score["f1_all_records_upper"] == 0

    def test_code_fence_allows_outer_whitespace_only(self):
        text = "  \n```json\n{\"위반여부\":1,\"근거문구\":\" x \"}\n```\n\t"
        result = evaluation.parse_response(text)
        assert result.valid and not result.strict_format and result.evidence == " x "
        assert not evaluation.parse_response(text + "설명").valid
