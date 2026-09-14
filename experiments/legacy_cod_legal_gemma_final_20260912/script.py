"""Fictional legal reasoning CoD probe; no external law or dev labels."""
import json
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from nara.vllm_model import VLLMModel
from scripts.experiment_cod_plain import MODEL,PAPER
from scripts.reporting import write_report

OUT=Path('output/experiments/cod-legal-gemma-final-20260912')
def main():
 from vllm import SamplingParams
 from vllm.reasoning.gemma4_utils import parse_thinking_output
 OUT.mkdir(parents=True,exist_ok=False)
 data=json.loads(Path('analysis/cod_legal_gemma/cases.json').read_text())
 model=VLLMModel(MODEL,thinking=True,max_num_seqs=6,max_num_batched_tokens=8192,enable_chunked_prefill=True)
 rows=[]
 for on in [False,True]:
  for shot in [0,4]:
   model.thinking=on;batch=[];messages=[]
   for case in data['cases']:
    payload=PAPER+'\n\n'+data['scope']+'\n\n'
    for ex in data['examples'][:shot]:payload+='Q: '+ex['question']+'\nA: '+ex['answer']+'\n\n'
    payload+='Q: '+case['question']+'\nA: '
    message=[{'role':'user','content':payload}];messages.append(message);batch.append({'prompt_token_ids':model.render_messages(message)})
   outputs=model.llm.generate(batch,sampling_params=SamplingParams(temperature=0,seed=0,max_tokens=512,skip_special_tokens=False),use_tqdm=False)
   for case,message,out in zip(data['cases'],messages,outputs):
    c=out.outputs[0];ids=list(c.token_ids);raw=model.tokenizer.decode(ids,skip_special_tokens=False);parsed=parse_thinking_output(raw)
    sid=model.tokenizer.convert_tokens_to_ids('<|channel>');eid=model.tokenizer.convert_tokens_to_ids('<channel|>');body=[]
    if sid in ids:
     end=ids.index(eid) if eid in ids else len(ids);span=ids[ids.index(sid)+1:end];label=model.tokenizer.encode('thought\n',add_special_tokens=False);body=span[len(label):] if span[:len(label)]==label else span
    answer='' if sid in ids and eid not in ids else parsed['answer'];match=re.search(r'####\s*(YES|NO|UNKNOWN)\b',answer)
    draft=answer.split('####')[0].strip();lines=[l.strip() for l in draft.splitlines() if l.strip()]
    rows.append(dict(**case,thinking_on=on,shots=shot,messages=message,raw_output=raw,token_ids=ids,thinking=model.tokenizer.decode(body,skip_special_tokens=False),thinking_body_tokens=len(body),thinking_closed=eid in ids,answer=answer,total_tokens=len(ids),correct=bool(match and match[1]==case['gold']),finish_reason=c.finish_reason,answer_note_word_counts=[len(re.sub(r'^\s*(?:[-*]|\d+[.)])\s*','',l).split()) for l in lines]))
   (OUT/'results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
   print(json.dumps({'on':on,'shots':shot,'correct':sum(r['correct'] for r in rows[-6:]),'length_stops':sum(r['finish_reason']=='length' for r in rows[-6:])}),flush=True)
 (OUT/'cases.json').write_text(json.dumps(data,ensure_ascii=False,indent=2));(OUT/'script.py').write_text(Path(__file__).read_text())
 (OUT/'manifest.json').write_text(json.dumps(dict(model=MODEL,prompt=PAPER,temperature=0,seed=0,max_tokens=512,thinking_budget=None,structured_outputs=None,description='Fictional exhaustive rules and synthetic legal cases. Paper instruction exact; legal examples authored locally, not paper examples. Format probe, not real-law accuracy or dev200 evaluation.'),indent=2))
 lines=['# Fictional legal CoD Gemma probe','','Six fixed synthetic legal questions, balanced YES/NO/UNKNOWN. Four separate synthetic demonstrations. Exact paper CoD wording plus supplied-rule task definition. Output512, temperature0, no separate thinking budget, no schema.']
 for r in rows:lines+=['',f"## {r['id']} ON={r['thinking_on']} shots={r['shots']}",f"Correct={r['correct']} thinking_body={r['thinking_body_tokens']} total={r['total_tokens']} finish={r['finish_reason']}",'','```text',r['raw_output'],'```']
 write_report(OUT/'report.md','\n'.join(lines)+'\n')
if __name__=='__main__':main()
