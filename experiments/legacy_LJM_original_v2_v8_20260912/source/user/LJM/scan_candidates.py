import gzip, json, re, csv, sys
from pathlib import Path

ROOT=Path(__file__).parent
path=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'open/train_unlabeled.jsonl.gz'
REGION_WORD=re.compile(r'(본점|주된 영업소|영업소|사업장|소재지|지역제한|관할구역)')
REGION_NAME=re.compile(r'[가-힣]+(?:특별시|광역시|특별자치시|도|특별자치도)')
EXPERIENCE=re.compile(r'실적|수행실적|이행실적|납품실적|계약실적')
AMOUNT=re.compile(r'(?P<num>[0-9][0-9,]*(?:\.[0-9]+)?)\s*(?P<unit>억|천만|백만|만)?\s*원?')
DIR=re.compile(r'이상|초과|미만|이하')
INSTITUTION=re.compile(r'국가기관|지방자치단체|지자체|공공기관|공기업|정부투자기관|대학병원|대학|국가에서|공공에서')
POST_AWARD=re.compile(r'낙찰금액|계약상대자|계약체결 후|계약 이후|연구비 집행|관리·보고|정산|회계법인|검증 절차|성과보고|대금 지급')
QUALIFICATION=re.compile(r'입찰참가자격|입찰 참가 자격|참가자격|입찰참가 조건|제한경쟁|참여자격|참여 가능')
DOCUMENT_ONLY=re.compile(r'제안서|작성방법|작성요령|제안서 양식|평가기준|평가방법|배점|평점|점수|실적건수|실적금액\s*\(합계\)|목차|서식|각주|※\s*주|해당 시 작성')
TEXT_AMOUNT=re.compile(r'([0-9][0-9,]*(?:\.[0-9]+)?)\s*(억|천만|백만|만)?\s*원?\s*(?:\([^)]*\))?\s*(이상|초과|미만|이하)')

def amount(m):
    n=float(m.group(1).replace(',','')); u=m.group(2) or ''
    return int(n*({'억':100_000_000,'천만':10_000_000,'백만':1_000_000,'만':10_000}.get(u,1)))

def sentences(text):
    return [x.strip() for x in re.split(r'(?<=[.!?。])\s+|\n+', text) if x.strip()]

def qualification_blocks(text):
    lines=[x.strip() for x in text.splitlines() if x.strip()]
    mark=re.compile(r'^(?:[①②③④⑤⑥⑦⑧⑨⑩]|[가나다라마바사아자차카타파하]\.|\d+(?:-\d+)?[.)]|\([가-힣]\))')
    blocks=[]; cur=[]
    for line in lines:
        # VAT/부가세 표기는 앞 금액 조건에 붙이고, 별도 조건 괄호는 경계로 분리한다.
        pieces=[]; pos=0
        for m in re.finditer(r'\([^)]*\)', line):
            inside=m.group(0)
            if re.search(r'VAT|부가세|부가가치세', inside, re.I):
                continue
            if line[pos:m.start()].strip(): pieces.append(line[pos:m.start()].strip())
            pieces.append(inside)
            pos=m.end()
        if pieces:
            if line[pos:].strip(): pieces.append(line[pos:].strip())
            lines_at_once=pieces
        else:
            lines_at_once=[line]
        for line_part in lines_at_once:
            line=line_part
            if mark.match(line) and cur:
                blocks.append(' '.join(cur)); cur=[]
            cur.append(line)
    if cur: blocks.append(' '.join(cur))
    return blocks

def docs_text(r): return '\n'.join(d.get('text','') for d in r.get('docs',[]))

# The competition data anonymizes regions.  `단위=기초` means a city/county/district
# restriction; it must not be treated as an ordinary broad-area restriction.
BASE_REGION_TOKEN = re.compile(r'\[지역:[^\]]*단위\s*=\s*기초[^\]]*\]', re.I)
REGION_TOKEN = re.compile(r'\[지역:[^\]]+\]', re.I)
ELIGIBILITY_HINT = re.compile(r'입찰참가자격|참가자격|참가资格|제한경쟁|주된 영업소|본점|사업장 소재지|소재한 업체')
EVALUATION_CONTEXT = re.compile(r'배점|평가점수|정량적 평가|평가 기준|평가기준|평가항목|평가요소|심사|평점|점수|유사용역 수행실적\s*\(|유사사업수행경험|문화행사 수행실적\s*\([^)]*점|수행실적\s*\([^)]*점|최고실적 금액|절대 평가', re.I)

def is_eligibility_block(block):
    """Keep explicit qualification blocks, reject evaluation/form/post-award text."""
    if POST_AWARD.search(block):
        return False
    if DOCUMENT_ONLY.search(block) and not QUALIFICATION.search(block):
        return False
    if EVALUATION_CONTEXT.search(block) and not QUALIFICATION.search(block):
        return False
    # Typical score-table row: requirement | count/grade | points.
    if re.search(r'\|\s*\d+\s*건\s*이상\s*\|\s*\d+', block):
        return False
    # Pipe-delimited score tables are structural rows, not eligibility sentences.
    # Do not split on every pipe; exclude only rows with unmistakable scoring cues.
    if block.count('|') >= 2 and re.search(
        r'평가|배점|평점|점수|누적실적건수|누적실적금액|최고실적 금액|실적없음|\d+(?:\.\d+)?\s*점', block):
        return False
    # Attached templates/forms can contain their own example thresholds.
    if re.search(r'\[?양식\s*#?\d*\]?|\[?서식\s*제?\d*호?\]?', block):
        return False
    return True

def region_level(text):
    """Return (has_region, has_basic_unit) using anonymized tokens and legal wording."""
    tokens = REGION_TOKEN.findall(text)
    basic = bool(BASE_REGION_TOKEN.search(text))
    explicit = bool(REGION_WORD.search(text) or re.search(r'주된 영업소|본점|사업장.*소재|소재한 업체', text))
    return bool(tokens or explicit), basic

def qualification_section(text):
    m=re.search(r'(입찰참가자격|입찰 참가 자격|공모·입찰 참가자격|공모·입찰 참가 자격)', text)
    if not m: return ''
    tail=text[m.start():]
    end=re.search(r'\n\s*\d+[.)]\s*', tail[1:])
    return tail if not end else tail[:end.start()+1]

def notice_limit(meta):
    law=meta.get('적용계약법'); owner=str(meta.get('소관구분') or '')
    # 1차 규칙: 배포 고시·지방 시행규칙에 보이는 일반 물품/용역 기준.
    # 공기업·준정부기관 국가계약은 별도 7.1억원 기준.
    if law=='지방계약법': return 500_000_000
    if law=='국가계약법' and ('공기업' in owner or '준정부' in owner): return 710_000_000
    return 230_000_000

def main():
    rows=[]; counts={f'v{i}':0 for i in range(2,9)}
    with gzip.open(path,'rt',encoding='utf-8') as f:
      for line in f:
        r=json.loads(line); text=docs_text(r); ss=sentences(text); blocks=qualification_blocks(text)
        qsection=qualification_section(text)
        qblocks=qualification_blocks(qsection) if qsection else []
        for line in text.splitlines():
          if '|' in line and EXPERIENCE.search(line) and TEXT_AMOUNT.search(line):
            blocks.append(line.strip())
        exp=[(i,s) for i,s in enumerate(blocks) if EXPERIENCE.search(s)]
        v2=v3=v4=v8=False; evidence=[]
        for i,block in exp:
          if not is_eligibility_block(block):
            continue
          ms=list(TEXT_AMOUNT.finditer(block))
          if not ms: continue
          if re.search(r'이상|초과',block) and not re.search(r'미만|이하',block): v2=True
          vals=[amount(m) for m in ms if m.group(3) in ('이상','초과')]
          budget=r.get('meta',{}).get('배정예산금액')
          if budget is not None and any(x>int(budget) for x in vals): v3=True
          if INSTITUTION.search(block): v4=True
          evidence.append(block[:700])
        meta=r.get('meta',{})
        est=meta.get('입찰추정가격')
        try: est=int(float(est)) if est is not None else None
        except: est=None
        region_sentence = re.compile(r'(지역제한|지역 제한|본점|주된 영업소|영업소|사업장).{0,120}(소재|두고|있는|지역 업체|제한)', re.S)
        has_region, has_basic_token = region_level(text)
        region=meta.get('지역제한여부')=='Y' or has_region or bool(region_sentence.search(text))
        region_blocks=[]
        for block in (qblocks or blocks):
          if re.search(r'양식|서식|제출처|제출 장소|발급기관|주소\s*[:：]', block):
            continue
          if region_sentence.search(block) or REGION_TOKEN.search(block): region_blocks.append(block)
        # General local-contract regional threshold used as a first-pass threshold.
        limit=notice_limit(meta)
        # v2는 실적 문장 자체뿐 아니라 공고 금액이 고시금액 미만인지 확인한다.
        # v2의 고시금액 미만 실적제한은 dev에서 물품·용역 2.3억원 경계를 사용한다.
        # 지역제한용 지방 기준(5억원)과 분리한다.
        v2 = v2 and est is not None and est < 230_000_000
        # v5 requires an explicit bidder-location restriction in the qualification
        # section; metadata Y alone is not sufficient.
        qualification_region = any(region_sentence.search(b) or REGION_TOKEN.search(b)
                                   for b in qblocks)
        region_code = meta.get('제한지역코드목록')
        explicit_region_anywhere = bool(region_sentence.search(text))
        v5=(qualification_region or explicit_region_anywhere or bool(region_code)) and est is not None and est>=limit
        v6=region and est is not None and est<limit and any(re.search(r'시[·ㆍ, ]?군|구|읍|면|동', b) for b in region_blocks)
        adjacent = re.compile(r'인접|인근|주변|접한 지역|까지 확대|연접')
        v7=v6 and any(adjacent.search(b) for b in region_blocks)
        # Metadata 지역제한여부=Y is only a broad signal.  Keep v6/v7 only when
        # the text explicitly identifies a basic administrative unit or token.
        basic_phrase = re.compile(r'(?:특별시|광역시|시|군|구)\s*(?:관내|소재|지역|이내|까지|업체|에|로 제한|로 한정)')
        basic_in_block = any(BASE_REGION_TOKEN.search(b) for b in region_blocks)
        basic_token_eligibility = bool(re.search(r'\[지역:[^\]]*단위\s*=\s*기초[^\]]*\].{0,120}(?:지역 업체|소재지|소재한 업체|본점|영업소)', text))
        v6 = region and est is not None and est < limit and (basic_in_block or basic_token_eligibility or
             any(basic_phrase.search(b) for b in region_blocks))
        bidder_region = re.compile(r'업체|사업자|법인|기업|본점|주된 영업소|영업소|사업장|소재지|지역 업체|관내 업체')
        v6 = region and est is not None and est < limit and any(
            BASE_REGION_TOKEN.search(b) and bidder_region.search(b) or
            basic_phrase.search(b) and bidder_region.search(b)
            for b in region_blocks)
        v7 = v6 and (any(adjacent.search(b) for b in region_blocks) or
                     len(REGION_TOKEN.findall(' '.join(region_blocks))) >= 2)
        if v8: pass
        # Region and experience in same nearby block.
        # v8 may state region and experience in separate qualification items.
        qregion = ' '.join(b for b in qblocks if region_sentence.search(b) or REGION_TOKEN.search(b))
        qexp = ' '.join(b for b in qblocks if EXPERIENCE.search(b) and TEXT_AMOUNT.search(b))
        v8=bool(qsection and qregion and qexp)
        # v4 likewise combines an experience requirement and a specific ordering
        # institution across adjacent qualification items.
        qexp_amount = any(EXPERIENCE.search(b) and TEXT_AMOUNT.search(b) for b in qblocks)
        qinst = any(INSTITUTION.search(b) for b in qblocks)
        v4 = v4 or (qexp_amount and qinst)
        flags={f'v{i}':x for i,x in [(2,v2),(3,v3),(4,v4 and est is not None and est>=limit),(5,v5),(6,v6),(7,v7),(8,v8)]}
        if any(flags.values()):
          for k,x in flags.items():
            if x: counts[k]+=1
          rows.append({'id':r['id'],'flags':','.join(k for k,x in flags.items() if x),'meta':meta,'evidence':' || '.join(evidence[:3])})
    out=ROOT/'candidate_v2_v8.csv'
    with out.open('w',encoding='utf-8-sig',newline='') as f:
      w=csv.DictWriter(f,fieldnames=['id','flags','meta','evidence']); w.writeheader(); w.writerows(rows)
    print(json.dumps({'input':str(path),'candidates':len(rows),'counts':counts,'output':str(out)},ensure_ascii=False))
if __name__=='__main__': main()
