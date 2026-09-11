"""Render the review document from the same criteria used by Predictor."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
criteria = json.loads((ROOT / 'nara/legal_criteria.json').read_text())
table = json.loads((ROOT / 'data/항목표.json').read_text())['항목']
context = json.loads((ROOT / 'analysis/legal_criteria_v1_context.json').read_text())
parts = ['# 24개 feature 법령 판단 기준',
         f"버전: `{criteria['version']}` · 대회 기준일: {criteria['snapshot_date']} · 작성일: 2026-09-10",
         criteria['derivation'],
         '이 문서는 모델에 추가하는 기준과 동일한 JSON에서 생성했다. 조문 요약과 대회 feature의 판정 해석을 구분한다. 공식 정답 기준이 확인되지 않은 부분은 검토 메모에 남겼다. 이번 작업에서는 추가 추론이나 정확도 평가를 실행하지 않았다.',
         '## 공통 판단 순서',
         '\n'.join(f'{i}. {line}' for i,line in enumerate(criteria['common'], 1)),
         '## 관련 법령의 핵심 내용',
         '| 법령·자료 | 핵심 내용 |\n|---|---|']
for key,source in criteria['sources'].items():
    parts.append(f"| [{key}](<../{source['path']}>) | {source['summary']} |")
parts += ['', '## 항목별 판단 기준']
for key,rule in criteria['items'].items():
    parts += [f"### {key} · {rule['name']}",
              f"**적용 조건:** {rule['applies_if']}",
              f"**위반으로 판단하는 경우:** {rule['violation_if']}",
              f"**예외와 혼동 방지:** {rule['exceptions']}"]
    if rule.get('review_note'):
        parts.append('**검토 메모:** ' + rule['review_note'])
    links=[]
    for ref in rule['references']:
        source=criteria['sources'][ref.split()[0]]
        links.append(f"[{ref}](<../{source['path']}>)")
    parts.append('**확인한 근거:** ' + ('; '.join(links) if links else '조문 없는 문서·메타 대조형 항목.'))
    parts.append('**원래 항목표 매핑:** 국가 — '+table[key]['국가계약법']+' / 지방 — '+table[key]['지방계약법'])
parts += ['## 해석상 남은 한계',
          '- v3: 항목표의 ≥1배·사업예산과 조문의 ≤1배·추정가격이 다르다. 초안은 조문상 1배 초과를 사용한다. 공식 채점 경계와 일치한다고 검증한 것은 아니다.\n- v5: 지방규칙 제24조가 참조하는 행안부 고시 원문이 동봉 파일 목록에 없어 해당 분기의 금액은 미확정이다. 다른 목적의 국가 고시금액을 대입하지 않는다.\n- v14~18: 항목명의 “일반물품”은 이 초안에서 연결 조문의 대상인 일반 물품·용역으로 해석했다. 이는 판정 구현의 해석이며 별도의 공식 답변을 확인한 것은 아니다.\n- 부재탐지는 제공된 공고·첨부의 요건 누락을 판단하는 대회 항목이다. 실제 계약 담당자가 별도로 어떤 확인을 했는지까지 추정하는 기준은 아니다.',
          '## 프롬프트 연결과 32K 검사',
          '`script.py --legal-criteria`를 지정하면 공통 기준과 현재 판단할 항목의 상세 기준·조문을 시스템 프롬프트에 추가한다. 기존 기본 프롬프트는 유지한다. 항목 분할은 기존 `--item-group-size` 옵션을 사용하며 자동 분할·원문 잘라내기는 하지 않는다.',
          '검사 조건: Gemma 로컬 토크나이저, thinking 활성화, dev 200건, 컨텍스트 32,768. 출력 예산과 128토큰을 예약했다. 초기 입력만 검사했으므로 검색 결과·재시도까지 포함한 실행 성공을 보장하지 않는다.',
          '| 회당 항목 수 | 총 호출 작업 수 | 최대 입력 토큰 | 출력 2,048일 때 초과 공고 | 출력 4,096일 때 초과 공고 |\n|---:|---:|---:|---:|---:|']
for row in context['configurations']:
    budgets={b['output_tokens']:b for b in row['budgets']}
    parts.append(f"| {row['group_size']} | {row['tasks']:,} | {row['max_input_tokens']:,} | {budgets[2048]['source_failures']} / 200 | {budgets[4096]['source_failures']} / 200 |")
parts += ['', '1항목씩/출력 2,048 설정은 초기 입력이 전부 들어가지만 최대 입력의 추가 여유가 39토큰뿐이며 호출 수가 4,800개다. 현재 thinking 기본 출력 4,096에서는 이 설정도 7건이 넘는다. 따라서 다음 실험 전에 기준 압축 또는 긴 문서 처리 방식을 정해야 한다. 위 호출 작업 수는 초기 작업 기준이며 검색·재시도는 추가 호출이다.',
          '검증: `uv run --locked python -m unittest discover -s tests -v` — 26개 통과. 기준 24개 전체 포함, 원본 파일 SHA-256, 그룹별 기준 선택, 입력 원문 보존 및 라벨 격리를 확인했다. 법률 해석의 정답성이나 개선된 F1을 검증한 테스트는 아니다.',
          '재생성: `uv run --locked python scripts/check_legal_criteria.py` 후 `uv run --locked python scripts/render_legal_criteria.py`.',
          '파일: [판단 기준 JSON](../nara/legal_criteria.json), [실제 전체 시스템 프롬프트](legal_criteria_v1_system_prompt.txt), [200건 토큰 검사](legal_criteria_v1_context.json).']
# Keep source table and budget table rows adjacent while separating prose blocks.
text=''
for part in parts:
    if part.startswith('|') and text.rstrip().endswith('|'):
        text=text.rstrip()+'\n'+part+'\n'
    else:
        text=text.rstrip()+'\n\n'+part+'\n'
(ROOT/'analysis/feature_legal_criteria_v1.md').write_text(text.lstrip())
