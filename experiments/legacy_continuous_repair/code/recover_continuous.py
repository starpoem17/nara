"""Retry failed groups once with unchanged prompts, retaining first-pass artifacts."""

if __name__ == "__main__":
    raise SystemExit("Archived code: create a fresh registered run; see docs/operations.md.")

import hashlib
import json
from pathlib import Path
import shutil
import time
from experiments.legacy_continuous_pilot.code.benchmark_continuous import ROOT, dump, jsonl
from nara.experiments.config import MODEL
from nara.records import prediction_payload as safe
from nara.experiments.config import configuration
from experiments.legacy_hybrid_repair.code.recover_hybrid200 import replay
from nara.records import read_records,write_submission
from nara.inference.predictor import Prediction,Limits
from nara.inference.prefix_predictor import SourceFirstPredictor
from nara.inference.continuous import StreamingModel,ContinuousPredictor
from nara.inference.hybrid_experiment import THINK
from nara.rules.qualification import judge
from nara.evaluation.evaluate_dev import evaluate

def rows(p):return [json.loads(s) for s in p.read_text().splitlines()]
def main():
    budget=json.loads((ROOT/'selection.json').read_text())['selected_tokens']
    folder=ROOT/f'mixed_continuous_{budget}';report=json.loads((folder/'report.json').read_text())
    assert report['failed_ids'] and 'recovery' not in report
    records={r['id']:r for r in read_records('data/dev.jsonl')};trace=rows(folder/'trace.jsonl')
    table=json.loads(Path('data/항목표.json').read_text())['항목']
    schema=json.loads(Path('data/정답스키마_디코딩.json').read_text())['properties']['판정']
    table,schema,_=configuration(table,schema,'groups12',True)
    limits=Limits(**report['limits']);full=SourceFirstPredictor(None,None,table,schema,limits=limits)
    for r in trace:
        if not r['error']:
            restored={k:v for t in r['trace'] for k,v in replay(records[r['record_id']],t,full).items()}
            restored.update(judge(records[r['record_id']])['judgments']);assert restored==r['judgments']
    saved=folder/'first_pass';saved.mkdir()
    for name in ['trace.jsonl','trace_completed.jsonl','report.json','request_timings.jsonl','lifecycle.jsonl','scheduler.jsonl']:
        shutil.copy2(folder/name,saved/name)
    policy={'prompt_change':False,'extra_predict_attempts':1,'scope':'Only failed groups; original mode/output/thinking budget; isolated scheduling',
            'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    dump(ROOT/'recovery_policy.json',policy);shutil.copy2(__file__,ROOT/'source/scripts/recover_continuous.py')
    from nara.retrieval.search import BGEEncoder,LegalRetriever
    from nara.inference.engine import VLLMModel
    import vllm
    start=time.monotonic();retriever=LegalRetriever('model/legal_index',BGEEncoder('models/bge-m3',device='cuda'))
    stock=vllm.LLM
    def configured(**kw):return stock(disable_log_stats=False,max_num_batched_tokens=budget,enable_chunked_prefill=True,**kw)
    vllm.LLM=configured
    try:base=VLLMModel(MODEL,thinking=True,max_num_seqs=8)
    finally:vllm.LLM=stock
    load=time.monotonic()-start;stream=StreamingModel(base)
    old_life=rows(saved/'lifecycle.jsonl');stream.serial=max(int(r['request_id'].split('-')[-1]) for r in old_life)+1
    start=time.monotonic();repairs=[]
    for r in trace:
        if not r['error']:continue
        record=records[r['record_id']];judgments={};errors=[]
        for t in r['trace']:
            if any(e['event']=='final' for e in t['events']):judgments.update(replay(record,t,full));continue
            keys=t['items'];ss=json.loads(json.dumps(schema));ss['properties']={k:ss['properties'][k] for k in keys};ss['required']=keys
            worker=ContinuousPredictor(stream,retriever,{k:table[k] for k in keys},ss,limits=limits)
            nr,nl=len(stream.rows),len(stream.lifecycle);tick=time.monotonic()
            new=worker.predict([record],item_groups=[keys],thinking_groups=[set(keys)==set(THINK)])[0]
            repairs.append({'id':r['record_id'],'items':keys,'seconds':time.monotonic()-tick,'error':new.error})
            for row in stream.rows[nr:]+stream.lifecycle[nl:]:row['task_id']=t['task_id']
            nt=safe(new)['trace'][0];t['events'].extend(nt['events']);t['search_rounds']+=nt['search_rounds'];t['retrieval_tokens']+=nt['retrieval_tokens']
            t['recovery']='Same prompt/mode/budgets, isolated failed group'
            if new.error:errors.append(new.error)
            else:judgments.update(new.judgments)
        r['error']='; '.join(errors) or None
        if not errors:judgments.update(judge(record)['judgments']);r['judgments']=judgments
    elapsed=time.monotonic()-start
    jsonl(folder/'trace.jsonl',trace);jsonl(folder/'request_timings.jsonl',rows(saved/'request_timings.jsonl')+stream.rows)
    jsonl(folder/'lifecycle.jsonl',old_life+stream.lifecycle)
    report['first_pass']={'failed_ids':report['failed_ids'],'prediction_seconds':report['prediction_seconds']}
    report['recovery']={'policy':policy,'prediction_seconds':elapsed,'separate_process_load_seconds':load,'groups':repairs,
        'scheduler_stats_scope':'first pass only; recovery scheduler not sampled','metrics_scope':'metrics list is first pass; recovery walltime is recorded separately','completion_trace_scope':'first pass only; final merged trace.jsonl'}
    report['prediction_seconds']+=elapsed;report['total_seconds']+=elapsed+load
    report['failed_ids']=[r['record_id'] for r in trace if r['error']]
    events=[e for r in trace for t in r['trace'] for e in t['events']];me=[e for e in events if e['event']=='model']
    for k in ['input_tokens','output_tokens','thinking_tokens']:report[k]=sum(e[k] for e in me)
    report['model_turns']=len(me);report['invalid_responses']=sum(e['event']=='invalid_response' for e in events);report['search_rounds']=sum(e['event']=='search' for e in events)
    dump(folder/'report.json',report)
    if not report['failed_ids']:
        write_submission([Prediction(**r) for r in trace],folder/'submission.csv')
        jsonl(folder/'rules.jsonl',[judge(r) for r in records.values()]);evaluate(folder,'data/dev_labels.csv','data/dev.jsonl',200)
    print(json.dumps({'stage':'recovery_complete','seconds':elapsed,'failed':report['failed_ids']}),flush=True)
if __name__=='__main__':main()
