"""Behavioral checks through Predictor.predict; no model downloads."""
import copy
from pathlib import Path
import tempfile
import unittest

from nara.inference import Limits, Predictor, Reply, compact
from nara.retrieval import SearchHit
from script import write_submission


TABLE = {f"v{i}": {"항목명": f"항목{i}", "비고": "", "부재탐지": i == 2}
         for i in range(1, 5)}
CELL = {"type": "object", "required": ["위반여부", "근거문구"],
        "additionalProperties": False,
        "properties": {"위반여부": {"type": "integer", "enum": [0, 1]},
                       "근거문구": {"type": ["string", "null"], "maxLength": 500}}}
SCHEMA = {"properties": {key: CELL for key in TABLE}}


def record(key="A"):
    return {"id": key, "meta": {}, "docs": [
        {"type": "공고문", "doc_id": "notice", "text": f"{key} 공고 원문 근거"},
        {"type": "첨부", "doc_id": "attachment", "text": "첨부 자료"}],
        "labels": "DO NOT LEAK"}


def final(turn, evidence=None):
    schema = turn.schema.get("anyOf", [turn.schema])[-1]
    keys = schema["properties"]["judgments"]["properties"]
    return compact({"action": "final", "judgments": {
        key: {"위반여부": int(evidence is not None), "근거문구": evidence} for key in keys}})


class Model:
    max_model_len = 100_000

    def __init__(self, behavior):
        self.behavior, self.calls = behavior, []

    def count_text(self, text):
        return len(text)

    def count_messages(self, messages):
        return sum(len(message["content"]) + 4 for message in messages)

    def generate(self, turns):
        self.calls.append(copy.deepcopy(turns))
        return {turn.task_id: Reply(self.behavior(turn), input_tokens=self.count_messages(turn.messages))
                for turn in reversed(turns)}


class Retriever:
    def __init__(self, fail=False, same=False):
        self.calls, self.fail, self.same = [], fail, same

    def search(self, queries, *, top_k):
        self.calls.append(queries)
        if self.fail:
            raise RuntimeError("offline search unavailable")
        return {key: [SearchHit(
            "p" if self.same else query, "법령 자료" if self.same else f"법령 자료 {query}",
            "law.txt", "article:1", "법령", "제1조", 0.9)] for key, query in reversed(list(queries.items()))}


def predict(model, retriever=None, records=None, limits=None, groups=None):
    p = Predictor(model, retriever or Retriever(), TABLE, SCHEMA,
                  limits=limits or Limits(output_tokens=512))
    return p.predict(records or [record()], item_groups=groups)


class InferenceTests(unittest.TestCase):
    def test_zero_round_and_label_isolation(self):
        model = Model(final)
        result = predict(model)[0]
        self.assertIsNone(result.error)
        self.assertEqual(set(result.judgments), set(TABLE))
        self.assertNotIn("DO NOT LEAK", compact(model.calls[0][0].messages))
        self.assertEqual(result.trace[0]["search_rounds"], 0)

    def test_two_rounds_refinement_and_id_routing(self):
        def behavior(turn):
            if len(turn.messages) == 2:
                return compact({"action": "search", "queries": [turn.task_id + ":first"] * 4})
            if len(turn.messages) == 4:
                self.assertIn(turn.task_id + ":first", turn.messages[-1]["content"])
                other = "1:0" if turn.task_id == "0:0" else "0:0"
                self.assertNotIn(other, turn.messages[-1]["content"])
                return compact({"action": "search", "queries": [turn.task_id + ":refined"]})
            self.assertNotIn("anyOf", turn.schema)
            self.assertIn("반드시 최종", turn.messages[-1]["content"])
            return final(turn)
        model, retriever = Model(behavior), Retriever()
        results = predict(model, retriever, [record("A"), record("B")])
        self.assertEqual([r.record_id for r in results], ["A", "B"])
        self.assertTrue(all(r.error is None for r in results))
        self.assertEqual([len(batch) for batch in retriever.calls], [8, 2])
        self.assertEqual([r.trace[0]["search_rounds"] for r in results], [2, 2])

    def test_mixed_completion_and_groups(self):
        def behavior(turn):
            if turn.task_id == "0:0" and len(turn.messages) == 2:
                return compact({"action": "search", "queries": ["query"]})
            return final(turn)
        model, retriever = Model(behavior), Retriever()
        results = predict(model, retriever, [record("A"), record("B")],
                          groups=[["v1", "v3"], ["v2", "v4"]])
        self.assertEqual(len(model.calls[0]), 4)
        self.assertEqual(len(model.calls[1]), 1)
        self.assertTrue(all(set(r.judgments) == set(TABLE) for r in results))
        for groups in ([["v1"]], [["v1", "v2"], ["v2", "v3", "v4"]], [[]]):
            with self.assertRaises(ValueError):
                predict(Model(final), groups=groups)

    def test_third_search_cannot_execute_or_fill_zeros(self):
        model = Model(lambda turn: compact({"action": "search", "queries": ["query"]}))
        retriever = Retriever()
        result = predict(model, retriever)[0]
        self.assertEqual(len(retriever.calls), 2)
        self.assertIsNotNone(result.error)
        self.assertIsNone(result.judgments)
        self.assertEqual(len(model.calls), 4)

    def test_invalid_json_retries_final_once(self):
        count = 0
        def behavior(turn):
            nonlocal count
            count += 1
            return "broken JSON" if count == 1 else final(turn)
        model = Model(behavior)
        self.assertIsNone(predict(model)[0].error)
        self.assertNotIn("anyOf", model.calls[-1][0].schema)

    def test_extra_queries_rejected_before_retrieval(self):
        retriever = Retriever()
        model = Model(lambda turn: compact({"action": "search", "queries": ["q"] * 5}))
        self.assertIsNotNone(predict(model, retriever)[0].error)
        self.assertEqual(retriever.calls, [])

    def test_failed_retrieval_consumes_round_and_model_can_finish(self):
        def behavior(turn):
            if "anyOf" in turn.schema:
                return compact({"action": "search", "queries": ["query"]})
            return final(turn)
        retriever = Retriever(fail=True)
        result = predict(Model(behavior), retriever)[0]
        self.assertEqual(len(retriever.calls), 2)
        self.assertEqual(result.trace[0]["search_rounds"], 2)
        self.assertIsNone(result.error)

    def test_deduplication_and_formatted_token_budgets(self):
        def behavior(turn):
            return (compact({"action": "search", "queries": ["query"]})
                    if "anyOf" in turn.schema else final(turn))
        limits = Limits(output_tokens=512, round_tokens=180, total_retrieval_tokens=350)
        result = predict(Model(behavior), Retriever(same=True), limits=limits)[0]
        events = [e for e in result.trace[0]["events"] if e["event"] == "search"]
        self.assertEqual([e["passage_ids"] for e in events], [["p"], []])
        self.assertGreater(events[0]["tokens"], len("법령 자료"))
        self.assertTrue(all(e["tokens"] <= 180 for e in events))
        self.assertLessEqual(result.trace[0]["retrieval_tokens"], 350)

    def test_evidence_is_from_single_original_document(self):
        result = predict(Model(lambda turn: final(turn, "공고 원문")))[0]
        self.assertEqual(result.judgments["v1"]["근거문구"], "공고 원문")
        self.assertIsNone(result.judgments["v2"]["근거문구"])
        for evidence in ("법령 자료", "원문 근거\n첨부 자료"):
            result = predict(Model(lambda turn: final(turn, evidence)))[0]
            self.assertIsNone(result.judgments["v1"]["근거문구"])

    def test_context_preserves_source_and_can_disable_search(self):
        model = Model(final)
        base = Predictor(model, Retriever(), TABLE, SCHEMA)._messages(record(), tuple(TABLE))
        model.max_model_len = model.count_messages(base) + 512 + 128
        result = predict(model)[0]
        self.assertIsNone(result.error)
        self.assertNotIn("anyOf", model.calls[0][0].schema)
        self.assertIn("A 공고 원문 근거", model.calls[0][0].messages[-1]["content"])
        model.max_model_len -= 1
        result = predict(model)[0]
        self.assertIsNone(result.judgments)
        self.assertIn("context", result.error)

    def test_required_search_then_exactly_one_final(self):
        def behavior(turn):
            if turn.schema['properties']['action']['const'] == 'search':
                self.assertNotIn('anyOf', turn.schema)
                return compact({'action': 'search', 'queries': ['query']})
            self.assertIn('법령 자료', turn.messages[-1]['content'])
            return final(turn)
        model, retriever = Model(behavior), Retriever()
        result = predict(model, retriever,
                         limits=Limits(output_tokens=512, search_rounds=1, require_search=True))[0]
        self.assertIsNone(result.error)
        self.assertEqual(len(model.calls), 2)
        self.assertEqual(len(retriever.calls), 1)
        self.assertGreater(result.trace[0]['retrieval_tokens'], 0)

    def test_required_search_cannot_be_bypassed_by_invalid_output(self):
        premature = compact({'action': 'final', 'judgments': {
            k: {'위반여부': 0, '근거문구': None} for k in TABLE}})
        model = Model(lambda turn: premature)
        result = predict(model, limits=Limits(search_rounds=1, require_search=True))[0]
        self.assertIsNotNone(result.error)
        self.assertIsNone(result.judgments)
        self.assertEqual(len(model.calls), 2)
        for calls in model.calls:
            self.assertEqual(calls[0].schema['properties']['action']['const'], 'search')

    def test_required_search_uses_remaining_context_without_truncation(self):
        def behavior(turn):
            if turn.schema['properties']['action']['const'] == 'search':
                return compact({'action': 'search', 'queries': ['q']})
            return final(turn)
        model = Model(behavior)
        limits = Limits(output_tokens=512, search_rounds=1, require_search=True)
        base = Predictor(model, Retriever(), TABLE, SCHEMA, limits=limits)._messages(record(), tuple(TABLE))
        source_tokens = model.count_messages(base)
        model.max_model_len = source_tokens + 2 * 512 + 200
        result = predict(model, limits=limits)[0]
        self.assertIsNone(result.error)
        self.assertLess(model.calls[0][0].max_tokens, 512)
        self.assertEqual(model.calls[1][0].max_tokens, 512)
        self.assertEqual(model.calls[1][0].messages[1]['content'], base[1]['content'])
        model.calls.clear()
        model.max_model_len = source_tokens + 512 + 256 + 31
        result = predict(model, limits=limits)[0]
        self.assertIsNotNone(result.error)
        self.assertEqual(model.calls, [])

    def test_required_search_failure_cannot_count_as_rag_success(self):
        def behavior(turn):
            return (compact({'action': 'search', 'queries': ['q']})
                    if turn.schema['properties']['action']['const'] == 'search' else final(turn))
        result = predict(Model(behavior), Retriever(fail=True),
                         limits=Limits(search_rounds=1, require_search=True))[0]
        self.assertIsNone(result.judgments)
        self.assertIn('no passages', result.error)
        with self.assertRaises(ValueError):
            Limits(search_rounds=0, require_search=True)

    def test_submission_refuses_failed_record(self):
        results = predict(Model(lambda turn: "invalid"))
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "submission.csv"
            with self.assertRaises(ValueError):
                write_submission(results, target)
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
