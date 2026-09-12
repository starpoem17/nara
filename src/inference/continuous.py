"""Completion-driven scheduling with the existing prompt, RAG and validation rules."""
from collections import deque
import time

from jsonschema import ValidationError
from nara.inference.predictor import Prediction
from nara.inference.prefix_predictor import SourceFirstPredictor
from nara.inference.engine import StreamingModel  # Compatibility for existing experiments.


class ContinuousPredictor(SourceFirstPredictor):
    """Refill each completed slot; cache_seed delays only a notice's own followers."""
    def _turn(self, task):
        """Compatibility for historical token/request diagnostics."""
        return self._legacy_conversation(task).next_turn()

    def _consume(self, conversation, turn, reply):
        queries = conversation.accept_reply(turn, reply)
        if queries:
            try:
                self._search({conversation.task_id: conversation}, {conversation.task_id: queries})
            except (ValueError, TypeError, KeyError, ValidationError) as exc:
                # Historical streaming execution retries invalid retrieval material;
                # offline execution propagates failures while packing that material.
                conversation.reject(exc.message if isinstance(exc, ValidationError) else str(exc))

    def predict(self,records,*,item_groups=None,thinking_groups=None,cache_seed=False,on_record=None):
        records=list(records);groups=[tuple(g) for g in (item_groups or [list(self.items)])]
        flat=[k for g in groups for k in g]
        if len({r['id'] for r in records})!=len(records):raise ValueError('Duplicate record IDs')
        if not groups or not all(groups) or len(flat)!=len(set(flat)) or set(flat)!=set(self.items):
            raise ValueError('Item groups must partition the item table exactly once')
        modes=[self.model.thinking]*len(groups) if thinking_groups is None else list(thinking_groups)
        if len(modes)!=len(groups):raise ValueError('One mode per group required')
        self.metrics={'model_seconds':0.,'retrieval_seconds':0.,'model_batches':0,'retrieval_batches':0}
        tasks=[];owned={};mode={};followers={};ready=deque();completed_records=set();flights={}
        tick=time.monotonic()
        for ri,record in enumerate(records):
            per=[self.conversation(f'{ri}:{gi}',record,g) for gi,g in enumerate(groups)]
            tasks.extend(per);owned[record['id']]=per
            for t,on in zip(per,modes):mode[t.task_id]=on
            if cache_seed:
                ready.append(per[0]);followers[per[0].task_id]=per[1:]
            else:ready.extend(per)
        def result(record):
            per=owned[record['id']];errors=[f'{t.task_id}: {t.error}' for t in per if t.error]
            return Prediction(record['id'],None if errors else {k:v for t in per for k,v in t.judgments.items()},
                '; '.join(errors) or None,[t.snapshot() for t in per])
        def advance(task):
            if not task.done:ready.appendleft(task);return
            ready.extendleft(reversed(followers.pop(task.task_id,[])))
            rid=task.record['id']
            if rid not in completed_records and all(t.done for t in owned[rid]):
                completed_records.add(rid)
                if on_record:on_record(result(task.record))
        try:
            while ready or flights:
                while ready and len(flights)<self.limits.batch_size:
                    task=ready.popleft();self.model.thinking=mode[task.task_id];turn=task.next_turn()
                    if turn is None:advance(task);continue
                    self.model.submit(turn);flights[task.task_id]=(task,turn)
                    self.metrics['model_batches']+=1
                if flights:
                    start=time.monotonic();replies=self.model.poll();self.metrics['model_seconds']+=time.monotonic()-start
                    for tid,reply in replies:
                        task,turn=flights.pop(tid);self.model.thinking=mode[tid]
                        self._consume(task,turn,reply);advance(task)
        except BaseException:
            self.model.abort();raise
        self.metrics['total_seconds']=time.monotonic()-tick
        assert len(completed_records)==len(records)
        return [result(r) for r in records]
