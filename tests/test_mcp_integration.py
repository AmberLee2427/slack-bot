import os
import pytest
import requests


MCP_BASE = os.environ.get("MCP_BASE_URL")
MCP_ENABLED = os.environ.get("MCP_INTEGRATION_TEST", "false").lower() == "true"



@pytest.mark.skipif(not MCP_ENABLED or not MCP_BASE, reason="MCP integration tests are disabled")
def test_mcp_health_endpoint_live(mcp_server):
    """Simple live test that queries the MCP /health endpoint and validates a JSON response."""
    url = MCP_BASE.rstrip("/") + "/health"
    headers = {}
    api_key = os.environ.get("MCP_API_KEY")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    resp = requests.get(url, headers=headers, timeout=10)
    assert resp.status_code == 200, f"unexpected status: {resp.status_code} - {resp.text}"
    payload = resp.json()
    assert isinstance(payload, dict)
    # expected keys from Nancy Brain health contract
    assert "status" in payload
    assert payload["status"] in ("ok", "degraded", "error")
