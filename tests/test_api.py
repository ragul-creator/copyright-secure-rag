from fastapi.testclient import TestClient

from apps.api.main import app


client = TestClient(app)


def test_health_and_readiness():
    assert client.get("/health").status_code == 200
    ready = client.get("/readyz")
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"


def test_register_upload_and_chat_flow():
    source_id = "API-SOURCE"
    document_id = "API-DOC"

    source = client.post(
        "/sources",
        json={
            "source_id": source_id,
            "name": "API Refund Policy",
            "rights_holder": "Example Corp",
            "license_spdx": "LicenseRef-Example",
            "rag_allowed": True,
            "generation_allowed": True,
            "quote_word_limit": 50,
            "status": "approved",
        },
    )
    assert source.status_code == 200

    upload = client.post(
        "/ingest/file",
        data={"source_id": source_id, "document_id": document_id},
        files={"file": ("refunds.txt", b"Customers may request refunds within 45 calendar days.", "text/plain")},
    )
    assert upload.status_code == 200
    assert upload.json()["chunks"] == 1

    answer = client.post(
        "/chat",
        json={"question": "How many days do customers have to request a refund?", "top_k": 4},
    )
    assert answer.status_code == 200
    body = answer.json()
    assert body["citations"]
    assert body["citations"][0]["source_id"] == source_id


def test_upload_rejects_unsupported_extension():
    source_id = "API-SOURCE-UNSUPPORTED"
    client.post(
        "/sources",
        json={
            "source_id": source_id,
            "name": "Unsupported test",
            "rights_holder": "Example Corp",
            "license_spdx": "LicenseRef-Example",
            "status": "approved",
        },
    )
    response = client.post(
        "/ingest/file",
        data={"source_id": source_id, "document_id": "BAD-DOC"},
        files={"file": ("payload.exe", b"binary", "application/octet-stream")},
    )
    assert response.status_code == 400
