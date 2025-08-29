import asyncio
import json
import sys
import os
from aiohttp import web
from aiohttp import FormData
import pytest
import pytest_asyncio

# Ensure project root is on sys.path so tests can import nancy_bot
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from nancy_bot import create_app


@pytest_asyncio.fixture
async def app_client(aiohttp_client):
    # create_app is an async function so await it to get the Application
    app = await create_app()
    return await aiohttp_client(app)


async def post_form(client, data: dict):
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    return await client.post('/slack/commands', data=data, headers=headers)


@pytest.mark.asyncio
async def test_status_endpoint_returns_ok(app_client):
    data = {
        'command': '/status',
        'user_id': 'U123',
        'text': ''
    }

    resp = await post_form(app_client, data)
    assert resp.status == 200
    body = await resp.json()
    # Slack expects a JSON object; our handler returns an ephemeral message payload
    assert isinstance(body, dict)
    assert 'text' in body or 'response_type' in body


@pytest.mark.asyncio
async def test_status_reconnect_triggers_recheck(app_client):
    data = {'command': '/status', 'user_id': 'U123', 'text': 'reconnect'}
    resp = await post_form(app_client, data)
    assert resp.status == 200
    body = await resp.json()
    # Should return a plain JSON acknowledgement
    assert isinstance(body, dict)
