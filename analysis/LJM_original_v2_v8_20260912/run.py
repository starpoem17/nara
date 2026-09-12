"""Independent, single-run execution of the two unchanged LJM modules."""
from __future__ import annotations
import argparse
import csv
import gzip
import hashlib
import importlib.util
import importlib.metadata
import platform
import json
from pathlib import Path
import re
import shutil
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
MODEL = ROOT / 'models/gemma-4-26B-A4B-it-NVFP4'
FEATURES = ['v4', 'v5', 'v6', 'v7']
MAX_OUTPUT = 2048
BATCH = 8
SEARCH = '관련 법령·고시금액을 검색한 뒤'
PROVIDED = '제공된 법령·고시금액을 사용한 뒤'


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')


def loadl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def clean_law(text):
    # Deletions only: amendment history and serialization debris, not legal wording.
    text = re.sub(r'<(?:개정|신설|전문개정|제목개정|본조신설|종전)[^>]*>', '', text)
    text = re.sub(r'\[(?:전문개정|제목개정|본조신설|종전)[^\]]*\]', '', text)
    text = text.replace('<![CDATA[', '').replace(']]>', '')
    return '\n'.join(line.rstrip() for line in text.splitlines() if line.strip()).strip()


def laws():
    cards, provenance = {}, {}
    for feature in FEATURES:
        spec = json.loads((OUT / 'law_specs' / f'{feature}.json').read_text())
        chunks, parts, seen = {}, [], set()
        for entry in spec['excerpts']:
            path = ROOT / entry['path']
            assert path.resolve().is_relative_to(ROOT / 'data/법령패키지')
            lines = path.read_text().splitlines()
            start, end = entry['start_line'], entry['end_line']
            assert 1 <= start <= end <= len(lines), entry
            indices = [i for i in range(start, end + 1) if (entry['path'], i) not in seen]
            seen.update((entry['path'], i) for i in indices)
            if not indices:
                continue
            raw = '\n'.join(lines[i-1] for i in indices)
            text = clean_law(raw)
            assert text
            # Verify cleanup introduced no characters or reordered original text.
            iterator = iter(raw)
            assert all(any(c == x for x in iterator) for c in text)
            title = lines[0].strip()
            chunks.setdefault(title, []).append(f'[{entry["locator"]}]\n{text}')
            parts.append({**entry, 'included_lines': indices, 'source_sha256': sha(path),
                          'source_header': lines[:7], 'raw': raw, 'text': text})
        cards[feature] = '\n\n'.join(f'[{title}]\n' + '\n\n'.join(sections) for title, sections in chunks.items())
        provenance[feature] = parts
    return cards, provenance


def prepare():
    from nara.inference.engine import TokenCounter
    assert not (OUT / 'manifest.json').exists(), 'Existing prepared run is immutable'
    records = loadl(ROOT / 'data/dev.jsonl')
    assert len(records) == 200 and len({r['id'] for r in records}) == 200
    snapshot = OUT / 'source/user/LJM'
    snapshot.mkdir(parents=True, exist_ok=True)
    for name in ['scan_candidates.py', 'v4_v7_candidate_extractor.py']:
        shutil.copy2(ROOT / 'user/LJM' / name, snapshot / name)
    scanner = module('ljm_scanner_original', snapshot / 'scan_candidates.py')
    extractor = module('ljm_extractor_original', snapshot / 'v4_v7_candidate_extractor.py')
    scan_dir = OUT / 'scanner'
    scan_dir.mkdir(exist_ok=True)
    packed = scan_dir / 'input.jsonl.gz'
    with gzip.open(packed, 'wt', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    scanner.ROOT, scanner.path = scan_dir, packed
    started = time.monotonic()
    scanner.main()
    scanner_seconds = time.monotonic() - started
    packed.unlink()
    started = time.monotonic()
    extracted = [extractor.extract_candidates(r) for r in records]
    extractor_seconds = time.monotonic() - started
    jsonl(OUT / 'extractor/extracted.jsonl', extracted)
    cards, provenance = laws()
    dump(OUT / 'law_provenance.json', provenance)
    dump(OUT / 'laws.json', cards)
    counter = TokenCounter(MODEL, thinking=False)
    requests, checks = [], []
    for item in extracted:
        for feature in FEATURES:
            original = extractor.gemma_prompt(item, feature)
            assert original.count(SEARCH) == 1
            adapted = original.replace(SEARCH, PROVIDED)
            content = adapted + '\n제공 법령:\n' + cards[feature]
            assert adapted.replace(PROVIDED, SEARCH) == original
            assert original.endswith(json.dumps(item, ensure_ascii=False) + '\n')
            messages = [{'role': 'user', 'content': content}]
            tokens = counter.count_messages(messages)
            checks.append({'id': item['id'], 'feature': feature, 'input_tokens': tokens,
                           'fits': tokens + MAX_OUTPUT <= counter.max_model_len})
            requests.append({'id': item['id'], 'feature': feature, 'messages': messages,
                             'original_prompt_sha256': hashlib.sha256(original.encode()).hexdigest(),
                             'input_tokens': tokens})
    dump(OUT / 'preflight.json', {'requests': checks, 'law_tokens': {k: counter.count_text(v) for k,v in cards.items()},
                                 'max_input_tokens': max(r['input_tokens'] for r in checks),
                                 'overflows': [r for r in checks if not r['fits']]})
    assert all(r['fits'] for r in checks), 'Cannot truncate LJM inputs; inspect preflight before running'
    jsonl(OUT / 'extractor/requests.jsonl', requests)
    inputs = ['data/dev.jsonl', 'data/항목표.json', 'src/inference/engine.py',
              'user/LJM/scan_candidates.py', 'user/LJM/v4_v7_candidate_extractor.py',
              'uv.lock', 'models/gemma-4-26B-A4B-it-NVFP4/config.json',
              'models/gemma-4-26B-A4B-it-NVFP4/chat_template.jinja',
              'models/gemma-4-26B-A4B-it-NVFP4/tokenizer.json']
    input_hashes = {p: sha(ROOT / p) for p in inputs if (ROOT / p).exists()}
    artifacts = [OUT / 'run.py', OUT / 'score.py', OUT / 'laws.json', OUT / 'law_provenance.json',
                 OUT / 'extractor/requests.jsonl', OUT / 'extractor/extracted.jsonl']
    artifacts += sorted((OUT / 'law_specs').glob('*.json'))
    dump(OUT / 'manifest.json', {'records': 200, 'scanner_features': [f'v{i}' for i in range(2,9)],
        'gemma_features': FEATURES, 'gemma_requests': len(requests), 'model': str(MODEL.relative_to(ROOT)),
        'model_revision': (MODEL / '.cache/huggingface/download/config.json.metadata').read_text().splitlines()[0],
        'python': platform.python_version(),
        'packages': {name: importlib.metadata.version(name) for name in ['vllm','torch','transformers']},
        'temperature': 0, 'seed': 0, 'thinking': False, 'output_tokens': MAX_OUTPUT, 'batch_size': BATCH,
        'max_model_len': 32768, 'structured_decoding': False, 'retries': 0,
        'prompt_replacement': [SEARCH, PROVIDED], 'message_roles': ['user'],
        'candidate_gating': False, 'extra_full_documents': False, 'extra_system_prompt': False,
        'additional_extraction_truncation': False, 'law_source': 'supplied package only',
        'scanner_seconds': scanner_seconds, 'extraction_seconds': extractor_seconds,
        'input_hashes': input_hashes,
        'artifact_hashes': {str(p.relative_to(OUT)): sha(p) for p in artifacts}})
    print(json.dumps({'stage': 'prepared', 'requests': len(requests), 'max_input_tokens': max(r['input_tokens'] for r in checks)}), flush=True)


def run():
    from nara.inference.engine import VLLMModel
    from vllm import SamplingParams
    manifest = json.loads((OUT / 'manifest.json').read_text())
    for path, digest in manifest['input_hashes'].items():
        assert sha(ROOT / path) == digest, path
    for path, digest in manifest['artifact_hashes'].items():
        assert sha(OUT / path) == digest, path
    target = OUT / 'extractor/responses.jsonl'
    assert not target.exists(), 'One run only; existing responses will not be overwritten'
    requests = loadl(OUT / 'extractor/requests.jsonl')
    start = time.monotonic()
    model = VLLMModel(MODEL, thinking=False, max_num_seqs=BATCH)
    load_seconds = time.monotonic() - start
    dump(OUT / 'engine.json', {**model.engine_info(), 'load_seconds': load_seconds})
    params = SamplingParams(temperature=0, seed=0, max_tokens=MAX_OUTPUT, skip_special_tokens=True)
    started = time.monotonic()
    with target.open('x') as stream:
        for offset in range(0, len(requests), BATCH):
            batch = requests[offset:offset+BATCH]
            prompts = [{'prompt_token_ids': model.render_messages(r['messages'])} for r in batch]
            for prompt, request in zip(prompts, batch):
                assert len(prompt['prompt_token_ids']) == request['input_tokens']
            tick = time.monotonic()
            outputs = model.llm.generate(prompts, sampling_params=params, use_tqdm=False)
            seconds = time.monotonic() - tick
            assert len(outputs) == len(batch)
            for request, output in zip(batch, outputs):
                completion = output.outputs[0]
                row = {'id': request['id'], 'feature': request['feature'], 'response': completion.text,
                       'raw_token_text': model.tokenizer.decode(completion.token_ids, skip_special_tokens=False),
                       'finish_reason': completion.finish_reason, 'stop_reason': completion.stop_reason,
                       'input_tokens': len(output.prompt_token_ids), 'output_tokens': len(completion.token_ids),
                       'batch_index': offset//BATCH, 'batch_seconds': seconds}
                stream.write(json.dumps(row, ensure_ascii=False) + '\n')
            stream.flush()
            dump(OUT / 'progress.json', {'completed': offset+len(batch), 'total': len(requests),
                                       'elapsed_seconds': time.monotonic()-started})
            print(json.dumps({'completed': offset+len(batch), 'seconds': round(time.monotonic()-started,2)}), flush=True)
    dump(OUT / 'runtime.json', {'load_seconds': load_seconds, 'inference_seconds': time.monotonic()-started,
                              'requests': len(requests), 'retries': 0})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['prepare', 'run'])
    args = parser.parse_args()
    {'prepare': prepare, 'run': run}[args.stage]()
