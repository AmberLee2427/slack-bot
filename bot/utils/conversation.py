"""
Conversation Manager
Handles conversation history and context management
"""
import logging
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class ConversationManager:
    """Manages conversation history and context"""
    
    def __init__(self, slack_client):
        self.slack_client = slack_client
    
    def _is_context_block_message(self, text: str) -> bool:
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

    async def get_conversation_history(self, channel_id: str, thread_ts: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch recent conversation history from Slack.
        Returns a list of messages with user info and timestamps.
        """
        try:
            url = "https://slack.com/api/conversations.history"
            headers = {"Authorization": f"Bearer {self.slack_client.bot_token}"}
            
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
    
    def format_conversation_context(self, conversation_history: List[Dict[str, Any]], query: str) -> str:
        """Format conversation history for LLM context"""
        context_text = ""
        if conversation_history and len(conversation_history) > 1:
            context_text = "\\n\\nRecent conversation context:\\n"
            for msg in conversation_history[-5:]:  # Last 5 messages for context
                if not msg["is_bot"]:
                    context_text += f"User: {msg['text']}\\n"
                else:
                    context_text += f"Assistant: {msg['text']}\\n"
            context_text += "\\nCurrent question: "
        
        return context_text + query
