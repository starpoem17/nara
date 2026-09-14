# File-backed legal retrieval

Code: [builder](<../../src/retrieval/index.py>), [retriever](<../../src/retrieval/search.py>). Caller: [dynamic RAG](<dynamic-rag.md>).

## Interface

```python
from nara.retrieval import BGEEncoder, LegalRetriever

encoder = BGEEncoder("models/bge-m3", device="cuda", batch_size=32)
retriever = LegalRetriever("model/legal_index", encoder)
hits = retriever.search({"record:turn:query": "중소 소프트웨어사업자의 사업 참여 제한"}, top_k=5)
```

- `search({query_id: text}, top_k=5) -> {query_id: list[SearchHit]}`; caller owns IDs. Immutable index; no conversation state.
- Hit fields: `passage_id, text, source, locator, title, section, score`. CPU exact dense search; at most `top_k` hits after whitespace-normalized text deduplication.
- Empty query map → `{}`. Invalid IDs/queries/limits, encoder mismatch, corrupt artifacts or invalid vectors → error.
- Local BGE-M3: CLS pooling, normalized 1024-dimensional vectors; pinned revision in [model contract](<../competition/submission.md#models-and-runtime>). Check available download metadata and index/query signatures (revision, dimensions, normalization, tokenizer/config/modules/pooling hashes). No weight downloads or silent input truncation.

## Build and artifacts

Run from project root; existing index directory is refused:

```bash
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 uv run --locked python -m nara.retrieval.index build \
  --device cuda --index model/legal_index
```

- Defaults: `--embed-model` = `PPS_EMBED_DIR` or `models/bge-m3`; `--corpus data/법령패키지`. Static assets use only this supplied corpus.
- TXT/CSV/HWPX extraction retains headers, expands merged cells into product rows, preserves locators/text offsets. Prefer article/section boundaries, then paragraphs/token splits: 512 BGE tokens including title/section prefix; 64 body-token overlap.
- Stage and validate before publishing: `passages.jsonl` (text, embedding input, provenance), `embeddings.npy` (normalized float32), `manifest.json` (format, encoder/chunk settings, source/artifact checksums, counts, build time).

Query from project root:

```bash
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 uv run --locked python -m nara.retrieval.index search \
  --device cpu --query "중소기업자간 경쟁제품 직접생산 확인 증명서"
```

Checks, measurements and ranking limitations: [experiments](<../maintenance/local-validation.md>).
