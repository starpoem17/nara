"""Current mixed-five pipeline: wait for each batch of up to eight model requests."""
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
from nara.hybrid_experiment import GROUPS
from nara.hypothesis6 import judge
from nara.continuous import StreamingModel
from nara.batch_barrier import BatchedPredictor
from nara.vllm_model import VLLMModel

def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def jsonl(p,x):p.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in x))
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',required=True,type=Path)
    parser.add_argument('--limit',type=int,default=200,help='First N dev notices; fewer than200 is execution validation only')
    args=parser.parse_args()
    if not 1<=args.limit<=200:parser.error('--limit must be in1..200')
    folder=args.output_dir;folder.mkdir(parents=True,exist_ok=False);records=read_records('data/dev.jsonl')[:args.limit]
    table=json.loads(Path('data/항목표.json').read_text())['항목'];schema=json.loads(Path('data/정답스키마_디코딩.json').read_text())['properties']['판정']
    table,schema,_=configuration(table,schema,'groups12',True)
    dump(folder/'plan.json',{'schedule':'batch_barrier','max_requests':8,'groups':GROUPS,'thinking':[False]*4+[True],
        'source_sha256':{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in ['scripts/run_batch_fallback.py','nara/batch_barrier.py','nara/continuous.py','nara/vllm_model.py','nara/hypothesis6.py','nara/compact_criteria.json','data/dev.jsonl']}})
    from nara.retrieval import BGEEncoder,LegalRetriever
    import vllm,torch
    tick=time.monotonic();retriever=LegalRetriever('model/legal_index',BGEEncoder('models/bge-m3',device='cuda'))
    stock=vllm.LLM
    def configured(**kw):return stock(disable_log_stats=False,max_num_batched_tokens=8192,enable_chunked_prefill=True,**kw)
    vllm.LLM=configured
    try:base=VLLMModel(MODEL,thinking=True,max_num_seqs=8)
    finally:vllm.LLM=stock
    load=time.monotonic()-tick
    simple={'type':'object','properties':{'answer':{'type':'integer'}},'required':['answer'],'additionalProperties':False}
    base.generate([Turn(str(i),[{'role':'user','content':'2+3을 계산하고 {"answer":5}로 답하라.'}],simple,512) for i in range(8)])
    assert base.llm.reset_prefix_cache()
    stream=StreamingModel(base);limits=Limits(output_tokens=2048,batch_size=8)
    predictor=BatchedPredictor(stream,retriever,table,schema,limits=limits)
    tick=time.monotonic();out=predictor.predict(records,item_groups=GROUPS,thinking_groups=[False]*4+[True],cache_seed=True)
    elapsed=time.monotonic()-tick
    for r,p in zip(records,out):
        if p.judgments is not None:p.judgments.update(judge(r)['judgments'])
    jsonl(folder/'trace.jsonl',[safe(p) for p in out]);jsonl(folder/'rules.jsonl',[judge(r) for r in records])
    jsonl(folder/'lifecycle.jsonl',stream.lifecycle);jsonl(folder/'request_timings.jsonl',stream.rows)
    # Every wave must empty before the next one admits any request.
    active=set();draining=False;waves=0
    for e in stream.lifecycle:
        if e['event']=='submit':
            assert not draining,'Refill occurred before whole batch completion'
            if not active:waves+=1
            active.add(e['request_id']);assert len(active)<=8
        else:
            active.remove(e['request_id']);draining=bool(active)
    assert not active
    report={'name':'mixed_batch_fallback','records':len(records),'schedule':'batch_barrier','groups':GROUPS,
        'prediction_seconds':elapsed,'load_seconds':load,'total_seconds':elapsed+load,'gpu':torch.cuda.get_device_name(0),
        'options':{'model_dir':MODEL,'max_model_len':32768,'thinking':'four OFF + six-feature ON1024','item_group_size':6},'limits':asdict(limits),
        'failed_ids':[p.record_id for p in out if p.error],'metrics':predictor.metrics,'batch_barrier_verified':True,'waves':waves}
    dump(folder/'report.json',report)
    if not report['failed_ids']:
        write_submission(out,folder/'submission.csv')
        if len(records)==200:
            from scripts.evaluate_dev import evaluate
            evaluate(folder,'data/dev_labels.csv','data/dev.jsonl',200)
    print(json.dumps({'stage':'complete','records':len(records),'seconds':elapsed,'failed':report['failed_ids'],'barrier_verified':True,'waves':waves}),flush=True)
if __name__=='__main__':main()
