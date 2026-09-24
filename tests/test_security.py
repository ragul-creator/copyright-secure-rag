from src.models import SourceRegistration
from src.security.licenses import register_source, LicenseError
from src.services.ingestion import ingest_document
from src.services.chat import chat
from src.services.db import verify_audit_chain, execute
from src.security.similarity import longest_common_word_span, ngram_jaccard, minhash_similarity


def source(source_id: str, **kwargs):
    return SourceRegistration(source_id=source_id,name=source_id,rights_holder="Example Corp",license_spdx="LicenseRef-Example",**kwargs)


def test_unlicensed_source_rejected():
    try:
        ingest_document("T1","UNKNOWN","D1","hello world")
        assert False
    except LicenseError:
        assert True


def test_revoked_source_rejected():
    register_source("T1",source("R",status="revoked"))
    try:
        ingest_document("T1","R","D2","some content")
        assert False
    except LicenseError:
        assert True


def test_similarity_detects_copy():
    a="one two three four five six seven eight nine ten"
    assert longest_common_word_span(a,a)==10
    assert ngram_jaccard(a,a)==1.0
    assert minhash_similarity(a,a) > 0.95


def test_chat_uses_approved_source():
    register_source("T2",source("A",quote_word_limit=50))
    ingest_document("T2","A","D3","Customers may request a refund within 30 calendar days of purchase. Refunds return to the original payment method.")
    out=chat("T2","How long do I have to request a refund?")
    assert out["citations"]
    assert all(c["source_id"] == "A" for c in out["citations"])
    assert out["decision"] in {"ALLOW","ALLOW_WITH_ATTRIBUTION","BLOCK"}


def test_tenant_isolation():
    register_source("TENANT-A",source("PRIVATE",quote_word_limit=50))
    ingest_document("TENANT-A","PRIVATE","A-DOC","Secret support codeword is cobalt-river-seven.")
    out=chat("TENANT-B","What is the cobalt river support codeword?")
    assert not out["citations"]
    assert out["decision"] == "ESCALATE"


def test_revocation_applies_at_retrieval_without_reingest():
    register_source("T3",source("LIVE",quote_word_limit=50))
    ingest_document("T3","LIVE","D-LIVE","Premium support is available Monday through Friday.")
    before=chat("T3","When is premium support available?")
    assert before["citations"]
    execute("UPDATE sources SET status='revoked' WHERE tenant_id=? AND source_id=?",("T3","LIVE"))
    after=chat("T3","When is premium support available?")
    assert not after["citations"]
    assert after["decision"] == "ESCALATE"


def test_audit_chain_is_tamper_evident():
    register_source("T4",source("AUDIT"))
    ingest_document("T4","AUDIT","D-AUDIT","Audit chain test content.")
    assert verify_audit_chain("T4") is True
    execute("UPDATE audit_events SET event_hash='bad' WHERE tenant_id=? AND id=(SELECT MIN(id) FROM audit_events WHERE tenant_id=?)",("T4","T4"))
    assert verify_audit_chain("T4") is False
