from __future__ import annotations
import uuid
from src.rag.retriever import Retriever
from src.rag.generator import Generator
from src.security.output_guard import CopyrightOutputGuard
from src.services.db import audit

retriever=Retriever(); generator=Generator(); guard=CopyrightOutputGuard()


def chat(tenant_id: str, question: str, top_k: int = 4):
    request_id=str(uuid.uuid4())
    contexts=retriever.search(tenant_id, question,top_k)
    answer=generator.generate(question,contexts)
    policy,signals=guard.evaluate(request_id,tenant_id,answer,contexts)
    notes=[]
    decision=policy["decision"]
    if decision=="REWRITE":
        retry=generator.generate(question,contexts,
             "The previous draft had excessive textual overlap. Paraphrase aggressively, keep it concise, and do not quote long passages.")
        p2,s2=guard.evaluate(request_id,tenant_id,retry,contexts)
        signals={"first_pass":signals,"second_pass":s2}
        if p2["decision"] in {"ALLOW","ALLOW_WITH_ATTRIBUTION"}:
            answer=retry; decision=p2["decision"]; notes.append("Response regenerated after copyright guardrail trigger.")
        else:
            answer="I found relevant approved support material, but I can't provide a response that reproduces that source too closely. Please ask a narrower question or consult the cited source."
            decision="BLOCK"; notes.append("Response blocked after regeneration still exceeded copyright policy.")
    elif decision=="BLOCK":
        answer="The response was blocked by the copyright policy engine."
        notes.append(policy.get("reason","Policy block"))
    elif decision=="ESCALATE":
        notes.append("No approved evidence was available; the assistant did not guess.")
    citations=[{"source_id":c["source_id"],"document_id":c["document_id"],"source_name":c["source_name"],"score":round(c["score"],4)} for c in contexts]
    audit({"event":"chat_completed","request_id":request_id,"decision":decision,"question":question,
           "citations":citations}, tenant_id)
    return {"request_id":request_id,"answer":answer,"decision":decision,"citations":citations,
            "copyright_signals":signals,"security_notes":notes}
