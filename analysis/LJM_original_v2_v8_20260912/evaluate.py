"""Read complete JSON code blocks without repairing any model judgment.

The original frozen scorer remains intact. This evaluation-only adapter records
code fences as instruction-format violations while exposing their unchanged JSON
payload for descriptive judgment metrics. It never changes inference inputs.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
from collections import Counter

OUT=Path(__file__).resolve().parent
FENCE=re.compile(r'\A```(?:json)?[ \t]*\r?\n(?P<body>[\s\S]*?)\r?\n```[ \t]*\Z',re.IGNORECASE)
spec=importlib.util.spec_from_file_location('frozen_score',OUT/'score.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
strict_parse=base.parse


def read_response(raw,feature):
    obj,issues=strict_parse(raw,feature)
    if obj is not None: return obj,issues
    match=FENCE.fullmatch(raw.strip())
    if not match: return obj,issues
    obj,issues=strict_parse(match['body'],feature)
    return obj,['markdown_code_fence',*issues]


def main():
    protocol=json.loads((OUT/'evaluation_protocol.json').read_text())
    assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==protocol['evaluate_sha256']
    base.parse=read_response
    base.main()
    rows=base.loadl(OUT/'extractor/responses.jsonl')
    diagnostics=Counter()
    for row in rows:
        strict_obj,_=strict_parse(row['response'],row['feature'])
        diagnostics['strict_json_objects']+=strict_obj is not None
        _,issues=read_response(row['response'],row['feature'])
        diagnostics.update(issues)
    result=json.loads((OUT/'evaluation.json').read_text())
    result['response_format_diagnostics']=dict(diagnostics)
    result['evaluate_sha256']=protocol['evaluate_sha256']
    result['evaluation_protocol']=protocol
    base.dump(OUT/'evaluation.json',result)
    report=OUT.parents[1]/'docs/reports/analysis'/OUT.name/'report.md'
    text=report.read_text().replace(f'{OUT.name}/score.py',f'{OUT.name}/evaluate.py')
    text=text.replace('run.py, score.py, law_specs/', 'run.py, score.py, evaluate.py, evaluation_protocol.json, law_specs/')
    text+='''\n## 응답 형식과 판정 해석을 구분한 평가\n\n원본 프롬프트는 JSON만 요구했지만 모델은 응답을 마크다운 코드블록으로 감쌌다. 초기 고정 scorer의 엄격한 JSON 파서는 이를 읽지 못한다. 원응답과 고정 scorer는 변경하지 않았다. `evaluate.py`는 응답 전체가 JSON 코드블록 하나인 경우에만 바깥 구분자를 벗겨 내부 JSON을 읽는다. 설명 앞뒤의 임의 문장 제거, JSON 수정, 필드 보충, 판정 값 변경은 하지 않는다.\n\n코드블록은 `markdown_code_fence` 형식 이슈로 계속 집계한다. 따라서 형식 이슈 수와 읽을 수 없는 판정 수는 다르다. `comparison` 등에 원본 예시와 다른 자료형이 나온 경우도 그대로 보존하고 별도 집계한다. 이는 결과를 읽기 위한 평가 처리이며 모델 재호출이나 실험 입력 수정이 아니다. 평가 처리 기준과 코드 해시는 `evaluation_protocol.json`에 별도로 고정했다.\n\n'''
    text+='```json\n'+json.dumps(dict(diagnostics),ensure_ascii=False,indent=2)+'\n```\n'
    report.write_text(text)


if __name__=='__main__':main()
