"""
Interactive Handler
Handles Slack interactive components like buttons and modals
"""
import json
import logging
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class InteractiveHandler:
    """Handles Slack interactive components (buttons, modals, etc.)"""
    
    def __init__(self, slack_client, base_dir: Path, message_handler=None):
        self.slack_client = slack_client
        self.base_dir = base_dir
        self.message_handler = message_handler
    
    async def handle_home_opened(self, event: Dict[str, Any]):
        """Handle when user opens Nancy's Home tab"""
        user_id = event["user"]
        
        try:
            # Load home page blocks from JSON file
            home_path = self.base_dir / "bot" / "home" / "blockkit_home.json"
            
            if home_path.exists():
                with open(home_path, 'r') as f:
                    home_blocks = json.load(f)
                    
                # Publish home view
                await self.slack_client.publish_home_view(
                    user_id=user_id,
                    view=home_blocks
                )
                logger.info(f"Published home view for user {user_id}")
            else:
                logger.error(f"Home page template not found at {home_path}")
                
        except Exception as e:
            logger.error(f"Error handling view repos: {e}")

    async def handle_keep_cooking(self, payload: Dict[str, Any]):
        """Handle 'Keep Cooking' button click - continue/expand Nancy's analysis with extended turns"""
        try:
            user_id = payload["user"]["id"]
            channel_id = payload["channel"]["id"]
            message = payload["message"]
            
            # Extract the original message text and context
            thread_ts = message.get("thread_ts") or message.get("ts")
            
            # Send acknowledgment that we're cooking more
            await self.slack_client.send_message(
                channel=channel_id,
                text="🍳 *Keep cooking activated!* Giving Nancy 5 more turns to expand her analysis...",
                thread_ts=thread_ts
            )
            
            # If we have a message handler, trigger expanded analysis with extended turns
            if self.message_handler:
                # Get conversation history for context
                conversation_history = []
                if hasattr(self.message_handler, 'conversation_manager'):
                    conversation_history = await self.message_handler.conversation_manager.get_conversation_context(
                        channel_id, thread_ts, max_messages=10
                    )
                
                # Create callback for sending updates
                async def send_update(text: str, is_final: bool = False):
                    if is_final:
                        # Send final expanded response with another Keep Cooking button
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
                            channel=channel_id,
                            text=text,
                            blocks=blocks,
                            thread_ts=thread_ts
                        )
                    else:
                        # Send intermediate status updates
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
                            channel=channel_id,
                            text=text,
                            blocks=blocks,
                            thread_ts=thread_ts
                        )
                
                # Use the LLM service's new continue method with extended turns
                llm_service = self.message_handler.llm_service
                await llm_service.continue_with_extended_turns(
                    callback_fn=send_update,
                    conversation_history=conversation_history,
                    thread_ts=thread_ts,
                    additional_turns=5  # Give Nancy 5 more turns to cook
                )
                
            else:
                # Fallback if no message handler is connected
                await self.slack_client.send_message(
                    channel=channel_id,
                    text="I'd love to keep cooking, but my expansion capabilities aren't connected yet! 🔧",
                    thread_ts=thread_ts
                )
            
            logger.info(f"Keep cooking with extended turns requested by user {user_id} for message in channel {channel_id}")
            
        except Exception as e:
            logger.error(f"Error handling keep cooking: {e}")

    async def handle_interactive_payload(self, payload: Dict[str, Any]):
        """Handle interactive components (buttons, etc.)"""
        user_id = payload["user"]["id"]
        trigger_id = payload.get("trigger_id")
        
        # Handle button actions
        if payload["type"] == "block_actions":
            action = payload["actions"][0]
            action_id = action["action_id"]
            
            if action_id == "btn_view_docs":
                await self.handle_view_docs(user_id, trigger_id)
            elif action_id == "btn_view_articles":
                await self.handle_view_articles(user_id, trigger_id)
            elif action_id == "btn_view_repos":
                await self.handle_view_repos(user_id, trigger_id)
            elif action_id == "btn_keep_cooking":
                await self.handle_keep_cooking(payload)
            else:
                logger.warning(f"Unknown action_id: {action_id}")

    async def handle_view_docs(self, user_id: str, trigger_id: str):
        """Handle 'Challenge Docs' button click"""
        try:
            # Create a modal or send a message about challenge docs
            modal = {
                "type": "modal",
                "title": {
                    "type": "plain_text",
                    "text": "📋 Challenge Docs"
                },
                "close": {
                    "type": "plain_text",
                    "text": "Close"
                },
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*Roman Galactic Exoplanet Survey - Data Challenge Resources*\n\nI have access to comprehensive documentation about:"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "• **Submission procedures** via `microlens-submit`\n• **Data challenge guidelines** and requirements\n• **Analysis workflows** and best practices\n• **Technical specifications** for Roman telescope\n• **Tutorial notebooks** for microlensing analysis"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "💬 *Just ask me anything!* Try questions like:\n• \"How do I submit my results?\"\n• \"What are the data challenge requirements?\"\n• \"Show me Roman telescope specifications\""
                        }
                    }
                ]
            }
            
            await self.slack_client.views_open(
                trigger_id=trigger_id,
                view=modal
            )
            
        except Exception as e:
            logger.error(f"Error in handle_view_docs: {e}")

    async def handle_view_articles(self, user_id: str, trigger_id: str):
        """Handle 'Research Articles' button click"""
        try:
            modal = {
                "type": "modal", 
                "title": {
                    "type": "plain_text",
                    "text": "📚 Articles"
                },
                "close": {
                    "type": "plain_text",
                    "text": "Close"
                },
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*Microlensing Research Papers in My Knowledge Base*\n\nI can help you with content from:"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "• **Foundation papers** (Paczynski 1986, Gould 1992)\n• **Binary lens theory** (Mao & Paczynski 1991)\n• **Planet detection** (Gould & Loeb 1992)\n• **Survey predictions** (Penny et al. 2019)\n• **Review articles** (Gaudi 2012, Mao 2012)\n• **Roman mission reports** (Spergel et al. 2015)"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "🔍 *Ask me about any research topic!*\n• \"Explain gravitational microlensing theory\"\n• \"What did Penny et al predict for Roman?\"\n• \"Compare different microlensing surveys\""
                        }
                    }
                ]
            }
            
            await self.slack_client.views_open(
                trigger_id=trigger_id,
                view=modal
            )
            
        except Exception as e:
            logger.error(f"Error in handle_view_articles: {e}")

    async def handle_view_repos(self, user_id: str, trigger_id: str):
        """Handle 'Code Repositories' button click"""
        try:
            modal = {
                "type": "modal",
                "title": {
                    "type": "plain_text",
                    "text": "💻 Code Repos"
                },
                "close": {
                    "type": "plain_text",
                    "text": "Close"
                },
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*Open Source Tools & Code in My Knowledge Base*\n\nI can help with documentation and examples from:"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "• **Analysis tools** (pyLIMA, MulensModel, VBMicrolensing)\n• **Roman simulators** (romanisim, gulls, PopSyCLE)\n• **Statistical tools** (emcee, dynesty, corner)\n• **Tutorial notebooks** (microlensing-tutorials)\n• **Data challenge tools** (microlens-submit)\n• **Roman pipeline** (romancal, roman_tools)"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "🛠️ *Get coding help and examples!*\n• \"How do I use pyLIMA for fitting?\"\n• \"Show me MulensModel examples\"\n• \"What's the difference between analysis tools?\""
                        }
                    }
                ]
            }
            
            await self.slack_client.views_open(
                trigger_id=trigger_id,
                view=modal
            )
            
        except Exception as e:
            logger.error(f"Error in handle_view_repos: {e}")
