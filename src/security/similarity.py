from __future__ import annotations
import re
from rapidfuzz.fuzz import ratio, partial_ratio
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def words(text: str) -> list[str]:
    return re.findall(r"\b\w+\b", text.lower())


def longest_common_word_span(a: str, b: str) -> int:
    A,B=words(a),words(b)
    if not A or not B:
        return 0
    prev=[0]*(len(B)+1); best=0
    for x in A:
        cur=[0]*(len(B)+1)
        for j,y in enumerate(B,1):
            if x==y:
                cur[j]=prev[j-1]+1
                best=max(best,cur[j])
        prev=cur
    return best


def _shingles(text: str, n: int = 5) -> set[tuple[str,...]]:
    xs=words(text)
    if len(xs) < n:
        return set()
    return {tuple(xs[i:i+n]) for i in range(len(xs)-n+1)}


def ngram_jaccard(a: str,b: str,n: int=5) -> float:
    ga,gb=_shingles(a,n),_shingles(b,n)
    if not ga or not gb:
        return 0.0
    return len(ga&gb)/len(ga|gb)


def minhash_similarity(a: str, b: str, n: int = 5) -> float:
    ga,gb=_shingles(a,n),_shingles(b,n)
    if not ga or not gb:
        return 0.0
    try:
        from datasketch import MinHash
    except ImportError:
        return len(ga&gb)/len(ga|gb)
    ma,mb=MinHash(num_perm=128),MinHash(num_perm=128)
    for g in ga:
        ma.update(" ".join(g).encode())
    for g in gb:
        mb.update(" ".join(g).encode())
    return float(ma.jaccard(mb))


def semantic_tfidf(a: str,b: str) -> float:
    if not a.strip() or not b.strip():
        return 0.0
    X=TfidfVectorizer(ngram_range=(1,2)).fit_transform([a,b])
    return float(cosine_similarity(X[0],X[1])[0,0])


def compare(answer: str, source: str) -> dict:
    return {
        "exact_span_words": longest_common_word_span(answer,source),
        "ngram_overlap": round(ngram_jaccard(answer,source),4),
        "minhash_similarity": round(minhash_similarity(answer,source),4),
        "fuzzy_ratio": round(ratio(answer,source)/100,4),
        "fuzzy_partial": round(partial_ratio(answer,source)/100,4),
        "semantic_similarity": round(semantic_tfidf(answer,source),4),
    }


def aggregate(answer: str, contexts: list[dict]) -> dict:
    results=[{"source_id":c["source_id"],"document_id":c["document_id"],**compare(answer,c["text"])} for c in contexts]
    if not results:
        return {"answer_words":len(words(answer)),"per_source":[],"max_exact_span_words":0,
                "max_ngram_overlap":0.0,"max_minhash_similarity":0.0,"max_fuzzy_partial":0.0,
                "max_semantic_similarity":0.0}
    return {
        "answer_words":len(words(answer)),
        "per_source":results,
        "max_exact_span_words":max(r["exact_span_words"] for r in results),
        "max_ngram_overlap":max(r["ngram_overlap"] for r in results),
        "max_minhash_similarity":max(r["minhash_similarity"] for r in results),
        "max_fuzzy_partial":max(r["fuzzy_partial"] for r in results),
        "max_semantic_similarity":max(r["semantic_similarity"] for r in results),
    }
