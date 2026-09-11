# Local engine module refactor: dev200 before/after

Completed 2026-09-11. User selected the local engine deepening, required compatibility with existing experiment calls, and approved automatic tests plus a matched 200-record before/after comparison. Implementation/interface: [local engine](../architecture/local-engine.md).

## Change and controls

Engine-specific rendering, sampling, reply conversion, request identity, cache reset and scheduler observation now reside in `nara/vllm_model.py`. `StreamingModel` remains importable from `nara.continuous`. Default execution uses explicit engine options and an observation scope that restores the engine callback on exit. Isolated-group recovery scheduler rows now enter the root aggregate alongside their request/lifecycle rows.

Only three runtime source files differ: `nara/vllm_model.py`, `nara/continuous.py`, `scripts/benchmark_prefix_pipeline.py`. Inputs, criteria, H6 rules, groups, budgets, admission policy, dependency lock and effective engine configuration were held fixed. All 200 initial prompt lengths/common-prefix counts match. The baseline includes pre-existing working-copy H6 edits; it is not the historical `analysis/prefix_pipeline200` run or a clean checkout of the earlier commit.

Both runs: local Gemma NVFP4/RTX5090, 12 OFF groups, 16 slots, step budget8192, context32768, output2048, initial2/live3/source48000/lookahead16. Warmup and first8 smoke are excluded from prediction time; internal retries and any recovery are included. Both runs had zero outer recovery time.

## Measurements

| Metric | Before | After |
|---|---:|---:|
| Prediction seconds | 296.6103 | 310.5711 |
| Model/retriever load seconds | 30.1413 | 27.4461 |
| Macro F1 | 0.268474 | 0.259844 |
| Micro F1 | 0.266344 | 0.261307 |
| Failed notices | 0 | 0 |
| Model requests | 2401 | 2403 |
| Invalid responses / internal retries | 1 | 3 |
| Output tokens | 114724 | 117245 |
| Cached input fraction | 90.8425% | 90.7775% |
| Peak requests in flight | 16 | 16 |
| Actual FULL graph steps | 12923 | 14419 |
| FULL steps with16 real tokens | 197 | 268 |
| Early next-notice prefill | 197/198 | 197/198 |
| Preempted request events | 0 | 0 |

After was13.9609s (+4.7068%) slower in this paired measurement; Macro F1 decreased0.008630. Output tokens increased2.20%; 227/4800 binary judgments and91 evidence fields changed. Neither the observed differences nor one pair of runs establish their cause or a repeatable performance/quality change. This refactor is not reported as a speed or F1 improvement.

## Verification

- Existing64 tests passed before; 74 passed after (10 new tests, including three recovery outcomes). Engine tests use a deterministic raw-engine adapter, not a replacement for the production engine module.
- Real GPU run audit passed:200 complete records,49-column CSV, unique request IDs, request/trace/token totals, zero thinking, seed completion before followers, source-window limits, FULL graphs and early prefill. Archived source hashes match; live runtime sources remained unchanged throughout each run.
- Real tokenizer and installed vLLM request parity against the archived before implementation is recorded in `analysis/engine_refactor200/request_parity.json`: all2400 initial requests have identical complete token-ID payloads and sampling fields; 12 OFF/ON, search/final and output-budget variants also match. This stops at request submission; it does not claim identical generated output.

## Artifacts and reproduction

Tracked summary/provenance: `analysis/engine_refactor200/comparison.json`; request-parity evidence: `analysis/engine_refactor200/request_parity.json`.

Local raw runs, reports, manifests and source snapshots (ignored `output/`):
- Before: `output/experiments/engine-refactor-before-20260911/`
- After: `output/experiments/engine-refactor-after-20260911/`
- GPU-free after preflight: `output/experiments/engine-refactor-preflight-20260911/`

```bash
uv run --locked python -m unittest discover -s tests
uv run --locked python scripts/run_experiment.py --output-dir FRESH_DIRECTORY
uv run --locked python analysis/engine_refactor200/verify.py FRESH_DIRECTORY
uv run --locked python analysis/engine_refactor200/request_parity.py output/experiments/engine-refactor-before-20260911
```

The archived before source is required for differential request verification. Source/data digests are included in comparison.json; raw data and full run snapshots stay local. Historical report/recovery redesign and judgment-conversation consolidation remain separate work.
