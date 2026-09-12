"""Mixed five-group dev200, same-six mode controls, and matched cache probes."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import shutil
import time
from nara.records import read_records,write_submission
from nara.inference.predictor import Limits,Turn,Prediction,compact
from nara.inference.prefix_predictor import SourceFirstPredictor
from nara.inference.hybrid_experiment import GROUPS,THINK,INSTANT,TimedLLM,predict_hybrid,run_phase
from nara.rules.qualification import judge
from nara.experiments.config import MODEL, configuration
from nara.evaluation.evaluate_dev import evaluate

OUT=Path('analysis/hybrid200')

def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def jsonl(path,values):path.write_text(''.join(compact(v)+'\n' for v in values))
from nara.records import prediction_payload as safe


def prepare(records,table,schema,limits):
    from nara.inference.engine import VLLMModel
    from transformers import AutoTokenizer
    model=VLLMModel.__new__(VLLMModel);model.tokenizer=AutoTokenizer.from_pretrained(MODEL,local_files_only=True)
    model.max_model_len=32768
    predictor=SourceFirstPredictor(model,None,table,schema,limits=limits)
    counts=[]
    for record in records:
        row={'id':record['id'],'groups':[]}
        for group in GROUPS:
            messages=predictor._messages(record,group)
            assert all(d['text'] in messages[1]['content'] for d in record['docs'])
            assert '[v2]' not in messages[1]['content'] and '[v3]' not in messages[1]['content']
            assert all((f'[{k}] ' in messages[1]['content'])==(k in group) for k in table)
            tokens={}
            for mode in [False,True] if group==THINK else [False]:
                model.thinking=mode;n=model.count_messages(messages)
                assert n+2048+128<=32768
                tokens[str(mode)]=n
            row['groups'].append(tokens)
        counts.append(row)
    ranked=sorted(counts,key=lambda r:r['groups'][0]['False'])
    selected=[ranked[round(i*(len(ranked)-1)/11)]['id'] for i in range(12)]
    paths=['src/__init__.py','src/runtime.py','src/records.py','src/paths.py',
           'src/experiments/__init__.py','src/experiments/config.py','src/inference/__init__.py',
           'src/retrieval/__init__.py','src/rules/__init__.py','src/evaluation/__init__.py',
           'src/experiments/benchmark_hybrid200.py','src/inference/hybrid_experiment.py','src/inference/prefix_predictor.py',
           'src/inference/engine.py','src/inference/predictor.py','src/inference/conversation.py','src/inference/compact_predictor.py','src/inference/compact_criteria.json',
           'src/rules/qualification.py','data/dev.jsonl','data/항목표.json','data/정답스키마_디코딩.json']
    hashes={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths}
    assert hashes['src/rules/qualification.py']==json.loads(Path('analysis/compact200/rule_freeze.json').read_text())['sha256']
    manifest={'groups':GROUPS,'thinking_features':THINK,'records':200,'counts':counts,'source_sha256':hashes,
      'main':'instant_first then instant_cached(3 independent requests), then six-feature thinking ON1024 per notice',
      'controls':'same six features on all200: OFF and ON256, each standalone batch1 without warmed document prefix; reuse main instant judgments for composite scores',
      'probe_ids':selected,'probes':'12 length quantiles,2 rounds alternating cold/warm order; same instant group2 prompt; fixed128 output tokens without structured decoding; warm via different instant group1; reset cache per condition',
      'time_definition':'vLLM scheduled->first token=prefill interval, first->last=decode, queued->scheduled=queue. Request latency, not exclusive GPU kernel duration; concurrent request intervals overlap.',
      'control_time_definition':'full composite walltime estimated as main walltime minus main thinking phase plus alternate standalone six-feature phase time; not separately measured full pipeline',
      'limits':asdict(limits)}
    dump(OUT/'manifest.json',manifest)
    for p in paths:
        dst=OUT/'source'/p;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst)
    for i,g in enumerate(GROUPS):
        messages=predictor._messages(records[0],g)
        (OUT/f'prompt_{i+1}.txt').write_text('[system]\n'+messages[0]['content']+'\n[user]\n{NOTICE_ID_META_FULL_DOCUMENTS}\n[판단 기준]\n'+messages[1]['content'].split('\n[판단 기준]\n',1)[1])
        dump(OUT/f'schema_{i+1}.json',predictor._schema(g,True))
    print(compact({'stage':'preflight','records':200,'max_input':max(max(t.values()) for r in counts for t in r['groups']),'probe_ids':selected}),flush=True)
    return manifest


def reset(observer):
    assert observer.reset_prefix_cache();observer.rows.clear();observer.batches.clear()


def finish(folder,predictions,timings,observer,elapsed,load,limits,mode):
    events=[e for p in predictions for t in p.trace for e in t['events']]
    me=[e for e in events if e['event']=='model']
    report={'name':folder.name,'options':{'model_dir':MODEL,'max_model_len':32768,'thinking':mode,'item_group_size':6},
            'limits':asdict(limits),'groups':GROUPS,'records':200,'gpu':'NVIDIA GeForce RTX 5090',
            'prediction_seconds':elapsed,'load_seconds':load,'total_seconds':elapsed+load,
            'failed_ids':[p.record_id for p in predictions if p.error],
            'model_turns':len(me),'search_rounds':sum(e['event']=='search' for e in events),
            'invalid_responses':sum(e['event']=='invalid_response' for e in events),
            'context_failures':sum(e['event']=='context_failure' for e in events),
            'input_tokens':sum(e['input_tokens'] for e in me),'output_tokens':sum(e['output_tokens'] for e in me),
            'thinking_tokens':sum(e['thinking_tokens'] for e in me),
            'model_seconds':sum(p['model_seconds'] for r in timings for p in r['phases']),
            'retrieval_seconds':sum(p['retrieval_seconds'] for r in timings for p in r['phases'])}
    dump(folder/'report.json',report);dump(folder/'notice_timings.json',timings)
    dump(folder/'model_batches.json',observer.batches);jsonl(folder/'request_timings.jsonl',observer.rows)
    if not report['failed_ids']:
        write_submission(predictions,folder/'submission.csv');evaluate(folder,'data/dev_labels.csv','data/dev.jsonl',200)
    return report


def run_main(records,predictor,observer,load,limits):
    folder=OUT/'main';folder.mkdir(exist_ok=False)
    reset(observer);observer.thinking_budget=None
    predictions=[];timings=[];rules=[];tick=time.monotonic()
    with (folder/'trace.jsonl').open('w') as stream:
        for i,record in enumerate(records):
            start=time.monotonic();p,phases=predict_hybrid(predictor,record,observer)
            rule=judge(record);rules.append(rule)
            if p.judgments is not None:p.judgments.update(rule['judgments'])
            timings.append({'id':record['id'],'seconds':time.monotonic()-start,'phases':phases})
            stream.write(compact(safe(p))+'\n');stream.flush();predictions.append(p)
            if (i+1)%5==0:print(compact({'stage':'main','records':i+1,'seconds':time.monotonic()-tick,'failed':sum(bool(x.error) for x in predictions)}),flush=True)
    elapsed=time.monotonic()-tick
    jsonl(folder/'rules.jsonl',rules)
    finish(folder,predictions,timings,observer,elapsed,load,limits,'mixed: four OFF, six-feature group ON1024')


def run_control(records,predictor,observer,budget):
    name='six_off' if budget==0 else 'six_on256'
    folder=OUT/name;folder.mkdir(exist_ok=False)
    reset(observer);observer.thinking_budget=budget or None
    timings=[];predictions=[];tick=time.monotonic()
    with (folder/'trace.jsonl').open('w') as stream:
        for i,record in enumerate(records):
            p,metric=run_phase(predictor,record,[THINK],bool(budget),name,observer)
            timings.append({'id':record['id'],**metric});predictions.append(p)
            stream.write(compact(safe(p))+'\n');stream.flush()
            if (i+1)%10==0:print(compact({'stage':name,'records':i+1,'seconds':time.monotonic()-tick,'failed':sum(bool(x.error) for x in predictions)}),flush=True)
    dump(folder/'report.json',{'phase':name,'records':200,'seconds':time.monotonic()-tick,'failed_ids':[p.record_id for p in predictions if p.error],
                              'thinking':bool(budget),'budget':budget,'same_features':THINK})
    dump(folder/'notice_timings.json',timings);dump(folder/'model_batches.json',observer.batches)
    jsonl(folder/'request_timings.jsonl',observer.rows)


def run_probes(records,predictor,observer,manifest):
    from vllm import SamplingParams
    observer.thinking_budget=None;predictor.model.thinking=False
    # Fixed-length synthetic decode uses the actual group prompts, but contributes no predictions.
    params=SamplingParams(temperature=0,seed=0,max_tokens=128,min_tokens=128,ignore_eos=True)
    record_map={r['id']:r for r in records};pairs=[]
    observer.rows.clear();observer.batches.clear()
    for repeat in range(2):
        for i,key in enumerate(manifest['probe_ids']):
            rec=record_map[key]
            seed=predictor.model._tokens(predictor._messages(rec,INSTANT[0]))
            target=predictor.model._tokens(predictor._messages(rec,INSTANT[1]))
            pair={'id':key,'repeat':repeat,'input_tokens':len(target),'conditions':{}}
            for condition in (['cold','warm'] if (i+repeat)%2==0 else ['warm','cold']):
                assert observer.reset_prefix_cache()
                seed_seconds=0.0
                if condition=='warm':
                    observer.set_phase(key,'probe_seed');t=time.monotonic()
                    observer.generate([{'prompt_token_ids':seed}],sampling_params=params,use_tqdm=False)
                    seed_seconds=time.monotonic()-t
                observer.set_phase(key,'probe_'+condition);t=time.monotonic()
                outputs=observer.generate([{'prompt_token_ids':target}],sampling_params=params,use_tqdm=False)
                elapsed=time.monotonic()-t
                assert len(outputs[0].outputs[0].token_ids)==128
                pair['conditions'][condition]={'seconds':elapsed,'seed_seconds':seed_seconds,**observer.rows[-1],
                    'output_sha256':hashlib.sha256(str(outputs[0].outputs[0].token_ids).encode()).hexdigest()}
            pairs.append(pair)
            print(compact({'stage':'probes','pairs':len(pairs)}),flush=True)
    folder=OUT/'probes';folder.mkdir(exist_ok=False)
    dump(folder/'pairs.json',pairs);jsonl(folder/'request_timings.jsonl',observer.rows);dump(folder/'model_batches.json',observer.batches)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',choices=['all','main','controls','probes','prepare'],default='all')
    args=parser.parse_args();OUT.mkdir(parents=True,exist_ok=True)
    records=read_records('data/dev.jsonl');assert len(records)==200
    table=json.loads(Path('data/항목표.json').read_text())['항목']
    schema=json.loads(Path('data/정답스키마_디코딩.json').read_text())['properties']['판정']
    table,schema,_=configuration(table,schema,'groups12',True);limits=Limits(output_tokens=2048)
    manifest=prepare(records,table,schema,limits) if not (OUT/'manifest.json').exists() else json.loads((OUT/'manifest.json').read_text())
    if args.stage=='prepare':return
    from nara.retrieval.search import BGEEncoder,LegalRetriever
    from nara.inference.engine import VLLMModel
    import vllm
    tick=time.monotonic()
    retriever=LegalRetriever('model/legal_index',BGEEncoder('models/bge-m3',device='cuda'))
    stock=vllm.LLM
    def measured_llm(**kwargs):
        kwargs['disable_log_stats']=False
        return stock(**kwargs)
    vllm.LLM=measured_llm
    try:model=VLLMModel(MODEL,thinking=True,max_num_seqs=8)
    finally:vllm.LLM=stock
    load=time.monotonic()-tick
    observer=TimedLLM(model.llm);model.llm=observer
    predictor=SourceFirstPredictor(model,retriever,table,schema,limits=limits)
    simple={'type':'object','properties':{'answer':{'type':'integer'}},'required':['answer'],'additionalProperties':False}
    warm=time.monotonic()
    for mode in [False,True]:
        model.thinking=mode
        model.generate([Turn(str(i),[{'role':'user','content':'2+3을 계산하고 {"answer":5}로 답하라.'}],simple,512) for i in range(8)])
    dump(OUT/f'engine_{args.stage}.json',{'load_seconds':load,'warmup_seconds':time.monotonic()-warm,'disable_log_stats':False,'max_model_len':32768,'max_num_seqs':8})
    if args.stage in ['all','main']:run_main(records,predictor,observer,load,limits)
    if args.stage in ['all','controls']:
        for budget in [0,256]:run_control(records,predictor,observer,budget)
    if args.stage in ['all','probes']:run_probes(records,predictor,observer,manifest)
    print(compact({'stage':'complete','requested':args.stage}),flush=True)

if __name__=='__main__':main()
