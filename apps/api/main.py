from __future__ import annotations

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest

from src.config import settings
from src.models import (
    ChatRequest,
    ChatResponse,
    ComplianceEvidenceCreate,
    IngestRequest,
    SourceRegistration,
    SourceStatusUpdate,
)
from src.observability import configure_observability
from src.rag.document_loader import DocumentLoadError
from src.rag.vector_store import get_vector_store
from src.security.auth import Principal, get_principal, require_roles
from src.security.licenses import LicenseError, add_compliance_evidence, register_source
from src.services.chat import chat
from src.services.db import audit, audit_recent, execute, query, verify_audit_chain
from src.services.ingestion import ingest_document, ingest_document_bytes


app = FastAPI(
    title="Copyright-Secure Customer Support RAG",
    version="0.4.0",
    docs_url="/docs" if settings.app_env != "prod" else None,
    redoc_url="/redoc" if settings.app_env != "prod" else None,
)
configure_observability(app)

origins = [x.strip() for x in settings.cors_origins.split(",") if x.strip()]
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["Authorization", "Content-Type"],
    )

CHAT = Counter("rag_chat_requests_total", "Chat requests", ["decision"])
INGEST = Counter("rag_ingest_total", "Ingestion attempts", ["status", "kind"])


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/readyz")
def readiness():
    try:
        query("SELECT 1 AS ok")
        store = get_vector_store()
        if store:
            store.healthcheck()
        return {
            "status": "ready",
            "database": "ok",
            "vector_backend": settings.vector_backend,
        }
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Dependency not ready: {type(exc).__name__}") from exc


@app.get("/whoami")
def whoami(principal: Principal = Depends(get_principal)):
    return {
        "subject": principal.subject,
        "tenant_id": principal.tenant_id,
        "roles": sorted(principal.roles),
    }


@app.post("/sources")
def create_source(
    src: SourceRegistration,
    principal: Principal = Depends(require_roles("admin", "knowledge_manager")),
):
    register_source(principal.tenant_id, src)
    return {"ok": True, "source_id": src.source_id, "tenant_id": principal.tenant_id}


@app.get("/sources")
def list_sources(
    principal: Principal = Depends(require_roles("admin", "knowledge_manager", "support", "viewer")),
):
    return query(
        """SELECT source_id,name,rights_holder,license_spdx,rag_allowed,generation_allowed,
                  attribution_required,quote_word_limit,expires_at,status FROM sources
                  WHERE tenant_id=? ORDER BY source_id""",
        (principal.tenant_id,),
    )


@app.patch("/sources/{source_id}/status")
def set_source_status(
    source_id: str,
    update: SourceStatusUpdate,
    principal: Principal = Depends(require_roles("admin", "knowledge_manager")),
):
    rows = query(
        "SELECT source_id FROM sources WHERE tenant_id=? AND source_id=?",
        (principal.tenant_id, source_id),
    )
    if not rows:
        raise HTTPException(404, "Source not found")
    execute(
        "UPDATE sources SET status=? WHERE tenant_id=? AND source_id=?",
        (update.status, principal.tenant_id, source_id),
    )
    audit(
        {
            "event": "source_status_changed",
            "source_id": source_id,
            "status": update.status,
            "actor": principal.subject,
        },
        principal.tenant_id,
    )
    return {"ok": True, "source_id": source_id, "status": update.status}


@app.post("/sources/{source_id}/evidence")
def add_evidence(
    source_id: str,
    evidence: ComplianceEvidenceCreate,
    principal: Principal = Depends(require_roles("admin", "knowledge_manager")),
):
    try:
        add_compliance_evidence(
            principal.tenant_id,
            source_id,
            evidence.tool,
            evidence.artifact_uri,
            evidence.artifact_sha256,
            evidence.verdict,
            evidence.details,
        )
    except LicenseError as exc:
        raise HTTPException(404, str(exc)) from exc
    return {"ok": True, "source_id": source_id, "verdict": evidence.verdict}


@app.get("/sources/{source_id}/evidence")
def list_evidence(
    source_id: str,
    principal: Principal = Depends(require_roles("admin", "knowledge_manager")),
):
    return query(
        """SELECT tool,artifact_uri,artifact_sha256,verdict,details_json,created_at
                  FROM compliance_evidence WHERE tenant_id=? AND source_id=? ORDER BY id DESC""",
        (principal.tenant_id, source_id),
    )


@app.post("/ingest")
def ingest(
    req: IngestRequest,
    principal: Principal = Depends(require_roles("admin", "knowledge_manager")),
):
    try:
        out = ingest_document(
            principal.tenant_id,
            req.source_id,
            req.document_id,
            req.text,
        )
        INGEST.labels("allowed", "text").inc()
        return out
    except LicenseError as exc:
        INGEST.labels("denied", "text").inc()
        raise HTTPException(403, str(exc)) from exc
    except ValueError as exc:
        INGEST.labels("invalid", "text").inc()
        raise HTTPException(400, str(exc)) from exc


@app.post("/ingest/file")
async def ingest_file(
    source_id: str = Form(...),
    document_id: str = Form(...),
    file: UploadFile = File(...),
    principal: Principal = Depends(require_roles("admin", "knowledge_manager")),
):
    try:
        data = await file.read(settings.max_upload_bytes + 1)
        out = ingest_document_bytes(
            principal.tenant_id,
            source_id,
            document_id,
            file.filename or document_id,
            data,
        )
        INGEST.labels("allowed", "file").inc()
        return out
    except LicenseError as exc:
        INGEST.labels("denied", "file").inc()
        raise HTTPException(403, str(exc)) from exc
    except (DocumentLoadError, ValueError) as exc:
        INGEST.labels("invalid", "file").inc()
        raise HTTPException(400, str(exc)) from exc
    finally:
        await file.close()


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(
    req: ChatRequest,
    principal: Principal = Depends(require_roles("admin", "knowledge_manager", "support", "viewer")),
):
    out = chat(principal.tenant_id, req.question, req.top_k)
    CHAT.labels(out["decision"]).inc()
    return out


@app.get("/audit/recent")
def get_audit_recent(
    limit: int = 100,
    principal: Principal = Depends(require_roles("admin", "knowledge_manager")),
):
    return audit_recent(principal.tenant_id, max(1, min(limit, 1000)))


@app.get("/audit/verify")
def verify_audit(principal: Principal = Depends(require_roles("admin"))):
    return {
        "tenant_id": principal.tenant_id,
        "valid": verify_audit_chain(principal.tenant_id),
    }


@app.get("/admin/overview")
def overview(
    principal: Principal = Depends(require_roles("admin", "knowledge_manager")),
):
    tenant = principal.tenant_id

    def count(sql: str):
        return query(sql, (tenant,))[0]["n"]

    return {
        "tenant_id": tenant,
        "sources": count("SELECT COUNT(*) AS n FROM sources WHERE tenant_id=?"),
        "approved_sources": count(
            "SELECT COUNT(*) AS n FROM sources WHERE tenant_id=? AND status='approved'"
        ),
        "documents": count("SELECT COUNT(*) AS n FROM documents WHERE tenant_id=?"),
        "chunks": count("SELECT COUNT(*) AS n FROM chunks WHERE tenant_id=?"),
        "approved_evidence": count(
            "SELECT COUNT(*) AS n FROM compliance_evidence WHERE tenant_id=? AND verdict='approved'"
        ),
        "audit_chain_valid": verify_audit_chain(tenant),
    }


@app.get("/metrics")
def metrics():
    return PlainTextResponse(
        generate_latest().decode(),
        media_type=CONTENT_TYPE_LATEST,
    )
