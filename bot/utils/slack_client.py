"""
Slack Client Utilities
Handles Slack API interactions and client management
"""
import os
import logging
from pathlib import Path
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.signature import SignatureVerifier
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class SlackClient:
    """Manages Slack API client and authentication"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self._load_environment()
        self._init_clients()
        
    def _load_environment(self):
        """Load environment variables from configuration"""
        env_path = self.base_dir / "bot/config/.env"
        load_dotenv(env_path)
        logger.info(f"Loaded environment from {env_path}")
        
    def _init_clients(self):
        """Initialize Slack API clients"""
        # Get tokens from environment with fallbacks for development
        self.bot_token = os.environ.get("SLACK_BOT_TOKEN", "")
        signing_secret = os.environ.get("SLACK_SIGNING_SECRET", "")
        
        if self.bot_token:
            self.client = AsyncWebClient(token=self.bot_token)
            logger.info("Slack client initialized successfully")
        else:
            logger.warning("No SLACK_BOT_TOKEN found - some features will be limited")
            self.client = None
            
        if signing_secret:
            self.signature_verifier = SignatureVerifier(signing_secret)
            logger.info("Slack signature verifier initialized")
        else:
            logger.warning("No SLACK_SIGNING_SECRET found - signature verification disabled")
            self.signature_verifier = None
    
    async def get_bot_user_id(self) -> str:
        """Get the bot's user ID (cached)"""
        if not hasattr(self, '_bot_user_id'):
            if not self.client:
                raise ValueError("Slack client not available")
            auth_result = await self.client.auth_test()
            self._bot_user_id = auth_result["user_id"]
        return self._bot_user_id
    
    def is_available(self) -> bool:
        """Check if Slack client is available"""
        return self.client is not None
    
    async def send_message(self, channel: str, text: str = None, blocks: list = None, thread_ts: str = None):
        """Send a message to Slack"""
        if not self.client:
            logger.error("Cannot send message - no Slack client")
            return None
            
        kwargs = {
            "channel": channel,
            "thread_ts": thread_ts
        }
        
        if text:
            kwargs["text"] = text
        if blocks:
            kwargs["blocks"] = blocks
            
        return await self.client.chat_postMessage(**kwargs)
    
    async def publish_home_view(self, user_id: str, view: dict):
        """Publish a home view for a user"""
        if not self.client:
            logger.error("Cannot publish home view - no Slack client")
            return None
            
        return await self.client.views_publish(user_id=user_id, view=view)
    
    async def views_open(self, trigger_id: str, view: dict):
        """Open a modal dialog"""
        if not self.client:
            logger.error("Cannot open modal - no Slack client")
            return None
            
        return await self.client.views_open(trigger_id=trigger_id, view=view)
