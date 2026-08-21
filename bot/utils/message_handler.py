"""
Message Handler
Handles message processing and response generation
"""

import asyncio
import logging
import os
from typing import Dict, Any, List, Callable, Optional

logger = logging.getLogger(__name__)


class MessageHandler:
    """Handles message processing and AI response generation"""

    def __init__(self, slack_client, conversation_manager, llm_service):
        self.slack_client = slack_client
        self.conversation_manager = conversation_manager
        self.llm_service = llm_service

        # Track processed events to prevent duplicates
        self.processed_events = set()

    def is_event_processed(self, event_id: str) -> bool:
        """Check if event has already been processed"""
        return event_id in self.processed_events

    def mark_event_processed(self, event_id: str):
        """Mark event as processed and clean up old events"""
        self.processed_events.add(event_id)

        # Clean up old events (keep only last 100)
        if len(self.processed_events) > 100:
            # Remove oldest 50 events
            events_to_remove = list(self.processed_events)[:50]
            for old_event in events_to_remove:
                self.processed_events.discard(old_event)

    async def process_message(self, event: Dict[str, Any]):
        """Process incoming messages"""
        logger.info(f"Processing event: {event}")

        # Create event ID for deduplication (use timestamp + user + text)
        event_id = (
            f"{event.get('ts', '')}-{event.get('user', '')}-{event.get('text', '')}"
        )

        if self.is_event_processed(event_id):
            logger.info(f"Skipping duplicate event: {event_id}")
            return

        self.mark_event_processed(event_id)

        # Skip bot messages (including our own messages)
        if event.get("subtype") == "bot_message" or event.get("bot_id"):
            logger.info("Skipping bot message")
            return

        # Handle different event types
        if event.get("type") == "app_mention":
            channel = event["channel"]
            text = event.get("text", "")
            user = event["user"]
        elif event.get("type") == "message":
            channel = event["channel"]
            text = event.get("text", "")
            user = event.get("user")
            if not user:  # Some message events don't have user field
                logger.warning(f"Message event missing user field: {event}")
                return
        else:
            logger.info(f"Ignoring event type: {event.get('type')}")
            return

        # Check if bot is mentioned or it's a DM
        if not self.slack_client.is_available():
            logger.error("No Slack client available")
            return

        try:
            bot_user_id = await self.slack_client.get_bot_user_id()

            # Don't process messages from ourselves
            if user == bot_user_id:
                logger.info("Skipping message from bot itself")
                return

            is_mention = f"<@{bot_user_id}>" in text
            is_dm = channel.startswith("D")

            if is_mention or is_dm:
                # Clean the message text
                clean_text = text.replace(f"<@{bot_user_id}>", "").strip()

                # Create a callback for sending intermediate messages
                status_ts = None
                status_updated_at = None
                status_min_display_seconds = float(
                    os.environ.get("SLACK_STATUS_MIN_DISPLAY_SECONDS", "1.5")
                )

                async def clear_status():
                    nonlocal status_ts

                    if not status_ts:
                        return
                    try:
                        await self.slack_client.delete_message(
                            channel=channel,
                            ts=status_ts,
                        )
                    except Exception as exc:
                        logger.warning(
                            "Unable to remove working status %s: %s",
                            status_ts,
                            exc,
                        )
                    status_ts = None

                async def send_message(
                    text: str,
                    thread_ts: str = None,
                    is_final: bool = False,
                    hit_turn_limit: bool = False,
                ):
                    nonlocal status_ts, status_updated_at

                    if is_final and hit_turn_limit:
                        # Only show "Keep Cooking" button when Nancy actually hit the turn limit
                        blocks = [
                            {
                                "type": "section",
                                "text": {"type": "mrkdwn", "text": text},
                            },
                            {
                                "type": "actions",
                                "elements": [
                                    {
                                        "type": "button",
                                        "text": {
                                            "type": "plain_text",
                                            "text": "🍳 Keep Cooking",
                                            "emoji": True,
                                        },
                                        "value": "keep_cooking",
                                        "action_id": "btn_keep_cooking",
                                        "style": "primary",
                                    }
                                ],
                            },
                        ]

                        await self.slack_client.send_message(
                            channel=channel,
                            text=text,  # Fallback text for notifications
                            blocks=blocks,
                            thread_ts=thread_ts or event.get("ts"),
                        )
                    elif is_final:
                        # Send final response without Keep Cooking button (Nancy finished early)
                        await self.slack_client.send_message(
                            channel=channel,
                            text=text,
                            thread_ts=thread_ts or event.get("ts"),
                        )
                    else:
                        # Keep one live status message instead of filling the thread.
                        blocks = [
                            {
                                "type": "context",
                                "elements": [{"type": "mrkdwn", "text": text}],
                            }
                        ]
                        if status_ts:
                            try:
                                if (
                                    status_updated_at is not None
                                    and status_min_display_seconds > 0
                                ):
                                    elapsed = (
                                        asyncio.get_running_loop().time()
                                        - status_updated_at
                                    )
                                    if elapsed < status_min_display_seconds:
                                        await asyncio.sleep(
                                            status_min_display_seconds - elapsed
                                        )
                                await self.slack_client.update_message(
                                    channel=channel,
                                    ts=status_ts,
                                    text=text,
                                    blocks=blocks,
                                )
                                status_updated_at = asyncio.get_running_loop().time()
                                return
                            except Exception as exc:
                                logger.warning(
                                    "Unable to update working status %s: %s",
                                    status_ts,
                                    exc,
                                )
                                status_ts = None

                        response = await self.slack_client.send_message(
                            channel=channel,
                            text=text,
                            blocks=blocks,
                            thread_ts=thread_ts or event.get("ts"),
                        )
                        if response:
                            status_ts = response.get("ts")
                            status_updated_at = asyncio.get_running_loop().time()

                # Generate response using RAG + LLM with callback
                # First, get conversation history for context
                thread_ts = event.get("thread_ts")  # If this is in a thread
                conversation_history = (
                    await self.conversation_manager.get_conversation_history(
                        channel_id=channel, thread_ts=thread_ts, limit=10
                    )
                )

                logger.info(f"Fetched {len(conversation_history)} messages for context")
                if conversation_history:
                    logger.info(f"Conversation history details:")
                    for i, msg in enumerate(conversation_history):
                        logger.info(
                            f"  [{i}] User: {msg.get('user', 'Unknown')}, Text: {msg.get('text', '')[:50]}..., Is_bot: {msg.get('is_bot', False)}"
                        )
                    logger.info(
                        f"Sample conversation context: {conversation_history[-1] if conversation_history else 'None'}"
                    )
                else:
                    logger.info("No conversation history retrieved")

                await self.generate_response_with_updates(
                    clean_text,
                    send_message,
                    event.get("ts"),
                    conversation_history,
                    thread_ts,  # Pass thread_ts for context caching
                    user,  # Pass user_id for rate limiting
                    status_cleanup_callback=clear_status,
                )
        except Exception as e:
            logger.error(f"Error in process_message: {e}")

    async def generate_response_with_updates(
        self,
        query: str,
        send_callback: Callable,
        original_ts: str,
        conversation_history: List[Dict[str, Any]] = None,
        thread_ts: str = None,
        user_id: str = None,
        status_cleanup_callback: Callable = None,
    ):
        """Generate AI response with intermediate updates and conversation context"""
        try:
            # Initial search status update
            await send_callback(
                ":information_source: _Searching knowledge base..._", original_ts
            )

            # Run the LLM service in a thread pool
            loop = asyncio.get_running_loop()
            message_queue = asyncio.Queue()
            response_timeout = float(
                os.environ.get("LLM_RESPONSE_TIMEOUT_SECONDS", "300")
            )
            heartbeat_interval = float(
                os.environ.get("SLACK_WORKING_UPDATE_SECONDS", "15")
            )
            deadline = loop.time() + response_timeout
            started_at = loop.time()
            next_heartbeat = started_at + heartbeat_interval

            # The LLM runs in a worker thread, so enqueue callbacks on the event loop.
            def sync_callback(
                message: str, is_final: bool = False, hit_turn_limit: bool = False
            ):
                logger.info(
                    f"Callback received: is_final={is_final}, hit_turn_limit={hit_turn_limit}, message='{message[:100]}...'"
                )
                try:
                    loop.call_soon_threadsafe(
                        message_queue.put_nowait,
                        (message, is_final, hit_turn_limit),
                    )
                    logger.info("Message queued successfully")
                except RuntimeError as e:
                    logger.error(f"Error queuing message: {e}", exc_info=True)

            # Start the LLM processing in a separate thread
            llm_future = loop.run_in_executor(
                None,
                self.llm_service.call_llm_with_callback,
                query,
                sync_callback,
                conversation_history,
                thread_ts,  # Pass thread_ts for context caching
                user_id,  # Pass user_id for rate limiting
            )

            # Process messages until the worker exits or the request deadline expires.
            while True:
                if llm_future.done() and message_queue.empty():
                    break

                remaining = deadline - loop.time()
                if remaining <= 0:
                    llm_future.cancel()
                    raise asyncio.TimeoutError(
                        f"LLM response exceeded {response_timeout:.0f} seconds"
                    )

                try:
                    wait_timeout = min(1.0, remaining)
                    if heartbeat_interval > 0:
                        wait_timeout = min(
                            wait_timeout,
                            max(0.01, next_heartbeat - loop.time()),
                        )
                    message, is_final, hit_turn_limit = await asyncio.wait_for(
                        message_queue.get(), timeout=wait_timeout
                    )
                    logger.info(
                        f"Processing queued message: is_final={is_final}, hit_turn_limit={hit_turn_limit}"
                    )
                    await send_callback(message, original_ts, is_final, hit_turn_limit)
                    if not is_final and heartbeat_interval > 0:
                        next_heartbeat = loop.time() + heartbeat_interval
                    logger.info("Message sent successfully")
                    message_queue.task_done()
                except asyncio.TimeoutError:
                    if (
                        heartbeat_interval > 0
                        and loop.time() >= next_heartbeat
                        and not llm_future.done()
                    ):
                        elapsed = int(loop.time() - started_at)
                        await send_callback(
                            f":hourglass_flowing_sand: _Still working... {elapsed}s elapsed_",
                            original_ts,
                        )
                        next_heartbeat = loop.time() + heartbeat_interval
                    continue
                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)

            # Process any remaining messages
            logger.info("Processing any remaining messages...")
            while not message_queue.empty():
                message, is_final, hit_turn_limit = await message_queue.get()
                logger.info(
                    f"Processing remaining message: is_final={is_final}, hit_turn_limit={hit_turn_limit}"
                )
                await send_callback(message, original_ts, is_final, hit_turn_limit)
                message_queue.task_done()

            # Wait for the LLM to complete
            await llm_future

        except asyncio.TimeoutError as e:
            logger.error("LLM response timed out: %s", e)
            await send_callback(
                "Sorry, the response timed out before Nancy finished processing it.",
                original_ts,
                is_final=True,
                hit_turn_limit=False,
            )
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            await send_callback(
                "Sorry, I encountered an error processing your request.",
                original_ts,
                is_final=True,
                hit_turn_limit=False,
            )
        finally:
            if status_cleanup_callback:
                try:
                    await status_cleanup_callback()
                except Exception as exc:
                    logger.warning("Unable to clean up working status: %s", exc)

    async def generate_response(self, query: str) -> str:
        """Generate AI response using RAG + LLM"""
        try:
            # Run the LLM service in a thread pool since it's synchronous but might take time
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, self.llm_service.call_llm, query
            )
            return response
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "Sorry, I encountered an error processing your request."
