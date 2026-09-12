"""Fixed random five-notice CoD style probe, no dev labels in prompt or selection."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import random
import re
import shutil
import time
from nara.records import read_records
from nara.inference.predictor import Limits,Turn
from nara.inference.prefix_predictor import SourceFirstPredictor
from nara.inference.engine import TokenCounter
from nara.experiments.experiment_v9_group import RecordedModel,MODEL,KEYS,dump
from nara.evaluation.reporting import write_report


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--prompt',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--repeat-at-end',action='store_true')
    args=ap.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=False)
    records=random.Random(20260912).sample(read_records('data/dev.jsonl'),5)
    instruction=args.prompt.read_text().strip()
    class FewshotPredictor(SourceFirstPredictor):
        def _messages(self,record,items):
            messages=super()._messages(record,items)
            messages[0]['content']+='\n'+instruction
            if args.repeat_at_end:
                messages[-1]['content']+='\n\n[Response instructions]\n'+instruction
            return messages
    table=json.loads(Path('data/항목표.json').read_text())['항목'];table={k:table[k] for k in KEYS}
    schema=json.loads(Path('data/정답스키마_디코딩.json').read_text())['properties']['판정']
    schema['properties']={k:schema['properties'][k] for k in KEYS};schema['required']=KEYS
    limits=Limits(batch_size=5,output_tokens=512)
    counter=TokenCounter(MODEL,thinking=True)
    predictor=FewshotPredictor(counter,None,table,schema,limits=limits)
    messages=[predictor._messages(r,KEYS) for r in records]
    for r,m in zip(records,messages):
        assert all(d['text'] in m[1]['content'] for d in r['docs'])
        assert counter.count_messages(m)+512+128<=32768
        rendered=counter.tokenizer.decode(counter.render_messages(m),skip_special_tokens=False)
        assert 'v9: Named model mandatory.' in rendered and 'v19: Issuance follows award.' in rendered
    manifest={'repeat_at_end':args.repeat_at_end,'seed':20260912,'ids':[r['id'] for r in records],'group':KEYS,'thinking':True,'thinking_budget':256,'limits':asdict(limits),'prompt_tokens':counter.count_text(instruction),'input_tokens':[counter.count_messages(m) for m in messages],
        'style_success':'First attempt: nonempty native thinking, both item labels, every nonempty line begins v9:/v19: and contains <=5 whitespace words; natural end before256; valid JSON, no retry/length stop. Five of five required.',
        'caveat':'Few-shot placement/prompt and batch5 differ from archived batch16. Five fixed random records assess format, not generalization.'}
    (out/'fewshot_prompt.txt').write_text(instruction+'\n')
    dump(out/'messages.json',messages);dump(out/'manifest.json',manifest)
    hashes={}
    for p in [Path(__file__),Path('src/experiments/experiment_v9_group.py'),*Path('src').rglob('*.py'),Path('src/inference/compact_criteria.json'),Path('data/dev.jsonl')]:
        rel=p.resolve().relative_to(Path.cwd());target=out/'source'/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target);hashes[str(rel)]=hashlib.sha256(p.read_bytes()).hexdigest()
    dump(out/'source_hashes.json',hashes)
    print(json.dumps({'stage':'preflight',**manifest}),flush=True)
    from nara.retrieval.search import BGEEncoder,LegalRetriever
    retriever=LegalRetriever('model/legal_index',BGEEncoder('models/bge-m3',device='cuda'))
    model=RecordedModel(MODEL,thinking=True,max_num_seqs=16,max_num_batched_tokens=8192,enable_chunked_prefill=True);model.raw_path=out/'raw_responses.jsonl'
    simple={'type':'object','properties':{'answer':{'type':'integer'}},'required':['answer'],'additionalProperties':False}
    model.generate([Turn('warmup',[{'role':'user','content':'Return {"answer":5}.'}],simple,512)])
    assert model.reset_prefix_cache()
    predictor=FewshotPredictor(model,retriever,table,schema,limits=limits)
    start=time.monotonic();predictions=predictor.predict(records,item_groups=[KEYS]);elapsed=time.monotonic()-start
    (out/'trace.jsonl').write_text(''.join(json.dumps(asdict(p),ensure_ascii=False)+'\n' for p in predictions))
    raw=[json.loads(l) for l in (out/'raw_responses.jsonl').read_text().splitlines()]
    start_id=model.tokenizer.convert_tokens_to_ids('<|channel>');end_id=model.tokenizer.convert_tokens_to_ids('<channel|>');label=model.tokenizer.encode('thought\n',add_special_tokens=False)
    analyses=[]
    for p in predictions:
        rows=[r for r in raw if r['record_id']==p.record_id];r=rows[0];ids=r['token_ids'];framed=start_id in ids and end_id in ids
        span=ids[ids.index(start_id)+1:ids.index(end_id)] if framed else []
        content=span[len(label):] if span[:len(label)]==label else span
        thought=model.tokenizer.decode(content,skip_special_tokens=False).strip() if framed else ''
        lines=[l.strip() for l in thought.replace('\\n','\n').splitlines() if l.strip()]
        notes_ok=bool(lines) and all(re.match(r'^v(?:9|19):',l) and len(l.split())<=5 for l in lines)
        both=all(any(l.startswith(k+':') for l in lines) for k in KEYS)
        success=framed and notes_ok and both and len(span)<256 and len(rows)==1 and not p.error and r['finish_reason']=='stop'
        analyses.append({'id':p.record_id,'success':success,'thinking':thought,'body_tokens':len(content) if framed else None,'budget_span':len(span) if framed else None,'lines':lines,'words_per_line':[len(l.split()) for l in lines], 'attempts':len(rows),'finish_reason':r['finish_reason'],'judgments':p.judgments,'error':p.error})
    result={'success':all(r['success'] for r in analyses),'successful_records':sum(r['success'] for r in analyses),'records':analyses,'seconds':elapsed}
    dump(out/'style_analysis.json',result)
    lines=['# CoD few-shot random-five style probe','',f"Success: {result['successful_records']}/5. Prediction seconds: {elapsed:.3f}.",'',manifest['style_success'],'',manifest['caveat']]
    for r in analyses:lines+=['',r['id']+f" — {r['body_tokens']} body tokens, success={r['success']}",'','```text',r['thinking'],'```']
    write_report(out/'report.md','\n'.join(lines)+'\n')
    print(json.dumps(result,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
