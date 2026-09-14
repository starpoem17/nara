"""Compare fixed-budget ON/CoD thinking, labels and exact-source evidence."""
import csv
import hashlib
import json
from pathlib import Path
import re
import sys
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.experiment_v9_group import score, KEYS, MODEL
from scripts.reporting import write_report
from nara.vllm_model import TokenCounter

ROOT = Path('output/experiments')
RUNS = {'off': ROOT/'v9-group512-20260912', 'on': ROOT/'v9-thinking512-20260912', 'cod': ROOT/'v9-cod512-20260912'}


def distribution(values):
    a=np.array(values)
    return {'n':len(a),'mean':float(a.mean()),'min':int(a.min()),'median':float(np.median(a)),
            'p90':float(np.percentile(a,90)),'p95':float(np.percentile(a,95)),'max':int(a.max()),'sum':int(a.sum())}


def main():
    out=ROOT/'v9-cod-comparison-20260912';out.mkdir(exist_ok=True)
    counter=TokenCounter(MODEL,thinking=True);tokenizer=counter.tokenizer
    start_id=tokenizer.convert_tokens_to_ids('<|channel>');end_id=tokenizer.convert_tokens_to_ids('<channel|>')
    truth={r['id']:r for r in csv.DictReader(open('data/dev_labels.csv'))}
    docs={r['id']:r['docs'] for r in map(json.loads,Path('data/dev.jsonl').read_text().splitlines())}
    result={}; summaries={}; predictions={};all_details={}
    for name,folder in RUNS.items():
        report=json.loads((folder/'report.json').read_text())
        if report['failed_ids']:raise ValueError(f'{name}: unresolved predictions')
        predicted={r['id']:r for r in csv.DictReader(open(folder/'predictions.csv'))};predictions[name]=predicted
        assert set(predicted)==set(truth)
        result[name]={'scores':{k:score(truth,predicted,k) for k in KEYS},'report':report,
                      'evidence':{k:{'positive':sum(r[k]=='1' for r in predicted.values()),
                                    'positive_missing':sum(r[k]=='1' and not r['e'+k[1:]] for r in predicted.values())} for k in KEYS}}
        for i,r in predicted.items():
            for k in KEYS:
                quote=r['e'+k[1:]]
                assert not quote or (r[k]=='1' and len(quote)<=500 and any(quote in d['text'] for d in docs[i]))
        if name=='off':continue
        raw=[json.loads(l) for l in (folder/'raw_responses.jsonl').read_text().splitlines()]
        attempts=[json.loads(l) for l in (folder/'attempts.jsonl').read_text().splitlines()]
        events=[e for r in attempts for t in r['trace'] for e in t['events'] if e['event']=='model']
        assert len(raw)==len(events)
        assert all(t['items']==KEYS for r in attempts for t in r['trace'])
        assert all(r['max_tokens']==512 and r['thinking_budget'] in (128,256) for r in raw)
        details=[];seen=set()
        for r in raw:
            ids=r['token_ids'];assert len(ids)<=512
            first=r['record_id'] not in seen;seen.add(r['record_id'])
            has_start=start_id in ids;has_end=end_id in ids
            start=ids.index(start_id)+1 if has_start else 0
            end=ids.index(end_id,start) if has_end else len(ids)
            span=ids[start:end]
            text=r['thinking'] or ''
            # Remove thought-channel label tokens from actual generated content span.
            label=tokenizer.encode('thought\n',add_special_tokens=False)
            content=span[len(label):] if span[:len(label)]==label else span
            framed = has_start and has_end
            text = tokenizer.decode(content, skip_special_tokens=False).strip() if framed else ''
            lines=[s.strip() for s in text.replace('\\n','\n').splitlines() if s.strip()]
            cleaned=[re.sub(r'^\s*(?:[-*#]+|\d+[.)])\s*','',s) for s in lines]
            words=[len(s.split()) for s in cleaned if s.strip()]
            detail=dict(id=r['record_id'],first_response=first,thinking_content_tokens=len(content) if framed else None,
                        budget_counted_span_tokens=len(span) if framed else None,budget=r['thinking_budget'],
                        at_budget_boundary=has_end and len(span)>=r['thinking_budget'],
                        end_marker=has_end,framed=framed,nonempty_lines=len(lines),line_words=words,
                        all_lines_le5=bool(words) and max(words)<=5,
                        korean_chars=len(re.findall('[가-힣]',text)),total_tokens=len(ids),
                        finish_reason=r['finish_reason'],thinking=text,answer=r['answer'])
            details.append(detail)
        assert seen==set(truth)
        primary=[d for d in details if d['first_response']]
        assert len(primary)==200
        words=[w for d in primary for w in d['line_words']]
        summary={'first_response':{'thinking_content_tokens':distribution([d['thinking_content_tokens'] for d in primary if d['framed']]),
                  'total_tokens':distribution([d['total_tokens'] for d in primary]),
                  'at_budget_boundary':sum(d['at_budget_boundary'] for d in primary),
                  'empty_thinking':sum(d['framed'] and not d['thinking'] for d in primary),
                  'unframed_outputs':sum(not d['framed'] for d in primary),
                  'line_words':distribution(words) if words else None,
                  'lines_le5_fraction':sum(w<=5 for w in words)/len(words) if words else None,
                  'all_lines_le5_records':sum(d['all_lines_le5'] for d in primary),
                  'records_with_korean':sum(d['korean_chars']>0 for d in primary),
                  'count_at_or_below':{str(b):sum(d['framed'] and d['budget_counted_span_tokens']<=b for d in primary) for b in [64,96,128,192,256]}},
                  'all_attempts':{'n':len(details),'thinking_content_tokens':distribution([d['thinking_content_tokens'] for d in details if d['framed']]),'at_budget_boundary':sum(d['at_budget_boundary'] for d in details)}}
        summaries[name]=summary;all_details[name]=details
    on=json.loads((RUNS['on']/'manifest.json').read_text());cod=json.loads((RUNS['cod']/'manifest.json').read_text())
    assert on['source_sha256']==cod['source_sha256'] and on['limits']==cod['limits']
    assert all(b['input_tokens']-a['input_tokens']==42 for a,b in zip(on['counts'],cod['counts']))
    changed=[{'id':i,'item':k,'gold':int(truth[i][k]),**{name:int(p[i][k]) for name,p in predictions.items()},
              'evidence':{name:p[i]['e'+k[1:]] for name,p in predictions.items()}}
             for i in truth for k in KEYS if len({p[i][k] for p in predictions.values()})>1]
    payload={'scores':result,'thinking':summaries,'validation':{'matched_on_cod_sources_limits':True,'all_input_token_deltas':42,'all_record_ids_and_evidence_verified':True},
             'method':'First-response statistics isolate style from retries. Budget boundary includes thought channel label; content token counts use original generated IDs excluding label and delimiters. Outputs lacking channel delimiters are excluded from thinking-length distributions, not counted as thinking. Empty channels have zero body tokens even if the runtime parser returns the thought label. Boundary is inferred from token positions, not an engine forced-stop flag. Nonempty lines are a descriptive proxy for steps; whitespace words, bullet/number prefix removed. Not a semantic step-compliance proof.'}
    for filename,data in [('comparison.json',payload),('thinking_details.json',all_details),('changed_judgments.json',changed)]:
        (out/filename).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    lines=['# v9/v19: OFF vs Thinking ON vs CoD ON', '', 'Same current feature criteria and dev200. Both new ON arms use total512 / thinking256, batch16; CoD adds42 input tokens. OFF reused. Zero-shot adaptation; not a reproduction of paper few-shot experiments.', '', '| Mode | Item | F1 | Precision | Recall | TP | FP | FN |','|---|---|---:|---:|---:|---:|---:|---:|']
    for name,r in result.items():
        for k,m in r['scores'].items():lines.append(f"| {name} | {k} | {m['f1']:.4f} | {m['precision']:.4f} | {m['recall']:.4f} | {m['tp']} | {m['fp']} | {m['fn']} |")
    lines+=['','Thinking summaries:','', '```json',json.dumps(summaries,ensure_ascii=False,indent=2),'```','',payload['method']]
    write_report(out/'comparison.md','\n'.join(lines)+'\n')
    print(json.dumps(payload,ensure_ascii=False))


if __name__=='__main__':main()
