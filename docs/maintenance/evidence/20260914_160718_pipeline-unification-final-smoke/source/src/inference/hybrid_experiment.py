"""Five groups and request timing for the bounded mixed-mode experiment."""
from dataclasses import asdict
import time
from nara.inference.predictor import Prediction
from nara.inference.prefix_predictor import split_predictor

THINK=['v1','v5','v9','v14','v22','v24']
INSTANT=[['v4','v6','v7','v8'],['v10','v11','v12','v13'],
         ['v15','v16','v17','v18'],['v19','v20','v21','v23']]
GROUPS=INSTANT+[THINK]


class TimedLLM:
    def __init__(self,llm):
        self.wrapped=llm
        self.rows=[];self.batches=[]
        self.record_id=None;self.phase='warmup';self.thinking_budget=None
    def __getattr__(self,name):return getattr(self.wrapped,name)
    def set_phase(self,record_id,phase):self.record_id,self.phase=record_id,phase
    def generate(self,*args,**kwargs):
        params=kwargs.get('sampling_params')
        if self.thinking_budget is not None and isinstance(params,list):
            for p in params:
                if p.thinking_token_budget is not None:p.thinking_token_budget=min(p.thinking_token_budget,self.thinking_budget)
        tick=time.monotonic()
        outputs=self.wrapped.generate(*args,**kwargs)
        elapsed=time.monotonic()-tick
        self.batches.append({'record_id':self.record_id,'phase':self.phase,'seconds':elapsed,'requests':len(outputs)})
        for output in outputs:
            s=output.metrics
            if s is None or not 0<s.scheduled_ts<=s.first_token_ts<=s.last_token_ts:
                raise ValueError('Missing/nonmonotonic vLLM request statistics')
            self.rows.append({'record_id':self.record_id,'phase':self.phase,'batch':len(self.batches)-1,
                 'request_id':output.request_id,'input_tokens':len(output.prompt_token_ids),
                 'cached_tokens':output.num_cached_tokens,'cache_creation_tokens':output.num_cache_creation_tokens,
                 'output_tokens':len(output.outputs[0].token_ids),'finish_reason':output.outputs[0].finish_reason,
                 'request_stats':asdict(s),'queue_seconds':s.scheduled_ts-s.queued_ts,
                 'prefill_seconds':s.first_token_ts-s.scheduled_ts,
                 'decode_seconds':s.last_token_ts-s.first_token_ts})
        return outputs


def run_phase(predictor,record,groups,thinking,phase,observer):
    predictor.model.thinking=thinking
    observer.set_phase(record['id'],phase)
    worker=split_predictor(predictor,groups)
    tick=time.monotonic()
    result=worker.predict([record],item_groups=groups)[0]
    metrics={'phase':phase,'thinking':thinking,'seconds':time.monotonic()-tick,**worker.metrics}
    for task in result.trace:task['task_id']=record['id']+':'+phase+':'+task['task_id']
    return result,metrics


def merge(record_id,predictions):
    errors=[p.error for p in predictions if p.error]
    judgments=None if errors else {k:v for p in predictions for k,v in p.judgments.items()}
    return Prediction(record_id,judgments,'; '.join(errors) or None,[t for p in predictions for t in p.trace])


def predict_hybrid(predictor,record,observer):
    specs=[('instant_first',INSTANT[:1],False),('instant_cached',INSTANT[1:],False),('thinking', [THINK],True)]
    results=[];metrics=[]
    for name,groups,thinking in specs:
        result,metric=run_phase(predictor,record,groups,thinking,name,observer)
        results.append(result);metrics.append(metric)
    return merge(record['id'],results),metrics
