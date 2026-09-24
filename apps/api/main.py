from __future__ import annotations
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from src.models import SourceRegistration, IngestRequest, ChatRequest, ChatResponse
from src.security.licenses import register_source, LicenseError
from src.services.ingestion import ingest_document
from src.services.chat import chat
from src.services.db import query

app=FastAPI(title="Copyright-Secure Customer Support RAG",version="0.1.0")
CHAT=Counter("rag_chat_requests_total","Chat requests",["decision"])
INGEST=Counter("rag_ingest_total","Ingestion attempts",["status"])

@app.get("/health")
def health(): return {"status":"ok"}

@app.post("/sources")
def create_source(src: SourceRegistration):
    register_source(src); return {"ok":True,"source_id":src.source_id}

@app.get("/sources")
def list_sources():
    return query("SELECT source_id,name,rights_holder,license_spdx,rag_allowed,generation_allowed,attribution_required,quote_word_limit,expires_at,status FROM sources ORDER BY source_id")

@app.post("/ingest")
def ingest(req: IngestRequest):
    try:
        out=ingest_document(req.source_id,req.document_id,req.text); INGEST.labels("allowed").inc(); return out
    except LicenseError as e:
        INGEST.labels("denied").inc(); raise HTTPException(403,str(e))

@app.post("/chat",response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    out=chat(req.question,req.top_k); CHAT.labels(out["decision"]).inc(); return out

@app.get("/audit/recent")
def audit_recent(limit:int=100):
    import json, os
    from src.config import settings
    if not os.path.exists(settings.audit_log): return []
    with open(settings.audit_log,encoding="utf-8") as f: lines=f.readlines()[-max(1,min(limit,1000)):]
    return [json.loads(x) for x in lines]

@app.get("/metrics")
def metrics():
    return PlainTextResponse(generate_latest().decode(),media_type=CONTENT_TYPE_LATEST)
