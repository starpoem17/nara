"""Verify frozen original-prompt fidelity without loading a model or labels."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]


def main():
    spec=importlib.util.spec_from_file_location('frozen_ljm',OUT/'source/user/LJM/v4_v7_candidate_extractor.py')
    ext=importlib.util.module_from_spec(spec);sys.modules[spec.name]=ext;spec.loader.exec_module(ext)
    loadl=lambda p:[json.loads(line) for line in p.read_text().splitlines()]
    extracted={r['id']:r for r in loadl(OUT/'extractor/extracted.jsonl')}
    records=loadl(ROOT/'data/dev.jsonl')
    assert all(ext.extract_candidates(r)==extracted[r['id']] for r in records)
    cards=json.loads((OUT/'laws.json').read_text())
    requests=loadl(OUT/'extractor/requests.jsonl')
    assert len(requests)==800 and len(extracted)==200
    assert len({(r['id'],r['feature']) for r in requests})==800
    for r in requests:
        prompt=ext.gemma_prompt(extracted[r['id']],r['feature'])
        expected=prompt.replace('관련 법령·고시금액을 검색한 뒤','제공된 법령·고시금액을 사용한 뒤')+'\n제공 법령:\n'+cards[r['feature']]
        assert r['messages']==[{'role':'user','content':expected}]
        assert hashlib.sha256(prompt.encode()).hexdigest()==r['original_prompt_sha256']
    for path in (OUT/'source/user/LJM').glob('*.py'):
        assert path.read_bytes()==(ROOT/'user/LJM'/path.name).read_bytes()
    manifest=json.loads((OUT/'manifest.json').read_text())
    for path,digest in manifest['artifact_hashes'].items():
        assert hashlib.sha256((OUT/path).read_bytes()).hexdigest()==digest,path
    for parts in json.loads((OUT/'law_provenance.json').read_text()).values():
        for part in parts:
            source=ROOT/part['path']
            assert hashlib.sha256(source.read_bytes()).hexdigest()==part['source_sha256']
            lines=source.read_text().splitlines()
            assert '\n'.join(lines[i-1] for i in part['included_lines'])==part['raw']
            # Exact allowed deletion transform, independently reconstructed.
            import re
            text=re.sub(r'<(?:개정|신설|전문개정|제목개정|본조신설|종전)[^>]*>','',part['raw'])
            text=re.sub(r'\[(?:전문개정|제목개정|본조신설|종전)[^\]]*\]','',text)
            text=text.replace('<![CDATA[','').replace(']]>','')
            text='\n'.join(line.rstrip() for line in text.splitlines() if line.strip()).strip()
            assert text==part['text']
    result={'requests_verified':800,'original_sources_byte_identical':True,'single_allowed_prompt_replacement':True,
            'full_original_extraction_json':True,'extraction_recomputed_exactly':200,'no_extra_system_prompt':True,
            'law_text_exact_allowed_deletions':True,'manifest_hashes_match':True}
    responses=OUT/'extractor/responses.jsonl'
    if (OUT/'runtime.json').exists():
        rows=loadl(responses)
        assert len(rows)==800
        assert {(r['id'],r['feature']) for r in rows}=={(r['id'],r['feature']) for r in requests}
        token_counts={(r['id'],r['feature']):r['input_tokens'] for r in requests}
        assert all(r['input_tokens']==token_counts[r['id'],r['feature']] for r in rows)
        result['responses_verified']=800
        result['all_input_token_counts_match']=True
    (OUT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__': main()
