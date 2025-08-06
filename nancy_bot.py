"""
Nancy - A simple Slack bot with RAG capabilities
Built specifically for microlensing assistance without unnecessary complexity
"""
import asyncio
import logging
import os
import json
import urllib.parse
from pathlib import Path
from typing import Dict, Any
from aiohttp import web

# Fix OpenMP issue before importing any ML libraries
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Set Nancy's base directory for all relative paths
NANCY_BASE_DIR = Path(__file__).parent.absolute()
os.environ["NANCY_BASE_DIR"] = str(NANCY_BASE_DIR)

from bot.plugins.rag.rag_service import RAGService
from bot.plugins.llm.llm_service import LLMService
from bot.utils import SlackClient, MessageHandler, InteractiveHandler, ConversationManager

logger = logging.getLogger(__name__)

class NancyBot:
    def __init__(self):
        # Initialize core components
        self.base_dir = NANCY_BASE_DIR
        
        # Initialize Slack client
        self.slack_client = SlackClient(self.base_dir)
        
        # Initialize AI services
        self.rag_service = RAGService(
            embeddings_path="knowledge_base/embeddings/index", 
            config_path="config/repositories.yml"
        )
        self.llm_service = LLMService(rag_service=self.rag_service, debugging=True)
        
        # Initialize handlers
        self.conversation_manager = ConversationManager(self.slack_client)
        self.message_handler = MessageHandler(
            self.slack_client, 
            self.conversation_manager, 
            self.llm_service
        )
        self.interactive_handler = InteractiveHandler(self.slack_client, self.base_dir)
        
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
            # if self.slack_client.signature_verifier and not self.slack_client.signature_verifier.is_valid(body, timestamp, signature):
            #     logger.error("Invalid signature verification")
            #     return web.Response(status=401, text="Invalid signature")
            logger.info("Signature verification temporarily disabled for testing")
            
            # Handle actual events
            if data.get("type") == "event_callback":
                event = data["event"]
                event_type = event.get("type")
                
                logger.info(f"Event received - type: {event_type}, full event: {event}")
                
                if event_type == "app_home_opened":
                    await self.interactive_handler.handle_home_opened(event)
                elif event_type in ["message", "app_mention"]:
                    logger.info(f"Processing message event: {event}")
                    await self.message_handler.process_message(event)
                else:
                    logger.warning(f"Unhandled event type: {event_type}")
                    
            return web.Response(text="OK")
            
        except Exception as e:
            logger.error(f"Error handling event: {e}")
            return web.Response(status=500)
    
    async def handle_interactive(self, request: web.Request) -> web.Response:
        """Handle Slack interactive components (buttons, modals, etc.)"""
        body = await request.text()
        
        try:
            # Interactive payloads come as form data with a 'payload' field
            parsed = urllib.parse.parse_qs(body)
            payload_str = parsed.get('payload', [''])[0]
            
            if not payload_str:
                logger.error("No payload found in interactive request")
                return web.Response(status=400)
            
            payload = json.loads(payload_str)
            logger.info(f"Interactive payload: {payload}")
            
            await self.interactive_handler.handle_interactive_payload(payload)
            
            return web.Response(text="OK")
            
        except Exception as e:
            logger.error(f"Error handling interactive component: {e}")
            return web.Response(status=500)
    
async def create_app() -> web.Application:
    """Create the web application"""
    app = web.Application()
    bot = NancyBot()
    
    app.router.add_post("/slack/events", bot.handle_event)
    app.router.add_post("/slack/interactive", bot.handle_interactive)
    
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
    app = asyncio.run(create_app())
    logger.info("Nancy Bot ready on http://0.0.0.0:3000")
    web.run_app(app, host="0.0.0.0", port=3000)
