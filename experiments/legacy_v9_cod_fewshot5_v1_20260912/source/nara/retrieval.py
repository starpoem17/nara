"""File-backed dense retrieval with an injected query encoder."""
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path

import numpy as np


BGE_REVISION = "5617a9f61b028005a4858fdac845db406aefb181"


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalized(vectors):
    vectors = np.asarray(vectors, dtype=np.float32)
    if vectors.ndim != 2 or not np.isfinite(vectors).all():
        raise ValueError("Embeddings must be a finite two-dimensional matrix")
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    if np.any(norms == 0):
        raise ValueError("Zero-length embedding")
    return vectors / norms


class BGEEncoder:
    """Load local BGE-M3 only; reject inputs that would be silently truncated."""

    def __init__(self, model_dir, *, device="cpu", batch_size=32,
                 revision=BGE_REVISION):
        import torch
        from sentence_transformers import SentenceTransformer

        model_dir = Path(model_dir)
        if batch_size < 1:
            raise ValueError("batch_size must be positive")
        for name in ("config.json", "tokenizer.json", "pytorch_model.bin", "model.safetensors"):
            metadata = model_dir / ".cache/huggingface/download" / (name + ".metadata")
            if metadata.exists() and metadata.read_text().splitlines()[0] != revision:
                raise ValueError(f"Local model revision differs: {name}")
        self.model = SentenceTransformer(
            str(model_dir), device=device, local_files_only=True,
            model_kwargs={"dtype": torch.float16 if device.startswith("cuda") else torch.float32},
        )
        self.tokenizer = self.model.tokenizer
        self.batch_size = batch_size
        self.signature = {
            "model": "BAAI/bge-m3",
            "revision": revision,
            "dimension": self.model.get_sentence_embedding_dimension(),
            "normalized": True,
            "tokenizer_sha256": file_sha256(model_dir / "tokenizer.json"),
            "pooling_sha256": file_sha256(model_dir / "1_Pooling/config.json"),
            "config_sha256": file_sha256(model_dir / "config.json"),
            "modules_sha256": file_sha256(model_dir / "modules.json"),
        }

    def encode(self, texts):
        texts = list(texts)
        if not texts:
            return np.empty((0, self.signature["dimension"]), dtype=np.float32)
        if any(not isinstance(text, str) or not text.strip() for text in texts):
            raise ValueError("Embedding inputs must be nonempty text")
        lengths = self.tokenizer(
            texts, add_special_tokens=True, truncation=False, return_length=True,
        )["length"]
        if max(lengths) > self.model.max_seq_length:
            raise ValueError(f"Embedding input exceeds {self.model.max_seq_length} tokens")
        return normalized(self.model.encode(
            texts, batch_size=self.batch_size, convert_to_numpy=True,
            normalize_embeddings=True, show_progress_bar=False,
        ))


@dataclass(frozen=True)
class SearchHit:
    passage_id: str
    text: str
    source: str
    locator: str
    title: str
    section: str
    score: float

    def to_dict(self):
        return asdict(self)


class LegalRetriever:
    """search({request_id: query}, top_k=5) returns hits under the same IDs.

    The matrix stays in CPU RAM. Search never reads or modifies another
    request's conversation. The injected encoder must match the index's model
    and preprocessing signature; query completion order is irrelevant to IDs.
    """

    def __init__(self, index_dir, encoder):
        index_dir = Path(index_dir)
        self.manifest = json.loads((index_dir / "manifest.json").read_text())
        if self.manifest["format_version"] != 1:
            raise ValueError("Unsupported index format")
        if self.manifest["encoder"] != encoder.signature:
            raise ValueError("Query encoder is incompatible with this index")
        for name in ("passages.jsonl", "embeddings.npy"):
            if file_sha256(index_dir / name) != self.manifest["artifacts"][name]:
                raise ValueError(f"Index checksum mismatch: {name}")
        self.passages = [
            json.loads(line)
            for line in (index_dir / "passages.jsonl").read_text().splitlines()
        ]
        self.vectors = np.load(index_dir / "embeddings.npy", allow_pickle=False)
        expected = (len(self.passages), encoder.signature["dimension"])
        if not self.passages or self.vectors.shape != expected:
            raise ValueError("Index passages and embedding dimensions disagree")
        if self.manifest["passage_count"] != len(self.passages):
            raise ValueError("Index passage count mismatch")
        if len({p["id"] for p in self.passages}) != len(self.passages):
            raise ValueError("Duplicate passage IDs")
        if not np.isfinite(self.vectors).all() or not np.allclose(
            np.linalg.norm(self.vectors, axis=1), 1.0, atol=1e-4
        ):
            raise ValueError("Index vectors are not finite and normalized")
        self.vectors.flags.writeable = False
        self.encoder = encoder

    def search(self, queries, *, top_k=5):
        if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 1:
            raise ValueError("top_k must be a positive integer")
        if not queries:
            return {}
        if any(not isinstance(key, str) or not key for key in queries):
            raise ValueError("Search request IDs must be nonempty strings")
        if any(not isinstance(q, str) or not q.strip() for q in queries.values()):
            raise ValueError("Search queries must be nonempty text")
        query_vectors = normalized(self.encoder.encode(list(queries.values())))
        if query_vectors.shape != (len(queries), self.vectors.shape[1]):
            raise ValueError("Query encoder returned an unexpected shape")
        scores = query_vectors @ self.vectors.T
        result = {}
        # Stable ordering makes equal-score results reproducible.
        for request_id, row in zip(queries, scores):
            hits, seen = [], set()
            for index in np.argsort(-row, kind="stable"):
                passage = self.passages[int(index)]
                key = " ".join(passage["text"].split())
                if key in seen:
                    continue
                seen.add(key)
                hits.append(SearchHit(
                    passage_id=passage["id"], text=passage["text"],
                    source=passage["source"], locator=passage["locator"],
                    title=passage["title"], section=passage["section"],
                    score=float(np.clip(row[index], -1, 1)),
                ))
                if len(hits) == top_k:
                    break
            result[request_id] = hits
        return result
