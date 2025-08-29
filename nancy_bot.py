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
import requests

# Fix OpenMP issue before importing any ML libraries
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Set Nancy's base directory for all relative paths
NANCY_BASE_DIR = Path(__file__).parent.absolute()
os.environ["NANCY_BASE_DIR"] = str(NANCY_BASE_DIR)

from bot.plugins.llm.llm_service import LLMService
from bot.utils import SlackClient, MessageHandler, InteractiveHandler, ConversationManager

logger = logging.getLogger(__name__)

class NancyBot:
    def __init__(self):
        # Initialize core components
        self.base_dir = NANCY_BASE_DIR

        # Initialize Slack client
        self.slack_client = SlackClient(self.base_dir)

        # Initialize AI services (do NOT instantiate heavy in-process RAG here)
        # LLMService will prefer an MCP adapter when MCP_BASE_URL is set, or accept an injected rag_service.
        self.llm_service = LLMService(rag_service=None, debugging=True)

        # Initialize handlers
        self.conversation_manager = ConversationManager(self.slack_client)
        self.message_handler = MessageHandler(
            self.slack_client,
            self.conversation_manager,
            self.llm_service,
        )
        self.interactive_handler = InteractiveHandler(
            self.slack_client,
            self.base_dir,
            self.message_handler,
        )
        
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

    async def handle_command(self, request: web.Request) -> web.Response:
        """Handle Slack slash commands (e.g., /status)"""
        body = await request.text()
        try:
            parsed = urllib.parse.parse_qs(body)
            command = parsed.get('command', [''])[0]
            text = parsed.get('text', [''])[0].strip()
            user_id = parsed.get('user_id', [''])[0]

            logger.info(f"Slash command received: {command} text={text} user={user_id}")

            # Only implement /status for now
            if command == '/status' or command == '/health':
                # If user asked to reconnect, attempt a hot-reconnect
                if text.lower() == 'reconnect':
                    ok, status = self._attempt_reconnect()
                    if ok:
                        resp_text = f"✅ RAG reconnected: {status}"
                    else:
                        resp_text = f"⚠️ Reconnect failed: {status}"
                else:
                    # Report current LLMService.rag_status if available
                    rag_status = getattr(self.llm_service, 'rag_status', None)
                    if rag_status:
                        if rag_status.get('available'):
                            resp_text = f"✅ RAG available (source: {rag_status.get('source')})"
                            # include extra details when present
                            details = {k: v for k, v in rag_status.items() if k not in ('available','source')}
                            if details:
                                resp_text += f"\nDetails: {details}"
                        else:
                            resp_text = f"⚠️ RAG unavailable (source: {rag_status.get('source')})"
                            if 'reason' in rag_status:
                                resp_text += f"\nReason: {rag_status.get('reason')}"
                    else:
                        resp_text = "⚠️ No RAG status available"

                payload = {
                    "response_type": "ephemeral",
                    "text": resp_text
                }
                return web.json_response(payload)

            # Unknown command
            return web.Response(status=404, text="Unknown command")

        except Exception as e:
            logger.error(f"Error handling slash command: {e}")
            return web.Response(status=500)

    def _attempt_reconnect(self) -> tuple[bool, str]:
        """Try to (re)connect the LLMService to an MCP-backed RAG adapter.

        Returns (ok, status_message)
        """
        try:
            MCP_BASE_URL = os.environ.get('MCP_BASE_URL')
            MCP_API_KEY = os.environ.get('MCP_API_KEY')
            if not MCP_BASE_URL:
                # Clear any existing rag and report
                self.llm_service.rag = None
                self.llm_service.rag_status = {"available": False, "source": "none", "reason": "MCP_BASE_URL not set"}
                return False, "MCP_BASE_URL not set"

            from bot.plugins.rag.mcp_adapter import MCPRAGAdapter

            adapter = MCPRAGAdapter(MCP_BASE_URL, api_key=MCP_API_KEY)
            health_url = MCP_BASE_URL.rstrip('/') + '/health'
            headers = {}
            if MCP_API_KEY:
                headers['Authorization'] = f'Bearer {MCP_API_KEY}'
            resp = requests.get(health_url, headers=headers, timeout=5)
            if not resp.ok:
                self.llm_service.rag = None
                self.llm_service.rag_status = {"available": False, "source": "mcp", "reason": f"health {resp.status_code}"}
                return False, f"health {resp.status_code}"

            # Success
            self.llm_service.rag = adapter
            self.llm_service.rag_status = {"available": True, "source": "mcp"}
            try:
                self.llm_service.update_rag_variables()
            except Exception:
                # Best-effort; don't fail reconnect if variable update hiccups
                pass
            return True, "connected via MCP"

        except Exception as e:
            # Ensure LLMService is left in degraded state
            try:
                self.llm_service.rag = None
                self.llm_service.rag_status = {"available": False, "source": "mcp", "reason": str(e)}
            except Exception:
                pass
            return False, str(e)
    
async def create_app() -> web.Application:
    """Create the web application"""
    app = web.Application()
    bot = NancyBot()
    
    app.router.add_post("/slack/events", bot.handle_event)
    app.router.add_post("/slack/interactive", bot.handle_interactive)
    app.router.add_post("/slack/commands", bot.handle_command)
    
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
