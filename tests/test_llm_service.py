import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from bot.plugins.llm.llm_service import LLMService


class DummyAdapter:
    def __init__(self, base_url: str, api_key: str | None = None):
        self.base_url = base_url
        self.api_key = api_key
        self._docs = [{"id": "doc1", "text": "hello world", "score": 0.9}]
        self.embeddings = SimpleNamespace(database=self)

    # Used by LLMService.update_rag_variables
    def search(self, sql: str):
        return [{"id": row["id"], "text": row["text"]} for row in self._docs]

    # RAG query interface
    def get_context_for_query(self, query: str) -> str:
        return f"context for {query}: {self._docs[0]['text']}"

    def _get_github_url(self, doc_id: str):
        return f"https://example.com/{doc_id}"

    # Adapter search used by tools
    def search_documents(self, query: str, limit: int = 5):
        return self._docs[:limit]

    # Keep the API compatible with existing tests/helpers
    def embeddings_search(self, sql: str):
        return self.search(sql)


class FakeResp:
    def __init__(self, ok: bool = True, status_code: int = 200, text: str = "ok"):
        self.ok = ok
        self.status_code = status_code
        self.text = text


@pytest.fixture(autouse=True)
def _mock_env(monkeypatch, tmp_path):
    """Provide a clean environment and temporary prompt/weights files."""
    monkeypatch.setenv("MCP_BASE_URL", "http://mcp.test")
    monkeypatch.setenv("MCP_API_KEY", "dummy")
    monkeypatch.setenv("NANCY_BASE_DIR", os.fspath(tmp_path))
    prompt_path = tmp_path / "system_prompt.txt"
    prompt_path.write_text("system prompt")
    weights_path = tmp_path / "model_weights.yaml"
    weights_path.write_text("{}")
    return {"prompt": prompt_path, "weights": weights_path}


def test_llm_service_initializes_with_mock_adapter(monkeypatch, _mock_env):
    # Patch MCPRAGAdapter and requests.get to avoid real network calls
    monkeypatch.setattr("bot.plugins.rag.mcp_adapter.MCPRAGAdapter", DummyAdapter)
    monkeypatch.setattr("bot.plugins.llm.llm_service.requests.get", lambda *_, **__: FakeResp())

    llm = LLMService(
        system_prompt=_mock_env["prompt"],
        model_weights_path=_mock_env["weights"],
        debugging=True,
    )

    assert llm.rag_status.get("available") is True
    assert llm.get_initial_context("ping").startswith("context for ping")
    assert llm.all_indexed_files == ["doc1"]
    assert llm.indexed_file_map["doc1"] == "hello world"
