from __future__ import annotations
import re
import httpx
from src.config import settings

SYSTEM = """You are a customer support assistant. Answer only from the supplied approved context.
Do not reproduce long passages verbatim. Synthesize the minimum information necessary to answer the question.
If the context is insufficient, say so. Do not invent policy details."""

class Generator:
    def generate(self, question: str, contexts: list[dict], retry_instruction: str | None = None) -> str:
        if settings.llm_provider.lower() == "openai" and settings.openai_api_key:
            return self._openai(question, contexts, retry_instruction)
        return self._extractive(question, contexts)

    def _openai(self, question, contexts, retry_instruction=None):
        ctx="\n\n".join(f"SOURCE {i+1}: {c['text']}" for i,c in enumerate(contexts))
        extra = f"\nAdditional security instruction: {retry_instruction}" if retry_instruction else ""
        payload={"model":settings.openai_model,"temperature":0.1,"messages":[
            {"role":"system","content":SYSTEM+extra},
            {"role":"user","content":f"Question: {question}\n\nApproved context:\n{ctx}"}
        ]}
        with httpx.Client(timeout=45) as client:
            r=client.post(settings.openai_base_url.rstrip("/")+"/chat/completions",
                headers={"Authorization":f"Bearer {settings.openai_api_key}"},json=payload)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()

    def _extractive(self, question, contexts):
        if not contexts:
            return "I couldn't find enough approved support information to answer that question."
        q=set(re.findall(r"[a-z0-9]+", question.lower()))
        candidates=[]
        for c in contexts:
            for sent in re.split(r"(?<=[.!?])\s+", c["text"]):
                sw=set(re.findall(r"[a-z0-9]+", sent.lower()))
                score=len(q & sw)
                if score: candidates.append((score, sent.strip()))
        best=[s for _,s in sorted(candidates, reverse=True)[:1]]
        if not best:
            return "I found approved documents, but they do not contain enough information to answer this reliably."
        # Deliberately short; copyright guard will still re-check it.
        return " ".join(best)
