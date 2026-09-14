# Local validation

Status: historical environment and implementation checks, with their original scopes and counts. Current migration verification is [recorded separately](structure-migration-verification.md); old command snippets below are historical provenance.

Recorded results as of 2026-09-10; not rerun during documentation cleanup.
Implementation: [retrieval](<../architecture/legal-retrieval.md>), [inference](<../architecture/dynamic-rag.md>).

## Reproduce

Run from project root; GPU checks require local models/index:

```bash
uv run --locked python -m unittest discover -s tests -v
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 uv run --locked python -m nara.tools.check_legal_retrieval
uv run --locked python -m nara.tools.check_dynamic_rag
```

Unit tests use small fixtures/injected models; no GPU. Retrieval check covers extraction, lengths and four expected-source queries with GPU FP16/CPU FP32 encoders. Dynamic check covers two revised searches, item groups of six, longest source and thinking JSON. Its item note forces search; it does not test voluntary search propensity.

## Recorded checks

| Evidence | Result / scope |
|---|---|
| [Retrieval report](<evidence/local-validation/legal_retrieval_check.json>) | 25 files, 1259 extracted entries, 6242 passages; 24.38 MiB matrix; no uncovered non-whitespace text; max 505/512 tokens. Four queries find expected source in top 5 on both encoders. Warm batch median GPU 0.0093s / CPU 0.1552s (4 threads); GPU peak allocation ~1094 MiB, not a co-resident reservation. |
| [Dynamic report](<evidence/dynamic_rag_check/report.json>) | RTX 5090/NVFP4, CUDA graphs, both models resident: load 64.32s including compilation; 2 records × 2 searches 11.38s (retrieval 0.162s); grouped record 4.42s; longest 6.29s; total 88.00s. |
| [Early prompt scan](<evidence/local-validation/rag_prompt_lengths.json>) | 200 original prompts: max 29846 tokens; sources fit, initial optional search disabled for 6 longest. Prompt/settings-specific, not a current invariant. |
| [Early eager smoke](<evidence/rag_smoke/report.json>), [dev32](<evidence/rag_dev32/report.json>) | 4/32 records, no failures or voluntary searches. dev32 load 28.85s + prediction 55.45s = 84.30s; not RAG-heavy throughput. |

## Later dev200 experiments

Scores, settings and per-run artifacts: [dev200 comparison](<../experiments/prompt-design/retrieval-and-thinking.md>).

- Optional search produced no searches; forcing one search did not improve Macro F1. Thinking with optional search had the highest observed Macro F1 of these three runs.
- Thinking initially succeeded on 199/200 records; one record required recovery with output budget 4096 instead of 2048. The combined result is not a single successful uniform-budget run.
- Exploratory: same dev data selected settings and measured quality; RTX 5090/NVFP4 results do not establish server INT8 quality/performance.

## Grouping latency

Same-notice timing comparison of 1/7/9/12 groups, including selection bias and an incomplete run: [grouping time](<../experiments/inference-scheduling/grouping-time.md>). The original benchmark measured timing; a later evaluation of the frozen predictions compares accuracy on 31 common successful notices.

## Open validation

- L40S/INT8 compatibility and full-test completion within the [runtime limit](<../competition/submission.md#limits-and-failure-accounting>).
- CPU vs GPU end-to-end inference and vLLM vs Sentence Transformers BGE. Small query cost alone does not establish the best backend.
- Retrieval relevance beyond smoke queries: introductory passages may outrank operative provisions; inspect traces before changing ranking.
