from __future__ import annotations
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from src.services.db import query
from src.security.licenses import source_is_active

class Retriever:
    def search(self, question: str, top_k: int = 4):
        rows = query("""SELECT c.chunk_id,c.document_id,c.source_id,c.text,s.name AS source_name,
                    s.status,s.rag_allowed,s.generation_allowed,s.expires_at,s.attribution_required,s.quote_word_limit
                    FROM chunks c JOIN sources s ON c.source_id=s.source_id""")
        active=[]
        for r in rows:
            ok,_ = source_is_active(r)
            if ok and r["generation_allowed"]:
                active.append(r)
        if not active: return []
        corpus=[r["text"] for r in active]
        vec=TfidfVectorizer(stop_words="english", ngram_range=(1,2), max_features=30000)
        X=vec.fit_transform(corpus+[question])
        scores=cosine_similarity(X[-1], X[:-1]).ravel()
        ranked=sorted(zip(active,scores), key=lambda x:x[1], reverse=True)[:top_k]
        return [{**r,"score":float(s)} for r,s in ranked if s>0]
