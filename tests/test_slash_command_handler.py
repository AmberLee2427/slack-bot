import os

import types
import sys

import pytest
import pytest_asyncio
from aiohttp.test_utils import TestClient, TestServer

# Provide a lightweight slack_sdk stub so nancy_bot imports without optional dependency
slack_pkg = types.ModuleType("slack_sdk")
slack_web = types.ModuleType("slack_sdk.web")
slack_async = types.ModuleType("slack_sdk.web.async_client")
slack_async.AsyncWebClient = type(
    "AsyncWebClient",
    (),
    {"__init__": lambda self, *a, **k: None, "auth_test": lambda self: {"user_id": "U_TEST"}},
)
slack_signature = types.ModuleType("slack_sdk.signature")
slack_signature.SignatureVerifier = type("SignatureVerifier", (), {"__init__": lambda self, *a, **k: None})
slack_web.async_client = slack_async
slack_pkg.web = slack_web
slack_pkg.signature = slack_signature

sys.modules.setdefault("slack_sdk", slack_pkg)
sys.modules.setdefault("slack_sdk.web", slack_web)
sys.modules.setdefault("slack_sdk.web.async_client", slack_async)
sys.modules.setdefault("slack_sdk.signature", slack_signature)

from nancy_bot import create_app


class DummyLLMService:
    def __init__(self, *_, **__):
        self.rag_status = {"available": True, "source": "test"}
        self.rag = None

    def update_rag_variables(self):
        return None


@pytest_asyncio.fixture
async def app_client(monkeypatch):
    # Avoid real MCP dependency during app startup
    monkeypatch.setattr("nancy_bot.LLMService", DummyLLMService)
    monkeypatch.setattr("nancy_bot.NancyBot._attempt_reconnect", lambda self: (True, "reconnected (test)"))
    monkeypatch.delenv("MCP_BASE_URL", raising=False)
    app = await create_app()
    server = TestServer(app)
    await server.start_server()
    client = TestClient(server)
    await client.start_server()
    try:
        yield client
    finally:
        await client.close()
        await server.close()


async def post_form(client, data: dict):
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    return await client.post("/slack/commands", data=data, headers=headers)


@pytest.mark.asyncio
async def test_status_endpoint_returns_ok(app_client):
    data = {"command": "/status", "user_id": "U123", "text": ""}

    resp = await post_form(app_client, data)
    body = await resp.json()

    assert resp.status == 200
    assert isinstance(body, dict)
    assert "text" in body and "ephemeral" in body.get("response_type", "ephemeral")


@pytest.mark.asyncio
async def test_status_reconnect_triggers_recheck(app_client):
    data = {"command": "/status", "user_id": "U123", "text": "reconnect"}

    resp = await post_form(app_client, data)
    body = await resp.json()

    assert resp.status == 200
    assert "reconnected" in body.get("text", "")


@pytest.mark.asyncio
async def test_mcp_api_key_issues_key(app_client, monkeypatch):
    monkeypatch.setenv("MCP_BASE_URL", "http://mcp.test")
    monkeypatch.setenv("MCP_API_KEY", "admin-key")

    import nancy_bot as nancy_mod

    class DummyResponse:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self._payload = payload
            self.text = ""

        @property
        def ok(self):
            return 200 <= self.status_code < 300

        def json(self):
            return self._payload

    def fake_post(url, json=None, headers=None, timeout=None):
        assert url == "http://mcp.test/v2/api-keys/issue"
        assert headers == {"X-API-Key": "admin-key"}
        return DummyResponse(200, {"api_key": "nb_test_key"})

    monkeypatch.setattr(nancy_mod.requests, "post", fake_post)

    data = {"command": "/mcp_api_key", "user_id": "U123", "text": ""}

    resp = await post_form(app_client, data)
    body = await resp.json()

    assert resp.status == 200
    assert "nb_test_key" in body.get("text", "")
