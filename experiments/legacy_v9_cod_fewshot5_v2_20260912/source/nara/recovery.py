"""Failed-notice recovery with preserved attempt evidence and complete accounting."""
from copy import deepcopy
from dataclasses import dataclass, field
import time


@dataclass
class Attempt:
    """One execution's predictions and measured cost; excludes earlier attempts."""
    trace: list
    seconds: float
    requests: list = field(default_factory=list)
    lifecycle: list = field(default_factory=list)
    scheduler: list = field(default_factory=list)


@dataclass
class RecoveryResult:
    trace: list
    attempts: list[Attempt]
    recovery_seconds: float = 0.

    @property
    def prediction_seconds(self):
        return self.attempts[0].seconds + self.recovery_seconds

    @property
    def requests(self):
        return [row for attempt in self.attempts for row in attempt.requests]

    @property
    def lifecycle(self):
        return [row for attempt in self.attempts for row in attempt.lifecycle]

    @property
    def scheduler(self):
        return [dict(row, stage='recovery') if index else row
                for index, attempt in enumerate(self.attempts) for row in attempt.scheduler]


def _by_id(trace, expected):
    indexed = {row['record_id']: row for row in trace}
    if len(indexed) != len(trace) or set(indexed) != set(expected):
        raise ValueError('Recovery predictions must match requested record IDs exactly')
    for row in trace:
        if not row['error'] and row['judgments'] is None:
            raise ValueError('Successful recovery requires judgments')
    return indexed


def _groups(prediction):
    result = {}
    items = set()
    for task in prediction['trace']:
        group = tuple(task['items'])
        if not group or len(set(group)) != len(group) or items.intersection(group):
            raise ValueError('Recovery trace groups must be nonempty and disjoint')
        items.update(group)
        result[group] = task
    if not result:
        raise ValueError('Recovery prediction must retain its group trace')
    return result


def _merge_tasks(original, replacement):
    old, new = _groups(original), _groups(replacement)
    if set(old) != set(new):
        raise ValueError('Recovery must preserve the original item groups')
    for group, task in old.items():
        later = new[group]
        task['events'].extend(deepcopy(later['events']))
        task['search_rounds'] += later['search_rounds']
        task['retrieval_tokens'] += later['retrieval_tokens']


def recover_notices(records, initial, *, rerun_notices, retry_group, replay_group,
                    rule_judgments, clock=time.monotonic):
    """One same-policy rerun, then one isolated attempt per still-failed group.

    Execution adapters return Attempt with only their own evidence. replay_group
    revalidates a successful task through the judgment interface, without inference.
    Inputs and attempt traces remain unchanged; the returned trace retains every
    attempt's events. Successful initial notices are never rerun or replaced.

    Time includes the initial and whole-notice execution durations, plus the full
    isolated-recovery interval (replay, generation, merge and rule application).
    Isolated Attempt.seconds are diagnostic, not added again to that interval.
    """
    records = list(records)
    by_record = {record['id']: record for record in records}
    if len(by_record) != len(records):
        raise ValueError('Duplicate recovery record IDs')
    _by_id(initial.trace, by_record)
    result = RecoveryResult(deepcopy(initial.trace), [initial])
    failed = {row['record_id'] for row in initial.trace if row['error']}
    if not failed:
        return result

    rerun = rerun_notices([r for r in records if r['id'] in failed])
    by_retry = _by_id(rerun.trace, failed)
    # Check partition identity before isolated execution or result replacement.
    for row in result.trace:
        if row['record_id'] in failed and set(_groups(row)) != set(_groups(by_retry[row['record_id']])):
            raise ValueError('Recovery must preserve the original item groups')
    result.attempts.append(rerun)
    result.recovery_seconds = rerun.seconds
    repaired = deepcopy(by_retry)
    for row in repaired.values():
        if not row['error']:
            continue
        start = clock()
        record = by_record[row['record_id']]
        judgments, errors = {}, []
        for group, task in _groups(row).items():
            if any(event['event'] == 'final' for event in task['events']):
                restored = replay_group(record, task)
                if set(restored) != set(group):
                    raise ValueError('Replayed judgments must match their item group')
                judgments.update(restored)
                continue
            attempt = retry_group(record, list(group))
            replacement = _by_id(attempt.trace, [record['id']])[record['id']]
            if set(_groups(replacement)) != {group}:
                raise ValueError('Isolated recovery must return only its requested group')
            result.attempts.append(attempt)
            _merge_tasks({'trace': [task]}, replacement)
            if replacement['error']:
                errors.append(replacement['error'])
            else:
                if set(replacement['judgments']) != set(group):
                    raise ValueError('Isolated judgments must match their item group')
                judgments.update(deepcopy(replacement['judgments']))
        row['error'] = '; '.join(errors) or None
        row['judgments'] = None if errors else {**judgments, **rule_judgments(record)}
        result.recovery_seconds += clock() - start

    for row in result.trace:
        if row['record_id'] not in repaired:
            continue
        replacement = repaired[row['record_id']]
        _merge_tasks(row, replacement)
        row['error'] = replacement['error']
        row['judgments'] = deepcopy(replacement['judgments'])
    return result
