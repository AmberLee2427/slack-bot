"""
Message Handler
Handles message processing and response generation
"""
import asyncio
import logging
import queue
import threading
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
        event_id = f"{event.get('ts', '')}-{event.get('user', '')}-{event.get('text', '')}"
        
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
                
                # Handle admin commands
                if clean_text.lower() in ["rate stats", "quota stats", "admin stats"]:
                    await self._handle_admin_rate_stats(channel, event.get("ts"))
                    return
                
                # Handle personal stats commands
                if clean_text.lower() in ["my stats", "my quota", "usage", "quota"]:
                    await self._handle_personal_stats(channel, user, event.get("ts"))
                    return
                
                # Create a callback for sending intermediate messages
                async def send_message(text: str, thread_ts: str = None, is_final: bool = False, hit_turn_limit: bool = False):
                    if is_final and hit_turn_limit:
                        # Only show "Keep Cooking" button when Nancy actually hit the turn limit
                        blocks = [
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": text
                                }
                            },
                            {
                                "type": "actions",
                                "elements": [
                                    {
                                        "type": "button",
                                        "text": {
                                            "type": "plain_text",
                                            "text": "🍳 Keep Cooking",
                                            "emoji": True
                                        },
                                        "value": "keep_cooking",
                                        "action_id": "btn_keep_cooking",
                                        "style": "primary"
                                    }
                                ]
                            }
                        ]
                        
                        await self.slack_client.send_message(
                            channel=channel,
                            text=text,  # Fallback text for notifications
                            blocks=blocks,
                            thread_ts=thread_ts or event.get("ts")
                        )
                    elif is_final:
                        # Send final response without Keep Cooking button (Nancy finished early)
                        await self.slack_client.send_message(
                            channel=channel,
                            text=text,
                            thread_ts=thread_ts or event.get("ts")
                        )
                    else:
                        # Send system/status messages using Block Kit context
                        blocks = [
                            {
                                "type": "context",
                                "elements": [
                                    {
                                        "type": "mrkdwn",
                                        "text": f"ℹ️ {text}"
                                    }
                                ]
                            }
                        ]
                        await self.slack_client.send_message(
                            channel=channel,
                            blocks=blocks,
                            thread_ts=thread_ts or event.get("ts")
                        )
                
                # Generate response using RAG + LLM with callback
                # First, get conversation history for context
                thread_ts = event.get("thread_ts")  # If this is in a thread
                conversation_history = await self.conversation_manager.get_conversation_history(
                    channel_id=channel, 
                    thread_ts=thread_ts, 
                    limit=10
                )
                
                logger.info(f"Fetched {len(conversation_history)} messages for context")
                if conversation_history:
                    logger.info(f"Conversation history details:")
                    for i, msg in enumerate(conversation_history):
                        logger.info(f"  [{i}] User: {msg.get('user', 'Unknown')}, Text: {msg.get('text', '')[:50]}..., Is_bot: {msg.get('is_bot', False)}")
                    logger.info(f"Sample conversation context: {conversation_history[-1] if conversation_history else 'None'}")
                else:
                    logger.info("No conversation history retrieved")
                
                await self.generate_response_with_updates(
                    clean_text, 
                    send_message, 
                    event.get("ts"),
                    conversation_history,
                    thread_ts,  # Pass thread_ts for context caching
                    user  # Pass user_id for rate limiting
                )
        except Exception as e:
            logger.error(f"Error in process_message: {e}")
    
    async def _handle_admin_rate_stats(self, channel: str, thread_ts: str = None):
        """Handle admin command to show rate limit statistics"""
        try:
            # Get rate limit stats
            all_stats = self.llm_service.rate_limiter.get_all_stats()
            
            if all_stats["total_users"] == 0:
                stats_text = (
                    "📊 *Rate Limit Statistics*\n\n"
                    f"Daily Limit: {all_stats['daily_limit']} queries per user\n"
                    f"Active Users: 0\n\n"
                    "_No users have made queries today._"
                )
            else:
                stats_text = (
                    "📊 *Rate Limit Statistics*\n\n"
                    f"Daily Limit: {all_stats['daily_limit']} queries per user\n"
                    f"Active Users: {all_stats['total_users']}\n\n"
                    "*User Breakdown:*\n"
                )
                
                for user_id, user_stats in all_stats["users"].items():
                    used = user_stats["used_today"]
                    remaining = user_stats["remaining"]
                    percentage = (used / all_stats['daily_limit']) * 100
                    
                    # Get a visual indicator
                    if percentage >= 100:
                        indicator = "🚫"
                    elif percentage >= 90:
                        indicator = "⚠️"
                    elif percentage >= 70:
                        indicator = "🟡"
                    else:
                        indicator = "✅"
                    
                    stats_text += f"{indicator} <@{user_id}>: {used}/{all_stats['daily_limit']} ({percentage:.0f}%)\n"
                
                stats_text += f"\n_Quotas reset at midnight UTC_"
            
            await self.slack_client.send_message(
                channel=channel,
                text=stats_text,
                thread_ts=thread_ts
            )
            
        except Exception as e:
            logger.error(f"Error handling admin rate stats: {e}")
            await self.slack_client.send_message(
                channel=channel,
                text="❌ Error retrieving rate limit statistics.",
                thread_ts=thread_ts
            )
    
    async def _handle_personal_stats(self, channel: str, user_id: str, thread_ts: str = None):
        """Handle user command to check their own rate limit statistics"""
        try:
            # Get user's personal stats
            user_stats = self.llm_service.rate_limiter.get_user_stats(user_id)
            
            used = user_stats["used_today"]
            daily_limit = user_stats["daily_limit"]
            remaining = user_stats["remaining"]
            percentage = (used / daily_limit) * 100 if daily_limit > 0 else 0
            
            # Get a visual indicator and status message
            if percentage >= 100:
                indicator = "🚫"
                status = "Quota Exceeded"
            elif percentage >= 90:
                indicator = "⚠️"
                status = "Almost Full"
            elif percentage >= 70:
                indicator = "🟡"
                status = "Getting High"
            else:
                indicator = "✅"
                status = "Looking Good"
            
            # Create a simple progress bar
            filled = int((percentage / 100) * 10)
            empty = 10 - filled
            progress_bar = "█" * filled + "░" * empty
            
            stats_text = (
                f"{indicator} *Your Nancy Usage Today*\n\n"
                f"*Status:* {status}\n"
                f"*Usage:* {used}/{daily_limit} queries ({percentage:.0f}%)\n"
                f"*Remaining:* {remaining} queries\n\n"
                f"*Progress:* `{progress_bar}` {percentage:.0f}%\n\n"
                f"_Your quota resets at midnight UTC_"
            )
            
            # Add helpful tips based on usage
            if percentage >= 90:
                stats_text += "\n\n💡 _Tip: You're running low! Consider saving complex questions for tomorrow._"
            elif percentage >= 70:
                stats_text += "\n\n💡 _Tip: You're using Nancy quite a bit today. Great questions!_"
            elif percentage <= 10:
                stats_text += "\n\n💡 _Tip: You have plenty of queries left. Feel free to ask detailed questions!_"
            
            await self.slack_client.send_message(
                channel=channel,
                text=stats_text,
                thread_ts=thread_ts
            )
            
        except Exception as e:
            logger.error(f"Error handling personal stats: {e}")
            await self.slack_client.send_message(
                channel=channel,
                text="❌ Error retrieving your usage statistics.",
                thread_ts=thread_ts
            )
    
    async def generate_response_with_updates(self, query: str, send_callback: Callable, original_ts: str, 
                                           conversation_history: List[Dict[str, Any]] = None, 
                                           thread_ts: str = None, user_id: str = None):
        """Generate AI response with intermediate updates and conversation context"""
        try:
            # Initial search status update
            await send_callback(":information_source: _Searching knowledge base..._", original_ts)
            
            # Create a queue to collect messages from the LLM thread
            message_queue = queue.Queue()
            
            # Run the LLM service in a thread pool
            loop = asyncio.get_event_loop()
            
            # Create a callback that the LLM service can use to queue messages
            def sync_callback(message: str, is_final: bool = False, hit_turn_limit: bool = False):
                logger.info(f"Callback received: is_final={is_final}, hit_turn_limit={hit_turn_limit}, message='{message[:100]}...'")
                try:
                    message_queue.put((message, is_final, hit_turn_limit))
                    logger.info("Message queued successfully")
                except Exception as e:
                    logger.error(f"Error queuing message: {e}", exc_info=True)
            
            # Start the LLM processing in a separate thread
            llm_future = loop.run_in_executor(
                None, 
                self.llm_service.call_llm_with_callback, 
                query, 
                sync_callback,
                conversation_history,
                thread_ts,  # Pass thread_ts for context caching
                user_id  # Pass user_id for rate limiting
            )
            
            # Process messages from the queue as they arrive
            while True:
                try:
                    # Check for new messages with a timeout
                    logger.info("Checking for queued messages...")
                    message, is_final, hit_turn_limit = message_queue.get(timeout=0.1)
                    logger.info(f"Processing queued message: is_final={is_final}, hit_turn_limit={hit_turn_limit}")
                    await send_callback(message, original_ts, is_final, hit_turn_limit)
                    logger.info("Message sent successfully")
                    message_queue.task_done()
                except queue.Empty:
                    # Check if the LLM processing is done
                    if llm_future.done():
                        logger.info("LLM processing completed")
                        break
                    continue
                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)
                    
            # Process any remaining messages
            logger.info("Processing any remaining messages...")
            while not message_queue.empty():
                message, is_final, hit_turn_limit = message_queue.get()
                logger.info(f"Processing remaining message: is_final={is_final}, hit_turn_limit={hit_turn_limit}")
                await send_callback(message, original_ts, is_final, hit_turn_limit)
                message_queue.task_done()
            
            # Wait for the LLM to complete
            await llm_future
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            await send_callback("Sorry, I encountered an error processing your request.", original_ts, is_final=True, hit_turn_limit=False)

    async def generate_response(self, query: str) -> str:
        """Generate AI response using RAG + LLM"""
        try:
            # Run the LLM service in a thread pool since it's synchronous but might take time
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self.llm_service.call_llm, query)
            return response
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "Sorry, I encountered an error processing your request."
