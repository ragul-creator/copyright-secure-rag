from __future__ import annotations
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from src.config import settings
from src.rag.vector_store import get_vector_store
from src.services.db import query
from src.security.licenses import source_is_active, get_source


def _can_use(tenant_id: str, src: dict) -> bool:
    can_retrieve, _ = source_is_active(tenant_id, src, "retrieve")
    can_generate, _ = source_is_active(tenant_id, src, "generate")
    return can_retrieve and can_generate


class Retriever:
    def search(self, tenant_id: str, question: str, top_k: int = 4):
        store = get_vector_store()
        if store:
            candidates = store.search(tenant_id, question, max(top_k * 3, top_k))
            approved = []
            for r in candidates:
                if float(r.get("score", 0.0)) < settings.retrieval_min_score:
                    continue
                src = get_source(tenant_id, r["source_id"])
                if src and _can_use(tenant_id, src):
                    approved.append({
                        **r,
                        "source_name": src["name"],
                        "status": src["status"],
                        "rag_allowed": src["rag_allowed"],
                        "generation_allowed": src["generation_allowed"],
                        "expires_at": src.get("expires_at"),
                        "attribution_required": src["attribution_required"],
                        "quote_word_limit": src["quote_word_limit"],
                        "license_spdx": src["license_spdx"],
                    })
                if len(approved) >= top_k:
                    break
            return approved

        rows = query(
            """SELECT c.chunk_id,c.document_id,c.source_id,c.text,s.name AS source_name,s.license_spdx,
                    s.status,s.rag_allowed,s.generation_allowed,s.expires_at,s.attribution_required,s.quote_word_limit
                    FROM chunks c JOIN sources s ON c.tenant_id=s.tenant_id AND c.source_id=s.source_id
                    WHERE c.tenant_id=?""",
            (tenant_id,),
        )
        active = [r for r in rows if _can_use(tenant_id, r)]
        if not active:
            return []
        corpus = [r["text"] for r in active]
        vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=30000)
        X = vec.fit_transform(corpus + [question])
        scores = cosine_similarity(X[-1], X[:-1]).ravel()
        ranked = sorted(zip(active, scores), key=lambda x: x[1], reverse=True)[:top_k]
        return [
            {**r, "score": float(s)}
            for r, s in ranked
            if float(s) >= settings.retrieval_min_score
        ]
