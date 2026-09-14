"""Tokenizer-only 32K preflight for the supplied-law criteria; no inference or labels."""
import argparse
import hashlib
import json
from pathlib import Path

from nara.inference.predictor import Predictor
from nara.inference.engine import VLLMModel
from nara.records import read_records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', default='models/gemma-4-26B-A4B-it-NVFP4')
    parser.add_argument('--input', default='data/dev.jsonl')
    parser.add_argument('--output', default='tmp/local-checks/legal_criteria_v1_context.json')
    parser.add_argument('--groups', type=int, nargs='+', default=[24, 6, 1])
    args = parser.parse_args()
    if any(not 1 <= size <= 24 for size in args.groups):
        parser.error('groups must be 1..24')
    from transformers import AutoTokenizer
    model = VLLMModel.__new__(VLLMModel)
    model.tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True)
    model.thinking, model.max_model_len = True, 32768
    table = json.loads(Path('data/항목표.json').read_text())['항목']
    schema = json.loads(Path('data/정답스키마_디코딩.json').read_text())['properties']['판정']
    records = read_records(args.input)
    predictor = Predictor(model, None, table, schema, legal_criteria=True)
    rows = []
    for size in args.groups:
        keys = list(table)
        groups = [keys[i:i+size] for i in range(0, len(keys), size)]
        counts = [{'id': record['id'], 'groups': [
            model.count_messages(predictor._messages(record, group)) for group in groups]}
            for record in records]
        budgets = []
        for output in [2048, 4096]:
            failed = [row['id'] for row in counts if max(row['groups']) + output + 128 > 32768]
            budgets.append({'output_tokens': output, 'source_failures': len(failed), 'failed_ids': failed,
                            'minimum_headroom': 32768 - max(max(r['groups']) for r in counts) - output - 128,
                            'optional_search_disabled_tasks': sum(
                                n + 2 * output + 256 > 32768 for row in counts for n in row['groups'])})
        row = {'group_size': size, 'tasks': len(groups)*len(records),
               'max_input_tokens': max(max(r['groups']) for r in counts), 'budgets': budgets, 'counts': counts}
        rows.append(row)
        print(json.dumps({k:v for k,v in row.items() if k != 'counts'}, ensure_ascii=False), flush=True)
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({'kind':'tokenizer-only; initial prompts, no retrieval/retries or inference',
        'thinking': True, 'context': 32768, 'records':len(records), 'model':args.model,
        'criteria_sha256': hashlib.sha256(Path('src/inference/legal_criteria.json').read_bytes()).hexdigest(),
        'input_sha256': hashlib.sha256(Path(args.input).read_bytes()).hexdigest(), 'configurations':rows},
        ensure_ascii=False, indent=2)+'\n')
    system = predictor._messages(records[0], list(table))[0]['content']
    path.with_name('legal_criteria_v1_system_prompt.txt').write_text(system+'\n')


if __name__ == '__main__':
    main()
