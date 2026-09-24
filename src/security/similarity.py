from __future__ import annotations
import re
from rapidfuzz.fuzz import ratio, partial_ratio
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def words(text): return re.findall(r"\b\w+\b", text.lower())

def longest_common_word_span(a: str, b: str) -> int:
    A,B=words(a),words(b)
    if not A or not B: return 0
    prev=[0]*(len(B)+1); best=0
    for x in A:
        cur=[0]*(len(B)+1)
        for j,y in enumerate(B,1):
            if x==y:
                cur[j]=prev[j-1]+1
                if cur[j]>best: best=cur[j]
        prev=cur
    return best

def ngram_jaccard(a: str,b: str,n: int=5) -> float:
    A,B=words(a),words(b)
    def grams(xs): return {tuple(xs[i:i+n]) for i in range(max(0,len(xs)-n+1))}
    ga,gb=grams(A),grams(B)
    if not ga or not gb: return 0.0
    return len(ga&gb)/len(ga|gb)

def semantic_tfidf(a: str,b: str) -> float:
    if not a.strip() or not b.strip(): return 0.0
    X=TfidfVectorizer(ngram_range=(1,2)).fit_transform([a,b])
    return float(cosine_similarity(X[0],X[1])[0,0])

def compare(answer: str, source: str) -> dict:
    return {
        "exact_span_words": longest_common_word_span(answer,source),
        "ngram_overlap": round(ngram_jaccard(answer,source),4),
        "fuzzy_ratio": round(ratio(answer,source)/100,4),
        "fuzzy_partial": round(partial_ratio(answer,source)/100,4),
        "semantic_similarity": round(semantic_tfidf(answer,source),4),
    }

def aggregate(answer: str, contexts: list[dict]) -> dict:
    results=[]
    for c in contexts:
        results.append({"source_id":c["source_id"],"document_id":c["document_id"],**compare(answer,c["text"])})
    if not results:
        return {"answer_words":len(words(answer)),"per_source":[],"max_exact_span_words":0,"max_ngram_overlap":0.0,"max_fuzzy_partial":0.0,"max_semantic_similarity":0.0}
    return {
        "answer_words": len(words(answer)),
        "per_source":results,
        "max_exact_span_words":max(r["exact_span_words"] for r in results),
        "max_ngram_overlap":max(r["ngram_overlap"] for r in results),
        "max_fuzzy_partial":max(r["fuzzy_partial"] for r in results),
        "max_semantic_similarity":max(r["semantic_similarity"] for r in results),
    }
