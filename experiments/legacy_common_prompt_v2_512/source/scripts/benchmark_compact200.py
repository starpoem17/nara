"""Full dev comparison with compressed criteria; labels used only by scoring/selection."""
import argparse
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
import logging
from pathlib import Path
import shutil
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from script import read_records, write_submission
from nara.inference import Limits, Turn, compact
from nara.compact_predictor import CompactPredictor
from scripts.benchmark_grouping_time import PLANS
from scripts.evaluate_dev import evaluate

MODEL = 'models/gemma-4-26B-A4B-it-NVFP4'
SIMILARITY = 0.01  # Frozen before measuring any new labels/predictions.


def configuration(table, schema, plan, hypothesis):
    keep = [k for k in table if not hypothesis or k not in ('v2', 'v3')]
    selected = {k: table[k] for k in keep}
    spec = deepcopy(schema)
    spec['properties'] = {k: spec['properties'][k] for k in keep}
    spec['required'] = keep
    groups = [[k for k in g if k in keep] for g in PLANS[plan]]
    assert all(groups) and sorted(k for g in groups for k in g) == sorted(keep)
    return selected, spec, groups


def preflight(out, records, table, schema, limits):
    from transformers import AutoTokenizer
    from nara.vllm_model import VLLMModel
    counter = VLLMModel.__new__(VLLMModel)
    counter.tokenizer = AutoTokenizer.from_pretrained(MODEL, local_files_only=True)
    counter.max_model_len = 32768
    configs = {}
    for plan in PLANS:
        for hypothesis in (False, True):
            counter.thinking = plan == 'ungrouped'
            t, s, groups = configuration(table, schema, plan, hypothesis)
            predictor = CompactPredictor(counter, None, t, s, limits=limits)
            name = plan + ('_on' if counter.thinking else '_off') + ('_h6' if hypothesis else '')
            folder = out/name
            folder.mkdir(exist_ok=True, parents=True)
            lengths = []
            for i, group in enumerate(groups):
                messages = predictor._messages(records[0], group)
                (folder/f'prompt_{i+1:02}.txt').write_text(messages[0]['content']+'\n')
                (folder/f'schema_{i+1:02}.json').write_text(json.dumps(predictor._schema(group, True), ensure_ascii=False, indent=2)+'\n')
                assert all((f'[{key}] ' in messages[0]['content']) == (key in group) for key in table)
                if hypothesis:
                    assert 'v2' not in [k for g in groups for k in g] and 'v3' not in t
                for record in records:
                    actual = predictor._messages(record, group)
                    # Documents are neither clipped nor rewritten, including in H6 runs.
                    assert all(d['text'] in actual[1]['content'] for d in record['docs'])
                    n = counter.count_messages(actual)
                    lengths.append({'id': record['id'], 'group': i+1, 'input_tokens': n})
            config = {'groups': groups, 'thinking': counter.thinking, 'hypothesis6': hypothesis,
                      'maximum_input_tokens': max(r['input_tokens'] for r in lengths),
                      'context_failures': [r for r in lengths if r['input_tokens']+limits.output_tokens+128 >32768],
                      'initial_search_disabled_tasks': sum(r['input_tokens']+2*limits.output_tokens+256>32768 for r in lengths),
                      'lengths': lengths}
            configs[name] = config
    manifest = {'records': len(records), 'ids': [r['id'] for r in records], 'configurations': configs,
                'limits': asdict(limits), 'max_model_len': 32768, 'thinking_budget': 1024,
                'selection': {'metric': 'macro_f1', 'within_best': SIMILARITY, 'tie_break': 'shortest measured inference'},
                'compression': 'English concise criteria from nara/legal_criteria.json; full documents intact',
                'source_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in
                   [Path('scripts/benchmark_compact200.py'), Path('nara/compact_criteria.json'), Path('nara/compact_predictor.py'),
                    Path('nara/inference.py'), Path('nara/conversation.py'), Path('nara/vllm_model.py'), Path('nara/legal_criteria.json'),
                    Path('data/dev.jsonl'), Path('data/항목표.json'), Path('data/정답스키마_디코딩.json')]}}
    (out/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    for p in manifest['source_sha256']:
        dest = out/'source'/p
        dest.parent.mkdir(exist_ok=True, parents=True)
        shutil.copy2(p, dest)
    assert all(not c['context_failures'] for c in configs.values()), 'Context overflow; fix compression before running'
    print(json.dumps({'stage': 'preflight', 'records':len(records), 'max_input':max(c['maximum_input_tokens'] for c in configs.values()), 'overflow':0}), flush=True)
    return manifest


def run(out, records, table, schema, limits, model, retriever, plan, hypothesis, load_seconds, gpu):
    import torch
    t, s, groups = configuration(table, schema, plan, hypothesis)
    model.thinking = plan == 'ungrouped'
    name = plan+('_on' if model.thinking else '_off')+('_h6' if hypothesis else '')
    folder = out/name
    if (folder/'report.json').exists():
        raise ValueError(f'Refusing to overwrite {folder}')
    if not model.llm.reset_prefix_cache():
        raise RuntimeError('Prefix cache reset failed')
    torch.cuda.synchronize()
    predictor = CompactPredictor(model, retriever, t, s, limits=limits)
    print(json.dumps({'stage':'start','name':name,'tasks':len(records)*len(groups)}),flush=True)
    tick = time.monotonic()
    rule_rows = []
    if hypothesis:
        from nara.hypothesis6 import judge
        rule_tick = time.monotonic()
        rule_rows = [judge(r) for r in records]
        rule_seconds = time.monotonic()-rule_tick
    predictions = predictor.predict(records, item_groups=groups)
    if hypothesis:
        for prediction, rules in zip(predictions, rule_rows):
            if prediction.judgments is not None:
                prediction.judgments.update(rules['judgments'])
        (folder/'rules.jsonl').write_text(''.join(compact(r)+'\n' for r in rule_rows))
    torch.cuda.synchronize()
    elapsed = time.monotonic()-tick
    events = [e for r in predictions for task in r.trace for e in task['events']]
    model_events = [e for e in events if e['event']=='model']
    report = {'name': name, 'plan':plan, 'hypothesis6':hypothesis,
              'options': {'model_dir':MODEL,'max_model_len':32768,'thinking':model.thinking,'item_group_size':max(map(len,groups))},
              'limits':asdict(limits), 'gpu':gpu, 'groups':groups, 'records':len(records),
              'load_seconds':load_seconds,'prediction_seconds':elapsed,'total_seconds':elapsed+load_seconds,
              'rule_seconds':rule_seconds if hypothesis else 0,
              'failed_ids':[r.record_id for r in predictions if r.error],
              'model_turns':len(model_events),'search_rounds':sum(e['event']=='search' for e in events),
              'invalid_responses':sum(e['event']=='invalid_response' for e in events),
              'context_failures':sum(e['event']=='context_failure' for e in events),
              'input_tokens':sum(e['input_tokens'] for e in model_events),
              'output_tokens':sum(e['output_tokens'] for e in model_events),
              'thinking_tokens':sum(e['thinking_tokens'] for e in model_events),
              'predictor_metrics':predictor.metrics}
    with (folder/'trace.jsonl').open('w') as stream:
        for r in predictions:
            payload = asdict(r)
            for task in payload['trace']:
                for event in task['events']:
                    if event['event']=='model':
                        try: json.loads(event['response'])
                        except (ValueError, TypeError): event['response']='[invalid non-JSON response omitted]'
            stream.write(compact(payload)+'\n')
    (folder/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    if not report['failed_ids']:
        write_submission(predictions, folder/'submission.csv')
        evaluate(folder, 'data/dev_labels.csv','data/dev.jsonl',200)
    print(json.dumps({'stage':'complete','name':name,'seconds':elapsed,'failures':report['failed_ids']}),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='analysis/compact200')
    parser.add_argument('--stage', choices=['baseline','hypothesis'],default='baseline')
    parser.add_argument('--prepare-only',action='store_true')
    args=parser.parse_args()
    logging.basicConfig(level=logging.INFO,format='[compact200] %(message)s')
    out=Path(args.output);out.mkdir(exist_ok=True,parents=True)
    records=read_records('data/dev.jsonl')
    table=json.loads(Path('data/항목표.json').read_text())['항목']
    schema=json.loads(Path('data/정답스키마_디코딩.json').read_text())['properties']['판정']
    limits=Limits(output_tokens=2048)
    if args.stage=='baseline':
        if (out/'manifest.json').exists() and not args.prepare_only:
            manifest=json.loads((out/'manifest.json').read_text())
            for p,h in manifest['source_sha256'].items():
                assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h, f'Changed source {p}'
        else:
            preflight(out,records,table,schema,limits)
        runs=[(p,False) for p in ['groups7','groups9','groups12','ungrouped']]
    else:
        manifest=json.loads((out/'manifest.json').read_text())
        for p,h in manifest['source_sha256'].items():
            assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h, f'Changed source {p}'
        candidates=[]
        for plan in ['groups7','groups9','groups12']:
            folder=out/(plan+'_off')
            score=json.loads((folder/'evaluation.json').read_text())
            report=json.loads((folder/'report.json').read_text())
            candidates.append({'plan':plan,'macro_f1':score['macro_f1'],'seconds':report['prediction_seconds']})
        best=max(c['macro_f1'] for c in candidates)
        winner=min((c for c in candidates if best-c['macro_f1']<=SIMILARITY+1e-12),key=lambda c:c['seconds'])
        selection={'candidates':candidates,'winner':winner,'within_best':SIMILARITY}
        (out/'selection.json').write_text(json.dumps(selection,indent=2)+'\n')
        p=Path('nara/hypothesis6.py'); dest=out/'source'/p;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
        (out/'hypothesis_manifest.json').write_text(json.dumps({'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'hypothesis_sha256':hashlib.sha256(Path('user/hypothesis.md').read_bytes()).hexdigest()},indent=2)+'\n')
        print(json.dumps({'stage':'selection',**selection}),flush=True)
        runs=[(winner['plan'],True),('ungrouped',True)]
    if args.prepare_only:return
    from nara.retrieval import BGEEncoder,LegalRetriever
    from nara.vllm_model import VLLMModel
    import torch
    tick=time.monotonic()
    encoder=BGEEncoder('models/bge-m3',device='cuda')
    retriever=LegalRetriever('model/legal_index',encoder)
    model=VLLMModel(MODEL,thinking=True,max_num_seqs=8)
    torch.cuda.synchronize()
    load_seconds=time.monotonic()-tick
    simple={'type':'object','properties':{'answer':{'type':'integer'}},'required':['answer'],'additionalProperties':False}
    tick=time.monotonic()
    model.thinking=False
    model.generate([Turn(str(i),[{'role':'user','content':'2+3을 계산하고 {"answer":5}로 답하라.'}],simple,512) for i in range(8)])
    (out/(args.stage+'_runtime.json')).write_text(json.dumps({'load_seconds':load_seconds,'warmup_seconds':time.monotonic()-tick,'method':'one resident engine per stage; reset prefix cache before each configuration; single pass'},indent=2)+'\n')
    for plan,hypothesis in runs:
        run(out,records,table,schema,limits,model,retriever,plan,hypothesis,load_seconds,torch.cuda.get_device_name(0))

if __name__=='__main__':main()
