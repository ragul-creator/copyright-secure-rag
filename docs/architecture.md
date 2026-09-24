# Architecture

The runtime is defense-in-depth:

1. **Source registration** stores rights metadata once per source.
2. **Ingestion gate** rejects unknown, revoked, expired, or RAG-disallowed sources.
3. **Provenance** hashes source documents and records document→source lineage.
4. **Retrieval guard** re-checks source status at query time, so revocation takes effect without re-embedding.
5. **Generation** is constrained to approved retrieved context.
6. **Output reproduction guard** combines exact-word spans, n-gram overlap, fuzzy similarity, and semantic similarity.
7. **Policy engine** maps signals to ALLOW / ALLOW_WITH_ATTRIBUTION / REWRITE / BLOCK / ESCALATE. OPA can be authoritative in production.
8. **Audit** records ingestion and generation decisions.
9. **Observability** exposes Prometheus metrics and supports Grafana dashboards.

External compliance workers can run ScanCode, ORT, CycloneDX generation, and Sigstore signing before a source is marked approved.
