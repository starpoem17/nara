"""Dev-informed briefing rule for current twelve-group runs only."""
import re

BRIEFING = r'(?:[가-힣()·]*설명회|현장설명)'
ABSENT = r'(?:불참|미참석|미참가|참석하지\s*(?:않|아니)|참가하지\s*(?:않|아니)|참석하지\s*못)'
ELIGIBLE = r'(?:입찰(?:\s*참가)?|제안서(?:\s*제출|\s*접수)?)'
DENIAL = r'(?:불가|금지|제외|허용되지|할\s*수\s*없|받지\s*않|접수하지\s*않|제출하지\s*못|참가하지\s*못)'
PATTERNS = [
    ('eligibility_list', re.compile(r'(?:입찰|용역수행)\s*참가\s*자격(?:(?![.!?]\s*\d+\. ).){0,700}?' + BRIEFING + r'에?\s*(?:참석|참가|참여)한\s*(?:자|업체)')),
    ('absent_excluded', re.compile(BRIEFING + r'.{0,40}?' + ABSENT + r'.{0,60}?' + ELIGIBLE + r'.{0,35}?' + DENIAL)),
    ('attendees_only', re.compile(BRIEFING + r'.{0,25}?(?:참석|참가|참여).{0,30}?(?:한하|한해|자만|업체만|업체에만|자에만).{0,45}?' + ELIGIBLE + r'.{0,35}?(?:가능|자격|허용|있|부여)')),
]

def _predict(record):
    documents = record['docs']
    meta = record.get('meta', {})
    negotiated = any('협상' in str(meta.get(k, '')) for k in ('계약방법', '낙찰방법'))
    negotiated = negotiated or any(re.search(r'협상에\s*의한\s*계약|계약\s*방법\s*[:：]?\s*협상', d['text']) for d in documents)
    result = {'id': record['id'], 'v22': 0, 'negotiated': bool(negotiated), 'rule': None, 'doc_id': None, 'e22': ''}
    if not negotiated:
        return result
    for doc in documents:
        # Collapse whitespace while preserving exact source offsets for evidence.
        positions = []
        chars = []
        for match in re.finditer(r'\s+|\S', doc['text']):
            chars.append(' ' if match.group().isspace() else match.group())
            positions.append((match.start(), match.end()))
        text = ''.join(chars)
        for name, pattern in PATTERNS:
            for match in pattern.finditer(text):
                # Supplier presentations/evaluation are not pre-bid briefings.
                context = text[max(0, match.start()-35):match.end()]
                if re.search(r'제안(?:서)?\s*설명회\s*\(평가\)|평가위원.*설명회|평가\s*대상.{0,10}제외', context):
                    continue
                quote = doc['text'][positions[match.start()][0]:positions[match.end()-1][1]]
                result.update(v22=1, rule=name, doc_id=doc['doc_id'], e22=quote)
                return result
    return result


def judge(record):
    """Return v2/v3/v22 judgments plus diagnostics; no model or labels."""
    from nara.hypothesis6 import judge as judge_experience

    result = judge_experience(record)
    briefing = _predict(record)
    quote = briefing['e22']
    # Evidence formatting must not change the binary rule decision.
    evidence = quote[:500] if quote and not quote.startswith(('=', '+', '@')) else None
    result['judgments']['v22'] = {'위반여부': briefing['v22'], '근거문구': evidence}
    result['briefing'] = briefing
    return result
