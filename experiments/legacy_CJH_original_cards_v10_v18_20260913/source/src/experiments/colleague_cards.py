"""Frozen original-card inputs and one-pass source-first experiment execution."""
from __future__ import annotations

import argparse
from collections import deque
from dataclasses import asdict
import gzip
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import time


ROOT = Path(__file__).resolve().parents[2] if Path(__file__).parent.name == 'experiments' else Path(__file__).resolve().parents[1]
MODEL = ROOT / 'models/gemma-4-26B-A4B-it-NVFP4'
CONTEXT = 36864  # User-approved exception for these two original-card runs only.
CATALOG = ROOT / 'data/법령패키지/중기부고시/중기부고시_경쟁제품_세부품명.csv'
RUNS = {
    'CMS': ROOT / 'analysis/CMS_original_cards_v19_v24_20260913',
    'CJH': ROOT / 'analysis/CJH_original_cards_v10_v18_20260913',
}
FEATURES = {'CMS': [f'v{i}' for i in range(19, 25)], 'CJH': [f'v{i}' for i in range(10, 19)]}
INSTRUCTION = '제공된 공고와 참고자료를 사용해 아래 판정카드의 항목을 판정하세요. 응답은 위반여부(0 또는 1)와 근거문구(문자열 또는 null)를 담은 JSON 하나로 작성하세요.'
SELECTOR = {
    'version': 1, 'exact_codes': '10-digit catalog codes in all documents or meta.세부품명번호목록',
    'exact_names': 'literal detailed product names of at least two characters in any document',
    'semantic': 'top five CSV rows by maximum cosine over complete document chunks and one complete meta query',
    'chunk_tokens': 2048, 'overlap_tokens': 128, 'top_k': 5,
    'ties': 'ascending original CSV row number', 'output_order': 'ascending original CSV row number',
    'scope': 'candidate references only; no classification, applicability or violation labels',
}
PARSING = {
    'version': 1, 'outer_whitespace': 'ignored for envelope parsing only; evidence strings unchanged',
    'duplicate_keys_and_nonfinite_constants': 'invalid JSON',
    'accepted': ['one bare JSON object', 'one entire JSON code fence with no outside text'],
    'strict_format': 'only bare JSON is strict; a single full code fence remains a recorded format violation',
    'keys': ['위반여부', '근거문구'], 'violation_type': 'integer 0 or 1, excluding bool',
    'evidence_type': 'string or null; preserve exactly, with no whitespace trimming or cleanup',
    'invalid': 'non-stop, unparseable, wrong fields or types; never substitute a judgment',
    'empty_evidence': 'null and the empty string count as empty only in evidence diagnostics',
    'denominators': 'valid-only confusion metrics plus invalid counts by gold and all-record possible F1 bounds',
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def install_input_guard():
    blocked = {ROOT / 'data/dev_labels.csv', *(ROOT / 'src/inference' / name for name in
                ('prompt.txt', 'compact_criteria.json', 'legal_criteria.json'))}
    def audit(event, args):
        if event == 'open' and isinstance(args[0], (str, bytes)):
            path = Path(args[0].decode() if isinstance(args[0], bytes) else args[0]).resolve()
            if path in blocked or any(path.is_relative_to(ROOT / 'user' / name) for name in ('KHJ', 'LJM')):
                raise PermissionError('Forbidden hypothesis/label input: ' + str(path))
    sys.addaudithook(audit)


def code_positions(record, code):
    pattern = re.compile(r'(?<!\d)' + re.escape(code) + r'(?!\d)')
    found = [{'doc_id': d['doc_id'], 'char_start': m.start(), 'char_end': m.end()}
             for d in record['docs'] for m in pattern.finditer(d['text'])]
    meta = json.dumps(record['meta'].get('세부품명번호목록'), ensure_ascii=False)
    found.extend({'field': 'meta.세부품명번호목록', 'serialized_char_start': m.start(),
                  'serialized_char_end': m.end()} for m in pattern.finditer(meta))
    return found


def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    opener = gzip.open if path.suffix == '.gz' else open
    with opener(path, 'wt', encoding='utf-8') as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + '\n')


def read_jsonl(path):
    opener = gzip.open if str(path).endswith('.gz') else open
    with opener(path, 'rt', encoding='utf-8') as stream:
        return [json.loads(line) for line in stream if line.strip()]


def cards_for(author):
    if author == 'CJH':
        paths = {p.stem: p for p in (ROOT / 'user/CJH').rglob('v*.md')}
        return {f: paths[f].read_bytes().decode('utf-8') for f in FEATURES[author]}, [paths[f] for f in FEATURES[author]]
    path = next((ROOT / 'user/CMS').rglob('*_정리본.md'))
    text = path.read_bytes().decode('utf-8')
    marks = list(re.finditer(r'(?m)^## (v\d+)[ \t]*\r?$', text))
    preamble = text[:marks[0].start()]
    sections = {m.group(1): text[m.start(): marks[i + 1].start() if i + 1 < len(marks) else len(text)]
                for i, m in enumerate(marks)}
    assert preamble + ''.join(sections[f] for f in FEATURES[author]) == text
    return {f: preamble + sections[f] for f in FEATURES[author]}, [path]


def source_text(record):
    header = {k: record[k] for k in ('id', 'meta', 'input_completeness', 'dropped_doc_counts') if k in record}
    docs = '\n\n'.join(f"[{d['type']}:{d['doc_id']}]\n{d['text']}" for d in record['docs'])
    return '[공고 정보]\n' + json.dumps(header, ensure_ascii=False, separators=(',', ':')) + '\n[문서]\n' + docs


def common_input(record, selection=None):
    common = INSTRUCTION + '\n\n' + source_text(record)
    if selection is not None:
        assert selection['source_sha256'] == sha(CATALOG)
        common += '\n\n[참고자료: 경쟁제품 목록 발췌]\n' + selection['header']
        common += ''.join(c['raw_csv'] for c in selection['candidates'])
    return common


def card_messages(common, law, card):
    content = common
    if law:
        content += '\n\n[참고자료: 법령·고시 원문 발췌]\n' + law
    return [{'role': 'user', 'content': content + '\n\n[판정카드]\n' + card}]


def law_material(spec):
    texts, sources, provenance = [], {}, []
    by_path = {}
    for span in spec['excerpts']:
        by_path.setdefault(span['path'], []).append(span)
    for name, spans in by_path.items():
        path = ROOT / name
        assert path.resolve().is_relative_to(ROOT / 'data/법령패키지')
        lines = path.read_bytes().decode('utf-8').splitlines(keepends=True)
        header = ''.join(lines[:7])
        chosen, used = [], set()
        for span in sorted(spans, key=lambda s: s['start_line']):
            start, end = span['start_line'], span['end_line']
            assert 1 <= start <= end <= len(lines), span
            indices = [i for i in range(start, end + 1) if i > 7 and i not in used]
            used.update(indices)
            if not indices:
                continue
            raw = ''.join(lines[i - 1] for i in indices)
            chosen.append(raw)
            provenance.append({**span, 'included_lines': indices, 'text': raw, 'source_sha256': sha(path)})
        texts.append(header + '\n'.join(chosen))
        sources[name] = sha(path)
    return '\n\n'.join(texts), provenance, sources


def query_chunks(record, tokenizer):
    result = [{'kind': 'meta', 'text': json.dumps(record['meta'], ensure_ascii=False, separators=(',', ':'))}]
    for doc in record['docs']:
        offsets = tokenizer(doc['text'], add_special_tokens=False, truncation=False,
                            return_offsets_mapping=True, verbose=False)['offset_mapping']
        begin = 0
        while begin < len(offsets):
            end = min(begin + SELECTOR['chunk_tokens'], len(offsets))
            lo, hi = offsets[begin][0], offsets[end - 1][1]
            result.append({'kind': 'document', 'doc_id': doc['doc_id'], 'char_start': lo,
                           'char_end': hi, 'text': doc['text'][lo:hi]})
            if end == len(offsets):
                break
            begin = end - SELECTOR['overlap_tokens']
    return result


def select_catalog(records):
    import csv
    import io
    import numpy as np
    from nara.retrieval.search import BGEEncoder, LegalRetriever

    started = time.monotonic()
    raw = CATALOG.read_bytes().decode('utf-8-sig')
    raw_lines = raw.splitlines(keepends=True)
    rows = list(csv.DictReader(io.StringIO(raw)))
    assert len(raw_lines) == len(rows) + 1 == 617
    encoder = BGEEncoder(ROOT / 'models/bge-m3', device='cuda')
    index = LegalRetriever(ROOT / 'model/legal_index', encoder)
    for entry in index.manifest['sources']:
        assert sha(ROOT / 'data/법령패키지' / entry['path']) == entry['sha256']
    source = CATALOG.relative_to(ROOT / 'data/법령패키지').as_posix()
    mapped = {int(p['locator'].split(':')[1]): i for i, p in enumerate(index.passages) if p['source'] == source}
    assert set(mapped) == set(range(2, len(rows) + 2))
    for number, row in enumerate(rows, 2):
        expected = '\n'.join(f'{k}: {v}' for k, v in row.items() if v.strip())
        assert index.passages[mapped[number]]['text'] == expected
    vectors = index.vectors[[mapped[i] for i in range(2, len(rows) + 2)]]
    selected = []
    for ri, record in enumerate(records):
        chunks = query_chunks(record, encoder.tokenizer)
        query_vectors = encoder.encode([c['text'] for c in chunks])
        scores = query_vectors @ vectors.T
        best = scores.max(axis=0)
        ranking = np.argsort(-best, kind='stable')[:SELECTOR['top_k']].tolist()
        text = '\n'.join(d['text'] for d in record['docs'])
        code_text = text + '\n' + json.dumps(record['meta'].get('세부품명번호목록'), ensure_ascii=False)
        codes = set(re.findall(r'(?<!\d)\d{10}(?!\d)', code_text))
        hits = []
        for i, row in enumerate(rows):
            reasons = []
            if row['세부품명번호'] in codes:
                reasons.append('exact_code')
            name = row['세부품명']
            positions = [{'doc_id': d['doc_id'], 'char_start': d['text'].find(name)}
                         for d in record['docs'] if len(name) >= 2 and name in d['text']]
            if positions:
                reasons.append('exact_detailed_name')
            if i in ranking:
                reasons.append('semantic_top5')
            if reasons:
                qi = int(scores[:, i].argmax())
                hits.append({'row_number': i + 2, 'values': row, 'raw_csv': raw_lines[i + 1],
                             'reasons': reasons, 'name_matches': positions,
                             'code_matches': code_positions(record, row['세부품명번호']), 'max_cosine': float(best[i]),
                             'best_query': qi})
        selected.append({'id': record['id'], 'source': str(CATALOG.relative_to(ROOT)),
                         'source_sha256': sha(CATALOG), 'header': raw_lines[0], 'candidates': hits,
                         'queries': [{**c, 'text_sha256': digest(c['text'])} for c in chunks]})
        if (ri + 1) % 20 == 0:
            print(json.dumps({'stage': 'reference_selection', 'records': ri + 1, 'seconds': time.monotonic() - started}), flush=True)
    out = RUNS['CJH']
    write_jsonl(out / 'product_candidates.jsonl.gz', selected)
    dump(out / 'selection_protocol.json', {**SELECTOR, 'source_sha256': sha(CATALOG),
         'index_manifest_sha256': sha(ROOT / 'model/legal_index/manifest.json'),
         'index_artifacts': index.manifest['artifacts'], 'encoder': encoder.signature,
         'seconds': time.monotonic() - started, 'records': len(records),
         'candidate_counts': {r['id']: len(r['candidates']) for r in selected}})
    return selected


def prepare():
    from nara.inference.engine import TokenCounter

    started = time.monotonic()
    records = read_jsonl(ROOT / 'data/dev.jsonl')
    assert len(records) == 200 and len({r['id'] for r in records}) == 200
    for out in RUNS.values():
        assert not (out / 'manifest.json').exists(), 'Frozen inputs cannot be overwritten'
    candidates_path = RUNS['CJH'] / 'product_candidates.jsonl.gz'
    if not candidates_path.exists():
        select_catalog(records)
    candidates = {r['id']: r for r in read_jsonl(candidates_path)}
    assert set(candidates) == {r['id'] for r in records}
    counter = TokenCounter(MODEL, thinking=False, max_model_len=CONTEXT)
    failures = []
    for author, out in RUNS.items():
        cards, original_paths = cards_for(author)
        laws, law_provenance, law_hashes = {}, {}, {}
        for feature in FEATURES[author]:
            spec = json.loads((out / 'law_specs' / (feature + '.json')).read_text())
            laws[feature], law_provenance[feature], hashes = law_material(spec)
            law_hashes.update(hashes)
        dump(out / 'laws.json', laws)
        dump(out / 'law_provenance.json', law_provenance)
        dump(out / 'cards.json', cards)
        dump(out / 'evaluation_protocol.json', PARSING)
        counts, all_requests, prefixes = [], {f: [] for f in FEATURES[author]}, {}
        for record in records:
            common = common_input(record, candidates[record['id']] if author == 'CJH' else None)
            rendered = []
            for feature in FEATURES[author]:
                messages = card_messages(common, laws[feature], cards[feature])
                content = messages[0]['content']
                tokens = counter.render_messages(messages)
                rendered.append(tokens)
                request = {'id': record['id'], 'feature': feature, 'task_id': record['id'] + ':' + feature,
                           'messages': messages, 'input_tokens': len(tokens), 'prompt_sha256': digest(content),
                           'prompt_token_ids': tokens, 'prompt_tokens_sha256': digest(json.dumps(tokens, separators=(',', ':'))),
                           'card_sha256': digest(cards[feature]), 'law_sha256': digest(laws[feature])}
                assert content.endswith(cards[feature])
                assert all(doc['text'] in content for doc in record['docs'])
                all_requests[feature].append(request)
                check = {k: v for k, v in request.items() if k not in ('messages', 'prompt_token_ids')}
                check['fits'] = len(tokens) + 512 <= CONTEXT
                counts.append(check)
                if not check['fits']:
                    failures.append({'author': author, **check})
            shared = 0
            for column in zip(*rendered):
                if len(set(column)) != 1:
                    break
                shared += 1
            assert shared > 0
            prefixes[record['id']] = shared
        for feature, requests in all_requests.items():
            write_jsonl(out / 'requests' / (feature + '.jsonl.gz'), requests)
        dump(out / 'preflight.json', {'requests': counts, 'common_prefix_tokens': prefixes,
             'max_input_tokens': max(c['input_tokens'] for c in counts),
             'law_tokens': {f: counter.count_text(s) for f, s in laws.items()},
             'card_tokens': {f: counter.count_text(s) for f, s in cards.items()},
             'overflow_count': sum(not c['fits'] for c in counts)})
        original_hashes = {}
        for path in original_paths:
            name = path.relative_to(ROOT)
            dest = out / 'source' / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
            original_hashes[str(name)] = sha(path)
        sources = ['src/experiments/colleague_cards.py', 'src/evaluation/colleague_cards.py',
                   'src/inference/engine.py', 'src/inference/conversation.py', 'src/inference/predictor.py',
                   'src/retrieval/search.py', 'src/evaluation/reporting.py', 'pyproject.toml', 'uv.lock']
        for name in sources:
            path = ROOT / name
            if not path.exists():
                raise ValueError('Missing experiment source: ' + name)
            dest = out / 'source' / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
            original_hashes[name] = sha(path)
        input_hashes = {'data/dev.jsonl': sha(ROOT / 'data/dev.jsonl'), **original_hashes, **law_hashes}
        for name in ('config.json', 'tokenizer.json', 'tokenizer_config.json', 'chat_template.jinja'):
            path = MODEL / name
            if path.exists():
                input_hashes[str(path.relative_to(ROOT))] = sha(path)
        if author == 'CJH':
            input_hashes[str(CATALOG.relative_to(ROOT))] = sha(CATALOG)
        artifacts = list((out / 'requests').glob('*.gz')) + list((out / 'law_specs').glob('*.json'))
        artifacts += [out / n for n in ('cards.json', 'laws.json', 'law_provenance.json', 'preflight.json', 'evaluation_protocol.json')]
        if author == 'CJH':
            artifacts += [out / 'product_candidates.jsonl.gz', out / 'selection_protocol.json', out / 'selection_preflight.json']
        dump(out / 'manifest.json', {'author': author, 'features': FEATURES[author], 'records': 200,
             'requests': len(counts), 'instruction': INSTRUCTION, 'input_hashes': input_hashes,
             'artifact_hashes': {str(p.relative_to(out)): sha(p) for p in artifacts},
             'model': str(MODEL.relative_to(ROOT)), 'thinking': False, 'temperature': 0, 'seed': 0,
             'output_tokens': 512, 'max_model_len': CONTEXT, 'max_num_seqs': 16,
             'max_num_batched_tokens': 8192, 'structured_decoding': False, 'retries': 0,
             'schedule': {'initial_records': 2, 'max_live_records': 3, 'max_live_source_tokens': 48000, 'lookahead_groups': 16},
             'source_mode': 'authored_cards_verbatim_with_user_approved_static_references',
             'selection_is_experimenter_choice': True, 'extended_context_this_experiment_only': True, 'default_context_unchanged': 32768, 'preparation_seconds_cumulative': time.monotonic() - started,
             'ready': not any(not c['fits'] for c in counts)})
        print(json.dumps({'stage': 'prepared', 'author': author, 'requests': len(counts),
                          'max_input_tokens': max(c['input_tokens'] for c in counts)}, ensure_ascii=False), flush=True)
    if failures:
        raise ValueError('Context overflow; no inference permitted: ' + json.dumps(failures, ensure_ascii=False))


def schedule(stream, requests, record_ids, features, source_tokens, on_reply, *, now=time.monotonic, events=None):
    """Execute prepared independent requests under the baseline admission policy."""
    ready, flights, live = deque(), {}, {}
    events = [] if events is None else events
    next_index = 0

    def admit(reason):
        nonlocal next_index
        if next_index == len(record_ids):
            return False
        rid = record_ids[next_index]
        total = sum(source_tokens[r] for r in live) + source_tokens[rid]
        if len(live) >= 3 or (live and total > 48000):
            return False
        live[rid] = set(features)
        ready.appendleft((rid, features[0]))
        next_index += 1
        events.append({'event': 'admit', 'id': rid, 'reason': reason, 'time': now(),
                       'live_ids': list(live), 'live_source_tokens': total, 'inflight': len(flights)})
        return True

    for _ in range(2):
        if not admit('startup'):
            break
    ready.reverse()
    try:
        while ready or flights or next_index < len(record_ids):
            while len(flights) < 16:
                outstanding = sum(len(todo - {features[0]}) for todo in live.values())
                seed_pending = any(features[0] in todo for todo in live.values())
                if not live:
                    admit('empty_pipeline')
                elif not seed_pending and outstanding <= 16:
                    admit('lookahead')
                if not ready:
                    break
                chosen = next((task for task in ready if task[1] == features[0]), ready[0])
                ready.remove(chosen)
                request = requests[chosen]
                from nara.inference.conversation import Turn
                turn = Turn(request['task_id'], request['messages'], {}, 512)
                stream.submit(turn)
                flights[turn.task_id] = chosen
            if flights:
                for task_id, reply in stream.poll():
                    rid, feature = flights.pop(task_id)
                    on_reply(requests[(rid, feature)], reply)
                    live[rid].remove(feature)
                    if feature == features[0]:
                        ready.extend((rid, f) for f in features[1:])
                    if not live[rid]:
                        del live[rid]
                        events.append({'event': 'record_complete', 'id': rid, 'time': now(), 'live_ids': list(live)})
            elif not ready and live:
                raise RuntimeError('No runnable task in live notice window')
    except BaseException as exc:
        events.append({'event': 'execution_aborted', 'time': now(), 'error': repr(exc),
                       'flights': flights, 'ready': list(ready), 'live': {k: sorted(v) for k, v in live.items()},
                       'engine_pending': {rid: item[0].task_id for rid, item in stream.pending.items()}})
        stream.abort()
        raise
    return events


def run():
    from nara.inference.engine import VLLMModel
    from nara.inference.conversation import Reply, Turn
    from vllm import SamplingParams
    from vllm.sampling_params import RequestOutputKind

    class RawCardModel(VLLMModel):
        _context_limit = CONTEXT

        def _tokens(self, messages):
            tokens = super()._tokens(messages)
            key = digest(messages[0]['content'])
            if key in self.expected_prompts:
                assert tokens == self.expected_prompts[key], 'Runtime prompt differs from frozen template tokens'
            return tokens

        def _sampling(self, turn, *, incremental=False):
            return SamplingParams(temperature=0, seed=0, max_tokens=turn.max_tokens,
                                  skip_special_tokens=True, output_kind=RequestOutputKind.FINAL_ONLY)

        def _reply(self, output, budget):
            completion = output.outputs[0]
            self.raw_outputs[output.request_id] = {'token_ids': list(completion.token_ids),
                'decoded_with_special_tokens': self.tokenizer.decode(completion.token_ids, skip_special_tokens=False),
                'stop_reason': completion.stop_reason}
            return Reply(completion.text, completion.finish_reason,
                         len(output.prompt_token_ids), len(completion.token_ids))

    prepared = {}
    for author, out in RUNS.items():
        assert not (out / 'responses').exists(), 'One pass only; preserve existing responses'
        manifest = json.loads((out / 'manifest.json').read_text())
        assert manifest['ready']
        for path, value in manifest['input_hashes'].items():
            assert sha(ROOT / path) == value, path
        for path, value in manifest['artifact_hashes'].items():
            assert sha(out / path) == value, path
        requests = {(r['id'], r['feature']): r for f in FEATURES[author]
                    for r in read_jsonl(out / 'requests' / (f + '.jsonl.gz'))}
        assert len(requests) == manifest['requests']
        preflight = json.loads((out / 'preflight.json').read_text())
        prepared[author] = (requests, preflight)
    tick = time.monotonic()
    assert json.loads((MODEL / 'config.json').read_text())['text_config']['max_position_embeddings'] >= CONTEXT
    model = RawCardModel(MODEL, max_model_len=CONTEXT, thinking=False, max_num_seqs=16, max_num_batched_tokens=8192,
                         enable_chunked_prefill=True, collect_scheduler_stats=True)
    model.raw_outputs = {}
    model.expected_prompts = {r['prompt_sha256']: r['prompt_token_ids']
                              for requests, _ in prepared.values() for r in requests.values()}
    load_seconds = time.monotonic() - tick
    tick = time.monotonic()
    warm = model.generate([Turn('infrastructure-warmup', [{'role': 'user', 'content': '1'}], {}, 1)])
    warmup_seconds = time.monotonic() - tick
    for author, out in RUNS.items():
        requests, preflight = prepared[author]
        assert model.reset_prefix_cache()
        model.raw_outputs.clear()
        stream = model.stream()
        (out / 'responses').mkdir()
        handles = {f: (out / 'responses' / (f + '.jsonl')).open('x') for f in FEATURES[author]}
        completed = []
        events, steps = [], []
        tick = time.monotonic()

        def on_reply(request, reply):
            # poll() may finish several requests together; route by task ID.
            stats = next(row for row in reversed(stream.rows) if row['task_id'] == request['task_id'])
            row = {'id': request['id'], 'feature': request['feature'], 'task_id': request['task_id'],
                   'prompt_sha256': request['prompt_sha256'], **asdict(reply),
                   **model.raw_outputs[stats['request_id']]}
            handles[request['feature']].write(json.dumps(row, ensure_ascii=False) + '\n')
            handles[request['feature']].flush()
            model.raw_outputs.pop(stats['request_id'])
            completed.append(request['task_id'])
            if len(completed) % 100 == 0:
                dump(out / 'progress.json', {'completed': len(completed), 'total': len(requests), 'seconds': time.monotonic() - tick})
                print(json.dumps({'author': author, 'completed': len(completed), 'seconds': time.monotonic() - tick}), flush=True)

        try:
            with model.observe_scheduler() as steps:
                schedule(stream, requests, list(preflight['common_prefix_tokens']), FEATURES[author],
                         preflight['common_prefix_tokens'], on_reply, events=events)
            elapsed = time.monotonic() - tick
        except BaseException as exc:
            dump(out / 'failure.json', {'error': repr(exc), 'completed': completed,
                 'unfinished': sorted(set(r['task_id'] for r in requests.values()) - set(completed)),
                 'unconsumed_raw_outputs': model.raw_outputs})
            raise
        finally:
            for handle in handles.values():
                handle.close()
            write_jsonl(out / 'request_timings.jsonl', stream.rows)
            write_jsonl(out / 'lifecycle.jsonl', stream.lifecycle)
            write_jsonl(out / 'admissions.jsonl', events)
            write_jsonl(out / 'scheduler.jsonl', steps)
        assert len(completed) == len(requests) and len(set(completed)) == len(requests)
        write_jsonl(out / 'admissions.jsonl', events)
        write_jsonl(out / 'scheduler.jsonl', steps)
        dump(out / 'runtime.json', {'inference_seconds': elapsed, 'model_load_seconds': load_seconds,
             'warmup_seconds': warmup_seconds, 'model_shared_across_suites': True,
             'execution_order': list(RUNS), 'requests': len(completed), 'engine': model.engine_info(),
             'cache_reset_before_suite': True, 'retries': 0})
        dump(out / 'progress.json', {'completed': len(completed), 'total': len(requests), 'seconds': elapsed})
        print(json.dumps({'stage': 'complete', 'author': author, 'seconds': elapsed}), flush=True)


def main():
    install_input_guard()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['select', 'prepare', 'run'])
    args = parser.parse_args()
    if args.stage == 'select':
        path = RUNS['CJH'] / 'product_candidates.jsonl.gz'
        assert not path.exists(), 'Do not overwrite frozen selection'
        select_catalog(read_jsonl(ROOT / 'data/dev.jsonl'))
    elif args.stage == 'prepare':
        prepare()
    else:
        run()


if __name__ == '__main__':
    main()
