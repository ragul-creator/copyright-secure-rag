from __future__ import annotations
import os
from dataclasses import dataclass


def _bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "dev")
    data_dir: str = os.getenv("DATA_DIR", "./data")
    sqlite_db: str = os.getenv("SQLITE_DB", "./data/app.db")
    database_url: str = os.getenv("DATABASE_URL", "")
    audit_log: str = os.getenv("AUDIT_LOG", "./data/audit.jsonl")

    auth_mode: str = os.getenv("AUTH_MODE", "disabled")
    jwt_secret: str = os.getenv("JWT_SECRET", "change-me-in-production")
    jwt_issuer: str = os.getenv("JWT_ISSUER", "copyright-secure-rag")
    jwt_audience: str = os.getenv("JWT_AUDIENCE", "copyright-secure-rag-api")

    llm_provider: str = os.getenv("LLM_PROVIDER", "extractive")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    opa_url: str = os.getenv("OPA_URL", "")
    opa_rights_url: str = os.getenv("OPA_RIGHTS_URL", "")
    fail_closed: bool = _bool("FAIL_CLOSED", "true")
    require_compliance_evidence: bool = _bool("REQUIRE_COMPLIANCE_EVIDENCE", "false")

    vector_backend: str = os.getenv("VECTOR_BACKEND", "local")
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_collection: str = os.getenv("QDRANT_COLLECTION", "customer_support")
    embedding_backend: str = os.getenv("EMBEDDING_BACKEND", "hashing")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    embedding_dim: int = int(os.getenv("EMBEDDING_DIM", "384"))

    max_exact_words: int = int(os.getenv("COPYRIGHT_MAX_EXACT_WORDS", "28"))
    ngram_threshold: float = float(os.getenv("COPYRIGHT_NGRAM_THRESHOLD", "0.55"))
    fuzzy_threshold: float = float(os.getenv("COPYRIGHT_FUZZY_THRESHOLD", "0.88"))
    semantic_threshold: float = float(os.getenv("COPYRIGHT_SEMANTIC_THRESHOLD", "0.96"))
    minhash_threshold: float = float(os.getenv("COPYRIGHT_MINHASH_THRESHOLD", "0.70"))
    candidate_limit: int = int(os.getenv("COPYRIGHT_CANDIDATE_LIMIT", "8"))
    lsh_enabled: bool = _bool("COPYRIGHT_LSH_ENABLED", "true")

    nemo_guardrails_url: str = os.getenv("NEMO_GUARDRAILS_URL", "")
    guardrails_ai_url: str = os.getenv("GUARDRAILS_AI_URL", "")
    external_guardrails_fail_closed: bool = _bool("EXTERNAL_GUARDRAILS_FAIL_CLOSED", "false")

    audit_s3_bucket: str = os.getenv("AUDIT_S3_BUCKET", "")
    audit_s3_prefix: str = os.getenv("AUDIT_S3_PREFIX", "copyright-rag-audit/")
    audit_worm_required: bool = _bool("AUDIT_WORM_REQUIRED", "false")
    audit_retention_days: int = int(os.getenv("AUDIT_RETENTION_DAYS", "365"))

    otel_enabled: bool = _bool("OTEL_ENABLED", "false")
    otel_service_name: str = os.getenv("OTEL_SERVICE_NAME", "copyright-secure-rag")
    otel_exporter_otlp_endpoint: str = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317")


settings = Settings()
