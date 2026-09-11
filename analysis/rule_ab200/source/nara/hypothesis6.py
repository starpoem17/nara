"""Hypothesis-6 rules with eligibility-heading and form/evaluation boundaries.

The original frozen baseline remains in the experiment source snapshots.
Never imports labels, retrieval, or a model.

Only explicit eligibility sections and monetary experience requirements count.
Unrecognized/ambiguous inputs default to 0 and remain visible in diagnostics.
Threshold source: supplied 국가계약법4 고시 (also referenced by local experience
rules), NOT the separate local regional-restriction cap. v3 uses allocated budget
as the hypothesis explicitly requests, unlike the baseline legal v3 denominator.
"""
from decimal import Decimal
import re

THRESHOLD = {'국가계약법': 230_000_000, '지방계약법': 230_000_000}
UNITS = {'조':10**12,'억':10**8,'천만':10**7,'백만':10**6,'십만':10**5,'만':10**4,'천':1000,'백':100}
NUMBER = r'\d[\d,]*(?:\.\d+)?'
UNIT = r'조|억|천만|백만|십만|만|천|백'
MONEY = re.compile(rf'(?<![\d.,])(?:(?:{NUMBER}\s*(?:{UNIT})\s*)+(?:{NUMBER}\s*)?원?|{NUMBER}\s*원)')
COMPONENT = re.compile(rf'({NUMBER})\s*({UNIT})?')
# Headings may be numbered, bulleted, spaced out, or have a short parenthesis.
ELIGIBILITY = re.compile(r'^(?:(?:제?\d+[.、):장절]|[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+[.、)]?|[가-하][.)]|[□■○◦●ㅇ※-])?)(?:입찰|제안|경쟁입찰|견적제출|입찰및제안)?(?:참가|참여|신청)(?:자격|업체자격|조건)|^(?:입찰|제안)업체(?:참가)?자격')
# A heading may carry scope notes, but registration/document instructions
# do not become headings merely because they start with "입찰참가자격".
ELIGIBILITY_TAIL = re.compile(r'^(?:및(?:방법|입찰절차))?(?:[:：].*|\(.*|※.*|은(?:아래|다음)조건.*)?$')
DOCUMENT_GUIDANCE = re.compile(r'등록증|면허증|허가증|사본|첨부|제출서류')
SECTION_PREFIX = r'(?:(?:제?\d+[.、):장절]|[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+[.、)]?|[가-하][.)]|[□■○◦●ㅇ※-]))?'
FORM_HEADING = re.compile(r'^' + SECTION_PREFIX + r'(?:[【\[(](?:별지)?서식[^】\])]*[】\])]|(?:별지)?서식\d+(?:호)?$)')
EVALUATION_HEADING = re.compile(r'^' + SECTION_PREFIX + r'(?:정량(?:적)?평가(?:항목(?:및배점)?)?|평가항목(?:및배점)?|(?:유사(?:용역|사업))?(?:수행)?실적평가기준)(?:$|[:：\(].*|\d+점$)')
NUMBERED = re.compile(r'^(제?\d+|[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+)[.、):장절]')
STOP = re.compile(r'^(?:[□■○◦●ㅇ-]|제?\d+[.、):장절]|[가-하][.)])?(?:입찰보증|제출서류|제안서제출|입찰서제출|낙찰|평가|심사|계약체결|대금|정산|기타사항|문의|유의사항|서식|별지|붙임)')
EXCLUDED = re.compile(r'배점|평가표|점수표|정량평가|정성평가|평가구간|작성요령|작성예시|작성기준|계약후|계약체결후|착수후|준공후|정산|사후보고')


def money_value(text):
    total = Decimal(0)
    for match in COMPONENT.finditer(text):
        total += Decimal(match[1].replace(',', '')) * UNITS.get(match[2], 1)
    return int(total)


def metadata_amount(value):
    if isinstance(value, (int,float)) and not isinstance(value,bool):
        return int(value) if value>0 else None
    if isinstance(value,str):
        normalized=value.replace(',','').strip()
        if normalized.isdigit():
            return int(normalized) or None
        match=MONEY.fullmatch(value.strip())
        if match:return money_value(match[0]) or None
    return None


def eligibility_spans(text):
    """Offsets into original text; the text is never normalized for evidence."""
    lines=[]
    offset=0
    for line in text.splitlines(keepends=True):
        lines.append((offset,line,re.sub(r'\s+','',line)))
        offset+=len(line)
    start=None
    heading_number=None
    spans=[]
    for offset,line,flat in lines:
        heading = ELIGIBILITY.match(flat)
        eligible = (len(flat)<=90 and heading is not None
                    and ELIGIBILITY_TAIL.fullmatch(flat[heading.end():]) is not None
                    and DOCUMENT_GUIDANCE.search(flat[heading.end():]) is None)
        excluded_section = (FORM_HEADING.match(flat) is not None
                            or EVALUATION_HEADING.match(flat) is not None)
        numbered=NUMBERED.match(flat)
        if start is not None:
            end=(eligible or excluded_section or STOP.search(flat) is not None
                 or (numbered is not None and heading_number is not None
                     and numbered[1] != heading_number))
            if end:
                spans.append((start,offset))
                start=None
        if eligible:
            start=offset
            heading_number=numbered[1] if numbered else None
    if start is not None:spans.append((start,len(text)))
    return spans


def conditions(text, start, end):
    """Paragraph/line clauses, joining wrapped lines inside one bullet only."""
    region=text[start:end]
    # Blank lines and new bullet/letter/number list entries delimit conditions.
    boundaries=[0]+[m.end() for m in re.finditer(r'\n\s*\n|\n(?=\s*(?:[-○◦●□■※]|[가-하][.)]|[①-⑳]|\d+[.)])\s*)',region)]+[len(region)]
    for a,b in zip(boundaries,boundaries[1:]):
        raw=region[a:b]
        left=len(raw)-len(raw.lstrip())
        right=len(raw.rstrip())
        if right>left:yield start+a+left,start+a+right


def judge(record):
    meta=record['meta']
    estimate=metadata_amount(meta.get('입찰추정가격'))
    budget=metadata_amount(meta.get('배정예산금액'))
    threshold=THRESHOLD.get(meta.get('적용계약법'))
    diagnostics=[]
    candidates=[]
    section_count=0
    for doc in record['docs']:
        text=doc['text']
        for start,end in eligibility_spans(text):
            section_count+=1
            for a,b in conditions(text,start,end):
                clause=text[a:b]
                flat=re.sub(r'\s+','',clause)
                if '실적' not in flat:continue
                base={'doc_id':doc['doc_id'],'start':a,'end':b,'text':clause}
                if EXCLUDED.search(flat) or ('|' in clause and re.search(r'배점|점수|평가',flat)):
                    diagnostics.append({**base,'status':'excluded_scoring_form_or_postcontract'});continue
                amounts=list(MONEY.finditer(clause))
                if not amounts:
                    diagnostics.append({**base,'status':'no_parseable_money'});continue
                matched=False
                for amount in amounts:
                    # Monetary lower bound; not years/counts or upper-bound bands.
                    suffix=re.sub(r'\s+','',clause[amount.end():amount.end()+18])
                    operator=re.match(r'(?:\([^)]{0,8}\))?(이상|초과)',suffix)
                    if not operator:continue
                    if re.search(r'미만|이하',flat):
                        diagnostics.append({**base,'status':'upper_bound_in_same_condition'});continue
                    value=money_value(amount[0])
                    # Keep exact evidence, <=500 chars, focused around the amount.
                    ev_start=max(a,a+amount.start()-180)
                    ev_end=min(b,ev_start+500)
                    evidence=text[ev_start:ev_end]
                    if evidence.startswith(('=','+','@')):evidence=None
                    candidates.append({**base,'amount':value,'operator':operator[1],
                                       'evidence':evidence,'status':'eligible_experience_lower_bound'})
                    matched=True
                if not matched and not any(x.get('start')==a and x.get('doc_id')==doc['doc_id'] for x in diagnostics):
                    diagnostics.append({**base,'status':'no_explicit_monetary_lower_bound'})
    special_local=(meta.get('적용계약법')=='지방계약법' and meta.get('계약방법')=='수의계약'
                   and any(re.search(r'특수\s*기술|특수\s*공법',d['text']) for d in record['docs']))
    work=meta.get('업무구분','')
    v2_scope=('용역' in work or '물품' in work or '제조' in work)
    c2=candidates if (threshold is not None and estimate is not None and estimate<threshold
                      and v2_scope and not special_local) else []
    c3=[c for c in candidates if budget is not None and c['amount']>budget]
    judgments={key:{'위반여부':int(bool(cs)),'근거문구':cs[0]['evidence'] if cs else None}
               for key,cs in [('v2',c2),('v3',c3)]}
    return {'record_id':record['id'],'judgments':judgments,'eligibility_sections':section_count,
            'estimated_price':estimate,'allocated_budget':budget,'v2_threshold':threshold,
            'v2_special_local_exception':special_local,'v2_scope':v2_scope,
            'unknown_metadata': [k for k,v in [('estimate',estimate),('budget',budget),('threshold',threshold)] if v is None],
            'unmatched_policy':'0; diagnostic does not prove legal compliance',
            'candidates':candidates,'diagnostics':diagnostics}
