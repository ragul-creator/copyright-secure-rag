from __future__ import annotations
import httpx
from src.config import settings


def local_decision(signals: dict, contexts: list[dict]):
    if not contexts:
        return {"decision":"ESCALATE","reason":"NO_APPROVED_CONTEXT"}
    quote_limit=min(int(c.get("quote_word_limit") or settings.max_exact_words) for c in contexts)
    if signals["max_exact_span_words"] > quote_limit:
        return {"decision":"REWRITE","reason":"EXACT_SPAN_LIMIT","limit":quote_limit}
    if signals["max_ngram_overlap"] >= settings.ngram_threshold:
        return {"decision":"REWRITE","reason":"NGRAM_OVERLAP"}
    if signals.get("max_minhash_similarity",0.0) >= settings.minhash_threshold and signals.get("answer_words",0) > quote_limit:
        return {"decision":"REWRITE","reason":"MINHASH_NEAR_COPY"}
    if signals.get("answer_words",0) > quote_limit and signals["max_fuzzy_partial"] >= settings.fuzzy_threshold and signals["max_exact_span_words"] >= max(10,quote_limit//2):
        return {"decision":"REWRITE","reason":"FUZZY_NEAR_COPY"}
    if signals.get("answer_words",0) > quote_limit and signals["max_semantic_similarity"] >= settings.semantic_threshold and signals["max_exact_span_words"] >= max(12,quote_limit//2):
        return {"decision":"REWRITE","reason":"HIGH_SIMILARITY_WITH_TEXTUAL_OVERLAP"}
    if any(c.get("attribution_required") for c in contexts):
        return {"decision":"ALLOW_WITH_ATTRIBUTION","reason":"ATTRIBUTION_REQUIRED"}
    return {"decision":"ALLOW","reason":"WITHIN_POLICY"}


def decide(tenant_id: str, signals: dict, contexts: list[dict]):
    local=local_decision(signals,contexts)
    if not settings.opa_url:
        return local
    payload={"input":{"tenant_id":tenant_id,"signals":signals,"contexts":[{
        "source_id":c["source_id"],"quote_word_limit":c.get("quote_word_limit",settings.max_exact_words),
        "attribution_required":bool(c.get("attribution_required")),"license_spdx":c.get("license_spdx")
    } for c in contexts]}}
    try:
        r=httpx.post(settings.opa_url,json=payload,timeout=2.0)
        r.raise_for_status()
        result=r.json().get("result")
        return result or (local if not settings.fail_closed else {"decision":"BLOCK","reason":"OPA_EMPTY_RESULT"})
    except Exception:
        return local if not settings.fail_closed else {"decision":"BLOCK","reason":"OPA_UNAVAILABLE_FAIL_CLOSED"}
