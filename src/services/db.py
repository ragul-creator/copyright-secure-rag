from __future__ import annotations
import json, os, sqlite3, threading
from datetime import datetime, timezone
from pathlib import Path
from src.config import settings

_lock = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
 source_id TEXT PRIMARY KEY, name TEXT NOT NULL, origin TEXT NOT NULL,
 rights_holder TEXT NOT NULL, license_spdx TEXT NOT NULL,
 rag_allowed INTEGER NOT NULL, generation_allowed INTEGER NOT NULL,
 attribution_required INTEGER NOT NULL, quote_word_limit INTEGER NOT NULL,
 expires_at TEXT, status TEXT NOT NULL, sha256 TEXT, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS documents (
 document_id TEXT PRIMARY KEY, source_id TEXT NOT NULL, text TEXT NOT NULL,
 sha256 TEXT NOT NULL, created_at TEXT NOT NULL,
 FOREIGN KEY(source_id) REFERENCES sources(source_id)
);
CREATE TABLE IF NOT EXISTS chunks (
 chunk_id TEXT PRIMARY KEY, document_id TEXT NOT NULL, source_id TEXT NOT NULL,
 ordinal INTEGER NOT NULL, text TEXT NOT NULL,
 FOREIGN KEY(document_id) REFERENCES documents(document_id)
);
"""

def connect():
    Path(settings.sqlite_db).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.sqlite_db, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn

def execute(sql, args=()):
    with _lock, connect() as conn:
        cur = conn.execute(sql, args)
        conn.commit()
        return cur

def query(sql, args=()):
    with _lock, connect() as conn:
        return [dict(r) for r in conn.execute(sql, args).fetchall()]

def audit(event: dict):
    Path(settings.audit_log).parent.mkdir(parents=True, exist_ok=True)
    event = {"ts": datetime.now(timezone.utc).isoformat(), **event}
    with _lock:
        with open(settings.audit_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
