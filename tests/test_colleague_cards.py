import json
import unittest
from experiments.legacy_CJH_original_cards_v10_v18_20260913.code.colleague_cards import schedule, common_input, card_messages, code_positions
from nara.inference.conversation import Reply


class FakeStream:
    def __init__(self, fail=False):
        self.pending = {}
        self.clock = 0
        self.events = []
        self.fail = fail
        self.aborted = False
    def submit(self, turn):
        self.pending[turn.task_id] = (turn, self.clock + (1 if turn.task_id.endswith(':v10') else 5))
        self.events.append(('submit', turn.task_id, self.clock, len(self.pending)))
    def poll(self):
        if self.fail:
            raise RuntimeError('synthetic engine failure')
        self.clock = min(v[1] for v in self.pending.values())
        result = []
        for key, (_, end) in list(self.pending.items()):
            if end <= self.clock:
                self.pending.pop(key)
                self.events.append(('complete', key, self.clock, len(self.pending)))
                result.append((key, Reply('RAW_UNPARSEABLE_OUTPUT', 'length')))
        return result
    def abort(self):
        self.aborted = True
        self.pending.clear()


class OriginalCardTests(unittest.TestCase):
    def inputs(self):
        ids = [str(i) for i in range(12)]
        features = [f'v{i}' for i in range(10, 19)]
        requests = {(rid, f): {'task_id': rid + ':' + f, 'messages': [{'role': 'user', 'content': rid + ' ' + f}]}
                    for rid in ids for f in features}
        return ids, features, requests
    def test_completion_refill_seeds_and_all_raw_failures_are_preserved(self):
        ids, features, requests = self.inputs()
        original = [r['messages'][0]['content'] for r in requests.values()]
        engine = FakeStream()
        received = []
        events = schedule(engine, requests, ids, features, {rid: 100 for rid in ids},
                          lambda request, reply: received.append((request['task_id'], reply)), now=lambda: engine.clock)
        self.assertEqual(len(received), 108)
        self.assertEqual(len(set(k for k, _ in received)), 108)
        self.assertTrue(all(r.text == 'RAW_UNPARSEABLE_OUTPUT' and r.finish_reason == 'length' for _, r in received))
        self.assertEqual(max(e[3] for e in engine.events), 16)
        self.assertEqual([r['messages'][0]['content'] for r in requests.values()], original)
        order = [(e, key) for e, key, _, _ in engine.events]
        for rid in ids:
            seed = order.index(('complete', rid + ':v10'))
            self.assertTrue(all(seed < order.index(('submit', rid + ':' + f)) for f in features[1:]))
        first_new = order.index(('submit', '2:v10'))
        self.assertLess(first_new, order.index(('complete', '1:v18')))
        self.assertTrue(all(len(e['live_ids']) <= 3 for e in events))
    def test_source_budget_does_not_drop_records(self):
        ids, features, requests = self.inputs()
        engine = FakeStream()
        received = []
        events = schedule(engine, requests, ids, features, {rid: 30000 for rid in ids},
                          lambda request, reply: received.append(request['task_id']))
        self.assertEqual(len(received), 108)
        self.assertTrue(all(len(e['live_ids']) == 1 for e in events if e['event'] == 'admit'))
    def test_runtime_failure_retains_pending_mapping_before_abort(self):
        ids, features, requests = self.inputs()
        engine = FakeStream(fail=True)
        events = []
        with self.assertRaisesRegex(RuntimeError, 'synthetic'):
            schedule(engine, requests, ids, features, {rid: 100 for rid in ids}, lambda *args: None, events=events)
        self.assertTrue(engine.aborted)
        self.assertEqual(events[-1]['event'], 'execution_aborted')
        self.assertEqual(len(events[-1]['engine_pending']), 2)
        self.assertEqual(len(events[-1]['flights']), 2)
    def test_source_and_card_bytes_survive_integration(self):
        card = ' [항목 번호]\nv10\n\n그대로\t남긴다.\n'
        doc = '원문\r\n\t 금액: 123  원'
        record = {'id': 'R', 'meta': {'가격': 123}, 'input_completeness': {'missing': True},
                  'dropped_doc_counts': {'제안요청서': 1}, 'docs': [{'type': '공고문', 'doc_id': 'D0', 'text': doc}]}
        content = card_messages(common_input(record), '법령 원문', card)[0]['content']
        self.assertTrue(content.endswith(card))
        self.assertIn(doc, content)
        self.assertIn('"제안요청서":1', content)
        self.assertEqual(content.count('[판정카드]'), 1)
    def test_code_provenance_rejects_longer_number_substrings(self):
        record = {'meta': {'세부품명번호목록': ['1234567890']}, 'docs': [
            {'doc_id': 'D0', 'text': '01234567890 / 1234567890 / 12345678901'}]}
        found = code_positions(record, '1234567890')
        self.assertEqual(len(found), 2)
        self.assertEqual(found[0]['char_start'], 14)
        self.assertEqual(found[1]['field'], 'meta.세부품명번호목록')


if __name__ == '__main__':
    unittest.main()
