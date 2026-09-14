"""Describe the frozen single run without tuning or replacing failed judgments."""
import csv
import hashlib
import json
from pathlib import Path
import statistics
from nara.evaluation.reporting import write_report

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
KEYS = ['v4','v5','v6','v7']


def loadl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


def csvwrite(path, rows):
    with path.open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def scores(rows, features):
    result = []
    for feature in features:
        cells = [r for r in rows if r['feature']==feature]
        valid = [r for r in cells if r['prediction'] in (0,1)]
        tp = sum(r['truth']==1 and r['prediction']==1 for r in valid)
        fp = sum(r['truth']==0 and r['prediction']==1 for r in valid)
        fn = sum(r['truth']==1 and r['prediction']==0 for r in valid)
        tn = sum(r['truth']==0 and r['prediction']==0 for r in valid)
        invalid_positive = sum(r['truth']==1 and r['prediction'] not in (0,1) for r in cells)
        invalid_negative = sum(r['truth']==0 and r['prediction'] not in (0,1) for r in cells)
        worst_denominator = 2*tp+fp+fn+invalid_positive+invalid_negative
        result.append({'feature':feature, 'n':len(cells), 'valid':len(valid), 'invalid':len(cells)-len(valid),
            'support':sum(r['truth'] for r in cells), 'invalid_positive':invalid_positive, 'invalid_negative':invalid_negative,
            'conservative_f1_all':2*tp/worst_denominator if worst_denominator else 0,
            'recall_all':tp/(tp+fn+invalid_positive) if tp+fn+invalid_positive else 0, 'tp':tp,'fp':fp,'fn':fn,'tn':tn,
            'precision':tp/(tp+fp) if tp+fp else 0, 'recall':tp/(tp+fn) if tp+fn else 0,
            'f1':2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0,
            'accuracy_all':(tp+tn)/len(cells) if cells else 0})
    return result


def table(rows):
    lines=['| 항목 | 정답 양성 | TP | FP | FN | TN | 판정 실패 | 정밀도 | 재현율 | F1 |',
           '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in rows:
        lines.append(f"| {r['feature']} | {r['support']} | {r['tp']} | {r['fp']} | {r['fn']} | {r['tn']} | {r['invalid']} | {r['precision']:.4f} | {r['recall']:.4f} | {r['f1']:.4f} |")
    return '\n'.join(lines)


def verdict(truth, prediction):
    if prediction not in (0,1): return 'INVALID'
    return ('T' if truth==prediction else 'F') + ('P' if prediction else 'N')


def parse(raw, feature):
    issues = []
    try:
        obj = json.loads(raw)
    except (ValueError, TypeError):
        return None, ['not_strict_json']
    if not isinstance(obj, dict): return None, ['not_object']
    required = {'label','violation','law','threshold','comparison','evidence','reason'}
    if set(obj) != required: issues.append('output_keys_differ')
    if obj.get('label') != feature: issues.append('label_mismatch')
    if type(obj.get('violation')) is not int or obj['violation'] not in (0,1): issues.append('invalid_violation')
    for key in ['law','comparison','evidence','reason']:
        if not isinstance(obj.get(key), str): issues.append(f'{key}_not_string')
    if obj.get('threshold') is not None and (isinstance(obj['threshold'], bool) or not isinstance(obj['threshold'], (int,float))):
        issues.append('threshold_not_number_or_null')
    return obj, issues


def main():
    manifest=json.loads((OUT/'manifest.json').read_text())
    for path,digest in manifest['artifact_hashes'].items():
        assert hashlib.sha256((OUT/path).read_bytes()).hexdigest()==digest, path
    records={r['id']:r for r in loadl(ROOT/'data/dev.jsonl')}
    with (ROOT/'data/dev_labels.csv').open(encoding='utf-8-sig') as f:
        labels={r['id']:r for r in csv.DictReader(f)}
    assert set(records)==set(labels) and len(labels)==200
    responses=loadl(OUT/'extractor/responses.jsonl')
    assert len(responses)==800 and len({(r['id'],r['feature']) for r in responses})==800
    assert {(r['id'],r['feature']) for r in responses}=={(i,k) for i in records for k in KEYS}
    extracted={r['id']:r for r in loadl(OUT/'extractor/extracted.jsonl')}
    with (OUT/'scanner/candidate_v2_v8.csv').open(encoding='utf-8-sig') as f:
        scan={r['id']:r for r in csv.DictReader(f)}
    scan_rows,ext_rows,model_rows=[],[],[]
    for rid in records:
        for key in [f'v{i}' for i in range(2,9)]:
            pred=int(key in scan.get(rid,{}).get('flags','').split(','))
            truth=int(labels[rid][key])
            scan_rows.append({'id':rid,'feature':key,'truth':truth,'prediction':pred,
                'outcome':verdict(truth,pred),'gold_evidence':labels[rid].get('e'+key[1:],''),
                'scanner_evidence':scan.get(rid,{}).get('evidence','')})
        for key in KEYS:
            ext_rows.append({'id':rid,'feature':key,'truth':int(labels[rid][key]),
                             'prediction':int(key in extracted[rid]['candidate_flags'])})
    for row in responses:
        rid,key=row['id'],row['feature']
        obj,issues=parse(row['response'],key)
        # Never infer zeros from parse failures or correct the model's decision.
        prediction=(obj['violation'] if obj is not None and 'invalid_violation' not in issues
                    and 'label_mismatch' not in issues and row['finish_reason']=='stop' else None)
        truth=int(labels[rid][key])
        evidence=(obj or {}).get('evidence')
        quote_match=isinstance(evidence,str) and bool(evidence) and any(evidence in d['text'] for d in records[rid]['docs'])
        model_rows.append({'id':rid,'feature':key,'truth':truth,'prediction':prediction,
            'outcome':verdict(truth,prediction),'candidate':int(key in extracted[rid]['candidate_flags']),
            'format_issues':';'.join(issues),'finish_reason':row['finish_reason'],
            'law':(obj or {}).get('law'),'threshold':(obj or {}).get('threshold'),
            'comparison':(obj or {}).get('comparison'),'evidence':evidence,'reason':(obj or {}).get('reason'),
            'evidence_exact_source_substring':quote_match,'gold_evidence':labels[rid].get('e'+key[1:],''),
            'input_tokens':row['input_tokens'],'output_tokens':row['output_tokens']})
    scan_scores=scores(scan_rows,[f'v{i}' for i in range(2,9)])
    ext_scores=scores(ext_rows,KEYS)
    model_scores=scores(model_rows,KEYS)
    candidate_breakdown={k:{str(flag):{'n':len(cells:=[r for r in model_rows if r['feature']==k and r['candidate']==flag]),
        'gold_positive':sum(r['truth'] for r in cells),'model_positive':sum(r['prediction']==1 for r in cells),
        'tp':sum(r['outcome']=='TP' for r in cells),'fp':sum(r['outcome']=='FP' for r in cells),
        'fn':sum(r['outcome']=='FN' for r in cells)} for flag in (0,1)} for k in KEYS}
    evaluation={'scanner_candidate_scores':scan_scores,'extractor_candidate_scores':ext_scores,
        'gemma_scores':model_scores,'candidate_breakdown':candidate_breakdown,
        'gemma_macro_f1':statistics.mean(r['f1'] for r in model_scores),
        'macro_f1_scope':'valid judgments only if any invalid; not a 24-item competition score',
        'conservative_macro_f1_all':statistics.mean(r['conservative_f1_all'] for r in model_scores),
        'format_issue_count':sum(bool(r['format_issues']) for r in model_rows),
        'invalid_count':sum(r['prediction'] is None for r in model_rows),
        'length_stops':sum(r['finish_reason']=='length' for r in responses),
        'positive_exact_quotes':sum(r['prediction']==1 and r['evidence_exact_source_substring'] for r in model_rows),
        'positive_count':sum(r['prediction']==1 for r in model_rows),
        'input_tokens':sum(r['input_tokens'] for r in responses),'output_tokens':sum(r['output_tokens'] for r in responses),
        'runtime':json.loads((OUT/'runtime.json').read_text()),
        'labels_sha256':hashlib.sha256((ROOT/'data/dev_labels.csv').read_bytes()).hexdigest(),
        'score_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'responses_sha256':hashlib.sha256((OUT/'extractor/responses.jsonl').read_bytes()).hexdigest()}
    dump(OUT/'evaluation.json',evaluation)
    csvwrite(OUT/'scanner/evaluation.csv',scan_rows)
    csvwrite(OUT/'extractor/candidate_evaluation.csv',ext_rows)
    csvwrite(OUT/'extractor/judgments.csv',model_rows)
    for key in KEYS:
        cells=[r for r in model_rows if r['feature']==key and (r['truth']==1 or r['prediction']!=0)]
        lines=[f'# {key}: 모든 정답 양성·모델 양성·판정 실패 사례','',
               '모델의 설명을 그대로 기록했다. 설명이 사실·법령과 일치한다고 보증하거나 오류의 원인으로 확정한 것은 아니다.','']
        for r in cells:
            lines += [f"## {r['id']} — {r['outcome']}",'',
                f"정답 {r['truth']} / 모델 {r['prediction']} / 추출 후보 {r['candidate']}",'',
                '정답 근거:','',str(r['gold_evidence'] or '(없음)'),'','모델 출력:','',
                '```json',json.dumps({k:r[k] for k in ['law','threshold','comparison','evidence','reason']},ensure_ascii=False,indent=2),'```','']
        write_report(OUT/f'cases_{key}.md','\n'.join(lines))
    scanlines=['# 후보 스캐너: 모든 오탐·미탐','', '후보 플래그를 정답 위반 라벨과 대조한 목록이며 최종 모델 판정은 아니다.','']
    for r in scan_rows:
        if r['outcome'] not in ('FP','FN'):continue
        scanlines += [f"## {r['id']} / {r['feature']} — {r['outcome']}",'',
                      '정답 근거: '+(r['gold_evidence'] or '(없음)'),'',
                      '스캐너 공통 실적 근거: '+(r['scanner_evidence'] or '(출력 없음)'), '']
    write_report(OUT/'scanner_cases.md','\n'.join(scanlines))
    lines=['# LJM 원본 두 코드 독립 실행 결과','',
        '## 실행 범위','',
        '성공 기준·채택/기각 기준 없이, LJM이 작성한 두 코드를 독립적으로 한 번 실행한 관찰 결과다. 기존 변형 실험과 성능을 비교하지 않는다.','',
        '- 후보 스캐너: `scan_candidates.py` 원본으로 dev 200개, v2~v8 후보를 계산. 입력·출력 경로만 실행 시 변경했다.',
        '- 추출기: `v4_v7_candidate_extractor.py`의 반환 JSON 전체를 `gemma_prompt(item, "v4"~"v7")`에 전달. 200개 모두 후보 유무와 관계없이 4회씩, 총 800회 호출했다.',
        '- 원본 함수 호출 뒤 「관련 법령·고시금액을 검색한 뒤」를 「제공된 법령·고시금액을 사용한 뒤」로 한 번 치환하고 해당 항목의 제공 법령 원문을 덧붙였다.',
        '- 별도 시스템 프롬프트, 기존 판정 프롬프트·해석 초안·출력 스키마, 후보 스캐너의 출력, 공고 전체 원문을 추가하지 않았다. 원본 추출 JSON 내부의 문맥·금액·후보 플래그는 그대로 전달했다.',
        '- 원본 코드 자체의 문맥 개수·문자수 제한, 중복 문맥, 금액 파싱, 후보 계산을 수정하지 않았다. 추가 절단·중복 제거도 하지 않았다.',
        '- 프롬프트의 항목 인자는 원본이 받는 식별자 v4~v7이다. 기존 항목별 설명 프롬프트를 덧붙이지 않았다.',
        '- 법령은 제공 패키지의 한글 원문과 연결 조항을 발췌. 출처명·조항을 표시하고 자체 요약·번역·금액 보충·누락 경고를 넣지 않았다. 시행일은 모델 입력에 넣지 않았으며 원본 출처 헤더는 추적 기록에만 보존했다.',
        '- 로컬 Gemma 4 26B A4B NVFP4 / vLLM, thinking OFF, temperature 0, seed 0, 문맥 32768, 출력 2048, 배치 8. 로컬 체크포인트 결과이며 주최측 BF16/INT8 실행의 재현은 아니다.',
        '- 자유 JSON 생성: 별도 문법 강제 없음. 정상 응답을 그대로 저장하고 재시도·판정 보정·실패의 비위반 대체를 하지 않았다. 출력 한도는 원본의 설명 필드를 보존하기 위한 실행 설정이며 LJM 코드에는 모델 설정이 명시되어 있지 않다.',
        '- 이번 결과를 이용한 프롬프트·규칙 튜닝이나 재실험 없음. 같은 dev를 앞선 작업에서 이미 확인했으므로 미사용 검증셋에 대한 독립 평가로 해석하지 않는다.','',
        '## 실험 1: 원본 후보 스캐너 v2~v8','',table(scan_scores),'',
        '후보를 양성으로 간주해 정답과 대조했다. 후보 검출 성능이며 최종 법령 판정 성능으로 명명하지 않는다. 후보 CSV에 없는 공고는 평가 시 후보 없음으로 펼쳤다. 모델 호출은 이 실험에 연결하지 않았다.','',
        '## 실험 2: 원본 추출기 + 원본 프롬프트 + Gemma','',table(model_scores),'',
        f"4항목 Macro F1: {evaluation['gemma_macro_f1']:.6f}. 전체 24항목 대회 점수가 아니다. 판정 실패가 있으면 위 정밀도·재현율·F1은 유효 판정 부분집합 기준이며 실패 수를 함께 확인해야 한다.",'',
        f"실패를 모두 오답으로 취급한 전체 200건 기준 보수적 Macro F1은 {evaluation['conservative_macro_f1_all']:.6f}이다. 이 보조 지표에서 양성 정답의 실패는 FN, 음성 정답의 실패는 FP로 계산할 뿐, 저장된 모델 판정을 대체하지 않는다.",'',
        '### 모델 호출 전 후보 검출','',table(ext_scores),'',
        '추출기 후보와 모델 판정은 별도 관찰값이다. 이 점수만으로 후보 플래그가 모델 성능에 미친 인과효과를 알 수 없다.','',
        '### 후보 유무별 모델 결과','',
        '| 항목 | 후보 | 공고 수 | 정답 양성 | 모델 양성 | TP | FP | FN |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for key,groups in candidate_breakdown.items():
        for flag,r in groups.items(): lines.append(f"| {key} | {flag} | {r['n']} | {r['gold_positive']} | {r['model_positive']} | {r['tp']} | {r['fp']} | {r['fn']} |")
    lines += ['', '## 출력과 실행 기록','',
        f"800회 중 형식 이슈 {evaluation['format_issue_count']}회, 판정 실패 {evaluation['invalid_count']}회, 길이 종료 {evaluation['length_stops']}회. 모델 양성 {evaluation['positive_count']}개 중 근거가 한 원문 문서의 연속 부분문자열인 경우는 {evaluation['positive_exact_quotes']}개다.",
        '위반 여부가 유효하고 항목 식별자가 일치하며 정상 종료한 응답은 다른 설명 필드의 형식 이슈가 있어도 이진 판정 집계에 포함하고, 이슈는 별도로 보존한다. 원본 프롬프트는 정확한 부분문자열 인용을 요구하지 않는다. 따라서 이 검사는 추가 관찰이며 불일치 근거를 삭제하거나 판정을 바꾸지 않았다. 모델의 법령·기준금액·비교값·이유는 검증된 법률 결론이 아니라 원응답이다.','',
        f"입력 {evaluation['input_tokens']:,}토큰 / 출력 {evaluation['output_tokens']:,}토큰. 모델 로딩 {evaluation['runtime']['load_seconds']:.2f}초 / 추론 {evaluation['runtime']['inference_seconds']:.2f}초. 스캐너 {manifest['scanner_seconds']:.3f}초 / 추출 {manifest['extraction_seconds']:.3f}초.",'',
        '## 전체 사례와 재현','',
        '- [스캐너 오탐·미탐](scanner_cases.md)',
        '- [v4 전체 양성·실패 사례](cases_v4.md) · [v5](cases_v5.md) · [v6](cases_v6.md) · [v7](cases_v7.md)',
        '- `extractor/judgments.csv`: 전체 800판정, 정답, 후보, 모든 모델 설명 필드, 출력 형식 진단.',
        '- `extractor/requests.jsonl`, `responses.jsonl`, `extracted.jsonl`: 실제 입력 메시지·원응답·원본 추출 결과.',
        '- `scanner/candidate_v2_v8.csv`, `evaluation.csv`: 원본 후보 출력과 전체 1400개 후보 대조.',
        '- `law_specs/`, `laws.json`, `law_provenance.json`: 발췌 줄 범위, 실제 입력 법령, 원문·정리 후 문구·출처 해시.',
        '- `manifest.json`, `preflight.json`, `engine.json`, `runtime.json`: 고정 설정·입력 해시·800회 토큰 검사·실행 시간.',
        '- `source/user/LJM/`: 변경하지 않은 원본 코드 사본. `run.py`, `score.py`: 실행 및 결과 정리 코드.','',
        '점수 재계산: `uv run --locked python analysis/LJM_original_v2_v8_20260912/score.py`.',
        '새 실행은 저장소 안의 새 analysis 폴더에 run.py, score.py, law_specs/를 복사한 뒤 prepare → run → score 순서로 실행한다. 같은 폴더의 기존 manifest·응답 덮어쓰기는 거부한다. 데이터·모델은 별도 제공 자료를 동일 위치에 준비해야 한다.','']
    write_report(OUT/'report.md','\n'.join(lines))
    print(json.dumps({'gemma_macro_f1':evaluation['gemma_macro_f1'],'invalid':evaluation['invalid_count'],'format_issues':evaluation['format_issue_count']},ensure_ascii=False))


if __name__=='__main__': main()
