"""Summarize timing measurements; projected durations are explicitly estimates."""
import argparse
import csv
import json
from pathlib import Path
from nara.evaluation.reporting import write_report

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--input', default='analysis/grouping_time32')
args = parser.parse_args()
folder = Path(args.input)
r = json.loads((folder/'report.json').read_text())
m = json.loads((folder/'manifest.json').read_text())
assert [row['name'] for row in r['runs']] == ['ungrouped','groups7','groups9','groups12'], 'Benchmark incomplete'
base = r['runs'][0]['seconds']
rows=[]
for run in r['runs']:
    row={k:run[k] for k in ['name','groups','initial_tasks','seconds','seconds_per_notice',
        'model_turns','search_rounds','failed_records','invalid_responses','context_failures',
        'input_tokens','output_tokens','thinking_tokens','model_seconds','retrieval_seconds']}
    row['complete_output_for_all_sampled_notices'] = run['failed_records'] == 0
    row['relative_time']=run['seconds']/base
    row['projected_200_prediction_seconds']=run['seconds_per_notice']*200
    row['projected_200_with_model_load_seconds']=row['projected_200_prediction_seconds']+r['load_seconds']
    rows.append(row)
with (folder/'comparison.csv').open('w',newline='') as stream:
    writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
lines=['# 그룹 분할에 따른 추론 시간',
       '정확도 평가는 하지 않았다. 아래 결과는 동일한 공고 표본에서 실제로 실행한 시간 비교다.',
       f"조건: {r['gpu']}, Gemma 4 26B A4B NVFP4, thinking ON(상한 1,024), 출력 상한 2,048, 문맥 32,768, 배치 8, temperature=0, seed=0. RAG 자율 검색 최대 2회, 재시도 1회. BGE-M3와 Gemma를 함께 GPU에 유지했다.",
       f"표본: dev 200건 중 네 구성의 초기 입력이 모두 들어가는 {m['eligible_records']}건을 길이순으로 나눠 각 구간 중앙의 {m['sample_size']}건을 선택했다. 원래 공고 순서를 유지했고 라벨을 읽지 않았다. 제외된 긴 공고 {len(m['excluded_ids'])}건과 숨겨진 평가 데이터의 처리시간을 대표하지 않는다.",
       '각 그룹은 전체 공고·첨부 원문과 담당 feature의 기준만 받는다. 같은 feature에는 모든 구성에서 같은 기준을 사용했다. 공통 프로토콜은 짧게 통일하고 법령 약칭도 해당 그룹에서 사용하는 것만 포함했다. 기준 JSON의 feature 간 참고 ID는 남을 수 있지만 다른 feature의 독립 판정 기준은 추가하지 않았다.',
       f"모델·검색기 초기화: {r['load_seconds']:.2f}초. 별도 커널 워밍업: {r['warmup_seconds']:.2f}초. 벤치마크 입력 준비: {r['preparation_seconds']:.2f}초. 모델을 한 번 로드해 1→7→9→12그룹 순으로 각 1회 측정했으며 구성마다 prefix cache를 초기화했다. 반복 측정에 따른 오차 범위는 산정하지 않았다.",
       '| 구성 | 32건 실측 | 건당 평균 처리시간 | 일괄 대비 | 초기 작업 / 실제 모델 응답 | 검색 | 실패 공고 | 200건 단순 환산(로딩 제외) |',
       '|---|---:|---:|---:|---:|---:|---:|---:|']
for row in rows:
    lines.append(f"| {row['groups']}그룹 | {row['seconds']:.2f}초 | {row['seconds_per_notice']:.2f}초 | {row['relative_time']:.2f}배 | {row['initial_tasks']} / {row['model_turns']} | {row['search_rounds']} | {row['failed_records']} | {row['projected_200_prediction_seconds']/60:.2f}분 |")
lines += ['', '건당 평균은 배치 실행 전체 시간을 공고 수로 나눈 처리량 지표이며, 개별 요청의 응답 지연시간은 아니다. 실측에는 초기화 후의 프롬프트 구성·토큰 계산·모델 실행·검색·검증·재시도가 들어가며 결과 파일 저장은 제외한다.',
          '| 구성 | 모델 실행 | 검색 실행 | 입력 토큰(캐시 할인 전) | 출력 토큰 | thinking 토큰 | 무효 응답 | 문맥 실패 |',
          '|---|---:|---:|---:|---:|---:|---:|---:|']
for row in rows:
    lines.append(f"| {row['groups']}그룹 | {row['model_seconds']:.2f}초 | {row['retrieval_seconds']:.3f}초 | {row['input_tokens']:,} | {row['output_tokens']:,} | {row['thinking_tokens']:,} | {row['invalid_responses']} | {row['context_failures']} |")
lines += ['', '2시간 제한의 충족 여부는 이 표본만으로 확정할 수 없다. 제출 서버는 L40S 및 다른 양자화 환경이며, 실제 평가 공고 수·길이·검색·실패 복구에 따라 시간이 달라진다. 200건 환산은 표본의 평균 처리시간 ×200일 뿐 전체 200건 실측이 아니다. 원래 200건 중 문맥 초과 공고를 제외한 선택 편향이 있다. 초기화 시간도 실행 제한에 포함해야 한다.',
          '실패 공고가 있는 구성의 시간은 정해진 재시도 정책까지 실행한 시간이며 모든 공고의 정상 출력 완성 시간은 아니다. 해당 구성의 200건 환산도 동일한 한계를 갖는다. 실패를 복구하는 추가 시간은 측정값에 포함하지 않았다. Thinking 토큰은 파서가 분리한 텍스트 기준이며, 종료되지 않은 thinking 응답에서는 과소 집계될 수 있다.',
          '기존 약 12.4분/200건 thinking 결과와는 법령 프롬프트와 표본이 다르므로 직접 속도 개선으로 비교하지 않는다.',
          '파일: [실행 보고](report.json), [설정·표본·토큰 검사](manifest.json), [비교 CSV](comparison.csv), [로그](run.log). 각 구성 폴더에 실제 프롬프트, 예측 trace 및 성공한 경우 submission.csv를 저장했다.',
          '재현: `uv run --locked python src/experiments/benchmark_grouping_time.py --output 새경로` 실행 후 `uv run --locked python src/evaluation/summarize_grouping_time.py --input 새경로`.']
effect_path = folder/'effect.json'
if effect_path.exists():
    effect = json.loads(effect_path.read_text())
    lines[1] = '아래 시간은 같은 공고 표본의 실측이다. 저장된 예측을 라벨과 대조한 사후 효과 평가도 추가했다.'
    overview = [
        '## 그룹 분할이 효과가 있었는가',
        '이번 표본에서는 Macro F1이 높아졌으며 12그룹의 증가폭이 가장 컸다. 오탐과 시간이 함께 늘었으므로 전체적인 개선이나 제출 적합성을 뜻하지는 않는다.',
        f"정확도는 네 구성이 모두 정상 출력한 공통 {effect['common_records']}건, 시간은 기존 {effect['sample_records']}건 처리 시도 실측이다. 9그룹의 출력 실패 1건은 모든 구성의 공통 정확도 비교에서 제외했다.",
        '| 구성 | 공통 31건 Macro F1 | 변화 | TP / FP / FN | 시간 배수 |',
        '|---|---:|---:|---:|---:|',
    ]
    for name, result in effect['results'].items():
        group = next(run['groups'] for run in r['runs'] if run['name'] == name)
        overview.append(f"| {group}그룹 | {result['macro_f1']:.4f} | {result['delta_macro_f1']*100:+.2f}%p | {result['tp']} / {result['fp']} / {result['fn']} | {result['relative_time']:.2f}배 |")
    overview += ['',
        '12그룹은 위반 검출 TP가 7→15로 늘고 미탐 FN은 21→13으로 줄었다. 동시에 오탐 FP가 12→31로 늘었다. 7·9그룹은 Macro F1이 올랐지만 Micro F1과 공고 전체 일치 수는 감소했다.',
        '공식 평가 입력은 1,853건이며 코드 실행은 초기화 포함 2시간 제한이다. [공식 평가 안내](https://dacon.io/competitions/official/236754/overview/evaluation) (2026-09-10 확인). 200건 환산만으로 제출 적합성을 판단해서는 안 된다.',
        '로컬 표본 처리량을 1,853건으로 단순 환산하고 모델 로딩을 더하면: ' + ', '.join(
            f"{next(run['groups'] for run in r['runs'] if run['name']==name)}그룹 약 {result['projected_1853_seconds_with_model_load']/3600:.2f}시간"
            for name,result in effect['results'].items()) + '.',
        'L40S 서버 시간 예측을 검증한 것은 아니지만, 현 고정 분할 방식은 로컬 환산부터 제한을 크게 넘는다. 정확도 개선의 가능성은 있으나 이 구성을 그대로 채택하기에는 시간 비용이 크다. 공통 31건·정답 위반 28개인 소표본이므로 전체 데이터에서의 개선도 확정하지 않는다.',
        '[상세 효과 분석](effect.md) · [항목별 결과](effect_per_item.csv) · [사후 평가 수치](effect.json)',
    ]
    lines = lines[:2] + overview + ['## 추론 시간 상세'] + lines[2:]
write_report(folder/'comparison.md', '\n\n'.join(lines).replace('|\n\n|','|\n|')+'\n')
print(json.dumps({'load_seconds':r['load_seconds'],'rows':rows},ensure_ascii=False,indent=2))
