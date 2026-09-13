"""Local engine execution, prompt rendering, cache lifecycle and observation."""
from contextlib import contextmanager
from dataclasses import asdict
import json
import time
from pathlib import Path

from nara.inference.predictor import Reply


class TokenCounter:
    """GPU-free preflight using the same rendering as engine requests."""
    def __init__(self, model_dir, *, thinking=False, max_model_len=32768):
        from transformers import AutoTokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
        self.thinking = thinking
        self.max_model_len = max_model_len

    def count_text(self, text):
        return len(self.tokenizer.encode(text, add_special_tokens=False))

    def render_messages(self, messages):
        return self.tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, tokenize=True, return_dict=False,
            enable_thinking=self.thinking,
        )

    def _tokens(self, messages):
        """Compatibility for older experiment token counters."""
        return self.render_messages(messages)

    def count_messages(self, messages):
        return len(self._tokens(messages))


class VLLMModel(TokenCounter):
    _request_serial = 0
    _context_limit = 32768  # Default/server ceiling; isolated experiments may override.

    def __init__(self, model_dir, *, max_model_len=32768, gpu_memory_utilization=0.86,
                 max_num_seqs=8, quantization="auto", thinking=False, enforce_eager=False,
                 max_num_batched_tokens=None, enable_chunked_prefill=None,
                 collect_scheduler_stats=False):
        from vllm import LLM
        config = json.loads((Path(model_dir) / "config.json").read_text())
        options = {}
        if quantization == "auto":
            if not config.get("quantization_config"):
                options["quantization"] = "int8_per_channel_weight_only"
        elif quantization != "none":
            options["quantization"] = quantization
        # The downloaded local NVFP4 checkpoint uses Cutlass MoE on Blackwell.
        if "nvfp4" in json.dumps(config.get("quantization_config", {})).lower():
            options["kernel_config"] = {"moe_backend": "cutlass"}
        if not 0 < max_model_len <= self._context_limit:
            raise ValueError(f"max_model_len must be in 1..{self._context_limit}")
        if thinking:
            options["reasoning_parser"] = "gemma4"
        # Omit optional keywords unless requested: legacy scripts inject them too.
        if max_num_batched_tokens is not None:
            options["max_num_batched_tokens"] = max_num_batched_tokens
        if enable_chunked_prefill is not None:
            options["enable_chunked_prefill"] = enable_chunked_prefill
        if collect_scheduler_stats:
            options.update(disable_log_stats=False, cudagraph_metrics=True)
        self.max_model_len, self.thinking = max_model_len, thinking
        self.llm = LLM(
            model=str(model_dir), tokenizer=str(model_dir), max_model_len=max_model_len,
            gpu_memory_utilization=gpu_memory_utilization, max_num_seqs=max_num_seqs,
            enable_prefix_caching=True, enforce_eager=enforce_eager, seed=0,
            limit_mm_per_prompt={"image": 0, "audio": 0, "video": 0},
            structured_outputs_config={"backend": "xgrammar", "reasoning_parser": "gemma4"},
            **options,
        )
        self.tokenizer = self.llm.get_tokenizer()

    def _sampling(self, turn, *, incremental=False):
        from vllm import SamplingParams
        from vllm.sampling_params import StructuredOutputsParams, RequestOutputKind
        search = turn.schema.get("properties", {}).get("action", {}).get("const") == "search"
        budget = ((min(256, turn.max_tokens // 4) if search else min(1024, turn.max_tokens // 2))
                  if self.thinking else None)
        options = {"output_kind": RequestOutputKind.FINAL_ONLY} if incremental else {}
        return SamplingParams(
            temperature=0, max_tokens=turn.max_tokens, seed=0,
            skip_special_tokens=False, thinking_token_budget=budget,
            structured_outputs=StructuredOutputsParams(json=turn.schema, disable_any_whitespace=True),
            **options)

    def _reply(self, output, budget):
        from vllm.reasoning.gemma4_utils import parse_thinking_output
        completion = output.outputs[0]
        text = self.tokenizer.decode(completion.token_ids, skip_special_tokens=False)
        parsed = parse_thinking_output(text)
        return Reply(parsed["answer"], completion.finish_reason,
                     len(output.prompt_token_ids), len(completion.token_ids),
                     thinking_tokens=self.count_text(parsed["thinking"] or ""), thinking_budget=budget)

    def generate(self, turns):
        params = [self._sampling(turn) for turn in turns]
        prompts = [{"prompt_token_ids": self._tokens(turn.messages)} for turn in turns]
        outputs = self.llm.generate(prompts, sampling_params=params, use_tqdm=False)
        if len(outputs) != len(turns):
            raise ValueError("vLLM returned an unexpected result count")
        # Offline results follow input order; legacy observers may adjust params.
        return {turn.task_id: self._reply(output, param.thinking_token_budget)
                for turn, output, param in zip(turns, outputs, params)}

    def stream(self):
        """Start a sequential execution stage with fresh request/lifecycle records."""
        return StreamingModel(self)

    def reset_prefix_cache(self):
        """Reset cached prefixes between stages, after all requests have drained."""
        return self.llm.reset_prefix_cache()

    def engine_info(self):
        cfg = self.llm.llm_engine.vllm_config
        return {"max_num_seqs": cfg.scheduler_config.max_num_seqs,
                "max_num_batched_tokens": cfg.scheduler_config.max_num_batched_tokens,
                "cudagraph_mode": str(cfg.compilation_config.cudagraph_mode),
                "capture_sizes": cfg.compilation_config.cudagraph_capture_sizes,
                "kv_cache_dtype": str(cfg.cache_config.cache_dtype),
                "gpu_memory_utilization": cfg.cache_config.gpu_memory_utilization}

    @contextmanager
    def observe_scheduler(self):
        """Collect raw step evidence; restore the engine on success or failure.

        Use collect_scheduler_stats=True at construction to enable graph stats.
        The yielded list can be cleared between stages after saving its rows.
        """
        core = self.llm.llm_engine.engine_core
        original = core.get_output
        rows = []

        def observed_get():
            output = original()
            stats = output.scheduler_stats
            if stats is not None:
                rows.append({"time": time.monotonic(), "running": stats.num_running_reqs,
                    "waiting": stats.num_waiting_reqs, "deferred": stats.num_skipped_waiting_reqs,
                    "kv_usage": stats.kv_cache_usage,
                    "preempted_requests": stats.prefix_cache_stats.preempted_requests,
                    "graph": asdict(stats.cudagraph_stats) if stats.cudagraph_stats is not None else None})
            return output

        core.get_output = observed_get
        try:
            yield rows
        finally:
            core.get_output = original


class StreamingModel:
    """Incremental execution for one active stream; submitted settings stay fixed.

    Sequential streams share the engine's request counter. Legacy serial overrides
    still work, but cannot reuse an already allocated request ID.
    """
    def __init__(self, model):
        self.base = model
        self.pending = {}
        self.rows = []
        self.lifecycle = []

    def __getattr__(self, name):
        return getattr(self.base, name)

    @property
    def thinking(self):
        return self.base.thinking

    @thinking.setter
    def thinking(self, value):
        self.base.thinking = value

    @property
    def serial(self):
        return self.base._request_serial

    @serial.setter
    def serial(self, value):
        if type(value) is not int or value < self.base._request_serial:
            raise ValueError("Request serial must not reuse allocated IDs")
        self.base._request_serial = value

    def submit(self, turn):
        params = self.base._sampling(turn, incremental=True)
        tokens = self.base._tokens(turn.messages)
        rid = f"continuous-{self.serial}"
        self.serial += 1
        self.base.llm.llm_engine.add_request(rid, {"prompt_token_ids": tokens}, params)
        self.pending[rid] = (turn, params.thinking_token_budget)
        self.lifecycle.append({"event": "submit", "request_id": rid, "task_id": turn.task_id,
            "time": time.monotonic(), "inflight": len(self.pending), "input_tokens": len(tokens),
            "thinking_budget": params.thinking_token_budget})

    def poll(self):
        completed = []
        for out in self.base.llm.llm_engine.step():
            if not out.finished:
                continue
            turn, budget = self.pending[out.request_id]
            reply = self.base._reply(out, budget)
            s = out.metrics
            if s is None or not 0 < s.scheduled_ts <= s.first_token_ts <= s.last_token_ts:
                raise ValueError("Missing/nonmonotonic request metrics")
            self.pending.pop(out.request_id)
            self.rows.append({"request_id": out.request_id, "task_id": turn.task_id,
                "input_tokens": reply.input_tokens, "output_tokens": reply.output_tokens,
                "cached_tokens": out.num_cached_tokens, "thinking_budget": budget,
                "finish_reason": reply.finish_reason, "request_stats": asdict(s),
                "prefill_seconds": s.first_token_ts - s.scheduled_ts,
                "decode_seconds": s.last_token_ts - s.first_token_ts,
                "queue_seconds": s.scheduled_ts - s.queued_ts})
            self.lifecycle.append({"event": "complete", "request_id": out.request_id,
                "task_id": turn.task_id, "time": time.monotonic(), "inflight": len(self.pending)})
            completed.append((turn.task_id, reply))
        return completed

    def abort(self):
        if self.pending:
            self.base.llm.llm_engine.abort_request(list(self.pending))
        self.pending.clear()
