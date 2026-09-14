# Local Python environment

The project uses uv and Python 3.12.13. Direct dependencies match the versions
listed in `docs/competition/submission.md`; `uv.lock` also pins transitive
packages. PyTorch, torchvision, and torchaudio use the official CUDA 13.0 index.
This environment targets Linux x86_64.

```bash
uv sync --locked
uv run --locked python your_script.py
```

Run these commands from the project directory. Activating `.venv` is optional
when using `uv run`. No global Python installation is modified.

This reproduces the published Python package versions, not the complete
competition container: the local host uses Ubuntu 24.04 and RTX 5090, while the
server uses Ubuntu 22.04 and L40S. Unpublished transitive package versions and
system libraries may differ from the server image.

These files configure local development. Do not export the full environment as
submission requirements: vLLM, torch, transformers, and xgrammar are fixed on the
server, and its preinstalled packages should normally be reused.

Dependency installation alone does not install model weights or verify inference.
The separate local model setup and GPU check are described below.

## Local Gemma 4 26B inference check

The local check uses
[RedHatAI/gemma-4-26B-A4B-it-NVFP4](https://huggingface.co/RedHatAI/gemma-4-26B-A4B-it-NVFP4),
revision `5557756b8dce33ac72f2bd702b11729fdba3b839`, downloaded into
`models/gemma-4-26B-A4B-it-NVFP4` (ignored by Git). This is a local NVFP4
checkpoint, not a verification of the organizer's BF16 revision / INT8 setup.

To download the same checkpoint on another machine:

```bash
uv run --locked python - <<'PY'
from huggingface_hub import snapshot_download
snapshot_download(
    'RedHatAI/gemma-4-26B-A4B-it-NVFP4',
    revision='5557756b8dce33ac72f2bd702b11729fdba3b839',
    local_dir='models/gemma-4-26B-A4B-it-NVFP4',
    ignore_patterns=['every_eval_ever/*'],
)
PY
```

Run the GPU check from the project root:

```bash
MAX_JOBS=2 uv run --locked python -m nara.tools.check_gemma_inference
```

Use `uv run` (or activate `.venv`) so FlashInfer can find the installed `ninja`
executable. `MAX_JOBS=2` limits first-run CUDA kernel compilation: unrestricted
parallel compilation was killed with exit code 137 on this 32GB RAM host.
The first run compiles kernels; subsequent runs reuse the local cache.

The check sets `max_model_len=32768`, `gpu_memory_utilization=0.90`, and
`max_num_seqs=1`, disables multimodal inputs, and uses `enforce_eager=True`.
It explicitly selects `kernel_config={"moe_backend": "cutlass"}` to use the
vLLM NVFP4 MoE kernel supported on RTX 5090, avoiding the much larger
automatically selected FlashInfer MoE build. Linear layers still use FlashInfer
CUTLASS NVFP4, with first-run compilation limited by `MAX_JOBS`.
It tests Korean output, structured JSON, 16K/32K input budgets, and rejection of
an input above the configured ceiling. The context budget includes the chat
format, input, and generated output; the long-input checks reserve 64 output
tokens. Results are written to `docs/maintenance/evidence/local-validation/gemma_inference_check.json`.
To check another context limit, pass `--max-model-len 16384` and a separate
`--output` path.

The supplied `open/baseline/script.py` still uses its original 16,384-token
context and INT8 setting. Its default `/opt/models/...` path does not exist on
this machine. The local check does not change that baseline.

Verified on 2026-09-10 with RTX 5090, vLLM 0.26.0, and torch 2.11.0+cu130:

- Korean short answer: `서울`.
- Structured JSON: `{"answer": 5}`.
- 16,320- and 32,704-token prompts: no input truncation; both answered `서울`.
- 32,769-token prompt: rejected with the configured 32,768-token limit.
- Model loading used 14.8 GiB; available KV cache was 11.37 GiB.
- Process exited successfully and released GPU memory.

These are synthetic smoke checks, not a long-document retrieval/accuracy or
throughput benchmark. vLLM warns that differing global NVFP4 scales in fused
linear layers may reduce accuracy; task-quality evaluation remains necessary.
