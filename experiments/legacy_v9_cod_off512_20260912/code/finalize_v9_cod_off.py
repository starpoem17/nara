"""Revalidate fenced JSON from saved outputs; never repair model judgments."""

if __name__ == "__main__":
    raise SystemExit("Archived code: create a fresh registered run; see docs/operations.md.")

import csv
from copy import deepcopy
import json
from pathlib import Path
import re
from jsonschema import validate
P=Path('output/experiments/v9-cod-off512-20260912')
def main():
 trace=[json.loads(l) for l in (P/'trace.jsonl').read_text().splitlines()]
 raw=[json.loads(l) for l in (P/'raw_responses.jsonl').read_text().splitlines()]
 records={r['id']:r for r in map(json.loads,Path('data/dev.jsonl').read_text().splitlines())}
 schema=json.loads((P/'schema.json').read_text());rows=[];recovered=[];fail=[]
 for p in trace:
  rid=p['record_id'];judgments=p['judgments'];origin='pipeline'
  if p['error']:
   judgments=None
   for index,r in reversed(list(enumerate(raw))):
    if r['record_id']!=rid or r['finish_reason']!='stop':continue
    answer=r['answer'].strip()
    if answer.startswith('```json\n') and answer.endswith('```'):answer=answer[len('```json\n'):-3].strip()
    elif answer.startswith('```\n') and answer.endswith('```'):answer=answer[4:-3].strip()
    try:d=json.loads(answer);validate(d,schema)
    except Exception:continue
    if d['action']!='final':continue
    judgments=deepcopy(d['judgments']);origin='saved_raw';recovered.append({'id':rid,'raw_index':index,'original_error':p['error']});break
  if judgments is None:fail.append(rid);continue
  row={'id':rid}
  for k,v in judgments.items():
   evidence=v['근거문구']
   if v['위반여부']==0 or (evidence and (evidence.startswith(('=','+','@')) or not any(evidence in d['text'] for d in records[rid]['docs']))):evidence=None
   row[k]=v['위반여부'];row['e'+k[1:]]=evidence or ''
  rows.append(row)
 result={'recovered_from_saved_outputs':recovered,'unresolved_ids':fail,'complete_records':len(rows),'method':'Use existing successful pipeline result; for errors, latest stopped raw output with exact schema-valid finalJSON after stripping outer code fence only. Same evidence quote filter. No changed labels, no zero filling, no new inference.'}
 (P/'revalidation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
 print(json.dumps(result,ensure_ascii=False))
 if fail:raise RuntimeError('Unresolved predictions; no full-set score')
 assert len(rows)==200
 with (P/'predictions.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=['id','v9','v19','e9','e19']);w.writeheader();w.writerows(rows)
if __name__=='__main__':main()
