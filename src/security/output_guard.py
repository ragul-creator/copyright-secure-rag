from __future__ import annotations
from src.config import settings
from src.rag.retriever import Retriever
from src.security.guardrail_adapters import validate_output
from src.security.similarity import aggregate
from src.security.policy import decide
from src.services.db import audit


class CopyrightOutputGuard:
    def __init__(self):
        self.retriever = Retriever()

    def _candidate_union(self, tenant_id: str, answer: str, contexts: list[dict]) -> list[dict]:
        candidates = self.retriever.search(tenant_id, answer, settings.candidate_limit)
        merged = {}
        for c in [*contexts, *candidates]:
            merged[(c["source_id"], c["document_id"], c.get("chunk_id"))] = c
        return list(merged.values())

    def evaluate(self, request_id: str, tenant_id: str, answer: str, contexts: list[dict]):
        candidates = self._candidate_union(tenant_id, answer, contexts)
        signals=aggregate(answer,candidates)
        external=validate_output(tenant_id,answer,contexts,signals)
        signals["external_guardrails"]=external
        blocked=next((x for x in external if x.get("enabled") and not x.get("allow")),None)
        policy={"decision":"BLOCK","reason":f"EXTERNAL_GUARDRAIL:{blocked['name']}:{blocked['reason']}"} if blocked else decide(tenant_id,signals,contexts)
        audit({"event":"copyright_output_check","request_id":request_id,
               "decision":policy["decision"],"reason":policy.get("reason"),"signals":signals,
               "retrieved_sources":[c["source_id"] for c in contexts],
               "scan_candidate_count":len(candidates)}, tenant_id)
        return policy,signals
