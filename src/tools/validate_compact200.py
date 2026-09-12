"""Final artifact audit: complete IDs, rule isolation, source hashes and budgets."""
from nara.paths import source_path
import hashlib
import json
from pathlib import Path
from nara.records import read_records
from nara.evaluation.evaluate_dev import read_csv,ITEMS


def main():
    root=Path('analysis/compact200')
    manifest=json.loads((root/'manifest.json').read_text())
    for p,h in manifest['source_sha256'].items():
        assert hashlib.sha256(source_path(p).read_bytes()).hexdigest()==h,p
    frozen=json.loads((root/'rule_freeze.json').read_text())['sha256']
    assert hashlib.sha256(Path('src/rules/qualification.py').read_bytes()).hexdigest()==frozen
    assert json.loads((root/'hypothesis_manifest.json').read_text())['source_sha256']==frozen
    winner=json.loads((root/'selection.json').read_text())['winner']['plan']
    names=['groups7_off','groups9_off','groups12_off','ungrouped_on',winner+'_off_h6','ungrouped_on_h6']
    records={r['id']:r for r in read_records('data/dev.jsonl')}
    rules={r['record_id']:r for r in map(json.loads,(root/'rules_preflight.jsonl').read_text().splitlines())}
    truth=read_csv('data/dev_labels.csv')
    assert len(records)==200 and set(records)==set(truth)==set(rules)
    audit=[]
    for name in names:
        folder=root/name
        report=json.loads((folder/'report.json').read_text())
        evaluation=json.loads((folder/'evaluation.json').read_text())
        prediction=read_csv(folder/'submission.csv')
        traces=[json.loads(l) for l in (folder/'trace.jsonl').read_text().splitlines()]
        assert len(traces)==200 and {r['record_id'] for r in traces}==set(records)==set(prediction)
        assert not report['failed_ids'] and not report['context_failures']
        assert evaluation['records']==200 and not evaluation['evidence']['invalid']
        assert not any(r['error'] or r['judgments'] is None for r in traces)
        events=[e for r in traces for t in r['trace'] for e in t['events'] if e['event']=='model']
        assert all(e['input_tokens']+e['max_output_tokens']+128<=32768 for e in events)
        thinking=report['options']['thinking']
        assert all(e['thinking_budget']==(1024 if thinking else None) for e in events)
        if thinking:assert any(e['thinking_tokens']>0 for e in events)
        else:assert not any(e['thinking_tokens'] for e in events)
        for r in traces:
            assert set(r['judgments'])==set(ITEMS)
            assert any(e['event']=='final' for t in r['trace'] for e in t['events'])
            for key in ITEMS:
                assert int(prediction[r['record_id']][key])==r['judgments'][key]['위반여부']
            if report['hypothesis6']:
                assert all(not set(t['items']) & {'v2','v3'} for t in r['trace'])
                for key in ['v2','v3']:
                    assert r['judgments'][key]==rules[r['record_id']]['judgments'][key]
        for i,group in enumerate(report['groups']):
            prompt=(folder/f'prompt_{i+1:02}.txt').read_text()
            assert all((f'[{k}] ' in prompt)==(k in group) for k in ITEMS)
            spec=json.loads((folder/f'schema_{i+1:02}.json').read_text())
            final=next(s for s in spec['anyOf'] if s['properties']['action']['const']=='final')
            assert set(final['properties']['judgments']['required'])==set(group)
        audit.append({'name':name,'complete_records':len(traces),'model_turns':len(events),
                      'maximum_input_tokens':max(e['input_tokens'] for e in events),
                      'maximum_reserved_context':max(e['input_tokens']+e['max_output_tokens']+128 for e in events),
                      'output_budgets':sorted({e['max_output_tokens'] for e in events}),
                      'thinking_enabled':thinking,'mode_verified':True,'rule_isolation_verified':True if report['hypothesis6'] else None})
    result={'status':'passed','unit_tests_pre_run':35,'source_hashes_unchanged':True,
            'rule_sha256':frozen,'records_per_run':200,'runs':audit}
    (root/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
