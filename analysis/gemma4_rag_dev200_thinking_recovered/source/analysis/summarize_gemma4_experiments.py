"""Summarize the three requested, fixed dev200 experiments after evaluation."""
import json
from pathlib import Path

root = Path('analysis')
folders = ['gemma4_rag_dev200_v1', 'gemma4_rag_dev200_forced1', 'gemma4_rag_dev200_thinking_recovered']
names = ['Thinking OFF · 자율 검색', 'Thinking OFF · 검색 1회 강제', 'Thinking ON · 자율 검색']
runs = [json.loads((root / name / 'evaluation.json').read_text()) for name in folders]
assert all(r['records'] == 200 and r['runtime']['failed'] == 0 for r in runs)
assert len({r['sha256']['data/dev.jsonl'] for r in runs}) == 1
assert len({r['sha256']['data/dev_labels.csv'] for r in runs}) == 1
selected = json.loads((root / folders[-1] / 'manifest.json').read_text())
assert selected['selected_search'] == 'optional max 2 rounds'
assert runs[0]['macro_f1'] > runs[1]['macro_f1']
rows = []
for name, folder, run in zip(names, folders, runs):
    rows.append({'experiment': name, 'folder': folder, 'macro_f1': run['macro_f1'],
                 'micro_f1': run['micro_f1'], 'true_positives': sum(r['tp'] for r in run['per_item']),
                 'false_positives': run['false_positives'], 'false_negatives': run['false_negatives'],
                 'exact_match_records': run['exact_match_records'], 'searched_records': run['searched_records'],
                 'seconds': run['runtime']['total_seconds']})
best = max(rows, key=lambda r: r['macro_f1'])
result = {'experiments': rows, 'best_macro_f1': best['experiment'],
          'forced_vs_optional_delta': runs[1]['macro_f1'] - runs[0]['macro_f1'],
          'thinking_vs_off_delta': runs[2]['macro_f1'] - runs[0]['macro_f1']}
(root / 'gemma4_experiments_summary.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
lines = ['# Gemma 4 dev200 실험 비교', '',
         '| 조건 | Macro F1 | Micro F1 | 위반 검출 / 153 | 오탐 | 미탐 | 완전 일치 공고 / 200 | 검색 공고 / 200 | 시간(초) |',
         '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
for r in rows:
    lines.append(f'| {r["experiment"]} | {r["macro_f1"]:.6f} | {r["micro_f1"]:.6f} | {r["true_positives"]} | '
                 f'{r["false_positives"]} | {r["false_negatives"]} | {r["exact_match_records"]} | '
                 f'{r["searched_records"]} | {r["seconds"]:.2f} |')
lines += ['', f'세 실험 중 Macro F1이 가장 높은 조건: **{best["experiment"]} ({best["macro_f1"]:.6f})**.',
          f'강제 검색의 Macro F1 변화: {result["forced_vs_optional_delta"]:+.6f}.',
          f'Thinking ON의 Macro F1 변화(같은 자율 검색 OFF 대비): {result["thinking_vs_off_delta"]:+.6f}.',
          '', '## 실험 조건과 선택 근거', '',
          '- 같은 dev 200건, 24항목, Gemma 4 26B A4B NVFP4, RTX 5090, 32,768토큰 문맥, 배치 8, temperature 0, seed 0.',
          '- 공고당 한 대화에서 24항목 판정. 기본 생성 한도는 세 실험 모두 2,048토큰. Thinking의 실패 1건만 복구 실행에서 4,096토큰을 사용했다.',
          '- 강제 검색은 첫 응답을 검색 JSON으로 제한하고 검색 후 최종 판정. 실제 200건 모두 검색 결과가 문맥에 들어갔다.',
          '- 긴 공고의 강제 검색어 생성 한도만 남은 문맥에 맞춰 축소했다. 원문과 법령 passage를 자르지 않았다.',
          '- 검색·생성 외 판단 지침, 입력, 모델 가중치와 법령 인덱스는 유지했다. 강제 검색 안내 문구와 최대 검색 횟수는 해당 정책에 맞췄다.',
          '- Thinking의 검색 정책은 앞선 두 실험의 Macro F1로 선택했다. 비강제 0.165237이 강제 0.164157보다 높아 자율 검색 최대 2회를 선택했다.',
          '- Thinking ON의 시스템 프롬프트 본문은 첫 비강제 실험과 정확히 같다. Gemma thinking 템플릿과 엔진 예산을 활성화했다.',
          '- vLLM thinking_token_budget=1024로 설정해 최종 JSON 공간을 남겼다. 이는 thinking 무제한 실험이 아니다. 일부 응답은 종료 구분자가 누락되거나 JSON이 잘려 재시도가 필요했다.',
          f'- 재시도를 포함해 Thinking 텍스트가 확인된 응답 {runs[2]["thinking_turns"]}개, 텍스트 토큰 합계 {runs[2]["thinking_text_tokens"]:,}. 공유용 병합 trace에서는 분리되지 않은 비정상 출력도 제외했다.',
          '- 최초 Thinking 실행은 199/200 성공. PPS-DEV-191 한 건을 같은 프롬프트·thinking 예산과 출력 한도 4096으로 복구했다. 표의 시간에는 최초 전체 실행과 복구 실행을 모두 포함했다.',
          '- 입력 문서 절단이나 실패 판정의 0 대체 없음. 정답 라벨은 추론 입력에 포함하지 않았고, 세 실험의 전체 입력·정답·예측 ID를 검증했다.',
          '', '## 해석 범위', '',
          '- 같은 dev 데이터를 검색 설정 선택과 평가에 함께 사용한 탐색적 결과다. 독립 테스트 점수나 통계적 유의성을 주장하지 않는다.',
          '- 제공 dev 분포는 실제 평가 분포를 대표하지 않는다. 로컬 NVFP4 모델 결과이며 대회 서버 INT8 결과와 구별한다.',
          '- 정확도는 비위반 비중의 영향을 받는다. 모든 판정을 0으로 내면 정확도 96.81%, Macro F1 0이다.',
          '', '## 상세 결과', '']
for name, folder in zip(names, folders):
    lines.append(f'- {name}: [항목별 평가]({folder}/evaluation.md), [오탐·미탐]({folder}/errors.csv), [실행 설정]({folder}/report.json)')
lines += ['', '각 폴더의 source/, system_prompt.txt, manifest.json, command.txt에 코드·프롬프트·해시·명령을 보존했다. 재추론은 새 출력 폴더를 지정한다.']
(root / 'gemma4_experiments_summary.md').write_text('\n'.join(lines) + '\n')
print(json.dumps(result, ensure_ascii=False, indent=2))
