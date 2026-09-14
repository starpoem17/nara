
if __name__ == "__main__":
    raise SystemExit("Archived code: create a fresh registered run; see docs/operations.md.")

from experiments.legacy_prefix_pipeline200.code.historical_paths import source_path
from copy import deepcopy
from pathlib import Path
import hashlib,json,shutil
from nara.inference.predictor import Prediction
from nara.records import write_submission

base=Path('analysis/gemma4_rag_dev200_thinking')
retry=Path('analysis/gemma4_thinking_recovery/output4096')
out=Path('analysis/gemma4_rag_dev200_thinking_recovered')
out.mkdir(exist_ok=False)
a=[json.loads(l) for l in (base/'trace.jsonl').read_text().splitlines()]
b=[json.loads(l) for l in (retry/'trace.jsonl').read_text().splitlines()]
failed={r['record_id'] for r in a if r['error']}
assert failed=={r['record_id'] for r in b}=={'PPS-DEV-191'}
assert all(r['error'] is None and r['judgments'] is not None for r in b)
manifest=json.loads((base/'manifest.json').read_text())
for path,h in manifest['sha256'].items():
    assert hashlib.sha256(source_path(path).read_bytes()).hexdigest()==h,path
replacement={r['record_id']:r for r in b}
combined=[]
for row in a:
    r=deepcopy(row)
    if r['record_id'] in failed:
        recovered=replacement[r['record_id']]
        r['judgments'],r['error']=recovered['judgments'],None
        r['trace'][0]['events'] += [{'event':'recovery_restart','run':str(retry),'max_output_tokens':4096}]+recovered['trace'][0]['events']
        r['trace'][0]['search_rounds']+=recovered['trace'][0]['search_rounds']
        r['trace'][0]['retrieval_tokens']+=recovered['trace'][0]['retrieval_tokens']
    else:
        assert r['judgments']==row['judgments']
    for task in r['trace']:
        for event in task['events']:
            if event['event']=='model' and event.get('response') and not event['response'].lstrip().startswith('{'):
                # An unclosed thinking block is not a public model answer.
                text=event['response'];event['response']=''
                event['unparsed_response_redacted']=True
                event['unparsed_response_sha256']=hashlib.sha256(text.encode()).hexdigest()
                event['unparsed_response_chars']=len(text)
    combined.append(r)
(out/'trace.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in combined))
write_submission([Prediction(**r) for r in combined],out/'submission.csv')
ra=json.loads((base/'report.json').read_text());rb=json.loads((retry/'report.json').read_text())
report=deepcopy(ra);report['failed']=0;report['options']['output_dir']=str(out)
for key in ['load_seconds','total_seconds','model_seconds','retrieval_seconds','model_batches','retrieval_batches','input_tokens','output_tokens','search_rounds','search_queries','prediction_seconds']:
    report[key]=ra[key]+rb[key]
report['recovery']={'initial_run':str(base),'initial_failed':ra['failed'],'initial_seconds':ra['total_seconds'],'retry_run':str(retry),'record_ids':sorted(failed),'retry_options':rb['options'],'retry_seconds':rb['total_seconds'],'merged_without_rerunning_other_199':True}
(out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
for name in ['context_check.json','system_prompt.txt','verification.txt']:
    shutil.copy2(base/name,out/name)
shutil.copytree(base/'source',out/'source')
manifest['recovery']=report['recovery'];manifest['sha256'][str(Path(__file__))]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
shutil.copy2(__file__,out/'source/merge_thinking_recovery.py')
(out/'command.txt').write_text((base/'command.txt').read_text()+(retry.parent/'command.txt').read_text()+'uv run --locked python -m experiments.legacy_gemma4_thinking_recovery.code.merge_thinking_recovery\n')
with (out/'verification.txt').open('a') as f:
    f.write('Initial thinking run: 199/200 valid; PPS-DEV-191 failed output length after retry. Recovered only that ID with max output 4096 and same thinking budget 1024. All other 199 judgments unchanged. Initial and recovery model events retained; unparsed non-JSON text redacted in merged trace. Original raw run preserved separately.\n')
print('Merged 199 unchanged predictions and one recovered prediction; all model attempts retained.')
