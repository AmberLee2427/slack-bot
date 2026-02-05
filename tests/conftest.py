import asyncio
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest
import requests
from aiohttp import web

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


class _StubMCPServer:
    """Small in-process MCP-like HTTP server for CI fallback."""

    def __init__(self, host: str = "127.0.0.1", port: int = MCP_PORT):
        self.host = host
        self.port = port
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.runner = None
        self.site = None

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def _startup(self):
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

        async def embeddings_sql(_request):
            rows = [{"id": "doc1", "text": "embedded text"}]
            return web.json_response({"rows": rows})

        async def doc_url(request):
            doc_id = request.match_info["doc_id"]
            return web.json_response({"github_url": f"https://example.com/{doc_id}"})

        async def retrieve(request):
            data = await request.json()
            doc_id = data.get("doc_id", "doc1")
            return web.json_response(
                {
                    "passage": {
                        "doc_id": doc_id,
                        "github_url": f"https://example.com/{doc_id}",
                        "text": "passage text",
                    }
                }
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

        self.runner = web.AppRunner(app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()

        # If port 0 was used, capture the actual assigned port.
        sockets = getattr(getattr(self.site, "_server", None), "sockets", None) or []
        if sockets:
            self.port = int(sockets[0].getsockname()[1])

    async def _shutdown(self):
        if self.runner:
            await self.runner.cleanup()

    def start(self):
        self.thread.start()
        asyncio.run_coroutine_threadsafe(self._startup(), self.loop).result(timeout=10)

    def stop(self):
        asyncio.run_coroutine_threadsafe(self._shutdown(), self.loop).result(timeout=10)
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join(timeout=5)

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"


@pytest.fixture(scope="session", autouse=True)
def mcp_server():
    """Always start a local MCP server for integration tests."""
    env = os.environ.copy()
    base_url = MCP_BASE_URL
    env["MCP_BASE_URL"] = base_url
    env["MCP_PORT"] = str(MCP_PORT)
    # Set a known API key for testing auth
    env["MCP_API_KEY"] = "test-key"

    os.environ["MCP_BASE_URL"] = base_url
    os.environ["MCP_PORT"] = str(MCP_PORT)

    proc = None
    stub = None

    force_stub = os.environ.get("MCP_TEST_FORCE_STUB", "").lower() in {"1", "true", "yes"}
    if force_stub:
        print("[tests] Using stub MCP server (forced via MCP_TEST_FORCE_STUB).")
        stub = _StubMCPServer(port=0)
        stub.start()
        base_url = stub.base_url
        os.environ["MCP_BASE_URL"] = base_url
    else:
        if not MCP_SERVER_PATH.exists():
            pytest.exit(
                f"MCP server script not found at {MCP_SERVER_PATH}. "
                "Run with MCP_TEST_FORCE_STUB=true to use the stub server.",
                returncode=1,
            )
        proc = subprocess.Popen(
            [sys.executable, "-u", os.fspath(MCP_SERVER_PATH), "--http-and-stdio"],
            cwd=os.fspath(MCP_SERVER_PATH.parent),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
        )

    health_url = f"{base_url}/health"
    if not _wait_for_health(health_url, timeout=30):
        if proc is not None:
            try:
                stdout, _ = proc.communicate(timeout=5)
            except Exception:
                stdout = ""
                try:
                    proc.terminate()
                    proc.wait(timeout=3)
                except Exception:
                    proc.kill()

            msg = f"MCP server failed health check at {health_url}"
            if stdout:
                msg = f"{msg}\n{stdout}"
            pytest.exit(msg, returncode=1)
        else:
            pytest.exit(f"MCP server failed health check at {health_url}", returncode=1)

    try:
        yield stub if stub is not None else proc
    finally:
        if proc is not None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except Exception:
                proc.kill()
        if stub is not None:
            stub.stop()
