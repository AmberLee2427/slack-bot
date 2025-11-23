import os
import subprocess
import time
import requests
import pytest

MCP_SERVER_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../ref/nancy-brain/run_mcp_server.py"))
MCP_HEALTH_URL = os.environ.get("MCP_BASE_URL", "http://localhost:8000/health")
MCP_ENABLED = os.environ.get("MCP_INTEGRATION_TEST", "false").lower() == "true"


def wait_for_health(url, timeout=30):
    """Wait for MCP /health endpoint to respond OK."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = requests.get(url, timeout=2)
            if resp.ok and resp.json().get("status") == "ok":
                return True
        except Exception:
            time.sleep(1)
    raise RuntimeError(f"MCP server did not become healthy at {url} within {timeout}s")


@pytest.fixture(scope="session")
def mcp_server():
    """Start MCP server before tests, yield, then stop."""
    if not MCP_ENABLED:
        yield None
        return
    proc = subprocess.Popen([
        "python", MCP_SERVER_PATH
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        wait_for_health(MCP_HEALTH_URL)
        yield proc
    finally:
        proc.terminate()
        proc.wait(timeout=10)
