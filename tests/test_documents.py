import pytest
from fastapi.testclient import TestClient

import document_tools
import api.main as api_main
from agent import call_tool


@pytest.fixture
def documents(tmp_path, monkeypatch):
    monkeypatch.setattr(document_tools, "DOCUMENT_DIR", tmp_path)
    return tmp_path


def test_retrieval_returns_relevant_cited_passage(documents):
    document_tools.save_document("policy.md", "Mobile transfer reviews require supervisor approval.")
    document_tools.save_document("other.txt", "The cafeteria opens at noon.")
    matches = call_tool("search_documents", {"query": "Mobile transfer approval"})["matches"]
    assert matches[0]["citation"] == "[policy.md#1]"
    assert "supervisor" in matches[0]["text"]
    assert all(match["source"] != "other.txt" for match in matches)


def test_no_match_or_empty_corpus(documents):
    assert document_tools.search_documents("unknown")["matches"] == []
    document_tools.save_document("policy.txt", "Mobile transfer approval")
    assert document_tools.search_documents("cafeteria")["matches"] == []


@pytest.mark.parametrize("name", ["../secret.txt", "C:\\secret.txt", "script.py"])
def test_reject_unsafe_filename(documents, name):
    with pytest.raises(ValueError):
        document_tools.save_document(name, "text")


def test_upload_and_duplicate_api(documents):
    client = TestClient(api_main.app)
    payload = {"filename": "policy.txt", "content": "Transfer approval requires review."}
    assert client.post("/documents", json=payload).status_code == 201
    assert client.post("/documents", json=payload).status_code == 409
    assert client.post("/documents", json={**payload, "filename": "../bad.txt"}).status_code == 400


def test_empty_and_oversize_documents(documents):
    for content in [" ", "a" * 1_000_001]:
        with pytest.raises(ValueError):
            document_tools.save_document("policy.txt", content)
