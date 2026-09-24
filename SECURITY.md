# Security Policy

This repository contains a copyright-aware RAG security reference implementation.

## Reporting security issues

Do not publish exploitable vulnerabilities as public issues. Report them privately to the repository owner through GitHub's private vulnerability reporting feature when enabled.

## Security invariants

- Unknown, revoked, expired, or RAG-disallowed sources must not enter the active corpus.
- Rights are re-evaluated at retrieval time so revocation can take effect without re-embedding.
- Generated output is checked before release for material textual overlap.
- Policy-engine failure is fail-closed when `FAIL_CLOSED=true`.
- Security decisions are auditable with request/source identifiers.

## Non-goals

Similarity thresholds are technical controls, not legal determinations. Deployments must calibrate policies for their rights agreements, jurisdictions, content types, and risk tolerance.
