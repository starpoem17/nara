"""Bounded batch sensitivity and prefill/decode probes; no layer/kernel instrumentation."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from script import read_records
from scripts.benchmark_compact200 import configuration,MODEL
from nara.inference import Limits,Turn,_Task
from nara.prefix_predictor import SourceFirstPredictor,split_predictor
from nara.continuous import StreamingModel,ContinuousPredictor
from nara.vllm_model import VLLMModel
from nara.hybrid_experiment import THINK
ROOT=Path('analysis/prefill_decode_probe')
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,default=str)+'\n')
def digest(x):return hashlib.sha256(json.dumps(x,separators=(',',':')).encode()).hexdigest()
def diff(a,b):return next((i for i,(x,y) in enumerate(zip(a,b)) if x!=y),min(len(a),len(b)))
def main():
    ROOT.mkdir(exist_ok=False)
    records=read_records('data/dev.jsonl')[:24]
    table=json.loads(Path('data/항목표.json').read_text())['항목'];schema=json.loads(Path('data/정답스키마_디코딩.json').read_text())['properties']['판정']
    table,schema,_=configuration(table,schema,'groups12',True)
    dump(ROOT/'plan.json',{'records':[r['id'] for r in records],'test1':'same24 barrier vs continuous, same engine and params; prefix reset',
        'test2_targets':'First4 raw-token divergences in test1, independent of labels',
        'prefill':'Same prompt plus common output prefix, max_tokens1/logprobs10, solo vs batch8, two repetitions',
        'decode':'Same extended prompt, start solo; after first returned token inject7 requests vs stay solo; compare only shared history; two repetitions',
        'limits':'No layer/kernel probes; token probes use unconstrained decoding without thinking budget so no forced token masks obscure scores; not a label-quality evaluation',
        'source_sha256':{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in ['scripts/probe_prefill_decode.py','nara/continuous.py','nara/vllm_model.py','nara/inference.py','nara/compact_criteria.json','data/dev.jsonl']}})
    from nara.retrieval import BGEEncoder,LegalRetriever
    import vllm
    from vllm import SamplingParams
    from vllm.sampling_params import RequestOutputKind
    tick=time.monotonic();retriever=LegalRetriever('model/legal_index',BGEEncoder('models/bge-m3',device='cuda'))
    stock=vllm.LLM
    def configured(**kw):return stock(disable_log_stats=False,max_num_batched_tokens=8192,enable_chunked_prefill=True,**kw)
    vllm.LLM=configured
    try:base=VLLMModel(MODEL,thinking=True,max_num_seqs=8)
    finally:vllm.LLM=stock
    dump(ROOT/'engine.json',{'load_seconds':time.monotonic()-tick,'config':str(base.llm.llm_engine.vllm_config)})
    simple={'type':'object','properties':{'answer':{'type':'integer'}},'required':['answer'],'additionalProperties':False}
    base.generate([Turn(str(i),[{'role':'user','content':'2+3을 계산하고 {"answer":5}로 답하라.'}],simple,512) for i in range(8)])
    worker=split_predictor(SourceFirstPredictor(base,None,table,schema,limits=Limits(output_tokens=2048)),[THINK])
    helper=ContinuousPredictor(base,None,worker.items,worker.judgment_schema,limits=worker.limits)
    turns=[helper._turn(_Task(r['id'],r,tuple(THINK),worker._messages(r,THINK))) for r in records]
    prompts={t.task_id:base._tokens(t.messages) for t in turns};ids_by_hash={digest(t):k for k,t in prompts.items()}
    engine=base.llm.llm_engine;stockstep=engine.step;raw=[]
    def observed():
        out=stockstep()
        for x in out:
            if x.finished:
                raw.append({'id':ids_by_hash[digest(list(x.prompt_token_ids))],'tokens':list(x.outputs[0].token_ids),
                    'text':base.tokenizer.decode(x.outputs[0].token_ids,skip_special_tokens=False),'finish_reason':x.outputs[0].finish_reason})
        return out
    engine.step=observed;runs={}
    for mode in ['barrier','continuous']:
        assert base.llm.reset_prefix_cache();raw.clear();tick=time.monotonic();stream=StreamingModel(base)
        if mode=='barrier':
            for i in range(0,24,8):base.generate(turns[i:i+8])
        else:
            cursor=0
            while cursor<24 or stream.pending:
                while cursor<24 and len(stream.pending)<8:stream.submit(turns[cursor]);cursor+=1
                stream.poll()
        assert len(raw)==24 and len({r['id'] for r in raw})==24 and all(r['finish_reason']=='stop' for r in raw)
        runs[mode]={r['id']:r.copy() for r in raw};dump(ROOT/(mode+'.json'),{'seconds':time.monotonic()-tick,'raw':list(runs[mode].values())})
        print(json.dumps({'stage':mode,'seconds':time.monotonic()-tick}),flush=True)
    engine.step=stockstep
    targets=[]
    for rec in records:
        rid=rec['id'];a=runs['barrier'][rid]['tokens'];b=runs['continuous'][rid]['tokens']
        if a!=b:targets.append({'id':rid,'at':diff(a,b),'common':a[:diff(a,b)]})
    assert targets,'No batch sensitivity reproduced; stage2 targets unavailable'
    targets=targets[:4];dump(ROOT/'targets.json',targets)
    serial=0
    def params(n,lp=10,stream=False):return SamplingParams(temperature=0,seed=0,max_tokens=n,logprobs=lp,skip_special_tokens=False,output_kind=RequestOutputKind.CUMULATIVE if stream else RequestOutputKind.FINAL_ONLY)
    def pack(out):
        c=out.outputs[0]
        return {'tokens':list(c.token_ids),'logprobs':[{str(k):asdict(v) for k,v in row.items()} for row in c.logprobs] if c.logprobs is not None else [],'cached_tokens':out.num_cached_tokens}
    probes=[]
    for target in targets:
        rid=target['id'];fixed=prompts[rid]+target['common'];others=[v for k,v in prompts.items() if k!=rid][:7]
        assert len(fixed)+32<32768
        for repeat in range(2):
            for batch in [False,True]:
                assert base.llm.reset_prefix_cache();ps=[fixed]+(others if batch else [])
                tick=time.monotonic();outs=base.llm.generate([{'prompt_token_ids':p} for p in ps],sampling_params=[params(1) for _ in ps],use_tqdm=False)
                assert list(outs[0].prompt_token_ids)==fixed
                probes.append({'test':'prefill','id':rid,'repeat':repeat,'batch':batch,'input_hash':digest(fixed),'seconds':time.monotonic()-tick,**pack(outs[0])})
            for inject in [False,True]:
                assert base.llm.reset_prefix_cache();serial+=1;request_id=f'target-{serial}';tick=time.monotonic()
                engine.add_request(request_id,{'prompt_token_ids':fixed},params(16,stream=True));submitted=False;injection=None;final=None;first=None
                while engine.has_unfinished_requests():
                    outputs=engine.step()
                    for out in outputs:
                        if out.request_id!=request_id:continue
                        c=out.outputs[0]
                        if c.token_ids and first is None:first=pack(out)
                        if inject and c.token_ids and not submitted and not out.finished:
                            injection={'after_tokens':len(c.token_ids),'time':time.monotonic()-tick}
                            for j,p in enumerate(others):engine.add_request(f'bg-{serial}-{j}',{'prompt_token_ids':p},params(16,lp=None))
                            submitted=True
                        if out.finished:final=pack(out)
                assert final and first
                if inject:assert submitted
                probes.append({'test':'decode','id':rid,'repeat':repeat,'inject':inject,'injection':injection,'first':first,'input_hash':digest(fixed),'seconds':time.monotonic()-tick,**final})
        dump(ROOT/'probes.json',probes)
        print(json.dumps({'stage':'token_probes','id':rid,'original_divergence_0based':target['at']}),flush=True)
    print(json.dumps({'stage':'complete'}),flush=True)
if __name__=='__main__':main()
