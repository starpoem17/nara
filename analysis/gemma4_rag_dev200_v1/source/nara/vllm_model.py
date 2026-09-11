"""Local vLLM adapter; ID routing and rendered-token accounting."""
import json
from pathlib import Path

from nara.inference import Reply


class VLLMModel:
    def __init__(self, model_dir, *, max_model_len=32768, gpu_memory_utilization=0.86,
                 max_num_seqs=8, quantization="auto", thinking=False, enforce_eager=False):
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
        if not 0 < max_model_len <= 32768:
            raise ValueError("max_model_len must be in 1..32768")
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

    def count_text(self, text):
        return len(self.tokenizer.encode(text, add_special_tokens=False))

    def _tokens(self, messages):
        return self.tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, tokenize=True, return_dict=False,
            enable_thinking=self.thinking,
        )

    def count_messages(self, messages):
        return len(self._tokens(messages))

    def generate(self, turns):
        from vllm import SamplingParams
        from vllm.reasoning.gemma4_utils import parse_thinking_output
        from vllm.sampling_params import StructuredOutputsParams
        params = [
            SamplingParams(
                temperature=0, max_tokens=turn.max_tokens, seed=0,
                skip_special_tokens=False,
                structured_outputs=StructuredOutputsParams(
                    json=turn.schema, disable_any_whitespace=True),
            ) for turn in turns
        ]
        prompts = [{"prompt_token_ids": self._tokens(turn.messages)} for turn in turns]
        outputs = self.llm.generate(prompts, sampling_params=params, use_tqdm=False)
        if len(outputs) != len(turns):
            raise ValueError("vLLM returned an unexpected result count")
        result = {}
        # vLLM's offline generate contract returns results in input order.
        for turn, output in zip(turns, outputs):
            completion = output.outputs[0]
            text = self.tokenizer.decode(completion.token_ids, skip_special_tokens=False)
            answer = parse_thinking_output(text)["answer"]
            result[turn.task_id] = Reply(
                answer, completion.finish_reason,
                len(output.prompt_token_ids), len(completion.token_ids))
        return result
