import os

import types
import sys
from unittest.mock import AsyncMock, Mock

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
slack_signature.SignatureVerifier = type(
    "SignatureVerifier",
    (),
    {
        "__init__": lambda self, *a, **k: None,
        "is_valid": lambda self, body, timestamp, signature: signature == "valid",
    },
)
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
    monkeypatch.setenv("SLACK_ALLOW_UNSIGNED_REQUESTS", "true")
    monkeypatch.setenv("PRIVATE_ALERT_TOKEN", "private-alert-secret")
    monkeypatch.setenv("PRIVATE_ALERT_CHANNEL_ID", "C_PRIVATE_ALERTS")
    monkeypatch.delenv("PRIVATE_ALERT_DRY_RUN", raising=False)
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
async def test_private_alert_posts_only_to_configured_channel(app_client):
    send_message = AsyncMock(return_value={"ok": True, "ts": "123.456"})
    app_client.server.app["bot"].slack_client.send_message = send_message

    resp = await app_client.post(
        "/api/private-alerts",
        json={
            "alert_id": "detector-temperature-001",
            "severity": "warning",
            "title": "Detector temperature drift",
            "summary": "A monitored value exceeded its configured threshold.",
            "occurred_at": "2026-08-19T12:00:00Z",
            "dashboard_url": "https://roman.science.stsci.edu/dashboard",
            "channel": "C_WRONG_CHANNEL",
        },
        headers={"Authorization": "Bearer private-alert-secret"},
    )

    assert resp.status == 200
    assert await resp.json() == {
        "ok": True,
        "dry_run": False,
        "alert_id": "detector-temperature-001",
    }
    assert send_message.await_args.kwargs["channel"] == "C_PRIVATE_ALERTS"


@pytest.mark.asyncio
async def test_private_alert_dry_run_validates_without_calling_slack(
    app_client, monkeypatch
):
    monkeypatch.setenv("PRIVATE_ALERT_DRY_RUN", "true")
    monkeypatch.delenv("PRIVATE_ALERT_CHANNEL_ID", raising=False)
    send_message = AsyncMock(return_value={"ok": True, "ts": "123.456"})
    app_client.server.app["bot"].slack_client.send_message = send_message

    resp = await app_client.post(
        "/api/private-alerts",
        json={
            "alert_id": "ice-thickness-warning-001",
            "severity": "warning",
            "title": "Global ice thickness",
            "summary": "Measured 258 nm; warning criterion is greater than 100 nm.",
            "occurred_at": "2026-08-20T14:08:48Z",
            "dashboard_url": "https://roman.science.stsci.edu/dashboard",
        },
        headers={"Authorization": "Bearer private-alert-secret"},
    )

    assert resp.status == 200
    body = await resp.json()
    assert body["ok"] is True
    assert body["dry_run"] is True
    assert body["alert_id"] == "ice-thickness-warning-001"
    assert body["preview"]["text"].startswith("[WARNING] Global ice thickness")
    assert body["preview"]["blocks"][-1]["elements"][0]["url"].startswith(
        "https://roman.science.stsci.edu/"
    )
    send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_private_alert_rejects_bad_token(app_client):
    resp = await app_client.post(
        "/api/private-alerts",
        json={"alert_id": "a1", "title": "Alert", "summary": "Summary"},
        headers={"Authorization": "Bearer wrong"},
    )

    assert resp.status == 401


@pytest.mark.asyncio
async def test_private_alert_validates_payload(app_client):
    resp = await app_client.post(
        "/api/private-alerts",
        json={"alert_id": "a1", "severity": "apocalypse"},
        headers={"Authorization": "Bearer private-alert-secret"},
    )

    assert resp.status == 400


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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("path", "body", "content_type"),
    [
        ("/slack/events", '{"type":"url_verification","challenge":"test"}', "application/json"),
        ("/slack/interactive", "payload=%7B%7D", "application/x-www-form-urlencoded"),
        ("/slack/commands", "command=%2Fstatus&user_id=U123", "application/x-www-form-urlencoded"),
    ],
)
async def test_slack_routes_reject_unsigned_requests(
    app_client, path, body, content_type
):
    app_client.server.app["bot"].allow_unsigned_slack_requests = False

    resp = await app_client.post(
        path,
        data=body,
        headers={"Content-Type": content_type},
    )

    assert resp.status == 401
    assert await resp.text() == "Invalid Slack signature"


@pytest.mark.asyncio
async def test_slack_route_accepts_valid_signature(app_client):
    bot = app_client.server.app["bot"]
    bot.allow_unsigned_slack_requests = False
    bot.slack_client.signature_verifier = slack_signature.SignatureVerifier("test")

    resp = await app_client.post(
        "/slack/commands",
        data="command=%2Fstatus&user_id=U123",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Slack-Request-Timestamp": "test",
            "X-Slack-Signature": "valid",
        },
    )

    assert resp.status == 200


@pytest.mark.asyncio
async def test_slack_route_rejects_verifier_exception(app_client):
    class BrokenVerifier:
        def is_valid(self, body, timestamp, signature):
            raise ValueError("malformed timestamp")

    bot = app_client.server.app["bot"]
    bot.allow_unsigned_slack_requests = False
    bot.slack_client.signature_verifier = BrokenVerifier()

    resp = await app_client.post(
        "/slack/commands",
        data="command=%2Fstatus&user_id=U123",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Slack-Request-Timestamp": "malformed",
            "X-Slack-Signature": "invalid",
        },
    )

    assert resp.status == 401
