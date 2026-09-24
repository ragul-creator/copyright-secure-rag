from __future__ import annotations
import httpx
from src.config import settings


def _validate(name: str, url: str, payload: dict) -> dict:
    if not url:
        return {"name":name,"enabled":False,"allow":True,"reason":"DISABLED"}
    try:
        response=httpx.post(url,json=payload,timeout=3.0)
        response.raise_for_status()
        body=response.json()
        return {"name":name,"enabled":True,"allow":bool(body.get("allow",True)),
                "reason":str(body.get("reason","OK")),"metadata":body.get("metadata",{})}
    except Exception as exc:
        allow=not settings.external_guardrails_fail_closed
        return {"name":name,"enabled":True,"allow":allow,
                "reason":"UNAVAILABLE_FAIL_OPEN" if allow else "UNAVAILABLE_FAIL_CLOSED",
                "error_type":type(exc).__name__}


def validate_output(tenant_id: str, answer: str, contexts: list[dict], signals: dict) -> list[dict]:
    payload={"tenant_id":tenant_id,"answer":answer,"contexts":[{
        "source_id":c["source_id"],"document_id":c["document_id"],"text":c["text"]
    } for c in contexts],"copyright_signals":signals}
    return [
        _validate("nemo_guardrails",settings.nemo_guardrails_url,payload),
        _validate("guardrails_ai",settings.guardrails_ai_url,payload),
    ]
