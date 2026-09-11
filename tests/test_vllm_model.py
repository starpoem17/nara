"""Exercise production engine conversion and lifecycle without loading GPU weights."""
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType, SimpleNamespace as NS
from unittest.mock import patch
import json
import sys
import tempfile
import unittest

from nara.inference import Turn
from nara.vllm_model import StreamingModel, TokenCounter, VLLMModel


@dataclass
class Stats:
    queued_ts: float = 1.
    scheduled_ts: float = 2.
    first_token_ts: float = 3.
    last_token_ts: float = 5.


@dataclass
class Graph:
    runtime_mode: str = 'FULL'
    num_unpadded_tokens: int = 16


class Tokenizer:
    def encode(self, text, **kwargs):
        return list(text.encode())

    def decode(self, tokens, **kwargs):
        return bytes(tokens).decode()

    def apply_chat_template(self, messages, **kwargs):
        assert kwargs == dict(add_generation_prompt=True, tokenize=True, return_dict=False,
                              enable_thinking=kwargs['enable_thinking'])
        return list(json.dumps([kwargs['enable_thinking'], messages]).encode())


class Params(NS):
    def __init__(self, **kwargs):
        super().__init__(output_kind='CUMULATIVE', **{k: v for k, v in kwargs.items() if k != 'output_kind'})
        self.output_kind = kwargs.get('output_kind', 'CUMULATIVE')


class RawEngine:
    def __init__(self, **kwargs):
        self.options = kwargs
        self.tokenizer = Tokenizer()
        self.llm_engine = self
        self.pending = {}
        self.added = []
        self.aborted = []
        self.resets = 0
        self.reset_result = True
        self.outputs = None
        self.stats = NS(num_running_reqs=16, num_waiting_reqs=2, num_skipped_waiting_reqs=1,
                        kv_cache_usage=.4, prefix_cache_stats=NS(preempted_requests=0),
                        cudagraph_stats=Graph())
        self.engine_core = NS(get_output=lambda: NS(scheduler_stats=self.stats))
        self.vllm_config = NS(
            scheduler_config=NS(max_num_seqs=kwargs['max_num_seqs'],
                                max_num_batched_tokens=kwargs.get('max_num_batched_tokens', 8192)),
            compilation_config=NS(cudagraph_mode='FULL_AND_PIECEWISE', cudagraph_capture_sizes=[1, 2, 4, 8, 16]),
            cache_config=NS(cache_dtype='auto', gpu_memory_utilization=kwargs['gpu_memory_utilization']))

    def get_tokenizer(self):
        return self.tokenizer

    def output(self, rid, prompt, params):
        text = json.dumps({'answer': bytes(prompt['prompt_token_ids']).decode(),
                           'thinking': 'thought' if params.thinking_token_budget else ''})
        return NS(request_id=rid, finished=True, prompt_token_ids=prompt['prompt_token_ids'],
                  num_cached_tokens=2, num_cache_creation_tokens=1, metrics=Stats(),
                  outputs=[NS(token_ids=list(text.encode()), finish_reason='stop')])

    def generate(self, prompts, *, sampling_params, use_tqdm):
        self.generated = deepcopy(list(zip(prompts, sampling_params)))
        return [self.output(f'offline-{i}', prompt, params)
                for i, (prompt, params) in enumerate(zip(prompts, sampling_params))]

    def add_request(self, rid, prompt, params):
        assert rid not in self.pending
        self.added.append((rid, deepcopy(prompt), deepcopy(params)))
        self.pending[rid] = self.output(rid, prompt, params)

    def step(self):
        self.engine_core.get_output()
        if self.outputs is not None:
            outputs, self.outputs = self.outputs, None
            for output in outputs:
                if output.finished:
                    self.pending.pop(output.request_id, None)
            return outputs
        outputs = list(reversed(self.pending.values()))
        self.pending.clear()
        return outputs

    def abort_request(self, ids):
        self.aborted.extend(ids)
        for rid in ids:
            self.pending.pop(rid, None)

    def reset_prefix_cache(self):
        self.resets += 1
        return self.reset_result


def turn(key='A', *, search=False, budget=2048):
    return Turn(key, [{'role': 'user', 'content': key}],
                {'properties': {'action': {'const': 'search' if search else 'final'}}}, budget)


class EngineTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.model_dir = Path(temp.name)
        (self.model_dir / 'config.json').write_text('{}')
        vllm = ModuleType('vllm')
        vllm.LLM = RawEngine
        vllm.SamplingParams = Params
        sampling = ModuleType('vllm.sampling_params')
        sampling.StructuredOutputsParams = NS
        sampling.RequestOutputKind = NS(FINAL_ONLY='FINAL_ONLY')
        gemma = ModuleType('vllm.reasoning.gemma4_utils')
        gemma.parse_thinking_output = json.loads
        transformers = ModuleType('transformers')
        transformers.AutoTokenizer = NS(from_pretrained=lambda *a, **kw: Tokenizer())
        modules = {'vllm': vllm, 'vllm.sampling_params': sampling,
                   'vllm.reasoning.gemma4_utils': gemma, 'transformers': transformers}
        self.addCleanup(patch.stopall)
        patch.dict(sys.modules, modules).start()

    def model(self, **kwargs):
        return VLLMModel(self.model_dir, **kwargs)

    def test_legacy_import_counter_and_constructor_injection(self):
        from nara.continuous import StreamingModel as OldStreamingModel
        self.assertIs(OldStreamingModel, StreamingModel)
        def configured(**kwargs):
            return RawEngine(disable_log_stats=False, cudagraph_metrics=True,
                             max_num_batched_tokens=8192, enable_chunked_prefill=True, **kwargs)
        with patch('vllm.LLM', configured):
            model = self.model(thinking=True)
        counter = VLLMModel.__new__(VLLMModel)
        counter.tokenizer = model.tokenizer
        counter.thinking = True
        self.assertEqual(counter._tokens(turn().messages), model.render_messages(turn().messages))
        self.assertEqual(counter.count_messages(turn().messages), model.count_messages(turn().messages))

    def test_preflight_and_generation_render_identically(self):
        for thinking in (True, False):
            with self.subTest(thinking=thinking):
                counter = TokenCounter(self.model_dir, thinking=thinking)
                model = self.model(thinking=thinking)
                model.generate([turn()])
                prompt = model.llm.generated[0][0]['prompt_token_ids']
                self.assertEqual(counter.render_messages(turn().messages), prompt)
                self.assertEqual(counter.count_messages(turn().messages), len(prompt))

    def test_offline_and_streaming_conversion_match(self):
        for thinking in (False, True):
            for search, budget in ((False, 2048), (True, 2048), (True, 128), (False, 512)):
                with self.subTest(thinking=thinking, search=search, budget=budget):
                    model = self.model(thinking=thinking)
                    task = turn(search=search, budget=budget)
                    offline = model.generate([task])['A']
                    stream = model.stream()
                    stream.submit(task)
                    model.thinking = not thinking
                    incremental = dict(stream.poll())['A']
                    self.assertEqual(offline, incremental)
                    prompt, params = model.llm.generated[0]
                    _, streamed_prompt, streamed_params = model.llm.added[0]
                    self.assertEqual(prompt, streamed_prompt)
                    self.assertEqual(streamed_params.output_kind, 'FINAL_ONLY')
                    self.assertEqual(params.output_kind, 'CUMULATIVE')
                    for key in ('temperature', 'seed', 'max_tokens', 'skip_special_tokens',
                                'thinking_token_budget', 'structured_outputs'):
                        self.assertEqual(getattr(params, key), getattr(streamed_params, key))
                    expected = (min(256, budget // 4) if search else min(1024, budget // 2)) if thinking else None
                    self.assertEqual(incremental.thinking_budget, expected)
                    self.assertEqual(incremental.thinking_tokens, 7 if thinking else 0)

    def test_mixed_modes_route_out_of_order_completions(self):
        model = self.model(thinking=True)
        stream = StreamingModel(model)
        stream.submit(turn('A'))
        stream.thinking = False
        stream.submit(turn('B'))
        replies = stream.poll()
        self.assertEqual([tid for tid, _ in replies], ['B', 'A'])
        self.assertEqual([r.thinking_budget for _, r in replies], [None, 1024])
        for key, reply in replies:
            self.assertEqual(json.loads(reply.text)[1][0]['content'], key)
        self.assertEqual([r['task_id'] for r in stream.rows], ['B', 'A'])
        self.assertEqual([r['inflight'] for r in stream.lifecycle], [1, 2, 1, 0])
        self.assertEqual(stream.rows[0]['prefill_seconds'], 1.)
        self.assertEqual(stream.rows[0]['decode_seconds'], 2.)
        self.assertEqual(stream.rows[0]['queue_seconds'], 1.)

    def test_request_ids_survive_retries_and_new_stages(self):
        model = self.model()
        first = model.stream()
        first.submit(turn())
        first.poll()
        first.submit(turn())
        first.poll()
        second = StreamingModel(model)
        second.serial = 10000
        second.submit(turn())
        second.poll()
        third = model.stream()
        third.submit(turn())
        third.poll()
        self.assertEqual([rid for rid, _, _ in model.llm.added],
                         ['continuous-0', 'continuous-1', 'continuous-10000', 'continuous-10001'])
        self.assertEqual(len(first.rows), 2)
        self.assertEqual(len(second.rows), 1)
        with self.assertRaises(ValueError):
            third.serial = 0

    def test_partial_completion_then_abort_cleans_outstanding_requests(self):
        model = self.model()
        stream = model.stream()
        stream.submit(turn('A'))
        stream.submit(turn('B'))
        rid = model.llm.added[0][0]
        partial = deepcopy(model.llm.pending[rid])
        partial.finished = False
        model.llm.outputs = [partial]
        self.assertEqual(stream.poll(), [])
        self.assertEqual(len(stream.pending), 2)
        stream.abort()
        self.assertEqual(set(model.llm.aborted), {'continuous-0', 'continuous-1'})
        self.assertFalse(stream.pending)
        self.assertFalse(model.llm.pending)
        stream.abort()
        self.assertEqual(len(model.llm.aborted), 2)

    def test_invalid_metrics_are_explicit_and_requests_remain_abortable(self):
        for stats in (None, Stats(scheduled_ts=0), Stats(first_token_ts=1), Stats(last_token_ts=2)):
            with self.subTest(stats=stats):
                model = self.model()
                stream = model.stream()
                stream.submit(turn())
                model.llm.pending['continuous-0'].metrics = stats
                with self.assertRaisesRegex(ValueError, 'metrics'):
                    stream.poll()
                self.assertFalse(stream.rows)
                stream.abort()
                self.assertEqual(model.llm.aborted, ['continuous-0'])

    def test_observation_restores_engine_and_keeps_stage_evidence(self):
        model = self.model(max_num_seqs=16, max_num_batched_tokens=8192,
                           enable_chunked_prefill=True, collect_scheduler_stats=True)
        self.assertFalse(model.llm.options['disable_log_stats'])
        self.assertTrue(model.llm.options['cudagraph_metrics'])
        self.assertTrue(model.llm.options['enable_chunked_prefill'])
        self.assertEqual(model.engine_info()['max_num_seqs'], 16)
        self.assertEqual(model.engine_info()['capture_sizes'], [1, 2, 4, 8, 16])
        original = model.llm.engine_core.get_output
        with self.assertRaisesRegex(RuntimeError, 'test failure'):
            with model.observe_scheduler() as scheduler:
                stream = model.stream()
                stream.submit(turn())
                stream.poll()
                self.assertEqual(scheduler[0]['graph']['runtime_mode'], 'FULL')
                saved = list(scheduler)
                scheduler.clear()
                self.assertTrue(model.reset_prefix_cache())
                stream = model.stream()
                stream.submit(turn())
                stream.poll()
                self.assertEqual(len(scheduler), 1)
                self.assertEqual(len(saved), 1)
                model.llm.stats = None
                model.llm.engine_core.get_output()
                self.assertEqual(len(scheduler), 1)
                raise RuntimeError('test failure')
        self.assertIs(model.llm.engine_core.get_output, original)
        with model.observe_scheduler() as scheduler:
            model.llm.stats = NS(num_running_reqs=0, num_waiting_reqs=0, num_skipped_waiting_reqs=0,
                                kv_cache_usage=0., prefix_cache_stats=NS(preempted_requests=0), cudagraph_stats=None)
            model.llm.engine_core.get_output()
            self.assertIsNone(scheduler[0]['graph'])
        self.assertIs(model.llm.engine_core.get_output, original)
        model.llm.reset_result = False
        self.assertFalse(model.reset_prefix_cache())

    def test_legacy_offline_observer_can_override_thinking_budget(self):
        from nara.hybrid_experiment import TimedLLM
        model = self.model(thinking=True)
        observer = TimedLLM(model.llm)
        observer.thinking_budget = 0
        model.llm = observer
        reply = model.generate([turn()])['A']
        self.assertEqual(reply.thinking_budget, 0)
        self.assertEqual(reply.thinking_tokens, 0)
        self.assertEqual(len(observer.rows), 1)


if __name__ == '__main__':
    unittest.main()
