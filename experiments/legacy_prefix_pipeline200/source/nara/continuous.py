"""Completion-driven scheduling with the existing prompt, RAG and validation rules."""
from collections import deque
from dataclasses import asdict
import json
import time

from jsonschema import Draft202012Validator, ValidationError
from nara.inference import _Task, Turn, Reply, Prediction, compact
from nara.prefix_predictor import SourceFirstPredictor


class StreamingModel:
    """Incremental local engine access; one immutable mode/budget per submitted turn."""
    def __init__(self, model):
        self.base=model;self.pending={};self.serial=0;self.rows=[];self.lifecycle=[]
    def __getattr__(self,name):return getattr(self.base,name)
    @property
    def thinking(self):return self.base.thinking
    @thinking.setter
    def thinking(self,value):self.base.thinking=value

    def submit(self,turn):
        from vllm import SamplingParams
        from vllm.sampling_params import StructuredOutputsParams,RequestOutputKind
        search=turn.schema.get('properties',{}).get('action',{}).get('const')=='search'
        budget=(min(256,turn.max_tokens//4) if search else min(1024,turn.max_tokens//2)) if self.thinking else None
        params=SamplingParams(temperature=0,max_tokens=turn.max_tokens,seed=0,
            skip_special_tokens=False,thinking_token_budget=budget,
            output_kind=RequestOutputKind.FINAL_ONLY,
            structured_outputs=StructuredOutputsParams(json=turn.schema,disable_any_whitespace=True))
        tokens=self.base._tokens(turn.messages)
        rid=f'continuous-{self.serial}';self.serial+=1
        self.base.llm.llm_engine.add_request(rid,{'prompt_token_ids':tokens},params)
        self.pending[rid]=(turn,budget)
        self.lifecycle.append({'event':'submit','request_id':rid,'task_id':turn.task_id,
                               'time':time.monotonic(),'inflight':len(self.pending),'input_tokens':len(tokens),'thinking_budget':budget})

    def poll(self):
        from vllm.reasoning.gemma4_utils import parse_thinking_output
        completed=[]
        for out in self.base.llm.llm_engine.step():
            if not out.finished:continue
            turn,budget=self.pending.pop(out.request_id)
            completion=out.outputs[0];text=self.base.tokenizer.decode(completion.token_ids,skip_special_tokens=False)
            parsed=parse_thinking_output(text)
            reply=Reply(parsed['answer'],completion.finish_reason,len(out.prompt_token_ids),len(completion.token_ids),
                        thinking_tokens=self.base.count_text(parsed['thinking'] or ''),thinking_budget=budget)
            s=out.metrics
            if s is None or not 0<s.scheduled_ts<=s.first_token_ts<=s.last_token_ts:
                raise ValueError('Missing/nonmonotonic request metrics')
            self.rows.append({'request_id':out.request_id,'task_id':turn.task_id,'input_tokens':len(out.prompt_token_ids),
                'output_tokens':len(completion.token_ids),'cached_tokens':out.num_cached_tokens,'thinking_budget':budget,
                'finish_reason':completion.finish_reason,'request_stats':asdict(s),
                'prefill_seconds':s.first_token_ts-s.scheduled_ts,'decode_seconds':s.last_token_ts-s.first_token_ts,
                'queue_seconds':s.scheduled_ts-s.queued_ts})
            self.lifecycle.append({'event':'complete','request_id':out.request_id,'task_id':turn.task_id,
                                   'time':time.monotonic(),'inflight':len(self.pending)})
            completed.append((turn.task_id,reply))
        return completed

    def abort(self):
        if self.pending:self.base.llm.llm_engine.abort_request(list(self.pending))
        self.pending.clear()


class ContinuousPredictor(SourceFirstPredictor):
    """Refill each completed slot; cache_seed delays only a notice's own followers."""
    def _turn(self,task):
        tokens=self.model.count_messages(task.messages)
        if tokens+self.limits.output_tokens+128>self.model.max_model_len:
            task.error='Source/conversation exceeds context; no text was truncated'
            task.trace.append({'event':'context_failure','input_tokens':tokens});return None
        search=(not task.force_final and task.rounds<self.limits.search_rounds
                and task.retrieval_tokens<self.limits.total_retrieval_tokens
                and tokens+2*self.limits.output_tokens+256<=self.model.max_model_len)
        required=self.limits.require_search and task.rounds==0
        output=self.limits.output_tokens
        if required:
            output=min(output,self.model.max_model_len-tokens-self.limits.output_tokens-256)
            if output<32:
                task.error='Required search cannot fit context; no text was truncated'
                task.trace.append({'event':'context_failure','input_tokens':tokens});return None
            search=True
        return Turn(task.task_id,task.messages,self._schema(task.items,search,required),output)

    def _accept(self,task,turn,reply):
        task.trace.append({'event':'model','input_tokens':reply.input_tokens,'output_tokens':reply.output_tokens,
            'finish_reason':reply.finish_reason,'response':reply.text,'error':reply.error,'max_output_tokens':turn.max_tokens,
            'thinking_tokens':reply.thinking_tokens,'thinking_budget':reply.thinking_budget,
            'required_search':self.limits.require_search and task.rounds==0})
        try:
            if reply.error or reply.finish_reason!='stop':raise ValueError(reply.error or f'Generation ended: {reply.finish_reason}')
            action=json.loads(reply.text);Draft202012Validator(turn.schema).validate(action)
            if action['action']=='search':
                if any(not q.strip() for q in action['queries']):raise ValueError('Empty search query')
                task.rounds+=1;task.messages.append({'role':'assistant','content':compact(action)})
                self._retrieve({task.task_id:task},{task.task_id:{f'{task.task_id}:{task.rounds}:{i}':q for i,q in enumerate(action['queries'])}})
            else:self._finish(task,action['judgments'])
        except (ValueError,TypeError,KeyError,ValidationError) as exc:
            self._retry(task,exc.message if isinstance(exc,ValidationError) else str(exc))

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
            per=[_Task(f'{ri}:{gi}',record,g,self._messages(record,g)) for gi,g in enumerate(groups)]
            tasks.extend(per);owned[record['id']]=per
            for t,on in zip(per,modes):mode[t.task_id]=on
            if cache_seed:
                ready.append(per[0]);followers[per[0].task_id]=per[1:]
            else:ready.extend(per)
        def result(record):
            per=owned[record['id']];errors=[f'{t.task_id}: {t.error}' for t in per if t.error]
            return Prediction(record['id'],None if errors else {k:v for t in per for k,v in t.judgments.items()},
                '; '.join(errors) or None,[{'task_id':t.task_id,'items':t.items,'search_rounds':t.rounds,
                'retrieval_tokens':t.retrieval_tokens,'events':t.trace} for t in per])
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
                    task=ready.popleft();self.model.thinking=mode[task.task_id];turn=self._turn(task)
                    if turn is None:advance(task);continue
                    self.model.submit(turn);flights[task.task_id]=(task,turn)
                    self.metrics['model_batches']+=1
                if flights:
                    start=time.monotonic();replies=self.model.poll();self.metrics['model_seconds']+=time.monotonic()-start
                    for tid,reply in replies:
                        task,turn=flights.pop(tid);self.model.thinking=mode[tid]
                        self._accept(task,turn,reply);advance(task)
        except BaseException:
            self.model.abort();raise
        self.metrics['total_seconds']=time.monotonic()-tick
        assert len(completed_records)==len(records)
        return [result(r) for r in records]
