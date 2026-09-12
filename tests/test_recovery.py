"""Recovery outcomes through the same interface as the default experiment."""
from copy import deepcopy
from dataclasses import asdict
import json
import unittest
from jsonschema import ValidationError

from nara.inference.predictor import Limits, Predictor
from nara.inference.recovery import Attempt, recover_notices
from test_inference import Model, Retriever, TABLE, SCHEMA, record, final


def judgment(label=0):
    return {'위반여부': label, '근거문구': None}


def task(items, marker, *, success=False):
    events = [{'event': 'model', 'marker': marker}]
    if success:
        events.append({'event': 'final'})
    return {'items': items, 'search_rounds': 1, 'retrieval_tokens': 7, 'events': events}


def prediction(rid, marker, *, failed=True, reverse=False):
    tasks = [task(['v1'], marker + '-1', success=not failed),
             task(['v4'], marker + '-4', success=True)]
    return {'record_id': rid, 'error': 'failed v1' if failed else None,
            'judgments': None if failed else {'v1': judgment(), 'v4': judgment(1)},
            'trace': list(reversed(tasks)) if reverse else tasks}


def attempt(trace, name, seconds):
    return Attempt(trace, seconds, [{'request_id': name}], [{'event': name}], [{'step': name}])


class RecoveryTests(unittest.TestCase):
    def forbidden(self, *args):
        self.fail('Unexpected recovery work')

    def test_successful_run_is_unchanged_without_recovery_calls(self):
        initial = attempt([prediction('A', 'main', failed=False)], 'main', 11.)
        saved = deepcopy(initial)
        result = recover_notices([record('A')], initial, rerun_notices=self.forbidden,
            retry_group=self.forbidden, replay_group=self.forbidden, rule_judgments=self.forbidden)
        self.assertEqual(result.trace, initial.trace)
        self.assertEqual(initial, saved)
        self.assertEqual(result.prediction_seconds, 11.)
        self.assertEqual(result.recovery_seconds, 0.)
        self.assertEqual(result.requests, initial.requests)

    def test_same_policy_rerun_preserves_success_and_merges_by_group(self):
        initial = attempt([prediction('A', 'main'), prediction('B', 'main', failed=False)], 'main', 11.)
        rerun = attempt([prediction('A', 'rerun', failed=False, reverse=True)], 'rerun', 3.)
        saved = deepcopy((initial, rerun))
        def run(selected):
            self.assertEqual([r['id'] for r in selected], ['A'])
            return rerun
        result = recover_notices([record('A'), record('B')], initial, rerun_notices=run,
            retry_group=self.forbidden, replay_group=self.forbidden, rule_judgments=self.forbidden)
        self.assertEqual((initial, rerun), saved)
        self.assertEqual(result.trace[1], initial.trace[1])
        self.assertEqual(result.trace[0]['judgments'], rerun.trace[0]['judgments'])
        for i in range(2):
            task = result.trace[0]['trace'][i]
            self.assertEqual(task['items'], initial.trace[0]['trace'][i]['items'])
            self.assertEqual(task['events'][0]['marker'], f'main-{1 if i == 0 else 4}')
            self.assertTrue(any(e.get('marker') == f'rerun-{1 if i == 0 else 4}' for e in task['events']))
            self.assertEqual(task['search_rounds'], 2)
            self.assertEqual(task['retrieval_tokens'], 14)
        self.assertEqual(result.prediction_seconds, 14.)
        self.assertEqual(result.recovery_seconds, 3.)
        self.assertEqual(result.scheduler, [{'step': 'main'}, {'step': 'rerun', 'stage': 'recovery'}])

    def test_isolated_recovery_retains_attempts_costs_rules_and_explicit_failure(self):
        for failed in (False, True):
            with self.subTest(failed=failed):
                initial = attempt([prediction('A', 'main')], 'main', 11.)
                rerun = attempt([prediction('A', 'rerun')], 'rerun', 3.)
                isolated = attempt([{'record_id': 'A', 'error': 'still invalid' if failed else None,
                    'judgments': None if failed else {'v1': judgment(1)},
                    'trace': [task(('v1',), 'isolated', success=not failed)]}], 'isolated', 4.)
                saved = deepcopy((initial, rerun, isolated))
                calls = []
                def retry(rec, items):
                    calls.append(('retry', rec['id'], items))
                    return isolated
                def replay(rec, saved_task):
                    calls.append(('replay', rec['id'], saved_task['items']))
                    return {'v4': judgment(1)}
                def rules(rec):
                    calls.append(('rules', rec['id']))
                    return {'v2': judgment()}
                ticks = iter([100., 107.])  # Includes replay and rules, not just 4s generation.
                result = recover_notices([record('A')], initial, rerun_notices=lambda _: rerun,
                    retry_group=retry, replay_group=replay, rule_judgments=rules, clock=lambda: next(ticks))
                self.assertEqual((initial, rerun, isolated), saved)
                self.assertEqual(result.prediction_seconds, 21.)
                self.assertEqual(result.recovery_seconds, 10.)
                self.assertEqual([r['request_id'] for r in result.requests], ['main', 'rerun', 'isolated'])
                self.assertEqual([r['event'] for r in result.lifecycle], ['main', 'rerun', 'isolated'])
                self.assertEqual([r['step'] for r in result.scheduler], ['main', 'rerun', 'isolated'])
                self.assertEqual(calls[:2], [('retry', 'A', ['v1']), ('replay', 'A', ['v4'])])
                self.assertEqual(len(calls), 2 if failed else 3)
                output = result.trace[0]
                self.assertEqual(output['error'], 'still invalid' if failed else None)
                self.assertEqual(output['judgments'], None if failed else
                                 {'v1': judgment(1), 'v4': judgment(1), 'v2': judgment()})
                self.assertEqual(output['trace'][0]['search_rounds'], 3)
                self.assertEqual(output['trace'][0]['retrieval_tokens'], 21)
                self.assertEqual(output['trace'][1]['search_rounds'], 2)

    def test_wrong_record_or_group_is_rejected_before_isolated_generation(self):
        initial = attempt([prediction('A', 'main')], 'main', 1.)
        invalid = [prediction('B', 'retry'), prediction('A', 'retry')]
        invalid[1]['trace'][0]['items'] = ['v5']
        for row in invalid:
            with self.subTest(row=row), self.assertRaises(ValueError):
                recover_notices([record('A')], initial,
                    rerun_notices=lambda _: attempt([row], 'retry', 1.),
                    retry_group=self.forbidden, replay_group=self.forbidden, rule_judgments=self.forbidden)

    def test_replay_uses_real_judgment_validation_without_model_calls(self):
        model = Model(lambda turn: final(turn, 'not in the original document'))
        predictor = Predictor(model, Retriever(), TABLE, SCHEMA, limits=Limits(search_rounds=0))
        rec = record('A')
        output = predictor.predict([rec])[0]
        trace = json.loads(json.dumps(asdict(output)))['trace'][0]
        saved = deepcopy(trace)
        calls = len(model.calls)
        restored = predictor.replay_judgments(rec, trace)
        self.assertEqual(restored, output.judgments)
        self.assertEqual(trace, saved)
        self.assertEqual(len(model.calls), calls)
        self.assertIsNone(restored['v1']['근거문구'])
        for change in ('final', 'finish_reason', 'schema', 'required_search'):
            bad = deepcopy(trace)
            if change == 'final':
                bad['events'][-1]['evidence_dropped'] = []
            elif change == 'finish_reason':
                next(e for e in bad['events'] if e['event'] == 'model')['finish_reason'] = 'length'
            elif change == 'schema':
                event = next(e for e in bad['events'] if e['event'] == 'model')
                action = json.loads(event['response']); del action['judgments']['v1']
                event['response'] = json.dumps(action)
            else:
                predictor.limits = Limits(require_search=True)
            with self.subTest(change=change), self.assertRaises(ValidationError if change == 'schema' else ValueError):
                predictor.replay_judgments(rec, bad)

    def test_saved_successful_groups_are_replayed_and_only_failed_group_generated(self):
        model = Model(lambda turn: final(turn, '공고 원문 근거'))
        predictor = Predictor(model, Retriever(), TABLE, SCHEMA, limits=Limits(search_rounds=0))
        rec = record('A')
        successful = asdict(predictor.predict([rec], item_groups=[['v1'], ['v2', 'v3', 'v4']])[0])
        damaged = deepcopy(successful)
        damaged['error'] = 'first group failed'; damaged['judgments'] = None
        damaged['trace'][0]['events'] = [{'event': 'invalid_response'}]
        isolated_calls = []
        def retry(record, items):
            isolated_calls.append(items)
            return Attempt([{'record_id': 'A', 'error': None, 'judgments': {'v1': successful['judgments']['v1']},
                             'trace': [successful['trace'][0]]}], .1)
        result = recover_notices([rec], Attempt([damaged], 1.),
            rerun_notices=lambda records: Attempt([damaged], 1.), retry_group=retry,
            replay_group=predictor.replay_judgments, rule_judgments=lambda _: {})
        self.assertEqual(isolated_calls, [['v1']])
        self.assertEqual(result.trace[0]['judgments'], successful['judgments'])
        self.assertIsNone(result.trace[0]['error'])
        from nara.experiments.recover_hybrid200 import replay
        self.assertEqual(replay(rec, successful['trace'][1], predictor),
                         predictor.replay_judgments(rec, successful['trace'][1]))


if __name__ == '__main__':
    unittest.main()
