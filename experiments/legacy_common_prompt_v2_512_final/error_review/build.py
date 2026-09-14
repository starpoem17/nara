"""Rebuild saved-output/source comparison; no model imports or inference."""
import csv
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
RUN = OUT.parent
sys.path.insert(0, str(ROOT))
from scripts.reporting import write_report


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lines(path):
    return [json.loads(s) for s in path.read_text().splitlines()]


def evidence_locations(record, quote):
    if not quote:
        return []
    found = []
    for doc in record['docs']:
        start = doc['text'].find(quote)
        if start >= 0:
            found.append({'doc_id': doc['doc_id'], 'line_start': doc['text'][:start].count('\n') + 1,
                          'line_end': doc['text'][:start + len(quote)].count('\n') + 1,
                          'text': quote})
    return found


def model_details(row, item):
    group = next(t for t in row['trace'] if item in t['items'])
    models = [e for e in group['events'] if e['event'] == 'model']
    raw = json.loads(models[-1]['response'])['judgments'][item]
    assert raw['위반여부'] == row['judgments'][item]['위반여부']
    return {'raw': raw, 'saved': row['judgments'][item], 'model_turns': len(models),
            'finish_reasons': [m['finish_reason'] for m in models],
            'output_tokens': [m['output_tokens'] for m in models],
            'search_rounds': group['search_rounds']}


def amount_outside(item, price):
    return ((item == 'v14' and price < 230_000_000)
            or (item in ('v15', 'v16') and not 100_000_000 <= price < 230_000_000)
            or (item in ('v17', 'v18') and price >= 100_000_000))


def md(text):
    return str(text).replace('|', '\\|').replace('\n', '<br>')


def main():
    records = {r['id']: r for r in lines(ROOT / 'data/dev.jsonl')}
    record_lines = {i: n for n, i in enumerate(records, 1)}
    truth = {r['id']: r for r in csv.DictReader((ROOT / 'data/dev_labels.csv').open())}
    table = read(ROOT / 'data/항목표.json')['항목']
    criteria = read(RUN / 'source/nara/compact_criteria.json')['items']
    plan = read(RUN / 'plan.json')
    for name in ('data/dev.jsonl', 'data/항목표.json'):
        assert sha(ROOT / name) == plan['source_sha256'][name]
    assert sha(ROOT / 'data/dev_labels.csv') == read(RUN / 'candidate/evaluation.json')['sha256']['data/dev_labels.csv']
    traces = {a: {r['record_id']: r for r in lines(RUN / a / 'trace.jsonl')}
              for a in ('original', 'candidate')}
    paired = [i for i in records if all(traces[a][i]['judgments'] is not None for a in traces)]
    notes = read(OUT / 'review_notes.json')
    pattern = re.compile(r'참가.?자격|참여.?가능|입찰.?참가|소재|영업소|실적|확인서|직접생산|소기업|소상공인|중소기업|중·소기업|대기업|상호출자|소프트웨어|동등|동급|제조사|모델|설명회|추정가격|기초금액|소요예산|사업예산', re.I)
    changes, matrix = [], Counter()
    for i in paired:
        for item in (f'v{n}' for n in range(1, 25)):
            old, new = [traces[a][i]['judgments'][item]['위반여부'] for a in traces]
            gold = int(truth[i][item])
            matrix[f'{gold}{old}{new}'] += 1
            if old == new:
                continue
            kind = { (1, 1, 0): 'new_fn', (1, 0, 1): 'resolved_fn',
                     (0, 1, 0): 'resolved_fp', (0, 0, 1): 'new_fp'}[gold, old, new]
            r = records[i]
            detail = {a: model_details(traces[a][i], item) for a in traces}
            quote = truth[i]['e' + item[1:]]
            case = {'id': i, 'item': item, 'item_name': table[item]['항목명'],
                    'transition': kind, 'gold': gold, 'original': old, 'candidate': new,
                    'meta': r['meta'], 'criterion': criteria[item],
                    'source_jsonl_line': record_lines[i],
                    'model': detail, 'gold_evidence_raw': quote,
                    'gold_evidence_exact_locations': evidence_locations(r, quote),
                    'gold_evidence_unescaped_locations': evidence_locations(r, quote.replace('\\n', '\n')),
                    'amount_outside_item_band': amount_outside(item, r['meta']['입찰추정가격']),
                    'review': notes.get(i + ':' + item), 'source_contexts': []}
            for arm in traces:
                detail[arm]['raw_evidence_exact_locations'] = evidence_locations(r, detail[arm]['raw']['근거문구'])
            for doc in r['docs']:
                ls = doc['text'].splitlines()
                selected = set()
                for n, s in enumerate(ls):
                    if pattern.search(s):
                        selected.update(range(max(0, n-2), min(len(ls), n+3)))
                case['source_contexts'].append({'doc_id': doc['doc_id'], 'total_lines': len(ls),
                    'lines': [{'line': n+1, 'text': ls[n]} for n in sorted(selected)]})
            if case['review']:
                excerpts = []
                for doc_id, first, last in case['review']['refs']:
                    doc = next(d for d in r['docs'] if d['doc_id'] == doc_id)
                    ls = doc['text'].splitlines()
                    assert 1 <= first <= last <= len(ls), (i, doc_id, first, last, len(ls))
                    excerpts.append({'doc_id': doc_id, 'line_start': first, 'line_end': last,
                                     'text': '\n'.join(ls[first-1:last])})
                case['review']['excerpts'] = excerpts
            changes.append(case)
    existing = {(c['id'], c['item'], int(c['gold']), int(c['original']), int(c['candidate']))
                for c in csv.DictReader((RUN / 'changed_judgments.csv').open())}
    assert existing == {(c['id'], c['item'], c['gold'], c['original'], c['candidate']) for c in changes}
    counts = Counter(c['transition'] for c in changes)
    assert counts == {'new_fn': 24, 'resolved_fn': 7, 'resolved_fp': 146, 'new_fp': 37}
    positives = [c for c in changes if c['gold']]
    assert all(c['review'] for c in positives)
    assert all(c['review'] or c['amount_outside_item_band'] for c in changes if c['transition']=='resolved_fp')
    assert all(set(d['finish_reasons']) == {'stop'} and d['search_rounds'] == 0
               for c in positives for d in c['model'].values())
    assert all(c['model']['candidate']['model_turns'] == 1 for c in positives)
    amount = [c for c in changes if c['transition'] == 'resolved_fp' and c['amount_outside_item_band']]
    assert len(amount) == 60
    used = [ROOT / 'data/dev.jsonl', ROOT / 'data/dev_labels.csv', ROOT / 'data/항목표.json',
            RUN / 'source/nara/compact_criteria.json', RUN / 'changed_judgments.csv',
            OUT / 'build.py', OUT / 'review_notes.json']
    used += [RUN / a / f for a in traces for f in ('trace.jsonl', 'common_prompt.txt')]
    summary = {'paired_records': len(paired), 'paired_judgments': len(paired)*24,
               'excluded_ids': [i for i in records if i not in paired], 'counts': dict(counts),
               'distinct_notices': {k: len({c['id'] for c in changes if c['transition'] == k}) for k in counts},
               'matrix_gold_original_candidate': dict(matrix),
               'per_item': {item: dict(Counter(c['transition'] for c in changes if c['item'] == item))
                            for item in (f'v{n}' for n in range(1,25))},
               'resolved_fp_outside_amount_band': len(amount),
               'resolved_fp_outside_amount_band_per_item': dict(Counter(c['item'] for c in amount)),
               'manually_noted_cases': len(notes),
               'all_31_positive_transitions_stop_only_no_search': True,
               'all_31_candidate_positive_transitions_single_turn': True,
               'positive_transition_retries': [{'id':c['id'], 'item':c['item'], 'arm':a, 'turns':d['model_turns']} for c in positives for a,d in c['model'].items() if d['model_turns']>1],
               'positive_transition_max_output_tokens': max(n for c in positives for d in c['model'].values() for n in d['output_tokens']),
               'source_sha256': {str(p.relative_to(ROOT)): sha(p) for p in used}}
    (OUT / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n')
    (OUT / 'cases.jsonl').write_text(''.join(json.dumps(c, ensure_ascii=False)+'\n' for c in changes))
    fieldnames = ['id','item','item_name','transition','gold','original','candidate','estimated_price',
                  'amount_outside_item_band','source_jsonl_line','original_raw_evidence','candidate_raw_evidence',
                  'review_category','review_note','verified_source_excerpts']
    flat = []
    for c in changes:
        rev = c['review'] or {}
        flat.append({**{k: c[k] for k in fieldnames if k in c},
                     'estimated_price': c['meta']['입찰추정가격'],
                     'original_raw_evidence': c['model']['original']['raw']['근거문구'],
                     'candidate_raw_evidence': c['model']['candidate']['raw']['근거문구'],
                     'review_category': rev.get('category', 'amount_band_screen' if c['amount_outside_item_band'] else 'indexed_only'),
                     'review_note': rev.get('note', '메타 추정가격이 동결된 해당 항목의 적용 금액대 밖이다. 원문 발췌는 cases.jsonl의 source_contexts에서 대조. 제품 지정·예외까지 확정한 판정은 아니다.' if c['amount_outside_item_band'] else ''),
                     'verified_source_excerpts': json.dumps(rev.get('excerpts', []), ensure_ascii=False)})
    for name, rows in [('cases.csv', flat), ('fn_transitions.csv', [c for c in flat if c['gold']]),
                       ('resolved_fp.csv', [c for c in flat if c['transition']=='resolved_fp'])]:
        with (OUT / name).open('w', newline='', encoding='utf-8-sig') as f:
            w=csv.DictWriter(f, fieldnames=fieldnames); w.writeheader(); w.writerows(rows)
    report = ['# 미탐·오탐 전환 사례 대조표', '',
              '198개 공고의 저장 응답과 제공 정답 기준. 원문 위치는 `data/dev.jsonl` 내부 문서의 1부터 시작하는 줄 번호. '
              '부재 판단은 발췌문만으로 입증되지 않으며 전체 문서를 함께 보아야 한다. '
              '법적 최종 판단이나 모델 내부 추론의 재구성이 아니다.', '',
              '분석 범위: 미탐 전환 31건 전부에 상세 검토 메모. 해소 오탐은 146건 모두 원문·메타·기존 응답을 색인하고, '
              '60건의 금액대 불일치 검산 및 나머지 86건의 원문 대조 메모. `indexed_only`는 이번 상세 검토 범위 밖의 새 오탐 37건.', '']
    for kind, label in [('new_fn','새로 발생한 미탐 24건'),('resolved_fn','해소된 미탐 7건'),('resolved_fp','해소된 오탐: 금액대 검산 외 86건')]:
        report += ['## '+label, '']
        for c in changes:
            if c['transition'] != kind or not c['review']: continue
            rev=c['review']; report += [f"### {c['id']} · {c['item']} {c['item_name']}", '',
                f"정답 {c['gold']} / 기존 {c['original']} → 수정 {c['candidate']} / 추정가격 {c['meta']['입찰추정가격']:,}원. 분류: {rev['category']}.", '', rev['note'], '',
                f"원문 레코드: [dev.jsonl]({ROOT / 'data/dev.jsonl'}:{c['source_jsonl_line']}). 개별 기준: `{c['criterion']}`.", '']
            for e in rev['excerpts']:
                report += [f"{e['doc_id']}:{e['line_start']}–{e['line_end']}", '', '> '+e['text'].replace('\n','\n> '), '']
            for a, label_a in [('original','기존'),('candidate','수정')]:
                d=c['model'][a]
                report += [f"{label_a} 원시 근거: {md(d['raw']['근거문구'])}. 저장 근거: {md(d['saved']['근거문구'])}.", '']
    report += ['## 해소 오탐 중 적용 금액대 밖의 60건', '',
               '동결된 v14~v18 기준과 메타 추정가격만으로 검산한 결과. 지정제품 여부 등 나머지 적용 조건·법적 예외를 확정한 숫자는 아니다.', '',
               '| 공고 | 항목 | 추정가격(원) |', '|---|---|---:|']
    report += [f"| {c['id']} | {c['item']} | {c['meta']['입찰추정가격']:,} |" for c in amount]
    write_report(OUT / 'case_review.md', '\n'.join(report)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='source_sha256'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
