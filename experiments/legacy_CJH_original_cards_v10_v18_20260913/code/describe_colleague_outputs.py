"""Describe raw output shapes after the frozen primary evaluation; never rescore."""

if __name__ == "__main__":
    raise SystemExit("Archived code: create a fresh registered run; see docs/operations.md.")

from collections import Counter, defaultdict
import json

from experiments.legacy_CJH_original_cards_v10_v18_20260913.code.evaluate_colleague_cards import FENCE, parse_response, _unique_object, _reject_constant
from experiments.legacy_CJH_original_cards_v10_v18_20260913.code.colleague_cards import FEATURES, ROOT, RUNS, dump, read_jsonl


def describe():
    for author, out in RUNS.items():
        assert (out / 'evaluation.json').exists() and (out / 'runtime_verification.json').exists()
        observations, all_rows = {}, []
        for feature in FEATURES[author]:
            rows = read_jsonl(out / 'responses' / (feature + '.jsonl'))
            counts, examples, invalid = Counter(), defaultdict(list), Counter()
            bare = fenced = 0
            for row in rows:
                parsed = parse_response(row['text'], row['finish_reason'])
                if parsed.valid:
                    bare += parsed.strict_format
                    fenced += not parsed.strict_format
                else:
                    invalid[(parsed.invalid_reason or '').split(':')[0]] += 1
                envelope = row['text'].strip()
                fence = FENCE.fullmatch(envelope)
                payload = fence.group(1) if fence else envelope
                try:
                    value = json.loads(payload, object_pairs_hook=_unique_object, parse_constant=_reject_constant)
                except ValueError:
                    shape = 'not_one_complete_json_payload'
                else:
                    if type(value) is not dict:
                        shape = 'non_object:' + type(value).__name__
                    elif set(value) == {'위반여부', '근거문구'}:
                        shape = 'requested_top_level_keys'
                    elif set(value) == {feature} and type(value[feature]) is dict:
                        shape = 'current_feature_nested_object:' + ','.join(sorted(value[feature]))
                    elif set(value) == {feature, 'e' + feature[1:]}:
                        shape = 'current_feature_and_evidence_keys'
                    else:
                        shape = 'other_top_level_keys:' + ','.join(sorted(value))
                counts[shape] += 1
                if len(examples[shape]) < 3:
                    examples[shape].append(row['id'])
                all_rows.append({'id': row['id'], 'feature': feature, 'valid': parsed.valid,
                                 'positive': parsed.violation == 1 if parsed.valid else None})
            observations[feature] = {
                'responses': len(rows), 'bare_valid': bare, 'fenced_valid': fenced,
                'invalid_reasons': dict(invalid), 'output_shapes': dict(counts),
                'examples': dict(examples), 'finish_reasons': dict(Counter(r['finish_reason'] for r in rows)),
            }
        pairs = {}
        if author == 'CJH':
            valid = {(r['id'], r['feature']) for r in all_rows if r['valid']}
            ids = {r['id'] for r in all_rows}
            for left, right in [('v15', 'v16'), ('v17', 'v18')]:
                pairs[left + '_' + right] = sum((rid, left) in valid and (rid, right) in valid for rid in ids)
        value = {'author': author, 'scope': 'Post-evaluation descriptive output-shape inventory only; no extra judgment extraction, repair, retry, or rescoring.',
                 'labels_used_in_this_shape_inventory': False,
                 'per_feature': observations, 'both_valid_pair_denominators': pairs}
        dump(out / 'output_observations.json', value)
        aggregate = Counter()
        for item in observations.values():
            aggregate.update(item['output_shapes'])
        report = ROOT / 'docs/reports' / out.relative_to(ROOT) / 'report.md'
        body = report.read_text()
        marker = '<!-- output-observation-caveat -->'
        valid_count = sum(item['bare_valid'] + item['fenced_valid'] for item in observations.values())
        total = sum(item['responses'] for item in observations.values())
        caveat = (marker + '\n**먼저 읽기:** 사전 파서가 판독한 응답은 '
                  f'{valid_count}/{total}개이며, 그마저 모두 완결 코드펜스 안의 JSON이다. '
                  '요청한 bare JSON 형식을 그대로 충족한 응답은 0개다. '
                  '아래 F1은 일부 유효 응답에만 해당하며 가설 전체의 판정 성능으로 읽으면 안 된다. '
                  '[주요 현상과 해석 범위](../../cms-cjh-original-summary.md)를 먼저 확인한다.\n\n')
        if author == 'CJH':
            caveat += ('v15·v16 및 v17·v18은 각 쌍의 두 응답이 모두 유효한 공고가 각각 0/200건이다. '
                       '따라서 아래 동시 양성 0건은 배타성 준수의 증거가 아니다.\n\n')
        caveat += '<!-- /output-observation-caveat -->\n\n'
        if marker not in body:
            title = f'# {author} 원문 판정카드 dev200 평가\n\n'
            assert body.count(title) == 1
            report.write_text(body.replace(title, title + caveat))
        report.write_text('\n'.join(line.rstrip() for line in report.read_text().splitlines()) + '\n')
        print(author, json.dumps({'shapes':dict(aggregate), 'both_valid_pairs': pairs}, ensure_ascii=False))


if __name__ == '__main__':
    raise SystemExit("Archived experiment: create a new registered run; see docs/operations.md. Historical evidence is read-only.")
    describe()
