from __future__ import annotations
import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer
from src.config import settings


_hashing = HashingVectorizer(n_features=settings.embedding_dim, alternate_sign=False, norm="l2")
_model = None


def embed_texts(texts: list[str]) -> list[list[float]]:
    global _model
    if settings.embedding_backend == "sentence_transformers":
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError("sentence_transformers backend requires requirements-production.txt") from exc
        if _model is None:
            _model = SentenceTransformer(settings.embedding_model)
        vectors = _model.encode(texts, normalize_embeddings=True)
        return np.asarray(vectors, dtype=np.float32).tolist()
    return _hashing.transform(texts).astype(np.float32).toarray().tolist()


def embed_text(text: str) -> list[float]:
    return embed_texts([text])[0]
