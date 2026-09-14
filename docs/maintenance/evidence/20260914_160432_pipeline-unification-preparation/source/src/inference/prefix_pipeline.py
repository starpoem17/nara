"""Bounded cross-notice scheduling with early admission of the next source prefix."""
from collections import deque
import time

from nara.inference.continuous import ContinuousPredictor
from nara.inference.predictor import Prediction


class PrefixPipelinePredictor(ContinuousPredictor):
    """Keep ready followers supplied while prefetching a bounded next notice."""
    def predict(self, records, *, item_groups, source_tokens, initial_records=2,
                max_live_records=3, max_live_source_tokens=48000,
                lookahead_groups=16, on_record=None):
        records = list(records)
        groups = [tuple(g) for g in item_groups]
        flat = [k for g in groups for k in g]
        if len({r['id'] for r in records}) != len(records):
            raise ValueError('Duplicate record IDs')
        if not groups or not all(groups) or len(flat) != len(set(flat)) or set(flat) != set(self.items):
            raise ValueError('Groups must partition predictor items')
        if not 1 <= initial_records <= max_live_records or max_live_source_tokens <= 0:
            raise ValueError('Invalid admission limits')
        if any(source_tokens[r['id']] <= 0 for r in records):
            raise ValueError('Positive source token counts required')
        self.metrics = {'model_seconds': 0., 'retrieval_seconds': 0.,
                        'model_batches': 0, 'retrieval_batches': 0}
        self.admission = []
        ready = deque(); flights = {}; live = {}; owned = {}; results = {}
        next_index = 0; start = time.monotonic(); last_block = None

        def result(rid):
            tasks = owned[rid]
            errors = [f'{t.task_id}: {t.error}' for t in tasks if t.error]
            return Prediction(rid, None if errors else {k: v for t in tasks for k, v in t.judgments.items()},
                '; '.join(errors) or None,
                [t.snapshot() for t in tasks])

        def finish(task):
            if not task.done:
                ready.appendleft(task)
                return
            rid = task.record['id']
            if task is owned[rid][0]:
                # Even a failed seed has processed the source; preserve the full
                # historical task set, and leave the notice failed for recovery.
                ready.extend(owned[rid][1:])
            if all(t.done for t in owned[rid]):
                results[rid] = result(rid)
                del live[rid]
                self.admission.append({'event': 'record_complete', 'record_id': rid,
                                       'time': time.monotonic(), 'live_ids': list(live)})
                if on_record:
                    on_record(results[rid])

        def admit(reason):
            nonlocal next_index, last_block
            if next_index >= len(records):
                return False
            record = records[next_index]; rid = record['id']
            total = sum(source_tokens[k] for k in live) + source_tokens[rid]
            blocked = ('record_window' if len(live) >= max_live_records else
                       'source_token_budget' if live and total > max_live_source_tokens else None)
            if blocked:
                key = (rid, blocked, tuple(live))
                if key != last_block:
                    self.admission.append({'event': 'admission_blocked', 'record_id': rid,
                        'reason': blocked, 'time': time.monotonic(), 'live_ids': list(live),
                        'prospective_source_tokens': total})
                    last_block = key
                return False
            tasks = [self.conversation(f'{rid}:{gi}', record, g)
                     for gi, g in enumerate(groups)]
            self.admission.append({'event': 'admit', 'record_id': rid, 'reason': reason,
                'time': time.monotonic(), 'older_live_ids': list(live),
                'live_source_tokens': total, 'ready_tasks': len(ready), 'inflight': len(flights)})
            owned[rid] = tasks; live[rid] = tasks; next_index += 1
            ready.appendleft(tasks[0]); last_block = None
            return True

        def next_task():
            # A not-yet-submitted seed takes priority; retries retain task identity.
            for task in ready:
                if task is owned[task.record['id']][0]:
                    ready.remove(task)
                    return task
            return ready.popleft()

        for _ in range(min(initial_records, len(records))):
            if not admit('startup'):
                break
        # Preserve input order for the initial seed batch.
        ready = deque(reversed(ready))
        try:
            while ready or flights or next_index < len(records):
                while len(flights) < self.limits.batch_size:
                    outstanding = sum(not t.done for per in live.values() for t in per[1:])
                    seed_pending = any(not per[0].done for per in live.values())
                    if not live:
                        admit('empty_pipeline')
                    elif not seed_pending and outstanding <= lookahead_groups:
                        admit('lookahead')
                    if not ready:
                        break
                    task = next_task(); self.model.thinking = False
                    turn = task.next_turn()
                    if turn is None:
                        finish(task)
                        continue
                    self.model.submit(turn)
                    flights[task.task_id] = (task, turn)
                    self.metrics['model_batches'] += 1
                if flights:
                    tick = time.monotonic()
                    replies = self.model.poll()
                    self.metrics['model_seconds'] += time.monotonic() - tick
                    for tid, reply in replies:
                        task, turn = flights.pop(tid)
                        self.model.thinking = False
                        self._consume(task, turn, reply)
                        finish(task)
                elif ready:
                    continue
                elif next_index < len(records) and live:
                    raise RuntimeError('No runnable task in live notice window')
        except BaseException:
            self.model.abort()
            raise
        self.metrics['total_seconds'] = time.monotonic() - start
        assert len(results) == len(records)
        return [results[r['id']] for r in records]
