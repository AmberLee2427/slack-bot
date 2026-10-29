"""Verify real authenticated MCP transport, discovery, and a read-only tool call."""

import json
import os

import requests


def main():
    session = requests.Session()
    session.headers.update({
        "X-API-Key": os.environ["MCP_API_KEY"],
        "Accept": "application/json, text/event-stream",
        "MCP-Protocol-Version": "2025-11-25",
    })
    url = "http://127.0.0.1:8000/mcp/"

    def rpc(method, params, request_id):
        response = session.post(url, json={
            "jsonrpc": "2.0", "id": request_id, "method": method, "params": params,
        }, timeout=90)
        response.raise_for_status()
        if response.headers.get("mcp-session-id"):
            session.headers["MCP-Session-Id"] = response.headers["mcp-session-id"]
        if "application/json" in response.headers.get("Content-Type", ""):
            payload = response.json()
        else:
            payload = next(json.loads(line[6:]) for line in response.text.splitlines()
                           if line.startswith("data: "))
        assert "error" not in payload, "MCP returned a protocol error"
        return payload["result"]

    try:
        rpc("initialize", {"protocolVersion": "2025-11-25", "capabilities": {},
                           "clientInfo": {"name": "nancy-update-gate", "version": "1"}}, 1)
        notification = session.post(url, json={"jsonrpc": "2.0",
                                    "method": "notifications/initialized"}, timeout=30)
        notification.raise_for_status()
        tools = rpc("tools/list", {}, 2)["tools"]
        names = {tool["name"] for tool in tools}
        assert {"search_knowledge_base", "retrieve_document_passage", "explore_document_tree"} <= names
        result = rpc("tools/call", {"name": "search_knowledge_base",
                                   "arguments": {"query": "microlensing", "limit": 1}}, 3)
        assert not result.get("isError"), "MCP tool call failed"
        text = "\n".join(block.get("text", "") for block in result.get("content", []))
        assert "score:" in text and "```" in text, "MCP search returned no useful result"
        print("MCP initialization, tool discovery, and search tool call passed")
    finally:
        if "MCP-Session-Id" in session.headers:
            session.delete(url, timeout=15)


if __name__ == "__main__":
    main()
