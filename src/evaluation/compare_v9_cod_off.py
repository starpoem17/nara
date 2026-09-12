"""Compare OFF CoD with frozen historical controls without rerunning them."""
import csv
import json
import re
from pathlib import Path
from nara.experiments.experiment_v9_group import score
from nara.evaluation.reporting import write_report
ROOT=Path('output/experiments');OUT=ROOT/'v9-cod-off512-20260912'
ARMS={'original12_off':('engine-refactor-after-20260911','submission.csv'),'direct_off':('v9-group512-20260912','predictions.csv'),'basic_on':('v9-thinking512-20260912','predictions.csv'),'cod_on':('v9-cod512-20260912','predictions.csv'),'cod_off':('v9-cod-off512-20260912','predictions.csv'),'cod_off_replay':('v9-cod-off512-20260912','predictions_first_valid.csv')}
def main():
 truth={r['id']:r for r in csv.DictReader(open('data/dev_labels.csv'))};all_rows={};summary={}
 for name,(folder,file) in ARMS.items():
  p=ROOT/folder;rows={r['id']:r for r in csv.DictReader(open(p/file))};assert set(rows)==set(truth);all_rows[name]=rows
  metrics={k:{**score(truth,rows,k),'positive_missing_evidence':sum(int(r[k])==1 and not r['e'+k[1:]] for r in rows.values())} for k in ['v9','v19']}
  runtime=json.loads((p/'report.json').read_text()) if name not in ('original12_off','cod_off_replay') else None
  summary[name]={'metrics':metrics,'runtime':runtime}
 raw=[json.loads(l) for l in (OUT/'raw_responses.jsonl').read_text().splitlines()];first={}
 for r in raw:first.setdefault(r['record_id'],r)
 notes=[r['note_tokens'] for r in first.values()];assert len(first)==200
 changes=[]
 for i in truth:
  for k in ['v9','v19']:
   before=all_rows['direct_off'][i];after=all_rows['cod_off'][i]
   if before[k]!=after[k]:changes.append(dict(id=i,item=k,gold=int(truth[i][k]),before=int(before[k]),after=int(after[k]),evidence=after['e'+k[1:]],notes=first[i]['notes']))
 strict_short=sum(bool(r['notes']) and all(len(re.sub(r'^\s*(?:[-*]|\d+[.)])\s*','',l).split())<=5 for l in r['notes'].splitlines() if l.strip()) for r in first.values())
 stats=dict(strict_short_notes=strict_short,first_responses=200,separator_present=sum(r['separator_present'] for r in first.values()),nonempty_notes=sum(bool(r['notes']) for r in first.values()),mean_note_tokens=sum(notes)/200,median_note_tokens=sorted(notes)[100],max_note_tokens=max(notes),mean_first_output_tokens=sum(r['output_tokens'] for r in first.values())/200)
 (OUT/'all_comparison.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));(OUT/'note_statistics.json').write_text(json.dumps(stats,indent=2));(OUT/'changes_vs_direct.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2))
 lines=['# OFF CoD dev200 comparison','','Historical results reused. Same full200 records, group4 v9/v19 only. Current v9 criteria retained. New OFF CoD adds3 synthetic examples and unconstrained notes+####+JSON. Total512 and batch16; same internal retry+one outer recovery. Original12group baseline used old v9/output2048. This is a bundled candidate comparison, not an isolated CoD/few-shot/grammar ablation.','','| Arm | Item | F1 | Precision | Recall | TP | FP | FN | Missing quotes among positives |','|---|---|---|---|---|---|---|---|---|']
 for arm,d in summary.items():
  for k,m in d['metrics'].items():lines.append(f"| {arm} | {k} | {m['f1']:.4f} | {m['precision']:.4f} | {m['recall']:.4f} | {m['tp']} | {m['fp']} | {m['fn']} | {m['positive_missing_evidence']} |")
 lines+=['','Saved-output revalidation: '+(OUT/'revalidation.json').read_text(),'', 'Runtime includes retries, excludes load; historical single-run timing not paired latency test.','',json.dumps({k:d['runtime'] for k,d in summary.items()},ensure_ascii=False),'','First response notes: '+json.dumps(stats),'','Changed predictions vs directOFF:']
 for c in changes:lines+=['',json.dumps(c,ensure_ascii=False)]
 write_report(OUT/'all_comparison.md','\n'.join(lines)+'\n');print(json.dumps({'summary':summary,'notes':stats,'changes':changes},ensure_ascii=False))
if __name__=='__main__':main()
