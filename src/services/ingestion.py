from __future__ import annotations
import hashlib, uuid
from datetime import datetime, timezone
from src.rag.chunking import chunk_text
from src.security.licenses import assert_ingest_allowed
from src.services.db import execute, audit

def ingest_document(source_id: str, document_id: str, text: str):
    src = assert_ingest_allowed(source_id)
    digest = hashlib.sha256(text.encode()).hexdigest()
    execute("INSERT OR REPLACE INTO documents(document_id,source_id,text,sha256,created_at) VALUES(?,?,?,?,?)",
            (document_id, source_id, text, digest, datetime.now(timezone.utc).isoformat()))
    execute("DELETE FROM chunks WHERE document_id=?", (document_id,))
    chunks = chunk_text(text)
    for i, chunk in enumerate(chunks):
        cid = f"{document_id}:{i}"
        execute("INSERT INTO chunks(chunk_id,document_id,source_id,ordinal,text) VALUES(?,?,?,?,?)",
                (cid, document_id, source_id, i, chunk))
    audit({"event":"document_ingested","source_id":source_id,"document_id":document_id,
           "sha256":digest,"chunks":len(chunks),"license":src["license_spdx"]})
    return {"document_id":document_id,"source_id":source_id,"sha256":digest,"chunks":len(chunks)}
