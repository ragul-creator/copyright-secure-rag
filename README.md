# Copyright-Secure Customer Support RAG

A working customer-support RAG chatbot with copyright/data-rights enforcement built into ingestion, retrieval, generation, output checking, policy decisions, and auditing.

## What is implemented

- Customer support RAG API + Streamlit UI
- Central source/license registry (no duplicated license blobs on every chunk)
- Runtime license expiry/revocation checks
- SHA-256 document provenance
- Approved-source-only retrieval
- Exact-span, 5-gram, RapidFuzz, and TF-IDF semantic similarity checks
- ALLOW / ATTRIBUTION / REWRITE / BLOCK / ESCALATE policy decisions
- Optional OPA fail-closed policy engine
- Audit JSONL and Prometheus metrics
- CycloneDX-style data BOM exporter
- ScanCode, ORT and Sigstore integration scripts
- Docker Compose services for API, UI, OPA, Qdrant, PostgreSQL/pgvector, Prometheus and Grafana
- Promptfoo/Giskard/Ragas evaluation hooks
- Security unit tests

## Quick start (local core)

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
export PYTHONPATH=.
python scripts/bootstrap_demo.py
uvicorn apps.api.main:app --reload
```

Then open API docs at `http://localhost:8000/docs`.

For the UI:

```bash
streamlit run apps/ui/app.py
```

## Full service stack

```bash
docker compose up --build
```

Endpoints: API 8000, UI 8501, OPA 8181, Qdrant 6333, PostgreSQL 5432, Prometheus 9090, Grafana 3000.

## Security flow

`Source -> license/provenance gate -> approved corpus -> runtime rights filter -> retrieval -> LLM -> reproduction detector -> OPA/local policy -> allow/rewrite/block -> audit`

## Important production note

Similarity thresholds in `.env.example` are engineering defaults for development, **not legal safe-harbor thresholds**. Calibrate them against the corpora, licenses, use cases, jurisdictions, and false-positive/false-negative tolerance relevant to your deployment. Keep legal interpretation separate from technical detection.

## Repository commands

```bash
make install
make test
make bootstrap
make api
# another terminal
make ui
```

For optional production integrations (Qdrant/PostgreSQL, SentenceTransformers, OpenTelemetry):

```bash
make install-prod
```

See [`docs/control-matrix.md`](docs/control-matrix.md) for the distinction between implemented runtime controls and external compliance/evaluation integrations.
