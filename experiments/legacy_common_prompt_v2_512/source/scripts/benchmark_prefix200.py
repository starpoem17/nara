"""Full200 source-first KV reuse, fixed groups12 OFF + frozen H6 rules."""
import argparse
from dataclasses import asdict
import hashlib
import json
import logging
from pathlib import Path
import shutil
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from script import read_records,write_submission
from nara.inference import Limits,Turn,compact
from nara.compact_predictor import CompactPredictor
from nara.prefix_predictor import SourceFirstPredictor,predict_notice
from nara.hypothesis6 import judge
from scripts.benchmark_compact200 import MODEL,configuration
from scripts.evaluate_dev import evaluate


class ObservedLLM:
    """Pass through unchanged generation, capturing vLLM's reported cache hits."""
    def __init__(self,llm):
        self.wrapped=llm
        self.rows=[]
        self.record_id=None
        self.phase='warmup'
        self.batches=[]
    def __getattr__(self,name):return getattr(self.wrapped,name)
    def set_phase(self,record_id,phase):self.record_id,self.phase=record_id,phase
    def generate(self,*args,**kwargs):
        start=time.monotonic()
        outputs=self.wrapped.generate(*args,**kwargs)
        self.batches.append({'record_id':self.record_id,'phase':self.phase,
                             'seconds':time.monotonic()-start,'requests':len(outputs)})
        for output in outputs:
            stats=output.metrics
            self.rows.append({'record_id':self.record_id,'phase':self.phase,
                'request_id':output.request_id,'input_tokens':len(output.prompt_token_ids),
                'cached_tokens':output.num_cached_tokens,
                'cache_creation_tokens':output.num_cache_creation_tokens,
                'output_tokens':len(output.outputs[0].token_ids),
                'finish_reason':output.outputs[0].finish_reason,
                'request_stats':asdict(stats) if stats is not None else None})
        return outputs


def lcp(rows):
    for i,values in enumerate(zip(*rows)):
        if len(set(values))!=1:return i
    return min(map(len,rows))


def predictor_with_common(common):
    """Keep the override through per-phase splitting without changing criteria."""
    class PromptPredictor(SourceFirstPredictor):
        def _messages(self, record, items):
            messages = super()._messages(record, items)
            messages[0]['content'] = common
            return messages
    return PromptPredictor


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',default='analysis/prefix200')
    parser.add_argument('--prepare-only',action='store_true')
    parser.add_argument('--batch-size',type=int,choices=(8,11),default=8,
                        help='Maximum group requests per batch and engine max_num_seqs')
    parser.add_argument('--output-tokens',type=int,default=2048)
    parser.add_argument('--common-prompt',type=Path,
                        help='Replace only the common system message; preserve group rules')
    args=parser.parse_args()
    out=Path(args.output);out.mkdir(exist_ok=True,parents=True)
    if (out/'report.json').exists() or (out/'trace.jsonl').exists():raise ValueError('Use a fresh output directory')
    logging.basicConfig(level=logging.WARNING)
    records=read_records('data/dev.jsonl')
    table=json.loads(Path('data/항목표.json').read_text())['항목']
    schema=json.loads(Path('data/정답스키마_디코딩.json').read_text())['properties']['판정']
    table,schema,groups=configuration(table,schema,'groups12',True)
    limits=Limits(output_tokens=args.output_tokens,batch_size=args.batch_size)
    predictor_type=SourceFirstPredictor
    if args.common_prompt is not None:
        common=args.common_prompt.read_text(encoding='utf-8').rstrip('\n')
        if not common.strip():raise ValueError('Common prompt must not be empty')
        predictor_type=predictor_with_common(common)
    from nara.vllm_model import VLLMModel
    from transformers import AutoTokenizer
    counter=VLLMModel.__new__(VLLMModel)
    counter.tokenizer=AutoTokenizer.from_pretrained(MODEL,local_files_only=True)
    counter.thinking=False;counter.max_model_len=32768
    predictor=predictor_type(counter,None,table,schema,limits=limits)
    original=CompactPredictor(counter,None,table,schema,limits=limits)
    counts=[]
    for record in records:
        rendered=[]
        for group in groups:
            messages=predictor._messages(record,group)
            old=original._messages(record,group)
            assert old[1]['content'] in messages[1]['content']
            assert all(d['text'] in messages[1]['content'] for d in record['docs'])
            assert all((f'[{key}] ' in messages[1]['content'])==(key in group) for key in table)
            assert '[v2]' not in messages[1]['content'] and '[v3]' not in messages[1]['content']
            tokens=counter._tokens(messages)
            assert len(tokens)+limits.output_tokens+128<=32768
            rendered.append(tokens)
        counts.append({'id':record['id'],'shared_prefix_tokens':lcp(rendered),
                       'input_tokens':[len(t) for t in rendered]})
    for i,group in enumerate(groups):
        messages=predictor._messages(records[0],group)
        suffix=messages[1]['content'][len(original._messages(records[0],group)[1]['content']):]
        (out/f'prompt_{i+1:02}.txt').write_text('[system]\n'+messages[0]['content']+'\n[user]\n{UNCHANGED_NOTICE_ID_META_AND_DOCUMENTS}'+suffix+'\n')
        (out/f'schema_{i+1:02}.json').write_text(json.dumps(predictor._schema(group,True),ensure_ascii=False,indent=2)+'\n')
    sources=['scripts/benchmark_prefix200.py','nara/prefix_predictor.py','nara/compact_predictor.py',
             'nara/compact_criteria.json','nara/inference.py','nara/conversation.py','nara/vllm_model.py','nara/hypothesis6.py',
             'scripts/benchmark_compact200.py','data/dev.jsonl','data/항목표.json','data/정답스키마_디코딩.json']
    hashes={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sources}
    if args.common_prompt is not None:
        (out/'common_prompt.txt').write_text(common+'\n',encoding='utf-8')
    frozen=json.loads(Path('analysis/compact200/rule_freeze.json').read_text())['sha256']
    assert hashes['nara/hypothesis6.py']==frozen
    manifest={'records':200,'groups':groups,'limits':asdict(limits),'thinking':False,'max_model_len':32768,
              'max_num_seqs':args.batch_size,'source_sha256':hashes,'counts':counts,'baseline':'analysis/compact200/groups12_off_h6',
              'change':'common system; unchanged notice/meta/docs before group criteria in user; first group then remaining groups, notice by notice',
              'caveat':'prompt role/order and scheduling changed together; historical baseline has no measured cache hit counts'}
    if args.batch_size==11:
        manifest.update(baseline='analysis/prefix200',
                        change='Same source-first prompts/groups/rules; batch_size and max_num_seqs 8 to 11; first group then all remaining 11, notice by notice',
                        caveat='Historical single-run comparison; batch/engine scheduling can change numerical results')
    if args.common_prompt is not None or args.output_tokens!=2048:
        manifest.update(baseline=None,
                        change='Explicit common-prompt/output-budget experiment; see parent experiment plan',
                        caveat='One pass; no automatic whole-notice recovery or prompt tuning',
                        common_prompt_path=str(args.common_prompt) if args.common_prompt else None,
                        common_prompt_sha256=hashlib.sha256(
                            predictor._messages(records[0],groups[0])[0]['content'].encode()).hexdigest())
    (out/'command.txt').write_text(' '.join(sys.argv)+'\n')
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    for p in sources:
        target=out/'source'/p;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
    print(json.dumps({'stage':'preflight','records':200,'max_input':max(max(c['input_tokens']) for c in counts),'overflow':0}),flush=True)
    if args.prepare_only:return
    from nara.retrieval import BGEEncoder,LegalRetriever
    import torch
    tick=time.monotonic()
    encoder=BGEEncoder('models/bge-m3',device='cuda')
    retriever=LegalRetriever('model/legal_index',encoder)
    # Preserve historical engine settings except the explicit concurrency limit.
    model=VLLMModel(MODEL,thinking=True,max_num_seqs=args.batch_size)
    model.thinking=False
    torch.cuda.synchronize();load=time.monotonic()-tick
    observer=ObservedLLM(model.llm);model.llm=observer
    simple={'type':'object','properties':{'answer':{'type':'integer'}},'required':['answer'],'additionalProperties':False}
    tick=time.monotonic()
    model.generate([Turn(str(i),[{'role':'user','content':'2+3을 계산하고 {"answer":5}로 답하라.'}],simple,512) for i in range(8)])
    warmup=time.monotonic()-tick
    assert model.llm.reset_prefix_cache()
    observer.rows.clear();observer.batches.clear()
    predictor=predictor_type(model,retriever,table,schema,limits=limits)
    predictions=[];timings=[];rule_rows=[]
    tick=time.monotonic();rule_seconds=0
    with (out/'trace.jsonl').open('w') as stream:
        for i,record in enumerate(records):
            start=time.monotonic()
            prediction,phase_metrics=predict_notice(predictor,record,groups,observer.set_phase)
            rstart=time.monotonic();rules=judge(record);rule_seconds+=time.monotonic()-rstart
            rule_rows.append(rules)
            if prediction.judgments is not None:prediction.judgments.update(rules['judgments'])
            timings.append({'id':record['id'],'seconds':time.monotonic()-start,'phases':phase_metrics})
            payload=asdict(prediction)
            for task in payload['trace']:
                for event in task['events']:
                    if event['event']=='model':
                        try:json.loads(event['response'])
                        except (ValueError,TypeError):event['response']='[invalid non-JSON response omitted]'
            stream.write(compact(payload)+'\n');stream.flush()
            predictions.append(prediction)
            if (i+1)%5==0:
                cached=sum(r['cached_tokens'] or 0 for r in observer.rows)
                total=sum(r['input_tokens'] for r in observer.rows)
                print(json.dumps({'stage':'progress','records':i+1,'seconds':time.monotonic()-tick,
                                  'cached_fraction':cached/total if total else 0,'failures':sum(bool(p.error) for p in predictions)}),flush=True)
    torch.cuda.synchronize();elapsed=time.monotonic()-tick
    events=[e for p in predictions for t in p.trace for e in t['events']]
    me=[e for e in events if e['event']=='model']
    cached=sum(r['cached_tokens'] or 0 for r in observer.rows)
    total=sum(r['input_tokens'] for r in observer.rows)
    phases=[p for r in timings for p in r['phases']]
    report={'name':'source_first_groups12_off_h6','options':{'model_dir':MODEL,'max_model_len':32768,'thinking':False,'item_group_size':max(map(len,groups))},
            'max_num_seqs':args.batch_size,'limits':asdict(limits),'groups':groups,'records':200,'gpu':torch.cuda.get_device_name(0),
            'prediction_seconds':elapsed,'load_seconds':load,'warmup_seconds':warmup,'total_seconds':elapsed+load,
            'rule_seconds':rule_seconds,'failed_ids':[p.record_id for p in predictions if p.error],
            'model_turns':len(me),'search_rounds':sum(e['event']=='search' for e in events),
            'invalid_responses':sum(e['event']=='invalid_response' for e in events),
            'context_failures':sum(e['event']=='context_failure' for e in events),
            'input_tokens':total,'output_tokens':sum(e['output_tokens'] for e in me),
            'thinking_tokens':sum(e['thinking_tokens'] for e in me),'cached_input_tokens':cached,
            'cached_fraction':cached/total,'cache_counts_available':all(r['cached_tokens'] is not None for r in observer.rows),
            'request_stats_available':all(r['request_stats'] is not None for r in observer.rows),
            'model_seconds':sum(p['model_seconds'] for p in phases),
            'retrieval_seconds':sum(p['retrieval_seconds'] for p in phases)}
    for name,value in [('report.json',report),('notice_timings.json',timings),('model_batches.json',observer.batches)]:
        (out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    (out/'cache_trace.jsonl').write_text(''.join(compact(r)+'\n' for r in observer.rows))
    (out/'rules.jsonl').write_text(''.join(compact(r)+'\n' for r in rule_rows))
    if not report['failed_ids']:
        write_submission(predictions,out/'submission.csv')
        evaluate(out,'data/dev_labels.csv','data/dev.jsonl',200)
    print(json.dumps({'stage':'complete',**report}),flush=True)

if __name__=='__main__':main()
