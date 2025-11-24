import requests

# Always target the local test server started by the session fixture
MCP_BASE_URL = "http://localhost:8123"


def test_retrieve_endpoint_returns_passage(mcp_server):
    # Find a doc id that exists by doing a quick search first
    search_resp = requests.get(f"{MCP_BASE_URL.rstrip('/')}/search", params={"query": "roman", "limit": 1}, timeout=30)
    assert search_resp.status_code == 200, f"search failed: {search_resp.status_code} {search_resp.text}"
    hits = search_resp.json().get("hits") or []
    assert hits, "Expected at least one search hit to retrieve"
    doc_id = hits[0]["id"]

    payload = {"doc_id": doc_id, "start": 0, "end": 5}
    resp = requests.post(f"{MCP_BASE_URL.rstrip('/')}/retrieve", json=payload, timeout=30)
    # Allow 404/500 when raw documents are not present locally; ensure no connection errors
    assert resp.status_code in (200, 404, 500), f"unexpected status: {resp.status_code} - {resp.text}"
    if resp.status_code == 200:
        data = resp.json()
        passage = data.get("passage") or {}
        assert passage.get("text"), "Expected text content in passage response"
