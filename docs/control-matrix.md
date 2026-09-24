# Copyright Control Matrix

| Layer | Control | Primary implementation/tool | Runtime? | Failure behavior |
|---|---|---|---|---|
| Provenance | Source registration and lineage | PostgreSQL/SQLite registry + SHA-256 | Ingestion | Deny unknown source |
| License detection | Detect declared/observed licensing | ScanCode Toolkit | Pre-ingestion worker | Hold for review |
| Compliance | Evaluate license policy | ORT + SPDX | Pre-ingestion worker | Hold/deny |
| BOM | Machine-readable rights inventory | CycloneDX | Build/compliance | Evidence artifact |
| Integrity | Sign approved manifests | Sigstore/Cosign | Build/compliance | Reject unverifiable manifest in hardened deployments |
| Rights enforcement | Central policy decision | OPA | Ingestion + runtime | Fail closed |
| Retrieval | Re-check current rights before context use | NeMo-compatible retrieval rail + local filter | Yes | Filter source |
| Verbatim detection | Longest common word span | Native detector | Yes | Rewrite/block |
| Near-copy detection | n-gram + RapidFuzz | RapidFuzz/native | Yes | Rewrite/block |
| Semantic overlap | similarity signal | TF-IDF today; SentenceTransformers optional | Yes | Contributes to rewrite |
| Evaluation | RAG/security regression | Promptfoo, Giskard, Ragas | CI/offline | Block release on failed gates |
| Observability | Security metrics/traces | Prometheus, Grafana, OpenTelemetry | Yes | Alert/incident workflow |

The system intentionally separates **offline compliance tooling** from the **latency-sensitive runtime path**. External tools are integrations; controls are not considered deployed merely because a dependency or configuration file exists.
