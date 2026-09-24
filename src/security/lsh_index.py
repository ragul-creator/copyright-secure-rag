from __future__ import annotations
import re
from src.config import settings
from src.services.db import query
from src.security.licenses import source_is_active


def _tokens(text: str):
    return re.findall(r"\b\w+\b",text.lower())


def _minhash(text: str):
    try:
        from datasketch import MinHash
    except ImportError:
        return None
    m=MinHash(num_perm=128)
    xs=_tokens(text)
    for i in range(max(0,len(xs)-4)):
        m.update(" ".join(xs[i:i+5]).encode())
    return m


def lsh_candidates(tenant_id: str, text: str, limit: int) -> list[dict]:
    if not settings.lsh_enabled:
        return []
    try:
        from datasketch import MinHashLSH
    except ImportError:
        return []
    target=_minhash(text)
    if target is None:
        return []
    rows=query("""SELECT c.chunk_id,c.document_id,c.source_id,c.text,s.name AS source_name,s.license_spdx,
                  s.status,s.rag_allowed,s.generation_allowed,s.expires_at,s.attribution_required,s.quote_word_limit
                  FROM chunks c JOIN sources s ON c.tenant_id=s.tenant_id AND c.source_id=s.source_id
                  WHERE c.tenant_id=? LIMIT 10000""",(tenant_id,))
    lsh=MinHashLSH(threshold=settings.minhash_threshold,num_perm=128)
    by_key={}
    for row in rows:
        ok_r,_=source_is_active(tenant_id,row,"retrieve")
        ok_g,_=source_is_active(tenant_id,row,"generate")
        if not (ok_r and ok_g):
            continue
        m=_minhash(row["text"])
        if m is None:
            continue
        key=row["chunk_id"]
        lsh.insert(key,m)
        by_key[key]=row
    return [by_key[k] for k in lsh.query(target)[:limit] if k in by_key]
