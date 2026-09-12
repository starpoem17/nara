"""Retry only failed groups, preserving original successful judgments and costs."""
import hashlib
import json
from pathlib import Path
import shutil
import time
from nara.experiments.benchmark_hybrid200 import OUT, dump, jsonl
from nara.experiments.config import MODEL
from nara.records import prediction_payload as safe
from nara.records import read_records,write_submission
from nara.inference.predictor import Prediction,Limits
from nara.inference.prefix_predictor import SourceFirstPredictor,split_predictor
from nara.inference.hybrid_experiment import TimedLLM
from nara.rules.qualification import judge
from nara.experiments.config import configuration
from nara.evaluation.evaluate_dev import evaluate


def replay(record,task,predictor):
    """Compatibility for historical recovery scripts."""
    return predictor.replay_judgments(record, task)


def main():
    folder=OUT/'optimized_off';report=json.loads((folder/'report.json').read_text())
    assert report['failed_ids'] and 'recovery' not in report
    records={r['id']:r for r in read_records('data/dev.jsonl')}
    trace=[json.loads(s) for s in (folder/'trace.jsonl').read_text().splitlines()]
    table=json.loads(Path('data/항목표.json').read_text())['항목']
    schema=json.loads(Path('data/정답스키마_디코딩.json').read_text())['properties']['판정']
    table,schema,_=configuration(table,schema,'groups12',True)
    limits=Limits(**report['limits']);full=SourceFirstPredictor(None,None,table,schema,limits=limits)
    # Replay all successful records before generating any replacement.
    for r in trace:
        if not r['error']:
            restored={k:v for t in r['trace'] for k,v in replay(records[r['record_id']],t,full).items()}
            restored.update(judge(records[r['record_id']])['judgments'])
            assert restored==r['judgments']
    saved=folder/'first_pass';saved.mkdir()
    for name in ['trace.jsonl','report.json','request_timings.jsonl','model_batches.json','notice_timings.json']:
        shutil.copy2(folder/name,saved/name)
    policy={'scope':'Only groups without a final event on failed records; all successful groups replayed through original postprocessing',
            'prompt_change':False,'mode':'OFF','output_tokens':2048,'batch_size':1,'extra_predict_attempts':1,
            'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    dump(OUT/'recovery_policy.json',policy);shutil.copy2(__file__,OUT/'source/scripts/recover_hybrid200.py')
    from nara.retrieval.search import BGEEncoder,LegalRetriever
    from nara.inference.engine import VLLMModel
    import vllm
    tick=time.monotonic();retriever=LegalRetriever('model/legal_index',BGEEncoder('models/bge-m3',device='cuda'))
    stock=vllm.LLM
    def measured(**kw):return stock(disable_log_stats=False,**kw)
    vllm.LLM=measured
    try:model=VLLMModel(MODEL,thinking=True,max_num_seqs=8)
    finally:vllm.LLM=stock
    load=time.monotonic()-tick;model.thinking=False;observer=TimedLLM(model.llm);model.llm=observer
    full=SourceFirstPredictor(model,retriever,table,schema,limits=limits)
    tick=time.monotonic();repairs=[]
    for r in trace:
        if not r['error']:continue
        record=records[r['record_id']];judgments={};errors=[]
        for t in r['trace']:
            if any(e['event']=='final' for e in t['events']):
                judgments.update(replay(record,t,full));continue
            observer.set_phase(record['id'],'instant_recovery')
            worker=split_predictor(full,[t['items']]);start=time.monotonic()
            new=worker.predict([record],item_groups=[t['items']])[0]
            phase={'phase':'instant_recovery','seconds':time.monotonic()-start,**worker.metrics}
            repairs.append({'id':record['id'],'items':t['items'],'phases':[phase],'error':new.error})
            nt=safe(new)['trace'][0]
            t['events'].extend(nt['events']);t['search_rounds']+=nt['search_rounds'];t['retrieval_tokens']+=nt['retrieval_tokens']
            t['recovery']='same prompt and OFF mode; isolated failed group'
            if new.error:errors.append(new.error)
            else:judgments.update(new.judgments)
        r['error']='; '.join(errors) or None
        if not errors:judgments.update(judge(record)['judgments']);r['judgments']=judgments
    elapsed=time.monotonic()-tick
    jsonl(folder/'trace.jsonl',trace)
    oldrows=[json.loads(s) for s in (saved/'request_timings.jsonl').read_text().splitlines()]
    oldbatches=json.loads((saved/'model_batches.json').read_text())
    for r in observer.rows:r['batch']+=len(oldbatches)
    jsonl(folder/'request_timings.jsonl',oldrows+observer.rows)
    dump(folder/'model_batches.json',oldbatches+observer.batches)
    timings=json.loads((saved/'notice_timings.json').read_text());dump(folder/'notice_timings.json',timings+repairs)
    report['first_pass']={'failed_ids':report['failed_ids'],'prediction_seconds':report['prediction_seconds']}
    report['recovery']={'policy':policy,'prediction_seconds':elapsed,'separate_process_load_seconds':load,'groups':repairs,
                        'success_replay_verified_records':sum(not r['error'] for r in [json.loads(s) for s in (saved/'trace.jsonl').read_text().splitlines()])}
    report['prediction_seconds']+=elapsed;report['total_seconds']+=elapsed+load
    report['model_seconds']+=sum(p['model_seconds'] for r in repairs for p in r['phases'])
    report['retrieval_seconds']+=sum(p['retrieval_seconds'] for r in repairs for p in r['phases'])
    report['failed_ids']=[r['record_id'] for r in trace if r['error']]
    events=[e for r in trace for t in r['trace'] for e in t['events']];me=[e for e in events if e['event']=='model']
    for key in ['input_tokens','output_tokens','thinking_tokens']:report[key]=sum(e[key] for e in me)
    report['model_turns']=len(me);report['invalid_responses']=sum(e['event']=='invalid_response' for e in events)
    report['search_rounds']=sum(e['event']=='search' for e in events)
    dump(folder/'report.json',report)
    if not report['failed_ids']:
        write_submission([Prediction(**r) for r in trace],folder/'submission.csv')
        evaluate(folder,'data/dev_labels.csv','data/dev.jsonl',200)
    print(json.dumps({'stage':'recovery_complete','seconds':elapsed,'failed':report['failed_ids']}),flush=True)

if __name__=='__main__':main()
