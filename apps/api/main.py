from __future__ import annotations
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

from src.models import SourceRegistration, SourceStatusUpdate, IngestRequest, ChatRequest, ChatResponse
from src.observability import configure_observability
from src.security.auth import Principal, get_principal, require_roles
from src.security.licenses import register_source, LicenseError
from src.services.ingestion import ingest_document
from src.services.chat import chat
from src.services.db import query, execute, audit, audit_recent, verify_audit_chain

app=FastAPI(title="Copyright-Secure Customer Support RAG",version="0.2.0")
configure_observability(app)
CHAT=Counter("rag_chat_requests_total","Chat requests",["decision"])
INGEST=Counter("rag_ingest_total","Ingestion attempts",["status"])


@app.get("/health")
def health():
    return {"status":"ok"}


@app.get("/whoami")
def whoami(principal: Principal = Depends(get_principal)):
    return {"subject":principal.subject,"tenant_id":principal.tenant_id,"roles":sorted(principal.roles)}


@app.post("/sources")
def create_source(src: SourceRegistration, principal: Principal = Depends(require_roles("admin","knowledge_manager"))):
    register_source(principal.tenant_id, src)
    return {"ok":True,"source_id":src.source_id,"tenant_id":principal.tenant_id}


@app.get("/sources")
def list_sources(principal: Principal = Depends(require_roles("admin","knowledge_manager","support","viewer"))):
    return query("""SELECT source_id,name,rights_holder,license_spdx,rag_allowed,generation_allowed,
                  attribution_required,quote_word_limit,expires_at,status FROM sources
                  WHERE tenant_id=? ORDER BY source_id""", (principal.tenant_id,))


@app.patch("/sources/{source_id}/status")
def set_source_status(source_id: str, update: SourceStatusUpdate, principal: Principal = Depends(require_roles("admin","knowledge_manager"))):
    rows=query("SELECT source_id FROM sources WHERE tenant_id=? AND source_id=?", (principal.tenant_id,source_id))
    if not rows:
        raise HTTPException(404,"Source not found")
    execute("UPDATE sources SET status=? WHERE tenant_id=? AND source_id=?", (update.status,principal.tenant_id,source_id))
    audit({"event":"source_status_changed","source_id":source_id,"status":update.status,"actor":principal.subject}, principal.tenant_id)
    return {"ok":True,"source_id":source_id,"status":update.status}


@app.post("/ingest")
def ingest(req: IngestRequest, principal: Principal = Depends(require_roles("admin","knowledge_manager"))):
    try:
        out=ingest_document(principal.tenant_id,req.source_id,req.document_id,req.text)
        INGEST.labels("allowed").inc()
        return out
    except LicenseError as e:
        INGEST.labels("denied").inc()
        raise HTTPException(403,str(e))


@app.post("/chat",response_model=ChatResponse)
def chat_endpoint(req: ChatRequest, principal: Principal = Depends(require_roles("admin","knowledge_manager","support","viewer"))):
    out=chat(principal.tenant_id,req.question,req.top_k)
    CHAT.labels(out["decision"]).inc()
    return out


@app.get("/audit/recent")
def get_audit_recent(limit:int=100, principal: Principal = Depends(require_roles("admin","knowledge_manager"))):
    return audit_recent(principal.tenant_id,max(1,min(limit,1000)))


@app.get("/audit/verify")
def verify_audit(principal: Principal = Depends(require_roles("admin"))):
    return {"tenant_id":principal.tenant_id,"valid":verify_audit_chain(principal.tenant_id)}


@app.get("/admin/overview")
def overview(principal: Principal = Depends(require_roles("admin","knowledge_manager"))):
    tenant=principal.tenant_id
    def count(sql):
        return query(sql,(tenant,))[0]["n"]
    return {
        "tenant_id":tenant,
        "sources":count("SELECT COUNT(*) AS n FROM sources WHERE tenant_id=?"),
        "approved_sources":count("SELECT COUNT(*) AS n FROM sources WHERE tenant_id=? AND status='approved'"),
        "documents":count("SELECT COUNT(*) AS n FROM documents WHERE tenant_id=?"),
        "chunks":count("SELECT COUNT(*) AS n FROM chunks WHERE tenant_id=?"),
        "audit_chain_valid":verify_audit_chain(tenant),
    }


@app.get("/metrics")
def metrics():
    return PlainTextResponse(generate_latest().decode(),media_type=CONTENT_TYPE_LATEST)
