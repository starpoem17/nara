"""Conversation rules through the same interfaces used by every live schedule."""
from copy import deepcopy
from dataclasses import asdict
import json
import unittest

from nara.inference import Limits, Predictor, Reply, _Task, compact
from nara.continuous import ContinuousPredictor
from nara.batch_barrier import BatchedPredictor
from nara.prefix_pipeline import PrefixPipelinePredictor
from test_inference import TABLE, SCHEMA, Retriever, record, final


KINDS = (Predictor, ContinuousPredictor, BatchedPredictor, PrefixPipelinePredictor)


class ScriptedModel:
    max_model_len = 100000
    thinking = False

    def __init__(self, behavior=final):
        self.behavior = behavior
        self.turns = []
        self.pending = {}
        self.aborted = False

    def count_text(self, text):
        return len(text)

    def count_messages(self, messages):
        return sum(len(m['content']) + 4 for m in messages)

    def response(self, turn):
        value = self.behavior(turn)
        return value if isinstance(value, Reply) else Reply(value)

    def generate(self, turns):
        self.turns.extend(deepcopy(turns))
        return {t.task_id: self.response(t) for t in reversed(turns)}

    def submit(self, turn):
        self.turns.append(deepcopy(turn))
        self.pending[turn.task_id] = deepcopy(turn)

    def poll(self):
        # Return later requests first, so identity cannot depend on completion order.
        key = next(reversed(self.pending))
        return [(key, self.response(self.pending.pop(key)))]

    def abort(self):
        self.aborted = True
        self.pending.clear()


class ConversationTests(unittest.TestCase):
    def make(self, kind, behavior=final, *, retriever=None, **limits):
        model = ScriptedModel(behavior)
        predictor = kind(model, retriever if retriever is not None else Retriever(),
                         TABLE, SCHEMA, limits=Limits(output_tokens=512, batch_size=4, **limits))
        return predictor, model

    def run_predictions(self, predictor, records=None, groups=None):
        records = records or [record()]
        groups = groups or [list(TABLE)]
        if isinstance(predictor, PrefixPipelinePredictor):
            return predictor.predict(records, item_groups=groups,
                                     source_tokens={r['id']: 1 for r in records})
        return predictor.predict(records, item_groups=groups)

    @staticmethod
    def required_search(turn):
        if turn.schema['properties']['action']['const'] == 'search':
            return compact({'action': 'search', 'queries': ['q']})
        return final(turn, '공고 원문 근거')

    def test_required_search_shrinks_action_but_preserves_source_and_final_budget(self):
        for kind in KINDS:
            with self.subTest(kind=kind.__name__):
                p, model = self.make(kind, self.required_search, search_rounds=1, require_search=True)
                original = p.conversation('probe', record(), TABLE).next_turn().messages
                model.max_model_len = model.count_messages(original) + 2 * 512 + 200
                result = self.run_predictions(p)[0]
                self.assertIsNone(result.error)
                self.assertEqual([t.max_tokens for t in model.turns], [456, 512])
                self.assertEqual(model.turns[1].messages[1], original[1])
                self.assertGreater(result.trace[0]['retrieval_tokens'], 0)
                self.assertEqual(result.judgments['v1']['근거문구'], '공고 원문 근거')
                self.assertIsNone(result.judgments['v2']['근거문구'])

    def test_context_limits_reject_required_search_and_disable_optional_search(self):
        for kind in KINDS:
            for required in (True, False):
                with self.subTest(kind=kind.__name__, required=required):
                    p, model = self.make(kind, search_rounds=1, require_search=required)
                    turn = p.conversation('probe', record(), TABLE).next_turn()
                    source = model.count_messages(turn.messages)
                    model.max_model_len = source + 512 + (256 + 31 if required else 128)
                    result = self.run_predictions(p)[0]
                    if required:
                        self.assertIn('Required search cannot fit', result.error)
                        self.assertEqual(model.turns, [])
                    else:
                        self.assertIsNone(result.error)
                        self.assertNotIn('anyOf', model.turns[0].schema)
                        self.assertEqual(model.turns[0].messages, turn.messages)
                        model.max_model_len -= 1
                        model.turns.clear()
                        self.assertIsNone(self.run_predictions(p)[0].judgments)
                        self.assertEqual(model.turns, [])

    def test_required_search_cannot_be_bypassed_by_invalid_or_premature_final(self):
        for kind in KINDS:
            for response in ('broken JSON', final):
                with self.subTest(kind=kind.__name__, response=response):
                    behavior = response if callable(response) else lambda t: response
                    # final() intentionally cannot read a search-only schema.
                    if response is final:
                        behavior = lambda t: compact({'action': 'final', 'judgments': {
                            k: {'위반여부': 0, '근거문구': None} for k in TABLE}})
                    p, model = self.make(kind, behavior, search_rounds=1, require_search=True)
                    result = self.run_predictions(p)[0]
                    self.assertIsNone(result.judgments)
                    self.assertIn('after retries', result.error)
                    self.assertEqual(len(model.turns), 2)
                    self.assertTrue(all(t.schema['properties']['action']['const'] == 'search'
                                        for t in model.turns))
                    self.assertEqual(p.retriever.calls, [])

    def test_required_search_needs_material_in_context(self):
        class NoResults(Retriever):
            def search(self, queries, **kwargs):
                self.calls.append(queries)
                return {k: [] for k in queries}

        class WrongIds(NoResults):
            def search(self, queries, **kwargs):
                self.calls.append(queries)
                return {'wrong': []}

        for kind in KINDS:
            for case in ('failure', 'empty', 'wrong_ids', 'cannot_pack'):
                with self.subTest(kind=kind.__name__, case=case):
                    retriever = {'failure': Retriever(fail=True), 'empty': NoResults(),
                                 'wrong_ids': WrongIds(), 'cannot_pack': Retriever()}[case]
                    extra = {'round_tokens': 1} if case == 'cannot_pack' else {}
                    p, model = self.make(kind, self.required_search, retriever=retriever,
                                         search_rounds=1, require_search=True, **extra)
                    result = self.run_predictions(p)[0]
                    self.assertIsNone(result.judgments)
                    self.assertIn('no passages', result.error)
                    self.assertEqual(result.trace[0]['search_rounds'], 1)
                    self.assertEqual(result.trace[0]['retrieval_tokens'], 0)
                    self.assertEqual(len(retriever.calls), 1)

    def test_result_deduplication_and_budgets_match_across_schedules(self):
        def behavior(turn):
            if 'anyOf' in turn.schema:
                return compact({'action': 'search', 'queries': ['q', 'q']})
            return final(turn, '법령 자료')

        for kind in KINDS:
            with self.subTest(kind=kind.__name__):
                p, _ = self.make(kind, behavior, retriever=Retriever(same=True),
                                 round_tokens=180, total_retrieval_tokens=350)
                result = self.run_predictions(p)[0]
                searches = [e for e in result.trace[0]['events'] if e['event'] == 'search']
                self.assertIsNone(result.error)
                self.assertEqual([e['passage_ids'] for e in searches], [['p'], []])
                self.assertGreater(searches[0]['tokens'], len('법령 자료'))
                self.assertLessEqual(searches[0]['tokens'], 180)
                self.assertLessEqual(result.trace[0]['retrieval_tokens'], 350)
                self.assertTrue(all(v['근거문구'] is None for v in result.judgments.values()))

    def test_retrieval_batching_and_query_identity_are_preserved(self):
        def behavior(turn):
            if len(turn.messages) == 2:
                return compact({'action': 'search', 'queries': [turn.task_id]})
            self.assertIn('법령 자료 ' + turn.task_id, turn.messages[-1]['content'])
            return final(turn)

        for kind in KINDS:
            with self.subTest(kind=kind.__name__):
                p, _ = self.make(kind, behavior)
                results = self.run_predictions(p, [record('A'), record('B')])
                self.assertEqual([r.record_id for r in results], ['A', 'B'])
                self.assertTrue(all(r.error is None for r in results))
                self.assertEqual([len(q) for q in p.retriever.calls],
                                 [2] if kind is Predictor else [1, 1])
                self.assertEqual(p.metrics['retrieval_batches'], len(p.retriever.calls))
                for result in results:
                    task = result.trace[0]
                    search = next(e for e in task['events'] if e['event'] == 'search')
                    self.assertEqual(search['queries'], {task['task_id'] + ':1:0': task['task_id']})

    def test_truncation_and_returned_errors_retry_without_cross_group_state(self):
        for kind in KINDS:
            for error in (Reply('bad', finish_reason='length'), Reply('', error='request failed')):
                with self.subTest(kind=kind.__name__, error=error):
                    seen = set()
                    def behavior(turn):
                        self.assertNotIn('DO NOT LEAK', compact(turn.messages))
                        if turn.task_id not in seen:
                            seen.add(turn.task_id)
                            return error
                        self.assertNotIn('anyOf', turn.schema)
                        return final(turn, '공고 원문 근거')
                    p, model = self.make(kind, behavior, instant_output_tokens=128)
                    results = self.run_predictions(p, [record('A'), record('B')],
                                                   [['v1', 'v2'], ['v3', 'v4']])
                    self.assertTrue(all(not r.error and set(r.judgments) == set(TABLE) for r in results))
                    self.assertEqual(len(model.turns), 8)
                    self.assertEqual({t.max_tokens for t in model.turns}, {128})
                    self.assertFalse(model.aborted)
                    for result in results:
                        for task in result.trace:
                            self.assertEqual(sum(e['event'] == 'invalid_response' for e in task['events']), 1)

    def test_engine_exceptions_keep_offline_retry_and_streaming_abort(self):
        for kind in KINDS:
            with self.subTest(kind=kind.__name__):
                p, model = self.make(kind)
                if kind is Predictor:
                    original = model.generate
                    calls = 0
                    def generate(turns):
                        nonlocal calls
                        calls += 1
                        if calls == 1:
                            raise RuntimeError('engine failed')
                        return original(turns)
                    model.generate = generate
                    result = self.run_predictions(p)[0]
                    self.assertIsNone(result.error)
                    self.assertEqual(calls, 2)
                    self.assertIn('engine failed', result.trace[0]['events'][0]['error'])
                    self.assertFalse(model.aborted)
                else:
                    def poll():
                        raise RuntimeError('engine failed')
                    model.poll = poll
                    with self.assertRaisesRegex(RuntimeError, 'engine failed'):
                        self.run_predictions(p)
                    self.assertTrue(model.aborted)
                    self.assertEqual(model.pending, {})

    def test_invalid_retrieval_material_keeps_execution_specific_handling(self):
        class InvalidMaterial(Retriever):
            def search(self, queries, **kwargs):
                hits = super().search(queries, **kwargs)
                # A malformed adapter result causes a JSON packing error.
                from dataclasses import replace
                return {k: [replace(v[0], source=object())] for k, v in hits.items()}
        def behavior(turn):
            if len(turn.messages) == 2:
                return compact({'action': 'search', 'queries': ['q']})
            return final(turn)
        for kind in KINDS:
            with self.subTest(kind=kind.__name__):
                p, _ = self.make(kind, behavior, retriever=InvalidMaterial())
                if kind is Predictor:
                    with self.assertRaises(TypeError):
                        self.run_predictions(p)
                else:
                    result = self.run_predictions(p)[0]
                    self.assertIsNone(result.error)
                    self.assertEqual(result.trace[0]['search_rounds'], 1)
                    self.assertTrue(any(e['event'] == 'invalid_response' for e in result.trace[0]['events']))

    def test_conversation_interface_owns_search_and_detaches_results(self):
        p, _ = self.make(Predictor, search_rounds=1)
        conversation = p.conversation('A:0', record(), TABLE)
        turn = conversation.next_turn()
        saved = deepcopy(turn.messages)
        queries = conversation.accept_reply(turn, Reply(compact({'action': 'search', 'queries': ['q']})))
        self.assertEqual(turn.messages, saved)
        with self.assertRaisesRegex(RuntimeError, 'Search results'):
            conversation.next_turn()
        hits = Retriever().search(queries, top_k=5)
        queries.clear()
        conversation.accept_search(hits)
        turn = conversation.next_turn()
        conversation.accept_reply(turn, Reply(final(turn, '공고 원문 근거')))
        self.assertTrue(conversation.done)
        self.assertIsNone(conversation.next_turn())
        snapshot = conversation.snapshot()
        snapshot['events'].clear()
        judgments = conversation.judgments
        judgments['v1']['위반여부'] = 0
        self.assertEqual(conversation.judgments['v1']['위반여부'], 1)
        self.assertEqual(len(conversation.snapshot()['events']), 4)

    def test_legacy_task_turn_and_finish_use_the_shared_rules(self):
        p, _ = self.make(ContinuousPredictor, search_rounds=0)
        rec = record()
        conversation = p.conversation('legacy', rec, TABLE)
        turn = conversation.next_turn()
        task = _Task('legacy', rec, tuple(TABLE), deepcopy(turn.messages))
        self.assertEqual(asdict(p._turn(task)), asdict(turn))
        reply = final(turn, 'not in the notice')
        p._finish(task, json.loads(reply)['judgments'])
        conversation.accept_reply(turn, Reply(reply))
        self.assertEqual(task.judgments, conversation.judgments)
        self.assertEqual(task.trace[-1], conversation.snapshot()['events'][-1])


if __name__ == '__main__':
    unittest.main()
