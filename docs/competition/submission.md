# Submission contract

Sources: [평가](https://dacon.io/competitions/official/236754/overview/evaluation), section 3; [규칙](https://dacon.io/competitions/official/236754/overview/rules), section 4 (Python). Verified: 2026-09-10.

## Package and paths

```text
submit.zip
├── script.py          # required Python entry point
├── requirements.txt   # optional pip-installable dependencies
└── model/             # optional static assets
```

- Use this root layout; some wrapper-folder differences may be normalized, but missing `script.py` fails installation validation. Optional-file contents can still fail installation/execution.
- Resolve paths from environment variables, never hardcoded absolute paths:

| Variable | Contract |
|---|---|
| `PPS_DATA_DIR` | Read-only supplied `data/`; `test.jsonl.gz` replaced with hidden unlabeled evaluation notices |
| `PPS_OUTPUT_DIR` | Automatically created output directory; write `submission.csv` here |
| `PPS_MODEL_DIR` | Read-only fixed LLM |
| `PPS_EMBED_DIR` | Read-only auxiliary embedding model |

## Output

- CSV: UTF-8 without BOM, exactly 49 columns in order: `id,v1,...,v24,e1,...,e24`.
- Exactly one row per input notice; every input ID present, no duplicate IDs.
- `v1`–`v24`: nonempty integer `0` or `1`; no probabilities, booleans, or text flags.
- Keep all evidence columns. Empty values are allowed for nonviolations or absent quotable evidence, including absence-detection items. Evidence validity: [evaluation](evaluation.md#evidence).

## Limits and failure accounting

| Resource | Limit |
|---|---|
| Daily submissions | 1 |
| Archive / extracted size | 2 GB / 8 GB |
| Dependency installation | 10 minutes |
| Script execution | 2 hours, including model loading and initialization |
| Hardware | 1 NVIDIA L40S, about 44.7 GiB usable VRAM; 7 vCPU; 60 GiB RAM |
| Isolation | One independent container per submission |
| Network | Package installation only; unavailable during script execution |

- Installation/structure failures do not consume the daily quota. Any failure after `script.py` starts does, including timeout and output validation failure.
- Scoring can take hours with queueing; leave time before the submission deadline. Dates: [sources](sources.md#dates).

## Models and runtime

| Component | Exact value |
|---|---|
| Fixed LLM | `google/gemma-4-26B-A4B-it` |
| LLM revision | `4d7ae4984b7db7de8f8457170b3f1a419ee76d52` |
| Auxiliary embedding model | `BAAI/bge-m3` |
| Embedding revision | `5617a9f61b028005a4858fdac845db406aefb181` |
| Base image | `vllm/vllm-openai:v0.26.0` (organizer pins digest) |
| OS / Python / CUDA | Ubuntu 22.04 / 3.12.13 / 13.0 |
| Host driver | NVIDIA 580+ |

- Load via local environment-variable paths using vLLM offline API (`from vllm import LLM`). Downloading by Hugging Face model ID fails at runtime.
- Put execution under `if __name__ == "__main__":`; module-level LLM creation fails with spawned subprocesses.
- BF16 LLM does not fit the GPU; quantized loading is required. Context ceiling: `max_model_len=32768`.
- Baseline example, not a required configuration: `quantization="int8_per_channel_weight_only"`, `max_model_len=16384`.
- Simultaneous GPU residency of LLM and embeddings is not guaranteed; choose embedding device/load order accordingly.
- Organizer recommends structured decoding; supplied schema: `data/정답스키마_디코딩.json` (resolve under `PPS_DATA_DIR`).
- Local GPU/runtime/precision are unrestricted. Reproducibility is limited to matching image, model revision, driver, vLLM, and seed; local/server predictions may differ.

## Dependencies

Server-fixed versions; `requirements.txt` cannot override:

```text
vllm==0.26.0
torch==2.11.0+cu130
transformers==5.14.1
xgrammar==0.2.3
```

Other preinstalled packages; organizer recommends reusing them without relisting in requirements:

```text
jsonschema==4.26.0      tokenizers==0.22.2       safetensors==0.8.0
openai==2.48.0         pydantic==2.13.4        numpy==2.2.6
requests==2.34.2       tqdm==4.69.1            pyyaml==6.0.3
regex==2026.7.19       sentencepiece==0.2.2    pandas==2.2.3
scikit-learn==1.6.1    rank-bm25==0.2.2        sentence-transformers==5.3.0
kiwipiepy==0.21.0      orjson==3.10.18
```

System packages: `git`, `build-essential`, `unzip`, `p7zip-full`, `tzdata`, `libgl1`, `libglib2.0-0`, `ca-certificates`, `procps`.
