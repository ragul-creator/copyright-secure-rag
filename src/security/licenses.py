from __future__ import annotations
from datetime import datetime, timezone
from src.models import SourceRegistration
from src.services.db import execute, query, audit
from src.security.rights_policy import rights_allowed


class LicenseError(RuntimeError):
    pass


def register_source(tenant_id: str, src: SourceRegistration):
    execute("""
    INSERT INTO sources(tenant_id,source_id,name,origin,rights_holder,license_spdx,rag_allowed,generation_allowed,
      attribution_required,quote_word_limit,expires_at,status,created_at)
    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
    ON CONFLICT(tenant_id,source_id) DO UPDATE SET name=excluded.name, origin=excluded.origin,
      rights_holder=excluded.rights_holder, license_spdx=excluded.license_spdx,
      rag_allowed=excluded.rag_allowed, generation_allowed=excluded.generation_allowed,
      attribution_required=excluded.attribution_required, quote_word_limit=excluded.quote_word_limit,
      expires_at=excluded.expires_at, status=excluded.status
    """, (tenant_id, src.source_id, src.name, src.origin, src.rights_holder, src.license_spdx,
            int(src.rag_allowed), int(src.generation_allowed), int(src.attribution_required),
            src.quote_word_limit, src.expires_at, src.status, datetime.now(timezone.utc).isoformat()))
    audit({"event":"source_registered", "source_id":src.source_id, "status":src.status,
           "license_spdx":src.license_spdx}, tenant_id)


def get_source(tenant_id: str, source_id: str):
    rows = query("SELECT * FROM sources WHERE tenant_id=? AND source_id=?", (tenant_id, source_id))
    return rows[0] if rows else None


def source_is_active(tenant_id: str, src: dict, action: str = "retrieve") -> tuple[bool, str]:
    if not src:
        return False, "UNKNOWN_SOURCE"
    if src.get("expires_at"):
        try:
            exp = datetime.fromisoformat(str(src["expires_at"]).replace("Z", "+00:00"))
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            if exp <= datetime.now(timezone.utc):
                return False, "LICENSE_EXPIRED"
        except ValueError:
            return False, "INVALID_EXPIRY"
    return rights_allowed(tenant_id, src, action)


def assert_ingest_allowed(tenant_id: str, source_id: str):
    src = get_source(tenant_id, source_id)
    ok, reason = source_is_active(tenant_id, src, "ingest")
    if not ok:
        audit({"event":"ingest_denied", "source_id":source_id, "reason":reason}, tenant_id)
        raise LicenseError(reason)
    return src
