import pytest

from src.rag.document_loader import DocumentLoadError, load_document_bytes


def test_load_text_and_markdown():
    assert load_document_bytes("policy.txt", b"Refunds are available in 30 days.") == "Refunds are available in 30 days."
    assert "Premium support" in load_document_bytes("guide.md", b"# Guide\n\nPremium support is available.")


def test_load_html_removes_scripts_and_keeps_visible_text():
    html = b"<html><style>.x{display:none}</style><body><h1>Refunds</h1><script>secret()</script><p>Within 30 days.</p></body></html>"
    text = load_document_bytes("policy.html", html)
    assert "Refunds" in text
    assert "Within 30 days." in text
    assert "secret" not in text


def test_rejects_unsupported_type():
    with pytest.raises(DocumentLoadError):
        load_document_bytes("policy.exe", b"not allowed")


def test_rejects_empty_file():
    with pytest.raises(DocumentLoadError):
        load_document_bytes("empty.txt", b"")
