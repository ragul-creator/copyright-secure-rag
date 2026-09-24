# Audit integrity

Every tenant audit record includes the previous event hash and its own SHA-256 hash. `/audit/verify` recomputes the chain to detect database/event modification.

Hash chaining is tamper-evident, not inherently immutable. For deployments requiring retention controls, configure an S3 bucket with Object Lock enabled, set `AUDIT_S3_BUCKET`, and optionally set `AUDIT_WORM_REQUIRED=true`. The audit sink writes each event as an object named by its event hash and requests Object Lock `COMPLIANCE` mode until the configured retention date.

Object Lock must be enabled and governed on the bucket itself; application configuration cannot retroactively make a normal bucket immutable.
