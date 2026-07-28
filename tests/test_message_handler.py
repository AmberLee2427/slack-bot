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


class SlowLLM:
    def call_llm_with_callback(
        self,
        query,
        callback,
        conversation_history,
        thread_ts,
        user_id,
    ):
        import time

        time.sleep(0.08)
        callback("finished", True)


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


@pytest.mark.asyncio
async def test_slow_llm_emits_working_heartbeat(monkeypatch):
    monkeypatch.setenv("SLACK_WORKING_UPDATE_SECONDS", "0.02")
    handler = MessageHandler(None, None, SlowLLM())
    delivered = []

    async def send(message, thread_ts, is_final=False, hit_turn_limit=False):
        delivered.append((message, is_final, hit_turn_limit))

    await handler.generate_response_with_updates("query", send, "123.45")

    heartbeats = [
        message
        for message, is_final, _ in delivered
        if not is_final and "Still working" in message
    ]
    assert len(heartbeats) >= 2
    assert delivered[-1] == ("finished", True, False)
