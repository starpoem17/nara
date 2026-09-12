"""Paper-verbatim CoD capability probe, independent of procurement pipeline."""
import json
from pathlib import Path
import re
import time
import yaml
from nara.inference.engine import VLLMModel
from nara.evaluation.reporting import write_report

OUT=Path('output/experiments/cod-plain-gemma-20260912')
MODEL='models/gemma-4-26B-A4B-it-NVFP4'
PAPER='Think step by step, but only keep a minimum draft for each thinking step, with 5 words at most. Return the answer at the end of the response after a separator ####.'
QUESTIONS=[
 ('A','Mia has 17 marbles and receives 8 more. She gives away 6. How many marbles remain?',19),
 ('B','Four boxes contain 7 pencils each. Nine pencils are used. How many pencils remain?',19),
 ('C','A ticket costs $6. Ben buys 3 tickets and pays $25. How much change does he receive?',7),
 ('D','A tank contains 48 liters. One quarter is drained, then 5 liters are added. How many liters are now in the tank?',41),
 ('E','A train travels at 60 kilometers per hour for 2 hours, then 40 kilometers per hour for 3 hours. What total distance does it travel in kilometers?',240),
]

def main():
 from vllm import SamplingParams
 from vllm.reasoning.gemma4_utils import parse_thinking_output
 OUT.mkdir(parents=True,exist_ok=False)
 config=yaml.safe_load(Path('analysis/cod_plain_gemma/gsm8k_cod.yaml').read_text())
 model=VLLMModel(MODEL,thinking=True,max_num_seqs=5,max_num_batched_tokens=8192,enable_chunked_prefill=True)
 rows=[]
 for thinking in [False,True]:
  for shot in [0,8]:
   model.thinking=thinking
   batch=[];messages=[]
   for qid,q,gold in QUESTIONS:
    payload=PAPER+'\n'
    if shot:payload+='\n'.join(config['format'].format(**ex) for ex in config['fewshot'][:shot])+'\n'
    payload+=config['format'].format(question=q,answer='')
    message=[{'role':'user','content':payload}];messages.append(message)
    batch.append({'prompt_token_ids':model.render_messages(message)})
   params=SamplingParams(temperature=0,seed=0,max_tokens=512,skip_special_tokens=False)
   start=time.monotonic();outputs=model.llm.generate(batch,sampling_params=params,use_tqdm=False)
   for (qid,q,gold),m,o in zip(QUESTIONS,messages,outputs):
    c=o.outputs[0];ids=list(c.token_ids);raw=model.tokenizer.decode(ids,skip_special_tokens=False);parsed=parse_thinking_output(raw)
    sid=model.tokenizer.convert_tokens_to_ids('<|channel>');eid=model.tokenizer.convert_tokens_to_ids('<channel|>')
    body=[]
    if sid in ids:
     end=ids.index(eid) if eid in ids else len(ids)
     span=ids[ids.index(sid)+1:end];label=model.tokenizer.encode('thought\n',add_special_tokens=False)
     body=span[len(label):] if span[:len(label)]==label else span
    answer=parsed['answer'];match=re.search(r'####\s*\$?(-?\d+(?:\.\d+)?)',answer)
    rows.append(dict(id=qid,question=q,gold=gold,thinking_on=thinking,shots=shot,messages=m,raw_output=raw,token_ids=ids,thinking=model.tokenizer.decode(body,skip_special_tokens=False),thinking_body_tokens=len(body),answer=answer,answer_tokens=model.count_text(answer),total_tokens=len(ids),correct=bool(match and float(match[1])==gold),finish_reason=c.finish_reason))
   (OUT/'results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
   print(json.dumps({'thinking':thinking,'shots':shot,'seconds':time.monotonic()-start,'outputs':[{k:r[k] for k in ['id','thinking_body_tokens','total_tokens','correct','finish_reason']} for r in rows[-5:]]}),flush=True)
 manifest={'model':MODEL,'paper_prompt':PAPER,'config_source':'https://github.com/sileix/chain-of-draft/blob/main/configs/gsm8k_cod.yaml','placement':'single user payload, following authors compose_request and llm_client','difference':'Paper has a minimum; repository has minimum. Use exact paper text with whitespace normalized. Synthetic questions independent of examples.','temperature':0,'seed':0,'max_tokens':512,'thinking_budget':None,'structured_outputs':None,'questions':QUESTIONS}
 (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
 (OUT/'src/cli.py').write_text(Path(__file__).read_text())
 (OUT/'gsm8k_cod.yaml').write_text(Path('analysis/cod_plain_gemma/gsm8k_cod.yaml').read_text())
 lines=['# Verbatim-paper CoD generic Gemma probe','','Paper wording; authors8 examples or zero-shot; single user payload. No procurement instructions/JSON schema/retrieval. Output512, no separate thinking budget. Five synthetic arithmetic questions; capability smoke check, not benchmark reproduction.']
 for r in rows:lines+=['',f"## {r['id']} thinking={r['thinking_on']} shots={r['shots']}",f"Correct={r['correct']} thinking body={r['thinking_body_tokens']} total={r['total_tokens']} finish={r['finish_reason']}",'','```text',r['raw_output'],'```']
 write_report(OUT/'report.md','\n'.join(lines)+'\n')
if __name__=='__main__':main()
