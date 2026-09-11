"""Freeze inputs and separate adapter, scheduling, and repeat-run variation."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from script import read_records
from scripts.benchmark_compact200 import configuration,MODEL
from nara.inference import Limits,Reply,_Task
from nara.prefix_predictor import SourceFirstPredictor,split_predictor
from nara.continuous import StreamingModel,ContinuousPredictor
from nara.vllm_model import VLLMModel
from nara.hybrid_experiment import THINK

ROOT=Path('analysis/continuous_diagnosis')
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,default=str)+'\n')
def digest(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def rows(p):return [json.loads(s) for s in Path(p).read_text().splitlines()]

def main():
    ROOT.mkdir(exist_ok=False)
    records=read_records('data/dev.jsonl')
    old=rows('analysis/hybrid200/six_on1024_batch8/trace.jsonl')
    new=rows('analysis/continuous200/six_continuous_8192/trace.jsonl')
    assert [r['record_id'] for r in old]==[r['id'] for r in records]==[r['record_id'] for r in new]
    from transformers import AutoTokenizer
    counter=VLLMModel.__new__(VLLMModel);counter.tokenizer=AutoTokenizer.from_pretrained(MODEL,local_files_only=True)
    counter.max_model_len=32768;counter.thinking=True
    table=json.loads(Path('data/항목표.json').read_text())['항목']
    schema=json.loads(Path('data/정답스키마_디코딩.json').read_text())['properties']['판정']
    table,schema,_=configuration(table,schema,'groups12',True)
    original=split_predictor(SourceFirstPredictor(counter,None,table,schema,limits=Limits(output_tokens=2048)),[THINK])
    keys=THINK;ss=json.loads(json.dumps(schema));ss['properties']={k:ss['properties'][k] for k in keys};ss['required']=keys
    current=ContinuousPredictor(counter,None,{k:table[k] for k in keys},ss,limits=Limits(output_tokens=2048,batch_size=8))
    captured=[];original_events=[r['trace'][0]['events'][0] for r in old]
    def capture(turns):
        replies={}
        for turn in turns:
            e=original_events[len(captured)];captured.append(turn)
            replies[turn.task_id]=Reply(e['response'],e['finish_reason'],e['input_tokens'],e['output_tokens'],thinking_tokens=e['thinking_tokens'],thinking_budget=e['thinking_budget'])
        return replies
    counter.generate=capture
    replay=[]
    for i in range(0,200,8):replay+=original.predict(records[i:i+8],item_groups=[THINK])
    assert len(captured)==200
    checks=[];turns=[]
    for i,(rec,turn,prev,now) in enumerate(zip(records,captured,old,new)):
        task=_Task(rec['id'],rec,tuple(THINK),current._messages(rec,tuple(THINK)))
        nxt=current._turn(task);assert nxt is not None
        assert turn.messages==nxt.messages and json.dumps(turn.schema)==json.dumps(nxt.schema) and turn.max_tokens==nxt.max_tokens
        ids=counter._tokens(turn.messages);other=counter._tokens(nxt.messages);assert ids==other
        assert len(ids)==prev['trace'][0]['events'][0]['input_tokens']==now['trace'][0]['events'][0]['input_tokens']
        assert replay[i].judgments==prev['judgments']
        # Independently replay new raw final JSON through original postprocessing.
        event=now['trace'][0]['events'][0];assert event['finish_reason']=='stop'
        action=json.loads(event['response']);original._finish(task,action['judgments']);assert task.judgments==now['judgments']
        checks.append({'id':rec['id'],'input_tokens':len(ids),'prompt_token_sha256':digest(ids),'schema_sha256':digest(turn.schema)})
        turns.append(nxt)
    dump(ROOT/'input_audit.json',{'records':200,'messages_and_ordered_schema_identical':True,'token_ids_identical':True,'historical_input_lengths_match':True,'old_and_new_postprocessing_replay_match':True,'checks':checks})
    dump(ROOT/'plan.json',{'ids':[r['id'] for r in records[:24]],'selection':'First24 in original input order; no selection by labels or output differences',
        'stages':['old_barrier_1','old_barrier_2','new_barrier','new_continuous_1','new_continuous_2'],
        'scope':'Same-engine raw-token diagnostics; same frozen Turn inputs; no full evaluation claim; reset prefix each stage, other warm state persists',
        'source_sha256':{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in ['scripts/diagnose_continuous.py','nara/continuous.py','nara/vllm_model.py','nara/inference.py','nara/conversation.py','nara/prefix_predictor.py','nara/compact_criteria.json','data/dev.jsonl']}})
    print(json.dumps({'stage':'input_audit_passed','records':200}),flush=True)
    from nara.retrieval import BGEEncoder,LegalRetriever
    import vllm
    tick=time.monotonic();retriever=LegalRetriever('model/legal_index',BGEEncoder('models/bge-m3',device='cuda'))
    stock=vllm.LLM
    def configured(**kw):return stock(disable_log_stats=False,max_num_batched_tokens=8192,enable_chunked_prefill=True,**kw)
    vllm.LLM=configured
    try:base=VLLMModel(MODEL,thinking=True,max_num_seqs=8)
    finally:vllm.LLM=stock
    load=time.monotonic()-tick
    from nara.inference import Turn
    simple={'type':'object','properties':{'answer':{'type':'integer'}},'required':['answer'],'additionalProperties':False}
    base.generate([Turn(str(i),[{'role':'user','content':'2+3을 계산하고 {"answer":5}로 답하라.'}],simple,512) for i in range(8)])
    import vllm.envs as envs
    dump(ROOT/'engine.json',{'load_seconds':load,'vllm_version':vllm.__version__,'batch_invariant':envs.VLLM_BATCH_INVARIANT,
        'multiprocessing':envs.VLLM_ENABLE_V1_MULTIPROCESSING,'config':str(base.llm.llm_engine.vllm_config)})
    selected=turns[:24];token_to_id={digest(base._tokens(t.messages)):t.task_id for t in selected};assert len(token_to_id)==24
    engine=base.llm.llm_engine;stockstep=engine.step;stockadd=engine.add_request
    raw=[];added=[];completed_ids={};effective=[]
    def observed_add(rid,prompt,params,*a,**kw):
        tokens=prompt['prompt_token_ids'];record_id=token_to_id[digest(tokens)]
        added.append({'request_id':rid,'record_id':record_id,'input_token_sha256':digest(tokens)})
        effective.append({'record_id':record_id,'params':str(params)})
        return stockadd(rid,prompt,params,*a,**kw)
    def observed_step():
        out=stockstep()
        for x in out:
            if not x.finished:continue
            record_id=token_to_id[digest(list(x.prompt_token_ids))];completed_ids[x.request_id]=record_id
            tokens=list(x.outputs[0].token_ids)
            raw.append({'id':record_id,'request_id':x.request_id,'input_token_sha256':digest(list(x.prompt_token_ids)),
                        'token_ids':tokens,'raw_text':base.tokenizer.decode(tokens,skip_special_tokens=False),'finish_reason':x.outputs[0].finish_reason})
        return out
    engine.add_request=observed_add;engine.step=observed_step
    for stage in ['old_barrier_1','old_barrier_2','new_barrier','new_continuous_1','new_continuous_2']:
        assert base.llm.reset_prefix_cache();raw.clear();added.clear();completed_ids.clear();effective.clear()
        results={};tick=time.monotonic();stream=StreamingModel(base)
        if stage.startswith('old'):
            for i in range(0,24,8):results.update(base.generate(selected[i:i+8]))
        elif stage=='new_barrier':
            for i in range(0,24,8):
                for t in selected[i:i+8]:stream.submit(t)
                while stream.pending:
                    for tid,reply in stream.poll():results[tid]=reply
        else:
            cursor=0
            while cursor<len(selected) or stream.pending:
                while cursor<len(selected) and len(stream.pending)<8:
                    stream.submit(selected[cursor]);cursor+=1
                for tid,reply in stream.poll():results[tid]=reply
        elapsed=time.monotonic()-tick
        assert len(results)==len(raw)==len(added)==24
        # Route identity is checked independently from actual returned prompt tokens.
        assert all(completed_ids[a['request_id']]==a['record_id'] for a in added)
        from vllm.reasoning.gemma4_utils import parse_thinking_output
        assert all(parse_thinking_output(x['raw_text'])['answer']==results[x['id']].text for x in raw)
        dump(ROOT/(stage+'.json'),{'seconds':elapsed,'raw':sorted(raw,key=lambda x:x['id']),
            'replies':{k:asdict(v) for k,v in results.items()},'submissions':added.copy(),'effective_sampling':effective.copy(),'lifecycle':stream.lifecycle})
        print(json.dumps({'stage':stage,'seconds':elapsed,'route_verified':True}),flush=True)
    print(json.dumps({'stage':'complete'}),flush=True)
if __name__=='__main__':main()
