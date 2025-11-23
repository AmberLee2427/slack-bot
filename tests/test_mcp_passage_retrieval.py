import os
import pytest
import requests

MCP_BASE = os.environ.get("MCP_BASE_URL")
MCP_ENABLED = os.environ.get("MCP_INTEGRATION_TEST", "false").lower() == "true"

@pytest.mark.skipif(not MCP_ENABLED or not MCP_BASE, reason="MCP integration tests are disabled")
def test_retrieve_document_passage():
    """End-to-end test for passage retrieval with explicit metadata."""
    url = MCP_BASE.rstrip("/") + "/call-tool"
    headers = {"Content-Type": "application/json"}
    api_key = os.environ.get("MCP_API_KEY")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    payload = {
        "name": "retrieve_document_passage",
        "arguments": {
            "doc_id": "microlensing_tools/MulensModel/README.md",
            "start": 0,
            "end": 10
        }
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=10)
    assert resp.status_code == 200, f"unexpected status: {resp.status_code} - {resp.text}"
    results = resp.json()
    assert isinstance(results, list)
    result = results[0]
    assert "text" in result["text"] or "Document" in result["text"]
    assert "Lines:" in result["text"]
    assert "Partial passage" in result["text"] or "partial" in result["text"].lower()
    assert "GitHub" in result["text"] or "github_url" in result["text"]

@pytest.mark.skipif(not MCP_ENABLED or not MCP_BASE, reason="MCP integration tests are disabled")
def test_retrieve_multiple_passages():
    """End-to-end test for batch passage retrieval and context assembly."""
    url = MCP_BASE.rstrip("/") + "/call-tool"
    headers = {"Content-Type": "application/json"}
    api_key = os.environ.get("MCP_API_KEY")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    payload = {
        "name": "retrieve_multiple_passages",
        "arguments": {
            "items": [
                {"doc_id": "microlensing_tools/MulensModel/README.md", "start": 0, "end": 5},
                {"doc_id": "microlensing_tools/MulensModel/README.md", "start": 5, "end": 10}
            ]
        }
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=10)
    assert resp.status_code == 200, f"unexpected status: {resp.status_code} - {resp.text}"
    results = resp.json()
    assert isinstance(results, list)
    result = results[0]
    assert "Retrieved" in result["text"]
    assert "Lines:" in result["text"]
    assert "Partial passage" in result["text"] or "partial" in result["text"].lower()
    assert "GitHub" in result["text"] or "github_url" in result["text"]
    # Check context assembly: both passages should be present
    assert result["text"].count("microlensing_tools/MulensModel/README.md") >= 2
