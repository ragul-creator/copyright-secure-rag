# Copyright-Secure Customer Support RAG

Production-oriented customer-support RAG with copyright/data-rights enforcement in ingestion, retrieval, generation, output checking, policy decisions, and auditing.

## Runtime controls

- Tenant-scoped customer support RAG API and Streamlit operations UI
- JWT authentication + RBAC (`admin`, `knowledge_manager`, `support`, `viewer`)
- Central rights/license registry; license data is not duplicated on every chunk
- Ingestion denial for unknown, revoked, expired, or RAG-disallowed sources
- Runtime rights re-check so revocation takes effect without re-embedding
- PostgreSQL or zero-dependency SQLite metadata backend
- Qdrant vector retrieval with tenant filters, or local TF-IDF fallback
- SHA-256 provenance for ingested documents
- Exact-span, 5-gram, RapidFuzz, MinHash/shingle, and semantic-similarity signals
- Independent corpus-candidate scan in addition to originally retrieved chunks
- ALLOW / ALLOW_WITH_ATTRIBUTION / REWRITE / BLOCK / ESCALATE actions
- OPA rights and output policies with fail-closed mode
- Optional NeMo Guardrails / Guardrails AI validation-service adapters
- Tamper-evident SHA-256 hash-chained audit events
- Prometheus metrics + Grafana + OpenTelemetry collector

## Compliance/evaluation toolchain

- ScanCode Toolkit ingestion scanning hook
- OSS Review Toolkit (ORT) hook
- SPDX license identifiers
- CycloneDX data BOM exporter
- Sigstore/Cosign manifest signing hook
- Promptfoo regression configuration
- Giskard and Ragas integration points
- GitHub Actions unit/security tests and OPA policy validation

## Local development

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
export PYTHONPATH=.
python scripts/bootstrap_demo.py
uvicorn apps.api.main:app --reload
```

Run the UI in another terminal:

```bash
streamlit run apps/ui/app.py
```

Local development defaults to SQLite, local TF-IDF retrieval, disabled authentication, and no external OPA requirement.

## Full infrastructure stack

```bash
docker compose up --build
```

This enables PostgreSQL, Qdrant, OPA, OpenTelemetry Collector, Prometheus and Grafana. The Compose file intentionally leaves `AUTH_MODE=disabled` for local stack usability; change it to `jwt` and provide a strong secret/identity integration before exposing the service.

Endpoints: API `8000`, UI `8501`, OPA `8181`, Qdrant `6333`, PostgreSQL `5432`, OTLP `4317/4318`, Prometheus `9090`, Grafana `3000`.

## JWT development token

```bash
export AUTH_MODE=jwt
export JWT_SECRET='replace-with-a-long-random-secret'
python scripts/issue_dev_token.py --tenant acme --roles admin,knowledge_manager,support
```

Tenant ID is taken from the authenticated principal rather than request JSON. See `docs/auth-and-tenancy.md`.

## Security flow

`identity -> tenant -> source rights -> ingestion/provenance -> tenant-filtered retrieval -> runtime rights recheck -> generation -> corpus copyright scan -> external guardrail signals -> OPA decision -> allow/rewrite/block -> hash-chained audit`

## Commands

```bash
make install
make test
make bootstrap
make api
make ui
make bom
```

Infrastructure dependencies only:

```bash
make install-infra
```

All optional production AI guardrail/model dependencies:

```bash
make install-prod
```

## Important legal/engineering boundary

Similarity thresholds are engineering controls, **not legal safe-harbor thresholds**. Calibrate them using the actual corpora, content types, contractual rights, applicable jurisdictions, and false-positive/false-negative costs. Technical tooling can provide evidence and enforce policy; it does not itself determine whether a use is legally permissible.

See `docs/control-matrix.md`, `docs/threat-model.md`, `docs/architecture.md`, and `SECURITY.md`.
