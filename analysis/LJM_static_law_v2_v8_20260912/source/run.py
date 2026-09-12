"""Frozen LJM candidate experiment. prepare/run never load dev labels; score is separate."""
from __future__ import annotations
import argparse, csv, gzip, hashlib, importlib.util, json, shutil, sys, time
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
from nara.records import read_records
from nara.inference.predictor import Predictor, Limits, Turn
from nara.inference.prefix_predictor import predict_notice
from nara.inference.engine import TokenCounter, VLLMModel

ROOT = Path.cwd()
KEYS = [f'v{i}' for i in range(2, 9)]
MODEL = 'models/gemma-4-26B-A4B-it-NVFP4'
OUT = ROOT / 'analysis/ljm_static_law_v2_v8_20260912'
COMMON = '''나라장터 입찰공고의 지정 검토 항목을 판정한다. 공고 원문, 메타데이터, 아래 제공 법령만 사용한다. 검색 도구는 없으며 검색을 요청하지 않는다.
적용법·업무·계약방법과 금액을 먼저 확인하고, 실제 필수 참가자격과 허용 예외를 대조하라. 평가 배점, 실적 작성 양식, 제출처·납품 장소, 계약 이후 의무를 참가자격으로 혼동하지 말라. 본문과 메타데이터가 충돌하면 실제 공고의 조건을 확인하라. 예산과 추정가격을 구별하고 확인되지 않은 부가세 환산을 하지 말라.
익명 지역 토큰의 단위=기초/광역을 구별한다. 토큰 반복은 서로 다른 지역의 증거가 아니며 익명 토큰만으로 인접성을 추측하지 않는다. 제공되지 않은 사실·예외·고시금액을 만들어 판단하지 말라.
추출 힌트가 제공되면 오류·누락 가능한 참고자료로만 사용한다. 후보 플래그는 위반 정답이 아니고 미탐지는 비위반의 증거가 아니다. 모든 원문을 검토하고 제공 법령에 따라 독립적으로 최종 판정하라.
지정된 JSON 형식으로 action=final, judgments의 해당 항목에 위반여부 0 또는 1과 근거문구를 출력한다. 양성 근거는 공고의 한 문서에서 그대로 인용한 500자 이내 부분문자열이어야 한다. 법령이나 추출 요약을 근거문구로 인용하지 말라. 비위반 근거는 null이다.'''

def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def jsonl(path, rows):
    path.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); sys.modules[name] = mod; spec.loader.exec_module(mod)
    return mod

def legal_cards():
    draft = json.loads(Path('src/inference/legal_criteria.json').read_text())
    paths = {key: Path(draft['sources'][key]['path']) for key in ['국가규칙','지방규칙','국가령','지방령','정부집행','지방집행','국가고시']}
    texts = {k:p.read_text() for k,p in paths.items()}
    def article(k, n):
        s = texts[k]; a = s.index(f'제{n}조('); b = s.find('\n제', a+4)
        return s[a:b if b >= 0 else None]
    def matching(s, needle): return next(line.strip() for line in s.splitlines() if needle in line)
    nr, lr, gov = article('국가규칙',25), article('지방규칙',25), article('정부집행',5)
    local = texts['지방집행'].splitlines()
    amounts = '국가고시 제1호 가목: 국가계약법 제4조 고시금액은 물품·용역 2억3천만원, 공사 88억원. 제2호 가목의 공기업·준정부기관 국제입찰 7억1천만원과 혼동하지 않는다.'
    region = '지역제한 상한 T: 국가 일반 물품·용역 2.3억원, 일반공사 88억원/전문·기타공사 10억원. 지방 일반 물품·용역은 세종시·시군구 5억원, 그 외 시·도는 행안부 고시액(동봉 자료에서 수치 미확인). 지방 건설기술·설계감리·엔지니어링 용역 3.3억원, 안전점검·정밀안전진단 1.5억원, 종합공사 150억원/전문·기타공사 10억원. 확인되지 않은 행안부 고시액을 국가 고시액이나 5억원으로 대체하지 않는다.'
    excerpts = {
        'v2': [('정부집행 제5조제1항', gov.splitlines()[0]),
               ('지방령 제20조제1항제5호', matching(article('지방령',20),'5. 특수한 기술')),
               ('지방집행 제5장 제3절 1-나-6)', '\n'.join(local[2609:2611]))],
        'v3': [('국가규칙 제25조제2항제1호 나목', matching(nr,'나. 공사ㆍ제조')),
               ('지방규칙 제25조제2항제1호 나목', matching(lr,'나. 공사ㆍ제조')),
               ('지방집행 제1장 제1절 7-나-16)', matching(texts['지방집행'],'16) 규모'))],
        'v4': [('정부집행 제5조제4항제2·3호', '\n'.join([matching(gov,'2. 특정한 명칭'), matching(gov,'3. 특정기관')])),
               ('지방집행 제1장 제1절 7-나-5·6)', '\n'.join(local[109:111]))],
        'v5': [('국가규칙 제24조제2항제2호', matching(article('국가규칙',24),'2. 물품의 제조')),
               ('지방규칙 제24조제2호 나목', matching(article('지방규칙',24),'나. 가목의')),
               ('지방집행 제4장 지역제한 표', local[2449])],
        'v6': [('정부집행 제5조제4항제6호', matching(gov,'6. 지역제한')),
               ('지방집행 제5장 제3절 1-나-3)', '\n'.join(local[2596:2599]))],
        'v7': [('국가규칙 제25조제3항 단서 각 호', '\n'.join([matching(nr,'1. 공사 등의 현장'),matching(nr,'2. 공사 등의 현장')])),
               ('지방규칙 제25조제3항 단서 각 호', '\n'.join([matching(lr,'1. 공사 등의 현장'),matching(lr,'2. 인접 시'),matching(lr,'3. 해당 지역')])),
               ('지방집행 제5장 제3절 1-나-3) 나·라', '\n'.join([local[2598],local[2602]]))],
        'v8': [('국가규칙 제25조제5항',matching(nr,'⑤각 중앙관서')),
               ('지방규칙 제25조제7항',matching(lr,'⑦ 지방자치단체')),
               ('지방집행 제5장 제3절 1-나-6)', '\n'.join(local[2609:2611]))],
    }
    cards = {}
    for key in KEYS:
        row = deepcopy(draft['items'][key])
        if key == 'v5': row['review_note'] = '행안부 고시액 미확인 분기는 제공 자료로 확인 가능한 범위에서만 판단한다. 외부 검색이나 임의 금액 대입은 하지 않는다.'
        card = f"[{key}] {row['name']}\n적용: {row['applies_if']}\n판정: {row['violation_if']}\n예외: {row['exceptions']}\n근거 조문: {'; '.join(row['references'])}\n"
        if row.get('review_note'): card += '실험 해석: '+row['review_note']+'\n'
        card += (region if key in ['v5','v6','v7'] else amounts)+'\n'
        if key == 'v4': card += '이 실험에서 물품·용역의 실적제한 고시금액은 국가계약법 제4조 기준 2.3억원으로 비교한다. 지역제한용 지방 5억원을 실적 기준으로 사용하지 않는다.\n'
        card += '\n'.join(f'배포 원문 발췌 ({ref}):\n{text}' for ref,text in excerpts[key])
        cards[key] = card
    return cards, {str(p):sha(p) for p in paths.values()}

def original_candidates(records):
    work = OUT/'original'; work.mkdir(exist_ok=True)
    # Redirect only input/output globals. User-owned source and all detection rules stay unchanged.
    scanner = load_module('ljm_scanner', 'user/LJM/scan_candidates.py')
    packed = work/'input.jsonl.gz'
    with gzip.open(packed,'wt',encoding='utf-8') as f:
        for r in records: f.write(json.dumps(r,ensure_ascii=False)+'\n')
    scanner.ROOT = work; scanner.path = packed
    tick = time.monotonic(); scanner.main(); scan_seconds = time.monotonic()-tick
    scans = {r['id']:r for r in csv.DictReader((work/'candidate_v2_v8.csv').open(encoding='utf-8-sig'))}
    extractor = load_module('ljm_extractor', 'user/LJM/v4_v7_candidate_extractor.py')
    tick = time.monotonic(); extracted = {r['id']:extractor.extract_candidates(r) for r in records}; ext_seconds = time.monotonic()-tick
    jsonl(work/'extractor.jsonl',extracted.values())
    hints = {}; candidates = []
    for r in records:
        scan = scans.get(r['id'],{}); ext = extracted[r['id']]
        flags = scan.get('flags','').split(',')
        per = {}
        for key in KEYS:
            payload = {'scan_candidate':key in flags}
            contexts = []
            if key in ['v2','v3','v4','v8'] and scan.get('evidence'):
                contexts.extend(scan['evidence'].split(' || '))
            if key in ['v4','v5','v6','v7']:
                payload['extractor_candidate'] = key in ext['candidate_flags']
                kinds = ['experience','institution'] if key == 'v4' else ['region']
                for kind in kinds:
                    contexts.extend(x['context'] for x in ext['evidence'][kind])
                payload['qualification_hint'] = ext['extracted']['has_qualification_experience' if key=='v4' else 'has_qualification_region']
            contexts = list(dict.fromkeys(contexts))
            # Frozen presentation budget; preserve complete raw extraction separately.
            budget = 1600; displayed = []
            for ctx in contexts:
                if budget <= 0: break
                part = ctx[:min(500,budget)]; displayed.append(part); budget -= len(part)
            payload['contexts'] = displayed
            payload['context_count_before_display_limit'] = len(contexts)
            payload['display_is_excerpt'] = True
            per[key] = payload
        hints[r['id']] = per
        candidates.append({'id':r['id'],'scan':{k:k in flags for k in KEYS},
                           'extractor':{k:k in ext['candidate_flags'] for k in KEYS[2:6]}})
    jsonl(work/'candidate_flags.jsonl', candidates)
    dump(work/'timing.json', {'scan_seconds':scan_seconds,'extractor_seconds':ext_seconds})
    return hints

def predictor_type(cards, hints, arm):
    class ExperimentPredictor(Predictor):
        def _messages(self, record, items):
            assert len(items)==1
            key=items[0]
            documents='\n\n'.join(f"[{d['type']}:{d['doc_id']}]\n{d['text']}" for d in record['docs'])
            source=f"[공고 ID] {record['id']}\n[메타]\n"+json.dumps(record['meta'],ensure_ascii=False,separators=(',',':'))+'\n[문서]\n'+documents
            content=source+'\n[해당 항목의 제공 법령과 기준]\n'+cards[key]
            if arm=='candidate': content+='\n[LJM 추출 힌트: 자동 추출, 정답 아님]\n'+json.dumps(hints[record['id']][key],ensure_ascii=False,separators=(',',':'))
            return [{'role':'system','content':COMMON},{'role':'user','content':content}]
    return ExperimentPredictor

def setup():
    records=read_records('data/dev.jsonl'); assert len(records)==200
    table=json.loads(Path('data/항목표.json').read_text())['항목']; table={k:table[k] for k in KEYS}
    schema=json.loads(Path('data/정답스키마_디코딩.json').read_text())['properties']['판정']
    schema['properties']={k:schema['properties'][k] for k in KEYS}; schema['required']=KEYS
    return records,table,schema,Limits(search_rounds=0,output_tokens=512,batch_size=8)

def prepare():
    OUT.mkdir(parents=True,exist_ok=False)
    records,table,schema,limits=setup()
    hints=original_candidates(records); cards,law_hashes=legal_cards()
    dump(OUT/'hints.json',hints); dump(OUT/'legal_cards.json',cards)
    sources=['user/LJM/scan_candidates.py','user/LJM/v4_v7_candidate_extractor.py',
             'src/inference/engine.py','src/inference/predictor.py','src/inference/conversation.py',
             'src/inference/prefix_predictor.py','src/inference/legal_criteria.json','data/dev.jsonl',
             'data/항목표.json','data/정답스키마_디코딩.json']
    hashes={p:sha(p) for p in sources}; hashes.update(law_hashes)
    for p in hashes:
        target=OUT/'source'/p; target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(p,target)
    shutil.copy2(__file__,OUT/'source/run.py')
    counter=TokenCounter(MODEL); counts=[]
    for arm in ['baseline','candidate']:
        pred=predictor_type(cards,hints,arm)(counter,None,table,schema,limits=limits)
        for r in records:
            for key in KEYS:
                messages=pred._messages(r,[key]); tokens=counter.count_messages(messages)
                assert all(d['text'] in messages[1]['content'] for d in r['docs'])
                assert tokens+limits.output_tokens+128<=counter.max_model_len,(arm,r['id'],key,tokens)
                counts.append({'arm':arm,'id':r['id'],'item':key,'input_tokens':tokens})
        for key in KEYS:
            dump(OUT/'prompts'/f'{arm}_{key}.json',{'system':COMMON,'law_card':cards[key],'hint_example':hints[records[0]['id']][key] if arm=='candidate' else None,'schema':pred._schema([key],False)})
    dump(OUT/'preflight.json',{'counts':counts,'max_input_tokens':max(x['input_tokens'] for x in counts),'source_truncation':False,'overflow':0})
    manifest={'records':200,'items':KEYS,'groups':[[k] for k in KEYS],'model':MODEL,'thinking':False,'limits':asdict(limits),
              'hashes':hashes,'runner_sha256':sha(OUT/'source/run.py'),'cards_sha256':sha(OUT/'legal_cards.json'),'hints_sha256':sha(OUT/'hints.json'),
              'comparison':'same static law + full source; candidate adds unmodified LJM detector outputs with deduplicated 1600-character context display',
              'ordering':'per notice, alternate baseline-first/candidate-first; cache reset per arm; first singleton seeds source prefix then six remaining groups',
              'v3_interpretation':'statute-first: >1x estimated price; original scanner uses >allocated budget; item table says >=1x and budget',
              'v4_threshold':'2.3e8 goods/services experience threshold; original scanner uses notice_limit (local 5e8)',
              'scope':'singleton style from groups21; v2/v3 explicitly moved from rules to Gemma for this experiment; only seven items scored',
              'labels':'not read during prepare or inference; no prompt/rule tuning after scoring'}
    dump(OUT/'manifest.json',manifest)
    print(json.dumps({'stage':'prepared','max_input':max(x['input_tokens'] for x in counts),'requests':len(counts)},ensure_ascii=False),flush=True)

def run():
    manifest=json.loads((OUT/'manifest.json').read_text())
    for p,value in manifest['hashes'].items(): assert sha(p)==value,p
    assert sha(__file__)==manifest['runner_sha256']
    assert sha(OUT/'legal_cards.json')==manifest['cards_sha256'] and sha(OUT/'hints.json')==manifest['hints_sha256']
    records,table,schema,limits=setup(); cards=json.loads((OUT/'legal_cards.json').read_text()); hints=json.loads((OUT/'hints.json').read_text())
    assert not (OUT/'baseline/trace.jsonl').exists()
    tick=time.monotonic(); model=VLLMModel(MODEL,thinking=False,max_num_seqs=8); load=time.monotonic()-tick
    simple={'type':'object','properties':{'answer':{'type':'integer'}},'required':['answer'],'additionalProperties':False}
    model.generate([Turn('warmup',[{'role':'user','content':'2+3을 계산하여 answer에 답하라.'}],simple,64)])
    dump(OUT/'engine.json',{'load_seconds':load,**model.engine_info()})
    predictors={a:predictor_type(cards,hints,a)(model,None,table,schema,limits=limits) for a in ['baseline','candidate']}
    totals={a:0.0 for a in predictors}; failures={a:[] for a in predictors}; timings=[]
    streams={}
    for arm in predictors:
        (OUT/arm).mkdir(exist_ok=True); streams[arm]=(OUT/arm/'trace.jsonl').open('w')
    started=time.monotonic()
    for i,r in enumerate(records):
        order=['baseline','candidate'] if i%2==0 else ['candidate','baseline']
        for arm in order:
            assert model.reset_prefix_cache()
            tick=time.monotonic()
            result,phases=predict_notice(predictors[arm],r,[[k] for k in KEYS])
            elapsed=time.monotonic()-tick; totals[arm]+=elapsed
            timings.append({'id':r['id'],'arm':arm,'seconds':elapsed,'phases':phases})
            if result.error: failures[arm].append({'id':r['id'],'error':result.error})
            streams[arm].write(json.dumps(asdict(result),ensure_ascii=False)+'\n'); streams[arm].flush()
        if (i+1)%10==0:
            dump(OUT/'progress.json',{'records':i+1,'seconds':time.monotonic()-started,'arm_seconds':totals,'failures':failures})
            print(json.dumps({'stage':'progress','records':i+1,'seconds':time.monotonic()-started,'failures':{k:len(v) for k,v in failures.items()}}),flush=True)
    for s in streams.values():s.close()
    dump(OUT/'timings.json',timings)
    dump(OUT/'runtime.json',{'records':len(records),'arm_seconds':totals,'load_seconds':load,'elapsed_seconds':time.monotonic()-started,'failures':failures,'search_enabled':False})
    print(json.dumps({'stage':'complete','arm_seconds':totals,'failures':failures}),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('stage',choices=['prepare','run']); args=parser.parse_args()
    {'prepare':prepare,'run':run}[args.stage]()
