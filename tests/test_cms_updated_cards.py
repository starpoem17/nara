"""CMS input fidelity and completion-driven scheduling, without model inference."""
from types import SimpleNamespace
import unittest

from jsonschema import validate, ValidationError
from experiments.legacy_CMS_updated_cards_v19_v24_dev200_20260913.code.cms_updated_cards import (
    EMPTY, ITEMS, PREFIX, authored_sources, card_blocks, check_budget,
    execute_once, output_schema, render_card,
)


class CMSInputTests(unittest.TestCase):
    def test_author_blocks_change_only_the_authorized_memo(self):
        import re
        source = authored_sources()["cards"][1].decode()
        original = re.findall(r"```text\n(.*?)\n```", source, re.S)
        cards, exclusion = card_blocks(source)
        self.assertEqual(exclusion["source_line"], 169)
        for item, block in zip(ITEMS, original):
            expected = block.replace(exclusion["removed_text"] + "\n", "") if item == "v24" else block
            self.assertEqual(cards[item], expected)

    def test_candidate_text_and_metadata_are_not_reinterpreted_or_trimmed(self):
        candidate = {"meta": {"원래값": "{원문후보}", "빈값": None},
            "input_completeness": {"완전관측": False}, "dropped_doc_counts": {},
            "segments": [{"text": " 첫 조각\n\n'인용' "}, {"text": "{META} 둘째"}]}
        result = render_card("[META]\n{META}\n[원문]\n{원문후보}", candidate)
        self.assertEqual(result, "[META]\n원래값: {원문후보}\n빈값: null\n"
            "input_completeness:\n  완전관측: false\ndropped_doc_counts:\n[원문]\n"
            + PREFIX + "' 첫 조각\n\n'인용' ', '{META} 둘째'")
        candidate["segments"] = []
        self.assertTrue(render_card("{META}\n[원문]\n{원문후보}", candidate).endswith("[원문]\n" + EMPTY))

    def test_token_exception_is_confined_to_one_notice_item(self):
        check_budget("PPS-DEV-189", "v24", 2024)
        for record_id, item, length in (("PPS-DEV-189", "v24", 2025),
                                      ("PPS-DEV-189", "v23", 2001),
                                      ("PPS-DEV-188", "v24", 2001)):
            with self.assertRaises(ValueError):
                check_budget(record_id, item, length)

    def test_schema_leaves_evidence_semantics_to_the_model_and_audit(self):
        schema = output_schema("v20")
        for judgment in (0, 1):
            for evidence in (None, "", "not a source quote" * 100):
                validate({"v20": {"위반여부": judgment, "근거문구": evidence}}, schema)
        for wrong in ({"v19": {"위반여부": 0, "근거문구": None}},
                      {"v20": {"위반여부": 2, "근거문구": None}},
                      {"v20": {"위반여부": 0, "근거문구": None}, "공고ID": "A"}):
            with self.assertRaises(ValidationError):
                validate(wrong, schema)


class SchedulingTests(unittest.TestCase):
    def test_refills_while_previous_requests_remain_and_routes_completion_ids(self):
        class Stream:
            def __init__(self):
                self.pending = []
                self.events = []

            def submit(self, turn):
                self.events.append(("submit", turn.task_id, len(self.pending)))
                self.pending.append(turn)
                self.assert_settings(turn)

            @staticmethod
            def assert_settings(turn):
                assert turn.max_tokens == 512
                assert turn.messages == [{"role": "user", "content": turn.task_id}]

            def poll(self):
                turn = self.pending.pop()  # Complete later requests before earlier ones.
                self.events.append(("complete", turn.task_id, len(self.pending)))
                return [(turn.task_id, SimpleNamespace(text=turn.task_id))]

        stream = Stream()
        rows = [{"task_id": str(i), "messages": [{"role": "user", "content": str(i)}],
                 "schema": output_schema("v19")} for i in range(40)]
        results, submitted = [], set()
        execute_once(stream, rows, lambda key, reply: results.append((key, reply.text)), submitted)
        self.assertEqual(len(results), 40)
        self.assertEqual(len(submitted), 40)
        self.assertEqual(set(results), {(str(i), str(i)) for i in range(40)})
        self.assertEqual(stream.events[16][0], "complete")
        self.assertEqual(stream.events[17], ("submit", "16", 15))
        self.assertTrue(all(size < 16 for event, _, size in stream.events if event == "submit"))
        self.assertEqual(sum(event == "submit" for event, _, _ in stream.events), 40)


if __name__ == "__main__":
    unittest.main()
