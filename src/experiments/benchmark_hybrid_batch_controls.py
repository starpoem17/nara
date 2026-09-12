"""Same six-feature ON controls at batch8; original mixed pipeline stays frozen."""
from pathlib import Path
import time
from nara.experiments.benchmark_hybrid200 import OUT, dump, jsonl, reset, finish
from nara.experiments.config import MODEL
from nara.records import prediction_payload as safe
from nara.records import read_records
from nara.inference.predictor import Limits,Turn
from nara.inference.hybrid_experiment import THINK,INSTANT,TimedLLM,merge
from nara.inference.prefix_predictor import SourceFirstPredictor,split_predictor
from nara.experiments.config import configuration
from nara.rules.qualification import judge
import json


def main():
    records=read_records('data/dev.jsonl')
    table=json.loads(Path('data/항목표.json').read_text())['항목']
    schema=json.loads(Path('data/정답스키마_디코딩.json').read_text())['properties']['판정']
    table,schema,_=configuration(table,schema,'groups12',True)
    from nara.retrieval.search import BGEEncoder,LegalRetriever
    from nara.inference.engine import VLLMModel
    import vllm
    tick=time.monotonic()
    retriever=LegalRetriever('model/legal_index',BGEEncoder('models/bge-m3',device='cuda'))
    stock=vllm.LLM
    def measured(**kw):return stock(disable_log_stats=False,**kw)
    vllm.LLM=measured
    try:model=VLLMModel(MODEL,thinking=True,max_num_seqs=8)
    finally:vllm.LLM=stock
    load=time.monotonic()-tick
    observer=TimedLLM(model.llm);model.llm=observer
    predictor=split_predictor(SourceFirstPredictor(model,retriever,table,schema,limits=Limits(output_tokens=2048)),[THINK])
    simple={'type':'object','properties':{'answer':{'type':'integer'}},'required':['answer'],'additionalProperties':False}
    model.generate([Turn(str(i),[{'role':'user','content':'2+3을 계산하고 {"answer":5}로 답하라.'}],simple,512) for i in range(8)])
    dump(OUT/'engine_batch_controls.json',{'load_seconds':load,'disable_log_stats':False,'max_num_seqs':8})
    for budget in [1024]:
        name=f'six_on{budget}_batch8';folder=OUT/name;folder.mkdir(exist_ok=False)
        reset(observer);observer.thinking_budget=budget
        predictions=[];chunks=[];tick=time.monotonic()
        with (folder/'trace.jsonl').open('w') as stream:
            for i in range(0,200,8):
                subset=records[i:i+8];observer.set_phase(','.join(r['id'] for r in subset),name)
                start=time.monotonic();result=predictor.predict(subset,item_groups=[THINK])
                chunks.append({'ids':[r['id'] for r in subset],'seconds':time.monotonic()-start,**predictor.metrics})
                for p in result:
                    for task in p.trace:task['task_id']=p.record_id+':'+name+':'+task['task_id']
                    stream.write(json.dumps(safe(p),ensure_ascii=False)+'\n')
                stream.flush();predictions.extend(result)
                print(json.dumps({'stage':name,'records':len(predictions),'seconds':time.monotonic()-tick,'failed':sum(bool(p.error) for p in predictions)}),flush=True)
        elapsed=time.monotonic()-tick
        dump(folder/'report.json',{'phase':name,'records':200,'seconds':elapsed,'failed_ids':[p.record_id for p in predictions if p.error],
              'thinking':True,'budget':budget,'batch_size':8,'same_features':THINK})
        dump(folder/'chunk_timings.json',chunks);dump(folder/'model_batches.json',observer.batches)
        jsonl(folder/'request_timings.jsonl',observer.rows)
    # Real end-to-end optimized pipeline: cache instant groups per notice,
    # then batch the six-feature ON256 requests for each block of eight notices.
    folder=OUT/'optimized';folder.mkdir(exist_ok=False)
    reset(observer);observer.thinking_budget=256
    full=SourceFirstPredictor(model,retriever,table,schema,limits=Limits(output_tokens=2048))
    results=[];timings=[];rules=[];tick=time.monotonic()
    with (folder/'trace.jsonl').open('w') as stream:
        for i in range(0,200,8):
            subset=records[i:i+8];partial={};phases=[]
            for j in range(0,len(subset),2):
                pair=subset[j:j+2];model.thinking=False
                partial.update({r['id']:[] for r in pair})
                for phase,groups in [('instant_first',INSTANT[:1]),('instant_cached',INSTANT[1:])]:
                    observer.set_phase(','.join(r['id'] for r in pair),phase)
                    worker=split_predictor(full,groups);start=time.monotonic()
                    output=worker.predict(pair,item_groups=groups)
                    phases.append({'phase':phase,'seconds':time.monotonic()-start,**worker.metrics})
                    for rec,p in zip(pair,output):
                        for task in p.trace:task['task_id']=rec['id']+':'+phase+':'+task['task_id']
                        partial[rec['id']].append(p)
            model.thinking=True;observer.set_phase(','.join(r['id'] for r in subset),'thinking_batch')
            start=time.monotonic();thinking=predictor.predict(subset,item_groups=[THINK])
            phases.append({'phase':'thinking_batch','seconds':time.monotonic()-start,**predictor.metrics})
            for rec,p in zip(subset,thinking):
                for task in p.trace:task['task_id']=rec['id']+':thinking_batch:'+task['task_id']
                merged=merge(rec['id'],partial[rec['id']]+[p]);rule=judge(rec);rules.append(rule)
                if merged.judgments is not None:merged.judgments.update(rule['judgments'])
                stream.write(json.dumps(safe(merged),ensure_ascii=False)+'\n');results.append(merged)
            stream.flush();timings.append({'ids':[r['id'] for r in subset],'phases':phases})
            print(json.dumps({'stage':'optimized','records':len(results),'seconds':time.monotonic()-tick,'failed':sum(bool(p.error) for p in results)}),flush=True)
    elapsed=time.monotonic()-tick
    jsonl(folder/'rules.jsonl',rules)
    finish(folder,results,timings,observer,elapsed,load,full.limits,'mixed: four OFF, six-feature ON256 batch8')
    # Optimized all-instant strategy: two seed requests then eight cached requests.
    folder=OUT/'optimized_off';folder.mkdir(exist_ok=False)
    reset(observer);observer.thinking_budget=None;model.thinking=False
    results=[];timings=[];rules=[];tick=time.monotonic()
    with (folder/'trace.jsonl').open('w') as stream:
        for i in range(0,200,2):
            pair=records[i:i+2];partial={r['id']:[] for r in pair};phases=[]
            for phase,groups in [('instant_first',INSTANT[:1]),('instant_cached',INSTANT[1:]+[THINK])]:
                observer.set_phase(','.join(r['id'] for r in pair),phase)
                worker=split_predictor(full,groups);start=time.monotonic()
                output=worker.predict(pair,item_groups=groups)
                phases.append({'phase':phase,'seconds':time.monotonic()-start,**worker.metrics})
                for rec,p in zip(pair,output):
                    for task in p.trace:task['task_id']=rec['id']+':'+phase+':'+task['task_id']
                    partial[rec['id']].append(p)
            for rec in pair:
                p=merge(rec['id'],partial[rec['id']]);rule=judge(rec);rules.append(rule)
                if p.judgments is not None:p.judgments.update(rule['judgments'])
                stream.write(json.dumps(safe(p),ensure_ascii=False)+'\n');results.append(p)
            stream.flush();timings.append({'ids':[r['id'] for r in pair],'phases':phases})
            if len(results)%10==0:print(json.dumps({'stage':'optimized_off','records':len(results),'seconds':time.monotonic()-tick,'failed':sum(bool(p.error) for p in results)}),flush=True)
    elapsed=time.monotonic()-tick
    jsonl(folder/'rules.jsonl',rules)
    finish(folder,results,timings,observer,elapsed,load,full.limits,False)
    print(json.dumps({'stage':'complete'}),flush=True)

if __name__=='__main__':main()
