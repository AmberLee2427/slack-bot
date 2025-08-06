"""
Nancy - A simple Slack bot with RAG capabilities
Built specifically for microlensing assistance without unnecessary complexity
"""
import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, Any
import queue
import threading
import aiohttp

# Fix OpenMP issue before importing any ML libraries
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Set Nancy's base directory for all relative paths
NANCY_BASE_DIR = Path(__file__).parent.absolute()
os.environ["NANCY_BASE_DIR"] = str(NANCY_BASE_DIR)

from aiohttp import web, ClientSession
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.signature import SignatureVerifier
import json
from dotenv import load_dotenv

from bot.plugins.rag.rag_service import RAGService
from bot.plugins.llm.llm_service import LLMService

# Load environment - now using NANCY_BASE_DIR
env_path = NANCY_BASE_DIR / "bot/config/.env"
load_dotenv(env_path)

logger = logging.getLogger(__name__)

class NancyBot:
    def __init__(self):
        # Get tokens from environment with fallbacks for development
        self.bot_token = os.environ.get("SLACK_BOT_TOKEN", "")
        signing_secret = os.environ.get("SLACK_SIGNING_SECRET", "")
        
        if self.bot_token:
            self.slack_client = AsyncWebClient(token=self.bot_token)
        else:
            logger.warning("No SLACK_BOT_TOKEN found - some features will be limited")
            self.slack_client = None
            
        if signing_secret:
            self.signature_verifier = SignatureVerifier(signing_secret)
        else:
            logger.warning("No SLACK_SIGNING_SECRET found - signature verification disabled")
            self.signature_verifier = None
            
        # Use correct paths for RAG service
        self.rag_service = RAGService(
            embeddings_path="knowledge_base/embeddings/index", 
            config_path="config/repositories.yml"
        )
        # Pass the existing RAG service to LLM service to avoid conflicts
        self.llm_service = LLMService(rag_service=self.rag_service, debugging=True)  # Force debugging on
        
        # Track processed events to prevent duplicates
        self.processed_events = set()
        
    async def handle_event(self, request: web.Request) -> web.Response:
        """Handle Slack events via HTTP"""
        body = await request.text()
        timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
        signature = request.headers.get("X-Slack-Signature", "")
        
        logger.info(f"Received request: body={body[:100]}...")
        logger.info(f"Headers - timestamp: {timestamp}, signature: {signature}")
        
        try:
            data = json.loads(body)
            
            # Handle URL verification challenge - allow this through without signature verification
            if data.get("type") == "url_verification":
                logger.info("Handling URL verification challenge")
                return web.Response(text=data["challenge"])
            
            # For other events, verify request is from Slack (if we have a verifier)
            # Temporarily disable signature verification for testing
            # if self.signature_verifier and not self.signature_verifier.is_valid(body, timestamp, signature):
            #     logger.error("Invalid signature verification")
            #     return web.Response(status=401, text="Invalid signature")
            logger.info("Signature verification temporarily disabled for testing")
            
            # Handle actual events
            if data.get("type") == "event_callback":
                event = data["event"]
                await self.process_message(event)
                
            return web.Response(text="OK")
            
        except Exception as e:
            logger.error(f"Error handling event: {e}")
            return web.Response(status=500)
    
    async def process_message(self, event: Dict[str, Any]):
        """Process incoming messages"""
        logger.info(f"Processing event: {event}")
        
        # Create event ID for deduplication (use timestamp + user + text)
        event_id = f"{event.get('ts', '')}-{event.get('user', '')}-{event.get('text', '')}"
        
        if event_id in self.processed_events:
            logger.info(f"Skipping duplicate event: {event_id}")
            return
            
        self.processed_events.add(event_id)
        
        # Clean up old events (keep only last 100)
        if len(self.processed_events) > 100:
            # Remove oldest 50 events
            events_to_remove = list(self.processed_events)[:50]
            for old_event in events_to_remove:
                self.processed_events.discard(old_event)
        
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
        if not self.slack_client:
            logger.error("No Slack client available")
            return
            
        try:
            bot_user_id = await self.get_bot_user_id()
            
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
                async def send_message(text: str, thread_ts: str = None, is_final: bool = False):
                    if is_final:
                        # Send final response as a regular message
                        await self.slack_client.chat_postMessage(
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
                        await self.slack_client.chat_postMessage(
                            channel=channel,
                            blocks=blocks,
                            thread_ts=thread_ts or event.get("ts")
                        )
                
                # Generate response using RAG + LLM with callback
                # First, get conversation history for context
                thread_ts = event.get("thread_ts")  # If this is in a thread
                conversation_history = await self.get_conversation_history(
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
                    thread_ts  # Pass thread_ts for context caching
                )
        except Exception as e:
            logger.error(f"Error in process_message: {e}")
            return
    
    def _is_context_block_message(self, text):
        """
        Check if a message is a context block (status update) that should be filtered out.
        These are typically messages like ':mag: _Searching for relevant information_'
        """
        if not text:
            return False
            
        # Check for common patterns in context block messages
        text_lower = text.lower().strip()
        
        # Pattern 1: Emoji followed by italic text (underscores)
        if text.startswith(':') and '_' in text:
            return True
            
        # Pattern 2: Common status messages
        status_indicators = [
            '_searching for',
            '_retrieving',
            '_analyzing',
            '_looking through',
            '_checking',
            '_found',
        ]
        
        for indicator in status_indicators:
            if indicator in text_lower:
                return True
                
        return False

    async def get_conversation_history(self, channel_id, thread_ts=None, limit=10):
        """
        Fetch recent conversation history from Slack.
        Returns a list of messages with user info and timestamps.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            url = "https://slack.com/api/conversations.history"
            headers = {"Authorization": f"Bearer {self.bot_token}"}
            
            params = {
                "channel": channel_id,
                "limit": limit,
                "inclusive": "true"  # Slack API expects string, not boolean
            }
            
            # If we're in a thread, get thread replies instead
            if thread_ts:
                url = "https://slack.com/api/conversations.replies"
                params["ts"] = thread_ts
                params["limit"] = limit
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("ok"):
                            messages = data.get("messages", [])
                            # Sort by timestamp (oldest first) and format for context
                            formatted_messages = []
                            for msg in sorted(messages, key=lambda x: float(x.get("ts", 0))):
                                # Skip system messages but keep bot messages (Nancy's responses)
                                if msg.get("subtype") and msg.get("subtype") != "bot_message":
                                    continue
                                    
                                user_id = msg.get("user", "Unknown")
                                text = msg.get("text", "")
                                ts = msg.get("ts", "")
                                
                                # Handle bot messages (Nancy's responses)
                                if msg.get("bot_id"):
                                    # Filter out context block messages (status updates)
                                    # These are messages that start with emoji and have underscores (italics)
                                    if self._is_context_block_message(text):
                                        continue
                                        
                                    bot_profile = msg.get("bot_profile", {})
                                    bot_name = bot_profile.get("name", "Nancy")
                                    formatted_messages.append({
                                        "user": f"Bot_{bot_name}",
                                        "text": text,
                                        "timestamp": ts,
                                        "is_bot": True
                                    })
                                else:
                                    # Regular user message
                                    formatted_messages.append({
                                        "user": user_id,
                                        "text": text,
                                        "timestamp": ts,
                                        "is_bot": False
                                    })
                            
                            logger.info(f"Retrieved {len(formatted_messages)} conversation messages")
                            return formatted_messages[-limit:]  # Return most recent N messages
                        else:
                            logger.error(f"Slack API error: {data.get('error', 'Unknown error')}")
                    else:
                        logger.error(f"HTTP error {response.status} fetching conversation history")
            
        except Exception as e:
            logger.error(f"Error fetching conversation history: {e}", exc_info=True)
            
        return []  # Return empty list on error
    
    async def generate_response_with_updates(self, query: str, send_callback, original_ts: str, conversation_history: list = None, thread_ts: str = None):
        """Generate AI response with intermediate updates and conversation context"""
        try:
            # Create a queue to collect messages from the LLM thread
            import queue
            import threading
            
            message_queue = queue.Queue()
            
            # Run the LLM service in a thread pool
            loop = asyncio.get_event_loop()
            
            # Create a callback that the LLM service can use to queue messages
            def sync_callback(message: str, is_final: bool = False):
                logger.info(f"Callback received: is_final={is_final}, message='{message[:100]}...'")
                try:
                    message_queue.put((message, is_final))
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
                thread_ts  # Pass thread_ts for context caching
            )
            
            # Process messages from the queue as they arrive
            while True:
                try:
                    # Check for new messages with a timeout
                    logger.info("Checking for queued messages...")
                    message, is_final = message_queue.get(timeout=0.1)
                    logger.info(f"Processing queued message: is_final={is_final}")
                    await send_callback(message, original_ts, is_final)
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
                message, is_final = message_queue.get()
                logger.info(f"Processing remaining message: is_final={is_final}")
                await send_callback(message, original_ts)
                message_queue.task_done()
            
            # Wait for the LLM to complete
            await llm_future
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            await send_callback("Sorry, I encountered an error processing your request.")

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
    
    async def get_bot_user_id(self) -> str:
        """Get the bot's user ID"""
        if not hasattr(self, '_bot_user_id'):
            auth_result = await self.slack_client.auth_test()
            self._bot_user_id = auth_result["user_id"]
        return self._bot_user_id

async def create_app() -> web.Application:
    """Create the web application"""
    app = web.Application()
    bot = NancyBot()
    
    app.router.add_post("/slack/events", bot.handle_event)
    
    return app

if __name__ == "__main__":
    # Configure logging to show in terminal
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # This ensures output goes to terminal
        ]
    )
    
    logger.info("Starting Nancy Bot...")
    app = create_app()
    logger.info("Nancy Bot ready on http://0.0.0.0:3000")
    web.run_app(app, host="0.0.0.0", port=3000)
