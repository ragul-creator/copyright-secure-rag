# Ingestion compliance pipeline

Production deployments can set `REQUIRE_COMPLIANCE_EVIDENCE=true`. When enabled, an approved source still cannot be ingested until the rights registry contains at least one approved compliance-evidence record.

Recommended flow:

1. Stage the candidate source outside the active RAG corpus.
2. Run `python scripts/compliance_scan.py <path>` in a controlled scanner worker with ScanCode and/or ORT installed.
3. Review detected licenses, copyrights, notices, source provenance and contractual rights.
4. Store the scanner artifact in an evidence store and calculate its SHA-256 digest.
5. Register the source and attach the evidence through `POST /sources/{source_id}/evidence` with an approved/review/rejected verdict.
6. Only approved evidence satisfies the production ingestion gate.
7. Generate the CycloneDX data BOM and optionally sign evidence/manifest artifacts with Cosign.

This separates automated evidence collection from the organization's actual rights determination. A scanner finding a license string does not by itself prove that the organization has every right required for the intended use.
