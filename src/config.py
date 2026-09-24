from __future__ import annotations
import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    data_dir: str = os.getenv("DATA_DIR", "./data")
    sqlite_db: str = os.getenv("SQLITE_DB", "./data/app.db")
    audit_log: str = os.getenv("AUDIT_LOG", "./data/audit.jsonl")
    llm_provider: str = os.getenv("LLM_PROVIDER", "extractive")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    opa_url: str = os.getenv("OPA_URL", "")
    fail_closed: bool = os.getenv("FAIL_CLOSED", "true").lower() == "true"
    max_exact_words: int = int(os.getenv("COPYRIGHT_MAX_EXACT_WORDS", "28"))
    ngram_threshold: float = float(os.getenv("COPYRIGHT_NGRAM_THRESHOLD", "0.55"))
    fuzzy_threshold: float = float(os.getenv("COPYRIGHT_FUZZY_THRESHOLD", "0.88"))
    semantic_threshold: float = float(os.getenv("COPYRIGHT_SEMANTIC_THRESHOLD", "0.96"))

settings = Settings()
