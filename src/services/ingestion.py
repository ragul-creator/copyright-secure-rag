from __future__ import annotations
import hashlib
from datetime import datetime, timezone

from src.rag.chunking import chunk_text
from src.rag.document_loader import load_document_bytes
from src.rag.vector_store import get_vector_store
from src.security.licenses import assert_ingest_allowed
from src.services.db import execute, audit


def ingest_document(tenant_id: str, source_id: str, document_id: str, text: str):
    src = assert_ingest_allowed(tenant_id, source_id)
    normalized = text.strip()
    if not normalized:
        raise ValueError("Document contains no extractable text")

    digest = hashlib.sha256(normalized.encode()).hexdigest()
    store = get_vector_store()
    if store:
        # Prevent stale vectors when a replacement document produces fewer chunks.
        store.delete_document(tenant_id, document_id)

    execute(
        """INSERT INTO documents(tenant_id,document_id,source_id,text,sha256,created_at) VALUES(?,?,?,?,?,?)
             ON CONFLICT(tenant_id,document_id) DO UPDATE SET source_id=excluded.source_id,text=excluded.text,
             sha256=excluded.sha256,created_at=excluded.created_at""",
        (tenant_id, document_id, source_id, normalized, digest, datetime.now(timezone.utc).isoformat()),
    )
    execute("DELETE FROM chunks WHERE tenant_id=? AND document_id=?", (tenant_id, document_id))

    chunks = chunk_text(normalized)
    records = []
    for i, chunk in enumerate(chunks):
        cid = f"{document_id}:{i}"
        execute(
            "INSERT INTO chunks(tenant_id,chunk_id,document_id,source_id,ordinal,text) VALUES(?,?,?,?,?,?)",
            (tenant_id, cid, document_id, source_id, i, chunk),
        )
        records.append({
            "chunk_id": cid,
            "document_id": document_id,
            "source_id": source_id,
            "ordinal": i,
            "text": chunk,
        })
    if store:
        store.upsert(tenant_id, records)

    audit(
        {
            "event": "document_ingested",
            "source_id": source_id,
            "document_id": document_id,
            "sha256": digest,
            "chunks": len(chunks),
            "license": src["license_spdx"],
        },
        tenant_id,
    )
    return {
        "document_id": document_id,
        "source_id": source_id,
        "sha256": digest,
        "chunks": len(chunks),
    }


def ingest_document_bytes(
    tenant_id: str,
    source_id: str,
    document_id: str,
    filename: str,
    data: bytes,
):
    text = load_document_bytes(filename, data)
    result = ingest_document(tenant_id, source_id, document_id, text)
    return {**result, "filename": filename, "bytes": len(data)}
