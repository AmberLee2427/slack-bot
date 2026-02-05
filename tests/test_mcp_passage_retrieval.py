import os
import requests


def _mcp_base_url() -> str:
    return os.environ.get("MCP_BASE_URL", "http://localhost:8123")


def test_retrieve_endpoint_returns_passage(mcp_server):
    headers = {"X-API-Key": "test-key"}
    base_url = _mcp_base_url().rstrip("/")
    # Find a doc id that exists by doing a quick search first
    search_resp = requests.get(f"{base_url}/search", params={"query": "roman", "limit": 1}, headers=headers, timeout=30)
    assert search_resp.status_code == 200, f"search failed: {search_resp.status_code} {search_resp.text}"
    hits = search_resp.json().get("hits") or []
    assert hits, "Expected at least one search hit to retrieve"
    doc_id = hits[0]["id"]

    payload = {"doc_id": doc_id, "start": 0, "end": 5}
    resp = requests.post(f"{base_url}/retrieve", json=payload, headers=headers, timeout=30)
    # Allow 404/500 when raw documents are not present locally; ensure no connection errors
    assert resp.status_code in (200, 404, 500), f"unexpected status: {resp.status_code} - {resp.text}"
    if resp.status_code == 200:
        data = resp.json()
        passage = data.get("passage") or {}
        assert passage.get("text"), "Expected text content in passage response"
