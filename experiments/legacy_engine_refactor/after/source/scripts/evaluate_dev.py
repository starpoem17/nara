"""Score a complete dev prediction CSV by ID; labels are used only here."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

from script import read_records


ITEMS = [f'v{i}' for i in range(1, 25)]


def read_csv(path):
    with Path(path).open(encoding='utf-8', newline='') as stream:
        reader = csv.DictReader(stream)
        required = ['id'] + ITEMS + [f'e{i}' for i in range(1, 25)]
        if reader.fieldnames != required:
            raise ValueError(f'{path}: unexpected columns')
        rows = list(reader)
    if len({r['id'] for r in rows}) != len(rows):
        raise ValueError(f'{path}: duplicate IDs')
    if any(r[k] not in ('0', '1') for r in rows for k in ITEMS):
        raise ValueError(f'{path}: nonbinary or missing judgment')
    return {r['id']: r for r in rows}


def evaluate(run_dir, labels_path, input_path, expected_records):
    run = Path(run_dir)
    truth, pred = read_csv(labels_path), read_csv(run / 'submission.csv')
    records = {r['id']: r for r in read_records(input_path)}
    if not (set(truth) == set(pred) == set(records)) or len(truth) != expected_records:
        raise ValueError('Expected complete, identical input/label/prediction ID sets')
    table = json.loads(Path('data/항목표.json').read_text())['항목']
    ids = list(records)
    y = [[int(truth[i][k]) for k in ITEMS] for i in ids]
    p = [[int(pred[i][k]) for k in ITEMS] for i in ids]
    per_item, errors = [], []
    for column, key in enumerate(ITEMS):
        a, b = [row[column] for row in y], [row[column] for row in p]
        tp = sum(t == 1 and v == 1 for t, v in zip(a, b))
        fp = sum(t == 0 and v == 1 for t, v in zip(a, b))
        fn = sum(t == 1 and v == 0 for t, v in zip(a, b))
        row = {'item': key, 'name': table[key]['항목명'], 'support': sum(a),
               'predicted_positive': sum(b), 'tp': tp, 'fp': fp, 'fn': fn,
               'tn': len(a) - tp - fp - fn,
               'precision': precision_score(a, b, zero_division=0),
               'recall': recall_score(a, b, zero_division=0),
               'f1': f1_score(a, b, zero_division=0)}
        per_item.append(row)
        for i, t, v in zip(ids, a, b):
            if t != v:
                errors.append({'id': i, 'item': key, 'name': row['name'],
                               'error': 'FP' if v else 'FN', 'gold': t, 'prediction': v,
                               'gold_evidence': truth[i]['e' + key[1:]],
                               'predicted_evidence': pred[i]['e' + key[1:]]})
    traces = [json.loads(line) for line in (run / 'trace.jsonl').read_text().splitlines()]
    if len(traces) != len(ids) or {r['record_id'] for r in traces} != set(ids):
        raise ValueError('Trace IDs differ from input')
    if any(r['error'] or r['judgments'] is None for r in traces):
        raise ValueError('Cannot report complete evaluation with failed predictions')
    # Cross-check that CSV labels are the actual traced model predictions.
    for record in traces:
        for key in ITEMS:
            if record['judgments'][key]['위반여부'] != int(pred[record['record_id']][key]):
                raise ValueError('CSV and trace predictions disagree')
    events = [e for r in traces for t in r['trace'] for e in t['events']]
    searches = [e for e in events if e['event'] == 'search']
    searched = sum(any(t['search_rounds'] for t in r['trace']) for r in traces)
    evidence = {'nonempty': 0, 'invalid': 0, 'positive_nonabsence_missing': 0}
    for i in ids:
        for key in ITEMS:
            quote = pred[i]['e' + key[1:]]
            positive = pred[i][key] == '1'
            absence = table[key]['부재탐지']
            evidence['positive_nonabsence_missing'] += positive and not absence and not quote
            if quote:
                evidence['nonempty'] += 1
                evidence['invalid'] += (not positive or absence or len(quote) > 500
                    or quote.startswith(('=', '+', '@'))
                    or not any(quote in d['text'] for d in records[i]['docs']))
    macro = f1_score(y, p, average='macro', zero_division=0)
    assert abs(macro - sum(r['f1'] for r in per_item) / 24) < 1e-12
    report = json.loads((run / 'report.json').read_text())
    options, limits = report['options'], report['limits']
    policy = '최초 검색 강제' if limits.get('require_search') else '자율 검색'
    if limits.get('require_search') and any(t['search_rounds'] < 1 or t['retrieval_tokens'] <= 0
                                          for r in traces for t in r['trace']):
        raise ValueError('Required retrieval missing from a successful prediction')
    result = {'records': len(ids), 'judgments': len(ids) * 24,
              'macro_f1': macro, 'micro_f1': f1_score(y, p, average='micro', zero_division=0),
              'macro_precision': precision_score(y, p, average='macro', zero_division=0),
              'macro_recall': recall_score(y, p, average='macro', zero_division=0),
              'label_accuracy': 1 - len(errors) / (len(ids) * 24),
              'exact_match_accuracy': accuracy_score(y, p),
              'exact_match_records': sum(a == b for a, b in zip(y, p)),
              'false_positives': sum(r['fp'] for r in per_item),
              'false_negatives': sum(r['fn'] for r in per_item),
              'zero_positive_items': [r['item'] for r in per_item if r['support'] == 0],
              'zero_division': 0, 'searched_records': searched,
              'retrieved_records': sum(any(t['retrieval_tokens'] > 0 for t in r['trace']) for r in traces),
              'search_rate': searched / len(ids), 'search_rounds': len(searches),
              'search_queries': sum(len(e['queries']) for e in searches),
              'search_errors': sum(e['error'] is not None for e in searches),
              'empty_search_rounds': sum(not e['passage_ids'] for e in searches),
              'invalid_model_responses': sum(e['event'] == 'invalid_response' for e in events),
              'thinking_turns': sum(e.get('thinking_tokens', 0) > 0 for e in events),
              'thinking_text_tokens': sum(e.get('thinking_tokens', 0) for e in events),
              'thinking_budgets': sorted({e['thinking_budget'] for e in events if e.get('thinking_budget') is not None}),
              'evidence_dropped': sum(len(e['evidence_dropped']) for e in events if e['event'] == 'final'),
              'evidence': evidence, 'runtime': report, 'per_item': per_item,
              'sha256': {str(path): hashlib.sha256(Path(path).read_bytes()).hexdigest()
                         for path in [labels_path, input_path, run / 'submission.csv']}}
    (run / 'evaluation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    with (run / 'errors.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['id', 'item', 'name', 'error', 'gold',
            'prediction', 'gold_evidence', 'predicted_evidence'])
        writer.writeheader()
        writer.writerows(errors)
    lines = [f'# Gemma 4 + RAG ({policy}): dev {len(ids)}건', '',
        f'- 주 지표: 항목별 양성 F1의 평균 **{macro:.6f} ({macro:.2%})**',
        f'- Micro F1: {result["micro_f1"]:.6f}; 판정 정확도: {result["label_accuracy"]:.2%}',
        f'- 24개 모두 일치한 공고: {result["exact_match_records"]}/{len(ids)}',
        f'- 오탐(FP): {result["false_positives"]}; 미탐(FN): {result["false_negatives"]}',
        f'- 검색 공고: {searched}/{len(ids)}; 검색 {len(searches)}회, 질의 {result["search_queries"]}개',
        f'- 로딩 포함 {report["total_seconds"]:.2f}초; 추론 {report["prediction_seconds"]:.2f}초',
        f'- Thinking이 확인된 응답: {result["thinking_turns"]}; thinking 텍스트 토큰: {result["thinking_text_tokens"]}; 적용 예산: {result["thinking_budgets"]}',
        '', f'모델: {options["model_dir"]}; GPU: {report["gpu"]}; 문맥: {options["max_model_len"]:,}; thinking: {options["thinking"]}.',
        f'대화당 {options["item_group_size"]}항목. {policy}, 최대 {limits["search_rounds"]}회, 회당 최대 {limits["queries_per_round"]}질의, BGE-M3 dense top-{limits["top_k"]}.',
        '프롬프트는 이번 실행 전에 고정했으며, 추론은 정답 라벨을 읽지 않는다.',
        '검색 자료는 제공 법령패키지만 사용. 실제 시스템 프롬프트는 system_prompt.txt 참조.',
        '', '## 항목별 결과', '',
        '| 항목 | 이름 | 정답 양성 | 예측 양성 | Precision | Recall | F1 | FP | FN |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in per_item:
        lines.append(f'| {r["item"]} | {r["name"]} | {r["support"]} | {r["predicted_positive"]} | '
                     f'{r["precision"]:.3f} | {r["recall"]:.3f} | {r["f1"]:.3f} | {r["fp"]} | {r["fn"]} |')
    context_path = run / 'context_check.json'
    context = json.loads(context_path.read_text()) if context_path.exists() else None
    command_path = run / 'command.txt'
    command = (command_path.read_text().strip() if command_path.exists() else
               f'uv run --locked python script.py --input {input_path} --output-dir NEW_OUTPUT_DIR')
    lines += ['', '## 해석 범위', '',
        (f'- 최대 초기 입력 {context["max_input_tokens"]:,}토큰.' if context else '- 초기 문맥 길이 측정 파일 없음.'),
        (f'- 문맥 예산으로 초기 검색이 제한된 공고 {len(context["initial_search_disabled"])}건. 상세 ID는 context_check.json.' if context else '- 초기 검색 제한 수는 별도 측정 필요.'),
        '- 검색 정책과 실제 호출 수를 함께 해석한다. 검색 정책 외 비교 조건은 별도 비교 보고서에서 확인한다.',
        '- 제공 dev 예시는 실제 평가 분포를 대표하지 않는다. 대회 서버의 INT8 모델과 다른 로컬 NVFP4 결과다.',
        '- 근거의 원문 일치는 형식 검사이며 법적 적절성 또는 대회 정성평가 점수가 아니다.',
        f'- 근거 검사: {json.dumps(evidence, ensure_ascii=False)}. 후처리에서 탈락한 근거 {result["evidence_dropped"]}개.',
        f'- 실패 예측을 0으로 대체하지 않는다. {len(ids)}건 전체 ID 정합성과 CSV/추론 로그의 판정 일치를 확인했다.',
        '- F1 분모가 0이면 0으로 처리하며 24항목 모두 평균에 포함한다.',
        '', '## 재현', '', '```bash', command,
        f'uv run --locked python -m scripts.evaluate_dev --run-dir {run}', '```', '',
        '코드/프롬프트 스냅샷: source/. 실행 설정: report.json. 오탐·미탐 원문 근거: errors.csv.']
    (run / 'evaluation.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('runtime', 'per_item', 'sha256')}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', required=True)
    parser.add_argument('--labels', default='data/dev_labels.csv')
    parser.add_argument('--input', default='data/dev.jsonl')
    parser.add_argument('--expected-records', type=int, default=200)
    args = parser.parse_args()
    evaluate(args.run_dir, args.labels, args.input, args.expected_records)
