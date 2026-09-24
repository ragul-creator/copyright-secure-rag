from __future__ import annotations
from src.security.similarity import aggregate
from src.security.policy import decide
from src.services.db import audit

class CopyrightOutputGuard:
    def evaluate(self, request_id: str, answer: str, contexts: list[dict]):
        signals=aggregate(answer,contexts)
        policy=decide(signals,contexts)
        audit({"event":"copyright_output_check","request_id":request_id,
               "decision":policy["decision"],"reason":policy.get("reason"),"signals":signals,
               "sources":[c["source_id"] for c in contexts]})
        return policy,signals
