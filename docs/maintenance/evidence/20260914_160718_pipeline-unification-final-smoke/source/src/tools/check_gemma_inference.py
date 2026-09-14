"""Verify local Gemma inference and the configured context boundary."""
import argparse
import json
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', default='models/gemma-4-26B-A4B-it-NVFP4')
    parser.add_argument('--max-model-len', type=int, default=32768)
    parser.add_argument('--output', default='tmp/local-checks/gemma_inference_check.json')
    args = parser.parse_args()
    from vllm import LLM, SamplingParams
    from vllm.sampling_params import StructuredOutputsParams
    import torch
    import vllm

    started = time.monotonic()
    llm = LLM(
        model=args.model, max_model_len=args.max_model_len,
        gpu_memory_utilization=0.90, max_num_seqs=1,
        limit_mm_per_prompt={'image': 0, 'audio': 0, 'video': 0},
        enforce_eager=True, seed=0, kernel_config={'moe_backend': 'cutlass'},
    )
    actual_limit = llm.llm_engine.vllm_config.model_config.max_model_len
    assert actual_limit == args.max_model_len
    report = {
        'model': args.model, 'vllm': vllm.__version__,
        'torch': torch.__version__, 'gpu': torch.cuda.get_device_name(0),
        'max_model_len': actual_limit, 'enforce_eager': True, 'moe_backend': 'cutlass',
        'gpu_memory_utilization': 0.90, 'max_num_seqs': 1,
        'load_seconds': round(time.monotonic() - started, 2), 'checks': [],
    }
    tokenizer = llm.get_tokenizer()

    def check(name, ids, max_tokens, expected=None, structured=None):
        start = time.monotonic()
        params = SamplingParams(temperature=0, max_tokens=max_tokens,
                                structured_outputs=structured)
        out = llm.generate([{'prompt_token_ids': ids}], params, use_tqdm=False)[0]
        result = out.outputs[0]
        assert len(out.prompt_token_ids) == len(ids), 'Input was truncated'
        assert result.token_ids, 'No generated tokens'
        if expected:
            assert expected in result.text, repr(result.text)
        entry = dict(name=name, input_tokens=len(ids),
                     output_tokens=len(result.token_ids), text=result.text,
                     finish_reason=result.finish_reason,
                     seconds=round(time.monotonic() - start, 2), passed=True)
        report['checks'].append(entry)
        print(json.dumps(entry, ensure_ascii=False), flush=True)
        return result.text

    def chat_ids(text):
        return tokenizer.apply_chat_template(
            [{'role': 'user', 'content': text}], tokenize=True,
            add_generation_prompt=True, enable_thinking=False, return_dict=False)

    check('korean_short', chat_ids('대한민국의 수도는 어디인가요? 도시 이름만 답하세요.'), 64, '서울')
    schema = {'type': 'object', 'properties': {'answer': {'type': 'integer'}},
              'required': ['answer'], 'additionalProperties': False}
    answer = check('structured_json', chat_ids('2 + 3의 답을 {"answer": 정수} JSON으로 답하세요.'),
                   64, structured=StructuredOutputsParams(json=schema))
    assert json.loads(answer) == {'answer': 5}
    # Preserve the full chat suffix while padding to the exact input budget.
    base = chat_ids('앞의 반복 문장은 무시하세요. 대한민국의 수도 이름만 답하세요.')
    filler = tokenizer.encode(' 참고 자료입니다.', add_special_tokens=False)
    for budget in sorted({min(16384, actual_limit), actual_limit}):
        input_size = budget - 64
        padding = input_size - len(base)
        assert padding >= 0
        ids = base[:1] + (filler * (padding // len(filler) + 1))[:padding] + base[1:]
        check(f'context_{budget}', ids, 64, '서울')
    try:
        llm.generate([{'prompt_token_ids': [filler[0]] * (actual_limit + 1)}],
                     SamplingParams(max_tokens=1), use_tqdm=False)
    except ValueError as exc:
        report['checks'].append(dict(name='over_limit_rejected', passed=True, error=str(exc)))
    else:
        raise AssertionError('Over-limit input was not rejected')
    report['total_seconds'] = round(time.monotonic() - started, 2)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(f'PASS: {args.output}', flush=True)


if __name__ == '__main__':
    main()
