"""Compare real token IDs and vLLM sampling against the saved pre-refactor code.

Usage: uv run --locked python src/tools/check_engine_request_parity.py BEFORE_RUN
No model weights or GPU engine are loaded; requests stop at engine submission.
"""
from nara.paths import source_path
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace as NS

from nara.records import read_records
from nara.inference.predictor import Limits, Turn, _Task
from nara.inference.continuous import ContinuousPredictor
from nara.inference.engine import TokenCounter, VLLMModel
from nara.experiments.config import MODEL, configuration
import msgspec


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Recorder:
    def __init__(self, tokenizer):
        self.llm_engine = self
        self.tokenizer = tokenizer
    def add_request(self, rid, prompt, params):
        self.last = (prompt, msgspec.to_builtins(params))
    def generate(self, prompts, *, sampling_params, use_tqdm):
        self.last = [(p, msgspec.to_builtins(s)) for p, s in zip(prompts, sampling_params)]
        return [NS(prompt_token_ids=p['prompt_token_ids'],
                   outputs=[NS(token_ids=self.tokenizer.encode('{}', add_special_tokens=False), finish_reason='stop')])
                for p in prompts]


def main():
    before = Path(sys.argv[1])
    manifest = json.loads((before / 'manifest.json').read_text())
    allowed = {'src/inference/engine.py', 'src/inference/continuous.py', 'src/experiments/benchmark_prefix_pipeline.py'}
    for name, digest in manifest['source_sha256'].items():
        assert hashlib.sha256((before / 'source' / name).read_bytes()).hexdigest() == digest, name
        if source_path(name).relative_to(source_path('.')).as_posix() not in allowed:
            assert hashlib.sha256(source_path(name).read_bytes()).hexdigest() == digest, name
    old_engine = load('before_vllm_model', before / 'source/nara/vllm_model.py')
    old_continuous = load('before_continuous', before / 'source/nara/continuous.py')
    tokenizer = TokenCounter(MODEL).tokenizer
    models = [kind.__new__(kind) for kind in (old_engine.VLLMModel, VLLMModel)]
    for model in models:
        model.tokenizer = tokenizer
        model.max_model_len = 32768
        model.thinking = False
        model.llm = Recorder(tokenizer)
    streams = [old_continuous.StreamingModel(models[0]), models[1].stream()]
    table = json.loads(Path('data/항목표.json').read_text())['항목']
    schema = json.loads(Path('data/정답스키마_디코딩.json').read_text())['properties']['판정']
    table, schema, groups = configuration(table, schema, 'groups12', True)
    predictors = [kind(stream, None, table, schema, limits=Limits(output_tokens=2048, batch_size=16))
                  for kind, stream in zip((old_continuous.ContinuousPredictor, ContinuousPredictor), streams)]
    digest = hashlib.sha256()
    total = 0
    for record in read_records('data/dev.jsonl'):
        for gi, group in enumerate(groups):
            for predictor, stream in zip(predictors, streams):
                task = _Task(f'{record["id"]}:{gi}', record, tuple(group), predictor._messages(record, group))
                request = predictor._turn(task)
                assert request is not None
                stream.submit(request)
                stream.pending.clear()
            assert models[0].llm.last == models[1].llm.last, (record['id'], gi)
            digest.update(json.dumps(models[0].llm.last, sort_keys=True, separators=(',', ':')).encode())
            total += 1
    variants = 0
    for thinking in (False, True):
        for search in (False, True):
            for budget in (64, 512, 2048):
                request = Turn('variant', [{'role': 'user', 'content': '2+3'}],
                               {'type': 'object', 'properties': {'action': {'const': 'search' if search else 'final'}}}, budget)
                for model, stream in zip(models, streams):
                    model.thinking = thinking
                    stream.submit(request)
                    stream.pending.clear()
                assert models[0].llm.last == models[1].llm.last
                replies = [model.generate([request]) for model in models]
                assert models[0].llm.last == models[1].llm.last
                assert replies[0] == replies[1]
                variants += 1
    summary = {'initial_requests': total, 'initial_request_token_ids_and_sampling_equal': True,
               'on_off_search_final_budget_variants': variants, 'offline_replies_and_sampling_equal': True,
               'request_payloads_sha256': digest.hexdigest(), 'gpu_engine_loaded': False,
               'baseline_run': str(before)}
    Path('analysis/engine_refactor200/request_parity.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
