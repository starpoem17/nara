"""Measure completion-driven scheduling and per-step token budgets on frozen prompts."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from script import read_records,write_submission
from scripts.benchmark_compact200 import configuration,MODEL
from scripts.benchmark_hybrid200 import safe
from nara.inference import Limits,Turn
from nara.vllm_model import VLLMModel
from nara.prefix_predictor import SourceFirstPredictor,split_predictor
from nara.hybrid_experiment import THINK,GROUPS,TimedLLM
from nara.continuous import StreamingModel,ContinuousPredictor
from nara.hypothesis6 import judge
from scripts.evaluate_dev import evaluate

ROOT=Path('analysis/continuous200')
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def jsonl(p,x):p.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in x))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tokens',type=int,default=8192)
    parser.add_argument('--kind',choices=['pilot','six','mixed','smoke'],default='pilot')
    args=parser.parse_args();records=read_records('data/dev.jsonl')
    plan=json.loads((ROOT/'plan.json').read_text())
    if args.kind in ['pilot','smoke']:
        ids=set(plan['pilot_ids'] if args.kind=='pilot' else plan['pilot_ids'][:8]);records=[r for r in records if r['id'] in ids]
    table=json.loads(Path('data/항목표.json').read_text())['항목']
    schema=json.loads(Path('data/정답스키마_디코딩.json').read_text())['properties']['판정']
    table,schema,_=configuration(table,schema,'groups12',True)
    from nara.retrieval import BGEEncoder,LegalRetriever
    import vllm
    tick=time.monotonic();retriever=LegalRetriever('model/legal_index',BGEEncoder('models/bge-m3',device='cuda'))
    # Reuse the exact frozen adapter initialization, injecting only measured engine settings.
    stock=vllm.LLM
    def configured(**kw):return stock(disable_log_stats=False,max_num_batched_tokens=args.tokens,enable_chunked_prefill=True,**kw)
    vllm.LLM=configured
    try:base=VLLMModel(MODEL,thinking=True,max_num_seqs=8)
    finally:vllm.LLM=stock
    load=time.monotonic()-tick
    config=base.llm.llm_engine.vllm_config
    engine={'load_seconds':load,'max_num_batched_tokens':config.scheduler_config.max_num_batched_tokens,
            'max_num_seqs':config.scheduler_config.max_num_seqs,'enable_chunked_prefill':config.scheduler_config.enable_chunked_prefill,
            'gpu_memory_utilization':config.cache_config.gpu_memory_utilization,
            'scheduler_reserve_full_isl':getattr(base.llm.llm_engine,'scheduler_reserve_full_isl',None)}
    simple={'type':'object','properties':{'answer':{'type':'integer'}},'required':['answer'],'additionalProperties':False}
    warm=[Turn(str(i),[{'role':'user','content':'2+3을 계산하고 {"answer":5}로 답하라.'}],simple,512) for i in range(8)]
    base.generate(warm)
    scheduler=[];original_get=base.llm.llm_engine.engine_core.get_output
    def observed_get():
        out=original_get();s=out.scheduler_stats
        if s is not None:
            scheduler.append({'time':time.monotonic(),'running':s.num_running_reqs,'waiting':s.num_waiting_reqs,
                'deferred':s.num_skipped_waiting_reqs,'kv_usage':s.kv_cache_usage,
                'evictions':len(s.kv_cache_eviction_events)})
        return out
    base.llm.llm_engine.engine_core.get_output=observed_get
    schedules=['barrier','continuous'] if args.kind=='pilot' and args.tokens==8192 else ['continuous']
    for schedule in schedules:
        name=f'{args.kind}_{schedule}_{args.tokens}';folder=ROOT/name;folder.mkdir(exist_ok=False)
        assert base.llm.reset_prefix_cache();scheduler.clear();base.thinking=True
        stream=StreamingModel(base);limits=Limits(output_tokens=2048,batch_size=8)
        groups=GROUPS if args.kind=='mixed' else [THINK]
        keys=[k for g in groups for k in g];ss=json.loads(json.dumps(schema));ss['properties']={k:ss['properties'][k] for k in keys};ss['required']=keys
        cls=ContinuousPredictor if schedule=='continuous' else SourceFirstPredictor
        predictor=cls(stream if schedule=='continuous' else base,retriever,{k:table[k] for k in keys},ss,limits=limits)
        completed=[];metrics=[];tick=time.monotonic()
        with (folder/'trace_completed.jsonl').open('w') as f:
            def saved(p):
                if args.kind=='mixed' and p.judgments is not None:p.judgments.update(judge(next(r for r in records if r['id']==p.record_id))['judgments'])
                f.write(json.dumps(safe(p),ensure_ascii=False)+'\n');f.flush();completed.append(p.record_id)
                if len(completed)%8==0 or len(completed)==len(records):
                    print(json.dumps({'stage':name,'records':len(completed),'seconds':time.monotonic()-tick,'id':p.record_id,'failed':bool(p.error)}),flush=True)
            if schedule=='continuous':
                results=predictor.predict(records,item_groups=groups,thinking_groups=[False]*4+[True] if args.kind=='mixed' else [True],cache_seed=args.kind=='mixed',on_record=saved)
                metrics.append(dict(predictor.metrics));rr=stream.rows;lifecycle=stream.lifecycle
            else:
                observer=TimedLLM(base.llm);base.llm=observer;results=[]
                for i in range(0,len(records),8):
                    observer.set_phase(','.join(r['id'] for r in records[i:i+8]),'barrier')
                    chunk=predictor.predict(records[i:i+8],item_groups=groups)
                    for p in chunk:saved(p)
                    results.extend(chunk);metrics.append(dict(predictor.metrics))
                rr=observer.rows;lifecycle=[];base.llm=observer.wrapped
        elapsed=time.monotonic()-tick
        if args.kind=='mixed':
            for p,r in zip(results,records):
                if p.judgments is not None:p.judgments.update(judge(r)['judgments'])
        jsonl(folder/'trace.jsonl',[safe(p) for p in results]);jsonl(folder/'request_timings.jsonl',rr)
        jsonl(folder/'lifecycle.jsonl',lifecycle);jsonl(folder/'scheduler.jsonl',scheduler)
        me=[e for p in results for t in p.trace for e in t['events'] if e['event']=='model']
        import torch
        report={'gpu':torch.cuda.get_device_name(0),'name':name,'records':len(records),'schedule':schedule,'groups':groups,'engine':engine,
            'prediction_seconds':elapsed,'load_seconds':load,'total_seconds':elapsed+load,
            'options':{'model_dir':str(MODEL),'max_model_len':32768,'thinking':'mixed' if args.kind=='mixed' else True,'item_group_size':6},'limits':asdict(limits),
            'failed_ids':[p.record_id for p in results if p.error],'model_turns':len(me),
            'search_rounds':sum(e['event']=='search' for p in results for t in p.trace for e in t['events']),
            'invalid_responses':sum(e['event']=='invalid_response' for p in results for t in p.trace for e in t['events']),
            'input_tokens':sum(e['input_tokens'] for e in me),'output_tokens':sum(e['output_tokens'] for e in me),
            'thinking_tokens':sum(e['thinking_tokens'] for e in me),'metrics':metrics}
        dump(folder/'report.json',report)
        if args.kind=='mixed' and not report['failed_ids']:
            write_submission(results,folder/'submission.csv');jsonl(folder/'rules.jsonl',[judge(r) for r in records])
            evaluate(folder,'data/dev_labels.csv','data/dev.jsonl',len(records))
        print(json.dumps({'stage':'complete','name':name,'seconds':elapsed,'failed':report['failed_ids']}),flush=True)

if __name__=='__main__':main()
