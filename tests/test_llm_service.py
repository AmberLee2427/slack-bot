import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from bot.plugins.llm import llm_service as llm_module
from bot.plugins.llm.llm_service import LLMService


class DummyAdapter:
    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        timeout: int = 5,
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
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
    monkeypatch.setattr(
        "bot.plugins.llm.llm_service.requests.get", lambda *_, **__: FakeResp()
    )

    llm = LLMService(
        system_prompt=_mock_env["prompt"],
        model_weights_path=_mock_env["weights"],
        debugging=True,
    )

    assert llm.rag_status.get("available") is True
    assert llm.rag.timeout == 90
    assert llm.get_initial_context("ping").startswith("context for ping")
    assert llm.all_indexed_files == ["doc1"]
    assert llm.indexed_file_map["doc1"] == "hello world"


def test_llm_service_uses_configured_mcp_timeout(monkeypatch, _mock_env):
    monkeypatch.setenv("MCP_TIMEOUT_SECONDS", "45")
    monkeypatch.setattr("bot.plugins.rag.mcp_adapter.MCPRAGAdapter", DummyAdapter)
    monkeypatch.setattr(
        "bot.plugins.llm.llm_service.requests.get", lambda *_, **__: FakeResp()
    )

    llm = LLMService(
        system_prompt=_mock_env["prompt"],
        model_weights_path=_mock_env["weights"],
    )

    assert llm.rag.timeout == 45


def _bare_service(custom_enabled: bool = True) -> LLMService:
    llm = object.__new__(LLMService)
    llm.debugging = False
    llm.custom_api_key = "custom-secret" if custom_enabled else None
    llm.custom_model = "agents-a1" if custom_enabled else None
    llm.custom_url = "https://api.example.test/v1" if custom_enabled else ""
    llm.custom_enabled = custom_enabled
    llm.llm_provider = "anthropic"
    llm.force_custom_fallback = False
    llm.provider_failure_callback = None
    llm.rate_limiter = MagicMock()
    return llm


def test_explicit_custom_provider_bypasses_anthropic_quota():
    llm = _bare_service()
    llm.llm_provider = "custom"

    provider, message = llm._provider_for_interaction("U123")

    assert provider == "custom"
    assert message is None
    llm.rate_limiter.check_and_increment.assert_not_called()


def test_quota_exhaustion_selects_custom_provider():
    llm = _bare_service()
    llm.rate_limiter.check_and_increment.return_value = (False, 100, 0)

    provider, message = llm._provider_for_interaction("U123")

    assert provider == "custom"
    assert message is None


def test_quota_exhaustion_without_custom_returns_limit_message():
    llm = _bare_service(custom_enabled=False)
    llm.rate_limiter.check_and_increment.return_value = (False, 100, 0)

    provider, message = llm._provider_for_interaction("U123")

    assert provider is None
    assert "Daily Limit Reached" in message


def test_allowed_interaction_stays_on_anthropic():
    llm = _bare_service()
    llm.rate_limiter.check_and_increment.return_value = (True, 100, 0)

    provider, message = llm._provider_for_interaction("U123")

    assert provider == "anthropic"
    assert message is None


def test_custom_provider_uses_openai_chat_completions(monkeypatch):
    llm = _bare_service()
    response = MagicMock()
    response.json.return_value = {
        "choices": [{"message": {"content": "SEARCH: microlensing limit 5"}}]
    }
    post = MagicMock(return_value=response)
    monkeypatch.setattr(llm_module.requests, "post", post)

    result = llm._query_custom(
        {
            "system": "system prompt",
            "messages": [{"role": "user", "content": "question"}],
        }
    )

    assert result == "SEARCH: microlensing limit 5"
    response.raise_for_status.assert_called_once_with()
    assert post.call_args.args[0] == "https://api.example.test/v1/chat/completions"
    request = post.call_args.kwargs
    assert request["headers"]["Authorization"] == "Bearer custom-secret"
    assert request["json"]["model"] == "agents-a1"
    assert request["json"]["messages"][0] == {
        "role": "system",
        "content": "system prompt",
    }
    assert "custom-secret" not in str(request["json"])


def test_anthropic_usage_error_latches_custom_fallback(monkeypatch):
    class UsageError(Exception):
        status_code = 429

    llm = _bare_service()
    notifier = MagicMock()
    llm.provider_failure_callback = notifier
    anthropic = MagicMock()
    anthropic.messages.create.side_effect = UsageError("rate limit exceeded")
    monkeypatch.setattr(llm_module, "anthropic_client", anthropic)
    custom = MagicMock(return_value="RESPONSE fallback worked [DONE]")
    monkeypatch.setattr(llm, "_query_custom", custom)
    payload = {
        "system": "system prompt",
        "messages": [{"role": "user", "content": "question"}],
    }

    first, _ = llm.querry_llm(payload, turn=0, provider="anthropic")
    second, _ = llm.querry_llm(payload, turn=1, provider="anthropic")

    assert first == "RESPONSE fallback worked [DONE]"
    assert second == first
    assert llm.force_custom_fallback is True
    assert anthropic.messages.create.call_count == 1
    assert custom.call_count == 2
    notifier.assert_called_once()
    assert isinstance(notifier.call_args.args[0], UsageError)


def _initialized_service(monkeypatch, env, max_turns=1):
    monkeypatch.setattr("bot.plugins.rag.mcp_adapter.MCPRAGAdapter", DummyAdapter)
    monkeypatch.setattr(
        "bot.plugins.llm.llm_service.requests.get", lambda *_, **__: FakeResp()
    )
    service = LLMService(
        system_prompt=env["prompt"],
        model_weights_path=env["weights"],
        max_turns=max_turns,
    )
    service.rate_limiter = MagicMock()
    service.rate_limiter.check_and_increment.return_value = (True, 100, 99)
    service.get_initial_context = MagicMock(return_value="retrieved evidence")
    return service


def test_done_without_response_forces_final_synthesis(monkeypatch, _mock_env):
    service = _initialized_service(monkeypatch, _mock_env)
    service.querry_llm = MagicMock(
        side_effect=[
            ("I have enough evidence. [DONE]", "turn one"),
            (
                "[BEGIN RESPONSE]The six columns are documented here.[END RESPONSE] [DONE]",
                "final turn",
            ),
        ]
    )
    callbacks = []

    service.call_llm_with_callback(
        "What are the output columns?",
        lambda message, is_final=False, hit_turn_limit=False: callbacks.append(
            (message, is_final, hit_turn_limit)
        ),
        user_id="U123",
    )

    assert callbacks == [("The six columns are documented here.", True, True)]
    assert service.querry_llm.call_count == 2
    final_payload = service.querry_llm.call_args_list[1].args[0]
    assert "The tool phase is over" in final_payload["messages"][-1]["content"]


def test_response_with_tool_request_is_progress_not_final(monkeypatch, _mock_env):
    service = _initialized_service(monkeypatch, _mock_env, max_turns=2)
    service.search_tool = MagicMock(return_value="RTModel source evidence")
    service.querry_llm = MagicMock(
        side_effect=[
            (
                "[SEARCH: RTModel FinalModels columns limit 8]\n"
                "[BEGIN RESPONSE]Hang on, the initial results were irrelevant. "
                "Let me inspect the RTModel source.[END RESPONSE]",
                "turn one",
            ),
            (
                "[BEGIN RESPONSE]The intervening columns are documented in "
                "the RTModel writer.[END RESPONSE] [DONE]",
                "turn two",
            ),
        ]
    )
    callbacks = []

    service.call_llm_with_callback(
        "What are the RTModel FinalModels columns?",
        lambda message, is_final=False, hit_turn_limit=False: callbacks.append(
            (message, is_final, hit_turn_limit)
        ),
        user_id="U123",
    )

    assert callbacks == [
        (
            "Hang on, the initial results were irrelevant. Let me inspect the "
            "RTModel source.",
            False,
            False,
        ),
        (
            "The intervening columns are documented in the RTModel writer.",
            True,
            False,
        ),
    ]
    assert service.querry_llm.call_count == 2


def test_failed_final_synthesis_reports_failure_not_placeholder(monkeypatch, _mock_env):
    service = _initialized_service(monkeypatch, _mock_env)
    service.querry_llm = MagicMock(
        side_effect=[
            ("I have enough evidence. [DONE]", "turn one"),
            ("Analysis complete - awaiting further instructions", "final turn"),
        ]
    )
    callbacks = []

    service.call_llm_with_callback(
        "What are the output columns?",
        lambda message, is_final=False, hit_turn_limit=False: callbacks.append(
            (message, is_final, hit_turn_limit)
        ),
        user_id="U123",
    )

    assert len(callbacks) == 1
    assert callbacks[0][1:] == (True, False)
    assert "failed to synthesize" in callbacks[0][0]
    assert "awaiting further instructions" not in callbacks[0][0]
