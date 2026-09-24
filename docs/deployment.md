# Deployment guide

This repository supports local development and a hardened container stack. The defaults are development-friendly and should not be exposed directly to the internet.

## Minimum production settings

1. Set `APP_ENV=prod`.
2. Set `AUTH_MODE=jwt` and replace `JWT_SECRET` with a long random value, or replace the shared-secret verifier with OIDC/JWKS.
3. Use strong PostgreSQL credentials and keep PostgreSQL, Qdrant, OPA, and Grafana on private networks.
4. Set explicit `CORS_ORIGINS` for the approved support frontend.
5. Set `REQUIRE_COMPLIANCE_EVIDENCE=true` when every source must have approved compliance evidence before ingestion.
6. Keep `FAIL_CLOSED=true` so rights/policy outages deny release rather than silently bypass controls.
7. Configure durable backups for PostgreSQL and Qdrant.
8. Configure `AUDIT_S3_BUCKET` plus object-lock retention when immutable audit retention is required.
9. Terminate TLS at an ingress/load balancer and add platform rate limiting/WAF controls.

## Start the stack

```bash
cp .env.example .env
# Edit .env before production use.
docker compose up --build -d
docker compose ps
curl -fsS http://localhost:8000/readyz
```

The API container runs as a non-root user. The UI waits for the API health check before starting.

## Knowledge ingestion

Register a source with rights metadata first. Support documents can then be submitted as raw text with `POST /ingest` or uploaded as TXT, Markdown, HTML, or PDF with `POST /ingest/file`.

The ingestion path is:

`rights check -> parse -> normalize -> SHA-256 provenance -> chunk -> remove prior document vectors -> embed -> vector upsert -> audit event`

Re-ingesting the same document ID replaces its relational chunks and deletes old vectors before the new upsert, preventing stale content from remaining searchable.

## Retrieval and answer release

Retrieval is tenant-scoped and applies `RETRIEVAL_MIN_SCORE` before context is sent to the generator. Rights are checked again at retrieval time so revocation takes effect without re-embedding.

Generated answers pass through similarity scanning and the policy engine before release. If a draft is too close to source text, the system attempts a rewrite and blocks it if the rewritten answer still exceeds policy.

## Operational checks

- `GET /health`: process liveness.
- `GET /readyz`: database and vector-backend readiness.
- `GET /metrics`: Prometheus metrics.
- `GET /audit/verify`: verifies the tenant audit hash chain.
- `GET /admin/overview`: knowledge-base/compliance summary.

Application upload limits are still enforced even when an ingress also enforces request-size limits.
