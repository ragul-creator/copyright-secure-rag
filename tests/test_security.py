from src.models import SourceRegistration
from src.security.licenses import register_source, LicenseError
from src.services.ingestion import ingest_document
from src.services.chat import chat
from src.security.similarity import longest_common_word_span, ngram_jaccard

def test_unlicensed_source_rejected():
    try:
        ingest_document("UNKNOWN","D1","hello world")
        assert False
    except LicenseError:
        assert True

def test_revoked_source_rejected():
    register_source(SourceRegistration(source_id="R",name="revoked",rights_holder="x",license_spdx="MIT",status="revoked"))
    try:
        ingest_document("R","D2","some content")
        assert False
    except LicenseError:
        assert True

def test_similarity_detects_copy():
    a="one two three four five six seven eight nine ten"
    assert longest_common_word_span(a,a)==10
    assert ngram_jaccard(a,a)==1.0

def test_chat_uses_approved_source():
    register_source(SourceRegistration(source_id="A",name="refund",rights_holder="x",license_spdx="LicenseRef-X",quote_word_limit=50))
    ingest_document("A","D3","Customers may request a refund within 30 calendar days of purchase. Refunds return to the original payment method.")
    out=chat("How long do I have to request a refund?")
    assert out["citations"]
    assert out["decision"] in {"ALLOW","ALLOW_WITH_ATTRIBUTION","BLOCK"}

def test_no_context_escalates():
    out=chat("What is the teleportation support policy?")
    assert out["decision"] in {"ESCALATE","ALLOW","BLOCK"}
