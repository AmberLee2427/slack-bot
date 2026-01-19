import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
import requests

# Ensure project root on import path
ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


MCP_SERVER_PATH = Path(__file__).parent.parent / "ref" / "nancy-brain" / "run_mcp_server.py"
MCP_PORT = 8123
MCP_BASE_URL = f"http://localhost:{MCP_PORT}"


def _wait_for_health(url: str, timeout: int = 15) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = requests.get(url, timeout=2)
            if resp.ok and resp.json().get("status") == "ok":
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


@pytest.fixture(scope="session", autouse=True)
def mcp_server():
    """Always start a local MCP server for integration tests."""
    env = os.environ.copy()
    env["MCP_BASE_URL"] = MCP_BASE_URL
    env["MCP_PORT"] = str(MCP_PORT)
    # Set a known API key for testing auth
    env["MCP_API_KEY"] = "test-key"

    os.environ["MCP_BASE_URL"] = MCP_BASE_URL
    os.environ["MCP_PORT"] = str(MCP_PORT)

    proc = subprocess.Popen(
        [sys.executable, "-u", os.fspath(MCP_SERVER_PATH), "--http-and-stdio"],
        cwd=os.fspath(MCP_SERVER_PATH.parent),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )

    health_url = f"{MCP_BASE_URL}/health"
    if not _wait_for_health(health_url, timeout=30):
        try:
            stdout, _ = proc.communicate(timeout=5)
        except Exception:
            stdout = ""
        pytest.exit(f"MCP server failed health check at {health_url}\n{stdout}", returncode=1)

    try:
        yield proc
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


@pytest.fixture(scope="session")
def mcp_stub_server():
    """Start a lightweight stub MCP HTTP server for integration-style tests."""
    loop = asyncio.new_event_loop()
    thread = threading.Thread(target=loop.run_forever, daemon=True)
    thread.start()

    app = web.Application()

    async def health(_request):
        return web.json_response({"status": "ok"})

    async def search(request):
        query = request.query.get("query", "")
        limit = int(request.query.get("limit", "5"))
        hits = [
            {"id": "doc1", "text": f"text for {query}", "score": 0.9},
            {"id": "doc2", "text": "more text", "score": 0.8},
        ][:limit]
        return web.json_response({"hits": hits})

    async def embeddings_sql(request):
        _ = await request.json()
        rows = [{"id": "doc1", "text": "embedded text"}]
        return web.json_response({"rows": rows})

    async def doc_url(request):
        doc_id = request.match_info["doc_id"]
        return web.json_response({"github_url": f"https://example.com/{doc_id}"})

    async def retrieve(request):
        data = await request.json()
        doc_id = data.get("doc_id", "doc1")
        return web.json_response(
            {"passage": {"github_url": f"https://example.com/{doc_id}", "text": "passage text"}}
        )

    app.add_routes(
        [
            web.get("/health", health),
            web.get("/search", search),
            web.post("/embeddings/sql", embeddings_sql),
            web.get("/doc/{doc_id}/url", doc_url),
            web.post("/retrieve", retrieve),
        ]
    )

    runner = web.AppRunner(app)
    asyncio.run_coroutine_threadsafe(runner.setup(), loop).result()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    asyncio.run_coroutine_threadsafe(site.start(), loop).result()
    port = site._server.sockets[0].getsockname()[1]
    base_url = f"http://127.0.0.1:{port}"

    try:
        yield base_url
    finally:
        asyncio.run_coroutine_threadsafe(runner.cleanup(), loop).result()
        loop.call_soon_threadsafe(loop.stop)
        thread.join()
