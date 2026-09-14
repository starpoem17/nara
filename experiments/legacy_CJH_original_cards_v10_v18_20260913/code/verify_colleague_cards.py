"""Check original source bytes against every frozen rendered experimental request."""

if __name__ == "__main__":
    raise SystemExit("Archived code: create a fresh registered run; see docs/operations.md.")

import csv
import hashlib
import io
import json
from pathlib import Path
import re
from experiments.legacy_CJH_original_cards_v10_v18_20260913.code.colleague_cards import ROOT, RUNS, FEATURES, MODEL, INSTRUCTION, install_input_guard, read_jsonl, sha, digest, dump
from nara.inference.engine import TokenCounter


def verify():
    install_input_guard()
    records = {r['id']: r for r in read_jsonl(ROOT / 'data/dev.jsonl')}
    csv_path = ROOT / 'data/법령패키지/중기부고시/중기부고시_경쟁제품_세부품명.csv'
    raw_csv = csv_path.read_bytes().decode('utf-8-sig')
    csv_lines = raw_csv.splitlines(keepends=True)
    csv_rows = list(csv.DictReader(io.StringIO(raw_csv)))
    candidates = {r['id']: r for r in read_jsonl(RUNS['CJH'] / 'product_candidates.jsonl.gz')}
    from transformers import AutoTokenizer
    bge_tokenizer = AutoTokenizer.from_pretrained(ROOT / 'models/bge-m3', local_files_only=True)
    max_query_tokens = 0
    for rid, row in candidates.items():
        record = records[rid]
        assert row['header'] == csv_lines[0] and row['source_sha256'] == sha(csv_path)
        assert [c['row_number'] for c in row['candidates']] == sorted({c['row_number'] for c in row['candidates']})
        for candidate in row['candidates']:
            index = candidate['row_number'] - 2
            assert candidate['values'] == csv_rows[index]
            assert candidate['raw_csv'] == csv_lines[index + 1]
            code = candidate['values']['세부품명번호']
            name = candidate['values']['세부품명']
            docs = {d['doc_id']: d['text'] for d in record['docs']}
            for match in candidate['name_matches']:
                assert docs[match['doc_id']][match['char_start']:].startswith(name) and len(name) >= 2
            for match in candidate['code_matches']:
                if 'doc_id' in match:
                    assert docs[match['doc_id']][match['char_start']:match['char_end']] == code
                else:
                    text = json.dumps(record['meta']['세부품명번호목록'], ensure_ascii=False)
                    assert text[match['serialized_char_start']:match['serialized_char_end']] == code
            assert bool(candidate['code_matches']) == ('exact_code' in candidate['reasons'])
            assert 0 <= candidate['best_query'] < len(row['queries'])
        assert sum('semantic_top5' in c['reasons'] for c in row['candidates']) == 5
        for query in row['queries']:
            if query['kind'] == 'meta':
                expected = json.dumps(record['meta'], ensure_ascii=False, separators=(',', ':'))
            else:
                doc = next(d for d in record['docs'] if d['doc_id'] == query['doc_id'])
                expected = doc['text'][query['char_start']:query['char_end']]
            assert query['text'] == expected and digest(expected) == query['text_sha256']
            count = len(bge_tokenizer.encode(expected, add_special_tokens=True, truncation=False))
            assert count <= 8192
            max_query_tokens = max(max_query_tokens, count)
    tokenizer = TokenCounter(MODEL, thinking=False, max_model_len=36864)
    cms_path = next((ROOT / 'user/CMS').rglob('*_정리본.md'))
    cms = cms_path.read_bytes().decode('utf-8')
    starts = list(re.finditer(r'(?m)^## (v\d+)[ \t]*\r?$', cms))
    cms_cards = {m.group(1): cms[:starts[0].start()] + cms[m.start(): starts[i+1].start() if i+1 < len(starts) else len(cms)]
                 for i,m in enumerate(starts)}
    checks = {}
    for author, out in RUNS.items():
        manifest = json.loads((out / 'manifest.json').read_text())
        assert manifest['ready'] and manifest['max_model_len'] == 36864
        assert manifest['thinking'] is False and manifest['output_tokens'] == 512 and manifest['retries'] == 0
        assert manifest['structured_decoding'] is False and manifest['max_num_seqs'] == 16
        assert not any('dev_labels' in p for p in manifest['input_hashes'])
        for p, value in manifest['input_hashes'].items():
            assert sha(ROOT / p) == value, p
            snapshot = out / 'source' / p
            if snapshot.exists():
                assert sha(snapshot) == value
        for p, value in manifest['artifact_hashes'].items():
            assert sha(out / p) == value, p
        laws = json.loads((out / 'laws.json').read_text())
        provenance = json.loads((out / 'law_provenance.json').read_text())
        for feature in FEATURES[author]:
            grouped = {}
            for part in provenance[feature]:
                path = ROOT / part['path']
                lines = path.read_bytes().decode('utf-8').splitlines(keepends=True)
                assert sha(path) == part['source_sha256']
                assert ''.join(lines[i-1] for i in part['included_lines']) == part['text']
                grouped.setdefault(part['path'], []).append(part['text'])
            expected = []
            for name, spans in grouped.items():
                lines = (ROOT / name).read_bytes().decode('utf-8').splitlines(keepends=True)
                expected.append(''.join(lines[:7]) + '\n'.join(spans))
            assert laws[feature] == '\n\n'.join(expected)
        seen, maximum = set(), 0
        original_draft = json.loads((out / 'preflight_draft.json').read_text())
        draft = {(c['id'], c['feature']):c for c in original_draft['checks']}
        for feature in FEATURES[author]:
            card = cms_cards[feature] if author == 'CMS' else (ROOT / 'user/CJH/판정카드(10~18)' / (feature + '.md')).read_bytes().decode('utf-8')
            requests = read_jsonl(out / 'requests' / (feature + '.jsonl.gz'))
            assert len(requests) == 200 and [r['id'] for r in requests] == list(records)
            for request in requests:
                rid = request['id']; record = records[rid]
                assert (rid, feature) not in seen
                seen.add((rid, feature))
                assert request['feature'] == feature and request['task_id'] == rid + ':' + feature
                header = {k: record[k] for k in ('id','meta','input_completeness','dropped_doc_counts') if k in record}
                expected = INSTRUCTION + '\n\n[공고 정보]\n' + json.dumps(header,ensure_ascii=False,separators=(',',':'))
                expected += '\n[문서]\n' + '\n\n'.join(f"[{d['type']}:{d['doc_id']}]\n{d['text']}" for d in record['docs'])
                if author == 'CJH':
                    selection = candidates[rid]
                    expected += '\n\n[참고자료: 경쟁제품 목록 발췌]\n' + csv_lines[0]
                    expected += ''.join(csv_lines[c['row_number']-1] for c in selection['candidates'])
                if laws[feature]:
                    expected += '\n\n[참고자료: 법령·고시 원문 발췌]\n' + laws[feature]
                expected += '\n\n[판정카드]\n' + card
                assert request['messages'] == [{'role':'user','content':expected}]
                assert request['card_sha256'] == digest(card) and request['prompt_sha256'] == digest(expected)
                assert draft[(rid, feature)]['prompt_sha256'] == request['prompt_sha256'], 'Context exception must not change content'
                tokens = tokenizer.render_messages(request['messages'])
                assert tokens == request['prompt_token_ids']
                assert len(tokens) == request['input_tokens'] and len(tokens)+512 <= 36864
                assert digest(json.dumps(tokens,separators=(',',':'))) == request['prompt_tokens_sha256']
                maximum = max(maximum, len(tokens)+512)
        assert len(seen) == len(FEATURES[author])*200
        checks[author] = {'requests_checked':len(seen),'maximum_input_plus_output':maximum,
            'context':36864,'unresolved_overflows':0,'content_unchanged_from_32768_draft':True,
            'original_cards_and_notice_fields_exact':True,'law_spans_and_catalog_rows_exact':True,
            'template_token_ids_exact':True,'input_and_artifact_hashes_verified':True,
            'maximum_bge_query_tokens':max_query_tokens,'labels_access_blocked':True,
            'verification_source_sha256':sha(__file__)}
        dump(out / 'preflight_verification.json',checks[author])
        print(json.dumps({'author':author,**checks[author]}),flush=True)
    return checks


if __name__ == '__main__':
    raise SystemExit("Archived experiment: create a new registered run; see docs/operations.md. Historical evidence is read-only.")
    verify()
