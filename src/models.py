from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field

class SourceRegistration(BaseModel):
    source_id: str
    name: str
    origin: str = "internal"
    rights_holder: str
    license_spdx: str
    rag_allowed: bool = True
    generation_allowed: bool = True
    attribution_required: bool = False
    quote_word_limit: int = 28
    expires_at: str | None = None
    status: Literal["approved", "review", "revoked"] = "approved"

class IngestRequest(BaseModel):
    source_id: str
    document_id: str
    text: str = Field(min_length=1)

class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    top_k: int = Field(default=4, ge=1, le=12)

class Citation(BaseModel):
    source_id: str
    document_id: str
    source_name: str
    score: float

class ChatResponse(BaseModel):
    request_id: str
    answer: str
    decision: Literal["ALLOW", "ALLOW_WITH_ATTRIBUTION", "REWRITE", "BLOCK", "ESCALATE"]
    citations: list[Citation]
    copyright_signals: dict
    security_notes: list[str]
