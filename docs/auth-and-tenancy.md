# Authentication, RBAC and tenant isolation

`AUTH_MODE=disabled` is intended only for local development. `AUTH_MODE=jwt` requires an HS256 bearer token containing `sub`, `tenant_id`, `roles`, `iss`, `aud`, `iat`, and `exp`.

Roles:
- `admin`: full control including audit verification.
- `knowledge_manager`: source registration, ingestion, source status changes, security overview.
- `support` / `viewer`: chat and source visibility only.

Tenant identity is derived from the authenticated token, never from request JSON. Database rows, vector-search filters, audit events, retrieval, and chatbot calls are scoped by that tenant ID. This is defense-in-depth: Qdrant filters by tenant and retrieved source metadata is revalidated against the tenant-scoped rights registry before generation.

For enterprise deployment, replace the shared-secret issuer with your OIDC/JWKS identity provider while keeping the same `Principal` interface.
