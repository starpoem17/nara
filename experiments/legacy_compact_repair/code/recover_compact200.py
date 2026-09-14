"""Bounded final-only repair for failed notices, preserving first-pass artifacts."""

if __name__ == "__main__":
    raise SystemExit("Archived code: create a fresh registered run; see docs/operations.md.")

from experiments.legacy_prefix_pipeline200.code.historical_paths import source_path
import argparse
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
import logging
from pathlib import Path
import shutil
import time
from nara.records import read_records,write_submission
from nara.inference.predictor import Limits,Prediction,compact
from nara.inference.compact_predictor import CompactPredictor
from nara.experiments.config import MODEL, configuration
from nara.evaluation.evaluate_dev import evaluate

POLICY={'output_tokens':2048,'thinking_budget':1024,'search_rounds':0,'retries':1,
        'evidence_max_chars':80,'scope':'rerun every group of failed notices only; preserve full source and legal criteria',
        'instruction':'Return final JSON. Use the shortest sufficient exact evidence quote, at most 80 characters.'}

class RepairPredictor(CompactPredictor):
    def _messages(self,record,items):
        messages=super()._messages(record,items)
        messages[0]['content']+='\n'+POLICY['instruction']
        return messages


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('names',nargs='+')
    args=parser.parse_args()
    logging.basicConfig(level=logging.INFO,format='[repair] %(message)s')
    root=Path('analysis/compact200')
    manifest=json.loads((root/'manifest.json').read_text())
    for p,h in manifest['source_sha256'].items():
        assert hashlib.sha256(source_path(p).read_bytes()).hexdigest()==h, f'Changed original source {p}'
    plans=[]
    for name in args.names:
        folder=root/name
        report=json.loads((folder/'report.json').read_text())
        if report['failed_ids']:
            if 'recovery' in report:raise ValueError(f'Already repaired {name}; inspect remaining failure')
            plans.append((folder,report))
    if not plans:
        print('No failed notices to repair',flush=True);return
    (root/'recovery_policy.json').write_text(json.dumps(POLICY,indent=2)+'\n')
    dest=root/'source/scripts/recover_compact200.py';dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(__file__,dest)
    records=read_records('data/dev.jsonl')
    table=json.loads(Path('data/항목표.json').read_text())['항목']
    schema=json.loads(Path('data/정답스키마_디코딩.json').read_text())['properties']['판정']
    from nara.inference.engine import VLLMModel
    import torch
    tick=time.monotonic()
    model=VLLMModel(MODEL,thinking=True,max_num_seqs=8)
    torch.cuda.synchronize()
    load=time.monotonic()-tick
    for folder,report in plans:
        saved=folder/'first_pass';saved.mkdir()
        for filename in ['trace.jsonl','report.json']:
            shutil.copy2(folder/filename,saved/filename)
        originals=[Prediction(**json.loads(line)) for line in (folder/'trace.jsonl').read_text().splitlines()]
        failed=[r for r in records if r['id'] in report['failed_ids']]
        t,s,groups=configuration(table,schema,report['plan'],report['hypothesis6'])
        for cell in s['properties'].values():
            evidence=cell['properties']['근거문구']
            if evidence.get('type')!='null':evidence['maxLength']=80
        model.thinking=report['options']['thinking']
        assert model.llm.reset_prefix_cache()
        predictor=RepairPredictor(model,None,t,s,limits=Limits(search_rounds=0,output_tokens=2048))
        for i,g in enumerate(groups):
            (folder/f'recovery_prompt_{i+1:02}.txt').write_text(predictor._messages(failed[0],g)[0]['content']+'\n')
            (folder/f'recovery_schema_{i+1:02}.json').write_text(json.dumps(predictor._schema(g,False),ensure_ascii=False,indent=2)+'\n')
        print(json.dumps({'stage':'repair_start','name':report['name'],'ids':report['failed_ids']}),flush=True)
        tick=time.monotonic()
        repaired=predictor.predict(failed,item_groups=groups)
        if report['hypothesis6']:
            from nara.rules.qualification import judge
            for p,r in zip(repaired,failed):
                if p.judgments is not None:p.judgments.update(judge(r)['judgments'])
        torch.cuda.synchronize()
        seconds=time.monotonic()-tick
        replacements={p.record_id:p for p in repaired}
        merged=[]
        for original in originals:
            if original.record_id in replacements:
                new=replacements[original.record_id]
                for task in new.trace:
                    task['task_id']='recovery:'+task['task_id']
                    task['attempt']='recovery'
                new.trace=original.trace+new.trace
                merged.append(new)
            else:merged.append(original)
        with (folder/'trace.jsonl').open('w') as stream:
            for p in merged:
                payload=asdict(p)
                for task in payload['trace']:
                    for e in task['events']:
                        if e['event']=='model':
                            try:json.loads(e['response'])
                            except (ValueError,TypeError):e['response']='[invalid non-JSON response omitted]'
                stream.write(compact(payload)+'\n')
        original_failures=report['failed_ids']
        report['first_pass']={'failed_ids':original_failures,'prediction_seconds':report['prediction_seconds'],
                              'model_turns':report['model_turns'],'invalid_responses':report['invalid_responses']}
        report['recovery']={'policy':POLICY,'prediction_seconds':seconds,'separate_process_load_seconds':load,
                            'ids':original_failures,'predictor_metrics':predictor.metrics}
        report['prediction_seconds']+=seconds
        # Actual experimental total includes this extra process startup; deployment
        # projection uses one resident model plus measured repair inference cost.
        report['total_seconds']+=seconds+load
        report['failed_ids']=[p.record_id for p in merged if p.error]
        events=[e for p in merged for t in p.trace for e in t['events']]
        me=[e for e in events if e['event']=='model']
        report.update(model_turns=len(me),search_rounds=sum(e['event']=='search' for e in events),
            invalid_responses=sum(e['event']=='invalid_response' for e in events),
            context_failures=sum(e['event']=='context_failure' for e in events),
            input_tokens=sum(e['input_tokens'] for e in me),output_tokens=sum(e['output_tokens'] for e in me),
            thinking_tokens=sum(e['thinking_tokens'] for e in me))
        (folder/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        if not report['failed_ids']:
            write_submission(merged,folder/'submission.csv')
            evaluate(folder,'data/dev_labels.csv','data/dev.jsonl',200)
        print(json.dumps({'stage':'repair_complete','name':report['name'],'seconds':seconds,'remaining':report['failed_ids']}),flush=True)

if __name__=='__main__':main()
