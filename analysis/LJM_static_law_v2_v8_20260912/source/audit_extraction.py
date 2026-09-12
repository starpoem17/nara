"""Label-free audit of LJM extraction and frozen prompt input isolation."""
import importlib.util,json,re,sys
from collections import Counter
from pathlib import Path
OUT=Path('analysis/ljm_static_law_v2_v8_20260912')
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
run=module('ljm_frozen_run',OUT/'source/run.py')
extractor=module('ljm_original_extractor',OUT/'source/user/LJM/v4_v7_candidate_extractor.py')
records,table,schema,limits=run.setup();cards=json.loads((OUT/'legal_cards.json').read_text());hints=json.loads((OUT/'hints.json').read_text())
base=run.predictor_type(cards,hints,'baseline')(None,None,table,schema,limits=limits)
candidate=run.predictor_type(cards,hints,'candidate')(None,None,table,schema,limits=limits)
for record in records:
 for key in run.KEYS:
  a=base._messages(record,[key]);b=candidate._messages(record,[key])
  assert a[0]==b[0] and b[1]['content'].startswith(a[1]['content']+'\n[LJM')
  tainted={**record,'labels':'SHOULD_NEVER_APPEAR_IN_PROMPT_7a93','gold':{'v2':1}}
  assert candidate._messages(tainted,[key])==b
  assert all(d['text'] in b[1]['content'] for d in record['docs'])
  assert list(candidate._schema([key],False)['properties']['judgments']['properties'])==[key]
extracted=[json.loads(x) for x in (OUT/'original/extractor.jsonl').read_text().splitlines()]
synthetic={'id':'SYNTHETIC','meta':{},'docs':[{'text':'입찰참가자격\n[지역:r1|단위=광역|광역=경기도]에 본점이 있는 업체\n법인 사업자 등록증 제출'}]}
synth=extractor.extract_candidates(synthetic)
v7_duplicates=[];bare_numbers=[];counts=Counter()
for item in extracted:
 counts.update(item['candidate_flags'])
 record=next(r for r in records if r['id']==item['id'])
 lines=extractor._lines('\n'.join(d.get('text','') for d in record.get('docs',[])))
 contexts=[extractor._context(lines,i) for i in range(len(lines))]
 txt=' '.join(ctx for ctx in contexts if not extractor.BAD_CONTEXT_RE.search(ctx) and extractor.REGION_RE.search(ctx))
 assert txt[:3000]==item['extracted']['region_text']
 tokens=re.findall(r'\[지역:[^\]]+\]',txt)
 if 'v7' in item['candidate_flags'] and not extractor.ADJACENT_RE.search(txt) and len(set(tokens))==1 and len(tokens)>1:
  v7_duplicates.append({'id':item['id'],'token_occurrences':len(tokens),'unique_tokens':len(set(tokens)),'example':tokens[0]})
 for a in item['extracted']['experience_amounts']:
  if not re.search(r'원|억|만',a['text']):bare_numbers.append({'id':item['id'],**a})
result={'prompt_pairs_checked':1400,'same_source_and_law_prefix':True,'top_level_gold_ignored':True,'single_feature_schema':True,
        'extractor_candidate_counts':dict(counts),'v7_single_unique_token_candidates':v7_duplicates,
        'amount_entries_without_currency_marker_count':len(bare_numbers),'amount_entries_without_currency_marker_examples':bare_numbers[:30],
        'synthetic_single_region':{'input':synthetic,'flags':synth['candidate_flags'],'region_text':synth['extracted']['region_text']},
        'synthetic_number_parser':extractor.parse_amounts('최근 3년간 2025년 수행실적 2건, 1억원 이상'),
        'notes':['Currency-marker absence is a contamination risk, not proof every such number is invalid.',
                 'Full pre-truncation region contexts reconstructed with unchanged original helper functions; saved prefix equality checked.',
                 'No labels read. Synthetic records are audit-only and are not used for inference or tuning.']}
run.dump(OUT/'extraction_audit.json',result)
print(json.dumps({k:v for k,v in result.items() if k not in ['amount_entries_without_currency_marker_examples']},ensure_ascii=False,indent=2))
