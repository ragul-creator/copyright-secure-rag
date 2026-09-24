from __future__ import annotations
import hashlib
import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from src.config import settings

_lock = threading.Lock()
_audit_lock = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
 tenant_id TEXT NOT NULL,
 source_id TEXT NOT NULL,
 name TEXT NOT NULL,
 origin TEXT NOT NULL,
 rights_holder TEXT NOT NULL,
 license_spdx TEXT NOT NULL,
 rag_allowed INTEGER NOT NULL,
 generation_allowed INTEGER NOT NULL,
 attribution_required INTEGER NOT NULL,
 quote_word_limit INTEGER NOT NULL,
 expires_at TEXT,
 status TEXT NOT NULL,
 sha256 TEXT,
 created_at TEXT NOT NULL,
 PRIMARY KEY (tenant_id, source_id)
);
CREATE TABLE IF NOT EXISTS documents (
 tenant_id TEXT NOT NULL,
 document_id TEXT NOT NULL,
 source_id TEXT NOT NULL,
 text TEXT NOT NULL,
 sha256 TEXT NOT NULL,
 created_at TEXT NOT NULL,
 PRIMARY KEY (tenant_id, document_id),
 FOREIGN KEY(tenant_id, source_id) REFERENCES sources(tenant_id, source_id)
);
CREATE TABLE IF NOT EXISTS chunks (
 tenant_id TEXT NOT NULL,
 chunk_id TEXT NOT NULL,
 document_id TEXT NOT NULL,
 source_id TEXT NOT NULL,
 ordinal INTEGER NOT NULL,
 text TEXT NOT NULL,
 PRIMARY KEY (tenant_id, chunk_id),
 FOREIGN KEY(tenant_id, document_id) REFERENCES documents(tenant_id, document_id)
);
CREATE TABLE IF NOT EXISTS compliance_evidence (
 id INTEGER PRIMARY KEY,
 tenant_id TEXT NOT NULL,
 source_id TEXT NOT NULL,
 tool TEXT NOT NULL,
 artifact_uri TEXT NOT NULL,
 artifact_sha256 TEXT NOT NULL,
 verdict TEXT NOT NULL,
 details_json TEXT NOT NULL,
 created_at TEXT NOT NULL,
 FOREIGN KEY(tenant_id, source_id) REFERENCES sources(tenant_id, source_id)
);
CREATE TABLE IF NOT EXISTS audit_events (
 id INTEGER PRIMARY KEY,
 tenant_id TEXT NOT NULL,
 ts TEXT NOT NULL,
 event_json TEXT NOT NULL,
 prev_hash TEXT NOT NULL,
 event_hash TEXT NOT NULL
);
"""


def _postgres() -> bool:
    return bool(settings.database_url and settings.database_url.startswith(("postgresql://", "postgres://")))


def _sql(sql: str) -> str:
    return sql.replace("?", "%s") if _postgres() else sql


@contextmanager
def connect():
    if _postgres():
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise RuntimeError("DATABASE_URL requires psycopg from requirements-infra.txt") from exc
        conn = psycopg.connect(settings.database_url, row_factory=dict_row)
        try:
            _init_postgres(conn)
            yield conn
            conn.commit()
        finally:
            conn.close()
    else:
        Path(settings.sqlite_db).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(settings.sqlite_db, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.executescript(SCHEMA)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()


def _init_postgres(conn) -> None:
    statements = [s.strip() for s in SCHEMA.split(";") if s.strip()]
    with conn.cursor() as cur:
        for statement in statements:
            if statement.startswith("CREATE TABLE IF NOT EXISTS audit_events") or statement.startswith("CREATE TABLE IF NOT EXISTS compliance_evidence"):
                statement = statement.replace("id INTEGER PRIMARY KEY", "id BIGSERIAL PRIMARY KEY")
            cur.execute(statement)


def execute(sql: str, args=()):
    with _lock, connect() as conn:
        return conn.execute(_sql(sql), args)


def query(sql: str, args=()):
    with _lock, connect() as conn:
        rows = conn.execute(_sql(sql), args).fetchall()
        return [dict(r) for r in rows]


def audit(event: dict, tenant_id: str = "system") -> dict:
    from src.security.audit_sink import write_worm_event
    Path(settings.audit_log).parent.mkdir(parents=True, exist_ok=True)
    with _audit_lock:
        with connect() as conn:
            if _postgres():
                conn.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (tenant_id,))
            else:
                conn.execute("BEGIN IMMEDIATE")
            rows=conn.execute(_sql("SELECT event_hash FROM audit_events WHERE tenant_id=? ORDER BY id DESC LIMIT 1"),(tenant_id,)).fetchall()
            prev_hash=dict(rows[0])["event_hash"] if rows else "0"*64
            ts=datetime.now(timezone.utc).isoformat()
            payload={"ts":ts,"tenant_id":tenant_id,**event,"prev_hash":prev_hash}
            canonical=json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(",",":"))
            event_hash=hashlib.sha256((prev_hash+canonical).encode()).hexdigest()
            payload["event_hash"]=event_hash
            conn.execute(_sql("INSERT INTO audit_events(tenant_id,ts,event_json,prev_hash,event_hash) VALUES(?,?,?,?,?)"),
                         (tenant_id,ts,json.dumps(payload,ensure_ascii=False),prev_hash,event_hash))
        with open(settings.audit_log,"a",encoding="utf-8") as f:
            f.write(json.dumps(payload,ensure_ascii=False)+"\n")
        write_worm_event(payload)
        return payload


def audit_recent(tenant_id: str, limit: int = 100) -> list[dict]:
    rows = query("SELECT event_json FROM audit_events WHERE tenant_id=? ORDER BY id DESC LIMIT ?", (tenant_id, limit))
    return [json.loads(r["event_json"]) for r in rows]


def verify_audit_chain(tenant_id: str) -> bool:
    rows = query("SELECT event_json,prev_hash,event_hash FROM audit_events WHERE tenant_id=? ORDER BY id ASC", (tenant_id,))
    expected_prev = "0" * 64
    for row in rows:
        payload = json.loads(row["event_json"])
        stored_hash = payload.pop("event_hash", None)
        canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        expected_hash = hashlib.sha256((expected_prev + canonical).encode()).hexdigest()
        if row["prev_hash"] != expected_prev or row["event_hash"] != expected_hash or stored_hash != expected_hash:
            return False
        expected_prev = expected_hash
    return True
