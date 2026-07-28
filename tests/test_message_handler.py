import pytest

from bot.utils.message_handler import MessageHandler


class CallbackLLM:
    def call_llm_with_callback(
        self,
        query,
        callback,
        conversation_history,
        thread_ts,
        user_id,
    ):
        callback("working", False)
        callback("finished", True)


class StalledLLM:
    def call_llm_with_callback(
        self,
        query,
        callback,
        conversation_history,
        thread_ts,
        user_id,
    ):
        import time

        time.sleep(0.2)


@pytest.mark.asyncio
async def test_llm_thread_callbacks_are_delivered():
    handler = MessageHandler(None, None, CallbackLLM())
    delivered = []

    async def send(message, thread_ts, is_final=False, hit_turn_limit=False):
        delivered.append((message, is_final, hit_turn_limit))

    await handler.generate_response_with_updates("query", send, "123.45")

    assert delivered == [
        (":information_source: _Searching knowledge base..._", False, False),
        ("working", False, False),
        ("finished", True, False),
    ]


@pytest.mark.asyncio
async def test_stalled_llm_returns_visible_timeout(monkeypatch):
    monkeypatch.setenv("LLM_RESPONSE_TIMEOUT_SECONDS", "0.05")
    handler = MessageHandler(None, None, StalledLLM())
    delivered = []

    async def send(message, thread_ts, is_final=False, hit_turn_limit=False):
        delivered.append((message, is_final, hit_turn_limit))

    await handler.generate_response_with_updates("query", send, "123.45")

    assert delivered[-1] == (
        "Sorry, the response timed out before Nancy finished processing it.",
        True,
        False,
    )
