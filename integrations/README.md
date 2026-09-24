# External guardrail integrations

The core copyright controls are implemented inside this repository. NeMo Guardrails and Guardrails AI can be deployed as independent validation services and connected through `NEMO_GUARDRAILS_URL` and `GUARDRAILS_AI_URL`.

Each service receives JSON containing `tenant_id`, `answer`, approved `contexts`, and calculated copyright signals. It should return:

```json
{"allow": true, "reason": "OK", "metadata": {}}
```

or a deny decision:

```json
{"allow": false, "reason": "policy_name"}
```

This sidecar boundary keeps the copyright service vendor-neutral and lets organizations upgrade NeMo/Guardrails AI independently. `EXTERNAL_GUARDRAILS_FAIL_CLOSED=true` changes adapter outages into a deny decision.

`requirements-production.txt` includes both frameworks for organizations that want to build the sidecars in Python.
