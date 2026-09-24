from __future__ import annotations
import hashlib
from datetime import datetime, timezone
from src.rag.chunking import chunk_text
from src.rag.vector_store import get_vector_store
from src.security.licenses import assert_ingest_allowed
from src.services.db import execute, audit


def ingest_document(tenant_id: str, source_id: str, document_id: str, text: str):
    src = assert_ingest_allowed(tenant_id, source_id)
    digest = hashlib.sha256(text.encode()).hexdigest()
    execute("""INSERT INTO documents(tenant_id,document_id,source_id,text,sha256,created_at) VALUES(?,?,?,?,?,?)
             ON CONFLICT(tenant_id,document_id) DO UPDATE SET source_id=excluded.source_id,text=excluded.text,
             sha256=excluded.sha256,created_at=excluded.created_at""",
            (tenant_id, document_id, source_id, text, digest, datetime.now(timezone.utc).isoformat()))
    execute("DELETE FROM chunks WHERE tenant_id=? AND document_id=?", (tenant_id, document_id))
    chunks = chunk_text(text)
    records = []
    for i, chunk in enumerate(chunks):
        cid = f"{document_id}:{i}"
        execute("INSERT INTO chunks(tenant_id,chunk_id,document_id,source_id,ordinal,text) VALUES(?,?,?,?,?,?)",
                (tenant_id, cid, document_id, source_id, i, chunk))
        records.append({"chunk_id":cid,"document_id":document_id,"source_id":source_id,"ordinal":i,"text":chunk})
    store = get_vector_store()
    if store:
        store.upsert(tenant_id, records)
    audit({"event":"document_ingested","source_id":source_id,"document_id":document_id,
           "sha256":digest,"chunks":len(chunks),"license":src["license_spdx"]}, tenant_id)
    return {"document_id":document_id,"source_id":source_id,"sha256":digest,"chunks":len(chunks)}
