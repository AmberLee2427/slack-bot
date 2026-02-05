import os
import requests

from bot.plugins.rag.mcp_adapter import MCPRAGAdapter


def _mcp_base_url() -> str:
    return os.environ.get("MCP_BASE_URL", "http://localhost:8123")


def test_mcp_health_endpoint_live(mcp_server):
    base_url = _mcp_base_url().rstrip("/")
    resp = requests.get(f"{base_url}/health", timeout=10)
    assert resp.status_code == 200
    assert resp.json().get("status") in ("ok", "degraded")


def test_mcp_adapter_round_trip(mcp_server):
    adapter = MCPRAGAdapter(_mcp_base_url(), api_key="test-key", timeout=15)

    results = adapter.search("microlensing", limit=3)
    assert results, "Expected search results from MCP server"
    first = results[0]
    assert first.get("id"), "Result missing id"
    assert "text" in first, "Result missing text"

    ctx = adapter.get_context_for_query("microlensing")
    assert isinstance(ctx, str)
    assert ctx.strip(), "Context should not be empty"

    url = adapter._get_github_url(first["id"])
    # Some docs may not have GitHub metadata; ensure call doesn't explode
    assert url is None or isinstance(url, str)
