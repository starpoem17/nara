"""Report only observed phase sensitivity; do not attribute a specific GPU kernel."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vllm.reasoning.gemma4_utils import parse_thinking_output
ROOT=Path('analysis/prefill_decode_probe')
def read(p):return json.loads(p.read_text())
def firstdiff(a,b):return next((i for i,(x,y) in enumerate(zip(a,b)) if x!=y),min(len(a),len(b)))
def difference(a,b):
    common=set(a)&set(b)
    return max((abs(a[k]['logprob']-b[k]['logprob']) for k in common),default=None)
def main():
    a={r['id']:r for r in read(ROOT/'barrier.json')['raw']};b={r['id']:r for r in read(ROOT/'continuous.json')['raw']}
    changes=[]
    for rid,x in a.items():
        y=b[rid];u=json.loads(parse_thinking_output(x['text'])['answer']);v=json.loads(parse_thinking_output(y['text'])['answer'])
        assert u['action']==v['action']=='final'
        changes.append({'id':rid,'raw_changed':x['tokens']!=y['tokens'],'first_divergence_0based':firstdiff(x['tokens'],y['tokens']) if x['tokens']!=y['tokens'] else None,
            'label_flips':sum(u['judgments'][k]['위반여부']!=v['judgments'][k]['위반여부'] for k in u['judgments'])})
    rows=read(ROOT/'probes.json');pref=[];dec=[];repeat=[]
    for target in read(ROOT/'targets.json'):
        rid=target['id']
        for rep in range(2):
            ps=[next(r for r in rows if r['test']=='prefill' and r['id']==rid and r['repeat']==rep and r['batch']==batch) for batch in [False,True]]
            assert ps[0]['input_hash']==ps[1]['input_hash']
            pref.append({'id':rid,'repeat':rep,'top1_changed':ps[0]['tokens']!=ps[1]['tokens'],'solo_token':ps[0]['tokens'][0],'batch_token':ps[1]['tokens'][0],
                'max_common_top10_logprob_difference':difference(ps[0]['logprobs'][0],ps[1]['logprobs'][0])})
            ds=[next(r for r in rows if r['test']=='decode' and r['id']==rid and r['repeat']==rep and r['inject']==inject) for inject in [False,True]]
            assert ds[0]['input_hash']==ds[1]['input_hash']
            at=firstdiff(ds[0]['tokens'],ds[1]['tokens']);n=min(len(ds[0]['tokens']),len(ds[1]['tokens']))
            initial=difference(ds[0]['logprobs'][0],ds[1]['logprobs'][0]);point=[]
            # At index i, history is common iff i <= first token divergence.
            for i in range(min(at+1,n)):
                point.append({'output_index':i,'logprob_difference':difference(ds[0]['logprobs'][i],ds[1]['logprobs'][i])})
            dec.append({'id':rid,'repeat':rep,'initial_top1_equal':ds[0]['tokens'][0]==ds[1]['tokens'][0],
                'initial_top10_difference':initial,'injection_after_tokens':ds[1]['injection']['after_tokens'],
                'tokens_changed':ds[0]['tokens']!=ds[1]['tokens'],'first_divergence_0based':at if at<n else None,
                'same_history_logprob_comparison':point})
        for test,field in [('prefill','batch'),('decode','inject')]:
            for condition in [False,True]:
                pair=[next(r for r in rows if r['test']==test and r['id']==rid and r['repeat']==rep and r[field]==condition) for rep in [0,1]]
                repeat.append({'id':rid,'test':test,'condition':condition,'tokens_identical':pair[0]['tokens']==pair[1]['tokens'],
                    'logprobs_identical':pair[0]['logprobs']==pair[1]['logprobs']})
    result={'test1':{'records':24,'raw_changed_records':sum(r['raw_changed'] for r in changes),'label_flips':sum(r['label_flips'] for r in changes),'per_record':changes},
        'prefill':pref,'decode':dec,'repeat':repeat,
        'interpretation':'Prefill probes rebuild the complete identical token history and generate just one token. Decode probes begin alone and add background only after first target output; compare only common histories. These test phase sensitivity, not a replay of original internal KV tensors or a proof of one specific kernel cause.'}
    (ROOT/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
