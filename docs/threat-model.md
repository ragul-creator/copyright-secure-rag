# Copyright Threat Model

Protected assets: licensed corpora, third-party content, customer support knowledge, provenance records, policy configuration, and generated outputs.

Primary risks include ingestion of unlicensed material, stale/expired rights, source provenance tampering, retrieval of revoked data, prompt attempts to extract source text, near-verbatim reproduction, policy bypass, and audit-log gaps.

Security invariants:
- Unknown or revoked sources do not enter or participate in RAG.
- Rights are checked again at retrieval time.
- Output is checked before release.
- Policy failures are fail-closed in production.
- Every security decision has a request/source identifier in the audit trail.
