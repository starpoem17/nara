import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

root=Path('/home/hwajoong/projects/nara')
os.chdir(root)
out=root/'analysis/common_prompt_v2_512'
out.mkdir(exist_ok=False)
original=json.loads((root/'nara/compact_criteria.json').read_text())['common']
candidate=(root/'analysis/prompt_candidates/common_v2.txt').read_text().rstrip('\n')
(out/'original_common.txt').write_text(original+'\n')
(out/'candidate_common.txt').write_text(candidate+'\n')
sources=sorted(set(list((root/'nara').glob('*.py'))+[root/p for p in [
 'nara/compact_criteria.json','scripts/benchmark_prefix200.py','scripts/benchmark_compact200.py',
 'scripts/benchmark_grouping_time.py','scripts/evaluate_dev.py','scripts/reporting.py','script.py',
 'data/dev.jsonl','data/항목표.json','data/정답스키마_디코딩.json','pyproject.toml','uv.lock',
 'models/gemma-4-26B-A4B-it-NVFP4/config.json','models/gemma-4-26B-A4B-it-NVFP4/tokenizer.json',
 'models/gemma-4-26B-A4B-it-NVFP4/tokenizer_config.json','models/gemma-4-26B-A4B-it-NVFP4/chat_template.jinja',
 'model/legal_index/manifest.json','model/legal_index/passages.jsonl','model/legal_index/embeddings.npy']] ))
hashes={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
for p in sources:
 if p.suffix=='.py' or 'nara'==p.parent.name or p.name in ('pyproject.toml','uv.lock'):
  target=out/'source'/p.relative_to(root);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
shutil.copy2(__file__,out/'launch.py')
plan={'created_local':time.strftime('%Y-%m-%d %H:%M:%S %z'),'status':'preflight',
 'order':['original','candidate'],'passes_per_arm':1,'records':200,
 'model':'models/gemma-4-26B-A4B-it-NVFP4','thinking':False,'max_model_len':32768,
 'output_tokens':512,'batch_size':11,'schedule':'each notice: first group, then remaining 11; no cross-notice concurrency',
 'groups':'groups12; v2/v3 use unchanged H6 rules','search_rounds':2,'queries_per_round':4,
 'retries':1,'extra_recovery':False,'primary_metric':'Macro F1 over all 24 items',
 'failure_policy':'Preserve failures; no zero fill or extra inference. If incomplete, paired successful-notice scores are diagnostic only.',
 'source_sha256':hashes,'prompt_sha256':{n:hashlib.sha256(s.encode()).hexdigest() for n,s in [('original',original),('candidate',candidate)]},
 'commands':{},'processes':[]}
def save(): (out/'plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
env=dict(os.environ,HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false',MAX_JOBS='2')
plan['environment_overrides']={k:env[k] for k in ['HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','TOKENIZERS_PARALLELISM','MAX_JOBS']}
save()
for phase in ['preflight','inference']:
 for arm in plan['order']:
  for p in sources:
   assert hashlib.sha256(p.read_bytes()).hexdigest()==hashes[str(p.relative_to(root))],f'Source drift: {p}'
  cmd=[str(root/'.venv/bin/python'),'-u','scripts/benchmark_prefix200.py','--output',str(out/arm),'--batch-size','11','--output-tokens','512','--common-prompt',str(out/f'{arm}_common.txt')]
  if phase=='preflight':cmd.append('--prepare-only')
  plan['status']=f'{phase}:{arm}';plan['commands'][f'{phase}:{arm}']=cmd;save()
  print(json.dumps({'stage':phase,'arm':arm,'status':'started'}),flush=True)
  tick=time.monotonic()
  with (out/f'{arm}_{phase}.log').open('w') as log:
   result=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT)
  entry={'phase':phase,'arm':arm,'returncode':result.returncode,'process_seconds':time.monotonic()-tick}
  plan['processes'].append(entry);save();print(json.dumps(entry),flush=True)
  if result.returncode:
   plan['status']='process_failed';save();raise SystemExit(result.returncode)
 if phase=='preflight':
  a=json.loads((out/'original/manifest.json').read_text());b=json.loads((out/'candidate/manifest.json').read_text())
  for key in ['groups','limits','source_sha256','max_num_seqs','thinking','max_model_len']:assert a[key]==b[key],key
  for i in range(1,13):
   pa=(out/f'original/prompt_{i:02}.txt').read_text();pb=(out/f'candidate/prompt_{i:02}.txt').read_text()
   assert pa.split('\n[user]\n',1)[1]==pb.split('\n[user]\n',1)[1]
   assert (out/f'original/schema_{i:02}.json').read_bytes()==(out/f'candidate/schema_{i:02}.json').read_bytes()
  print(json.dumps({'stage':'preflight','status':'both_passed','max_input_original':max(max(r['input_tokens']) for r in a['counts']),'max_input_candidate':max(max(r['input_tokens']) for r in b['counts'])}),flush=True)
plan['status']='inference_complete';save()
print(json.dumps({'status':'both_complete','path':str(out)}),flush=True)
