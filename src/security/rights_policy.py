from __future__ import annotations
import httpx
from src.config import settings


def local_rights_allowed(source: dict, action: str) -> tuple[bool, str]:
    if source.get("status") != "approved":
        return False, f"STATUS_{str(source.get('status')).upper()}"
    if action in {"ingest", "retrieve"} and not source.get("rag_allowed"):
        return False, "RAG_NOT_ALLOWED"
    if action == "generate" and not source.get("generation_allowed"):
        return False, "GENERATION_NOT_ALLOWED"
    return True, "APPROVED"


def rights_allowed(tenant_id: str, source: dict, action: str) -> tuple[bool, str]:
    local_ok, local_reason = local_rights_allowed(source, action)
    if not local_ok:
        return False, local_reason
    if not settings.opa_rights_url:
        return True, local_reason
    payload = {"input": {"tenant_id": tenant_id, "action": action, "source": {
        "source_id": source.get("source_id"),
        "status": source.get("status"),
        "rag_allowed": bool(source.get("rag_allowed")),
        "generation_allowed": bool(source.get("generation_allowed")),
        "expires_at": source.get("expires_at"),
        "license_spdx": source.get("license_spdx"),
    }}}
    try:
        r = httpx.post(settings.opa_rights_url, json=payload, timeout=2.0)
        r.raise_for_status()
        result = r.json().get("result") or {}
        return bool(result.get("allow")), str(result.get("reason") or "OPA_DECISION")
    except Exception:
        if settings.fail_closed:
            return False, "OPA_RIGHTS_UNAVAILABLE_FAIL_CLOSED"
        return True, "OPA_RIGHTS_UNAVAILABLE_LOCAL_FALLBACK"
