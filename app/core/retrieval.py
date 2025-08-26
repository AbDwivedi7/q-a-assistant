from __future__ import annotations
import os
import faiss
import numpy as np

# Minimal FAISS helper; embeddings would typically come from an embedding model.

class SimpleIndexer:
    def __init__(self, dim: int = 384):
        self.dim = dim
        self.index = faiss.IndexFlatIP(dim)
        self.docs: list[str] = []

    def _embed(self, text: str) -> np.ndarray:
        # Toy hashing-based embedding (for demo without API). Replace with real embeddings in prod.
        rng = np.random.default_rng(abs(hash(text)) % (2**32))
        v = rng.random(self.dim)
        v /= np.linalg.norm(v) + 1e-9
        return v.astype("float32")

    def add(self, texts: list[str]):
        vecs = np.vstack([self._embed(t) for t in texts])
        self.index.add(vecs)
        self.docs.extend(texts)

    def search(self, query: str, k: int = 3) -> list[str]:
        qv = self._embed(query)[None, :]
        _, idx = self.index.search(qv, k)
        return [self.docs[i] for i in idx[0] if i < len(self.docs)]