"""
Nancy - A simple Slack bot with RAG capabilities
Built specifically for microlensing assistance without unnecessary complexity
"""
import asyncio
import hmac
import logging
import os
import json
import urllib.parse
from html import escape
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
        self.allow_unsigned_slack_requests = os.environ.get(
            "SLACK_ALLOW_UNSIGNED_REQUESTS", ""
        ).strip().lower() in {"1", "true", "yes"}
        if self.allow_unsigned_slack_requests:
            logger.warning(
                "Unsigned Slack requests are enabled. "
                "Use SLACK_ALLOW_UNSIGNED_REQUESTS only in local tests or CI."
            )

        # Initialize AI services (do NOT instantiate heavy in-process RAG here)
        # LLMService will prefer an MCP adapter when MCP_BASE_URL is set, or accept an injected rag_service.
        self.llm_service = LLMService(
            rag_service=None,
            debugging=None,
            provider_failure_callback=self._notify_provider_failure,
        )

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

    def _notify_provider_failure(self, exc: Exception) -> None:
        """Send one operator DM when Anthropic fails over to the custom model."""
        user_id = os.environ.get("SLACK_ALERT_USER_ID", "").strip()
        token = self.slack_client.bot_token
        if not user_id:
            logger.warning("SLACK_ALERT_USER_ID is not configured; skipping provider alert")
            return
        if not token:
            logger.warning("Slack bot token is unavailable; skipping provider alert")
            return

        status_code = getattr(exc, "status_code", None)
        reason = f"HTTP {status_code}" if status_code else type(exc).__name__
        headers = {"Authorization": f"Bearer {token}"}
        conversation = requests.post(
            "https://slack.com/api/conversations.open",
            headers=headers,
            data={"users": user_id},
            timeout=15,
        )
        conversation.raise_for_status()
        conversation_data = conversation.json()
        if not conversation_data.get("ok"):
            raise RuntimeError(
                f"Slack conversations.open failed: {conversation_data.get('error')}"
            )

        message = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers=headers,
            data={
                "channel": conversation_data["channel"]["id"],
                "text": (
                    ":warning: *Nancy provider failover*\n\n"
                    f"`{os.environ.get('CLAUDE_MODEL', 'Anthropic')}` failed "
                    f"({reason}). Nancy has switched to "
                    f"`{self.llm_service.custom_model}` and remains available.\n\n"
                    "Check `docker logs nancy-slack-bot` for the full error. "
                    "The fallback remains active until Nancy restarts."
                ),
            },
            timeout=15,
        )
        message.raise_for_status()
        message_data = message.json()
        if not message_data.get("ok"):
            raise RuntimeError(
                f"Slack chat.postMessage failed: {message_data.get('error')}"
            )

    def _is_valid_slack_request(self, request: web.Request, body: str) -> bool:
        """Verify a Slack request, failing closed outside explicit test mode."""
        if self.allow_unsigned_slack_requests:
            return True

        verifier = self.slack_client.signature_verifier
        if verifier is None:
            logger.error(
                "Rejecting Slack request because SLACK_SIGNING_SECRET is not configured"
            )
            return False

        timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
        signature = request.headers.get("X-Slack-Signature", "")
        if not timestamp or not signature:
            logger.warning("Rejected Slack request with missing signature headers")
            return False

        try:
            is_valid = verifier.is_valid(body, timestamp, signature)
        except Exception:
            logger.warning(
                "Rejected Slack request because signature verification failed",
                exc_info=True,
            )
            return False

        if not is_valid:
            logger.warning("Rejected Slack request with an invalid signature")
            return False

        return True

    def _spawn(self, coro, *, name: str):
        """Run a coroutine in the background and log exceptions.

        Slack expects a fast HTTP 200 acknowledgement; we should not block request
        handlers on long-running work (LLM calls, Slack API calls, etc.).
        """
        task = asyncio.create_task(coro, name=name)

        def _done(t: asyncio.Task):
            try:
                t.result()
            except Exception as e:
                logger.error("Background task %s failed: %s", name, e, exc_info=True)

        task.add_done_callback(_done)
        return task

    async def handle_private_alert(self, request: web.Request) -> web.Response:
        """Post an authenticated alert to a fixed private channel."""
        if request.content_length is not None and request.content_length > 65536:
            return web.json_response(
                {"ok": False, "error": "request body is too large"}, status=413
            )

        dry_run = os.environ.get("PRIVATE_ALERT_DRY_RUN", "").strip().lower() in {
            "1",
            "true",
            "yes",
        }
        expected_token = os.environ.get("PRIVATE_ALERT_TOKEN", "").strip()
        channel_id = os.environ.get("PRIVATE_ALERT_CHANNEL_ID", "").strip()
        if not expected_token or (not dry_run and not channel_id):
            logger.error("Private alert endpoint is not fully configured")
            return web.json_response(
                {"ok": False, "error": "private alerts are not configured"},
                status=503,
            )

        authorization = request.headers.get("Authorization", "")
        scheme, _, supplied_token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not hmac.compare_digest(
            supplied_token, expected_token
        ):
            return web.json_response(
                {"ok": False, "error": "unauthorized"}, status=401
            )

        try:
            payload = await request.json()
        except (json.JSONDecodeError, ValueError):
            return web.json_response(
                {"ok": False, "error": "request body must be JSON"}, status=400
            )
        if not isinstance(payload, dict):
            return web.json_response(
                {"ok": False, "error": "request body must be an object"}, status=400
            )

        required = ("alert_id", "title", "summary")
        missing = [key for key in required if not str(payload.get(key, "")).strip()]
        if missing:
            return web.json_response(
                {"ok": False, "error": f"missing required fields: {', '.join(missing)}"},
                status=400,
            )

        severity = str(payload.get("severity", "warning")).strip().lower()
        severity_labels = {
            "info": ":information_source: INFO",
            "warning": ":warning: WARNING",
            "critical": ":rotating_light: CRITICAL",
            "resolved": ":white_check_mark: RESOLVED",
        }
        if severity not in severity_labels:
            return web.json_response(
                {
                    "ok": False,
                    "error": "severity must be info, warning, critical, or resolved",
                },
                status=400,
            )

        alert_id = str(payload["alert_id"]).strip()[:128]
        title = escape(str(payload["title"]).strip()[:120], quote=False)
        summary = escape(str(payload["summary"]).strip()[:2500], quote=False)
        occurred_at = escape(
            str(payload.get("occurred_at", "")).strip()[:80], quote=False
        )
        dashboard_url = str(payload.get("dashboard_url", "")).strip()
        if dashboard_url and not dashboard_url.startswith("https://"):
            return web.json_response(
                {"ok": False, "error": "dashboard_url must use https"}, status=400
            )

        context = [f"ID: `{escape(alert_id, quote=False)}`"]
        if occurred_at:
            context.append(f"Observed: {occurred_at}")
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{severity_labels[severity]} — {title}"[:150],
                    "emoji": True,
                },
            },
            {"type": "section", "text": {"type": "mrkdwn", "text": summary}},
            {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": " • ".join(context)}],
            },
        ]
        if dashboard_url:
            blocks.append(
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Open dashboard"},
                            "url": dashboard_url,
                            "action_id": "open_private_alert_dashboard",
                        }
                    ],
                }
            )

        message_text = f"[{severity.upper()}] {title}: {summary}"[:3000]
        if dry_run:
            logger.info("Validated private alert %s in dry-run mode", alert_id)
            return web.json_response(
                {
                    "ok": True,
                    "dry_run": True,
                    "alert_id": alert_id,
                    "preview": {"text": message_text, "blocks": blocks},
                }
            )

        try:
            response = await self.slack_client.send_message(
                channel=channel_id,
                text=message_text,
                blocks=blocks,
            )
        except Exception:
            logger.exception("Failed to deliver private alert %s", alert_id)
            return web.json_response(
                {"ok": False, "error": "Slack delivery failed"}, status=502
            )
        if response is None:
            return web.json_response(
                {"ok": False, "error": "Slack client is unavailable"}, status=503
            )
        return web.json_response(
            {"ok": True, "dry_run": False, "alert_id": alert_id}
        )
        
    async def handle_event(self, request: web.Request) -> web.Response:
        """Handle Slack events via HTTP"""
        body = await request.text()
        if not self._is_valid_slack_request(request, body):
            return web.Response(status=401, text="Invalid Slack signature")
        
        try:
            data = json.loads(body)
            
            # Slack signs URL verification challenges like every other event.
            if data.get("type") == "url_verification":
                logger.info("Handling URL verification challenge")
                return web.Response(text=data["challenge"])
            
            # Handle actual events
            if data.get("type") == "event_callback":
                event = data["event"]
                event_type = event.get("type")
                
                logger.info(f"Event received - type: {event_type}, full event: {event}")
                
                if event_type == "app_home_opened":
                    self._spawn(self.interactive_handler.handle_home_opened(event), name="slack:app_home_opened")
                elif event_type in ["message", "app_mention"]:
                    logger.info(f"Processing message event: {event}")
                    self._spawn(self.message_handler.process_message(event), name=f"slack:{event_type}")
                else:
                    logger.warning(f"Unhandled event type: {event_type}")
                    
            return web.Response(text="OK")
            
        except Exception as e:
            logger.error(f"Error handling event: {e}")
            return web.Response(status=500)
    
    async def handle_interactive(self, request: web.Request) -> web.Response:
        """Handle Slack interactive components (buttons, modals, etc.)"""
        body = await request.text()
        if not self._is_valid_slack_request(request, body):
            return web.Response(status=401, text="Invalid Slack signature")
        
        try:
            # Interactive payloads come as form data with a 'payload' field
            parsed = urllib.parse.parse_qs(body)
            payload_str = parsed.get('payload', [''])[0]
            
            if not payload_str:
                logger.error("No payload found in interactive request")
                return web.Response(status=400)
            
            payload = json.loads(payload_str)
            logger.info(f"Interactive payload: {payload}")
            
            # ACK immediately; process in background to avoid Slack timeouts
            self._spawn(self.interactive_handler.handle_interactive_payload(payload), name="slack:interactive")
            
            return web.Response(text="OK")
            
        except Exception as e:
            logger.error(f"Error handling interactive component: {e}")
            return web.Response(status=500)

    async def handle_command(self, request: web.Request) -> web.Response:
        """Handle Slack slash commands (e.g., /status)"""
        body = await request.text()
        if not self._is_valid_slack_request(request, body):
            return web.Response(status=401, text="Invalid Slack signature")

        try:
            parsed = urllib.parse.parse_qs(body)
            command = parsed.get('command', [''])[0]
            text = parsed.get('text', [''])[0].strip()
            user_id = parsed.get('user_id', [''])[0]

            logger.info(f"Slash command received: {command} text={text} user={user_id}")

            # Status/health check
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

            if command in ("/mcp_api_key", "/mcp-api-key"):
                mcp_base_url = os.environ.get("MCP_BASE_URL", "").strip()
                mcp_admin_key = os.environ.get("MCP_API_KEY", "").strip()
                if not mcp_base_url:
                    resp_text = "⚠️ MCP_BASE_URL is not configured on the bot."
                    return web.json_response({"response_type": "ephemeral", "text": resp_text})
                if not mcp_admin_key:
                    resp_text = "⚠️ MCP_API_KEY is not configured on the bot."
                    return web.json_response({"response_type": "ephemeral", "text": resp_text})

                issue_url = f"{mcp_base_url.rstrip('/')}/v2/api-keys/issue"
                payload = {"contact": f"slack:{user_id}", "label": "slack"}
                try:
                    resp = requests.post(
                        issue_url,
                        json=payload,
                        headers={"X-API-Key": mcp_admin_key},
                        timeout=10,
                    )
                    if resp.ok:
                        data = resp.json()
                        api_key = data.get("api_key")
                        if api_key:
                            resp_text = (
                                "Here is your Nancy Brain MCP API key:\n"
                                f"`{api_key}`\n"
                                "Use it as an `X-API-Key` header."
                            )
                        else:
                            resp_text = "⚠️ Key issuance succeeded but no key was returned."
                    else:
                        detail = ""
                        try:
                            detail = resp.json().get("detail", "")
                        except Exception:
                            detail = resp.text.strip()
                        if detail:
                            resp_text = f"⚠️ Key issuance failed: {detail}"
                        else:
                            resp_text = "⚠️ Key issuance failed."
                except Exception as e:
                    logger.error("Error issuing MCP API key: %s", e, exc_info=True)
                    resp_text = "⚠️ Failed to contact nancy-brain for key issuance."

                return web.json_response({"response_type": "ephemeral", "text": resp_text})

            # Unknown command
            return web.Response(status=404, text="Unknown command")

        except Exception as e:
            logger.error(f"Error handling slash command: {e}")
            return web.Response(status=500)

    async def handle_health(self, request: web.Request) -> web.Response:
        """Lightweight health endpoint for Docker/ops.

        Returns 200 when the HTTP server is up. Includes best-effort RAG status.
        """
        rag_status = getattr(self.llm_service, 'rag_status', None)
        payload = {
            "ok": True,
            "rag": rag_status or {"available": False, "source": "unknown"},
        }
        return web.json_response(payload)

    async def handle_root(self, request: web.Request) -> web.Response:
        return web.Response(text="Nancy Slack Bot")

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
                headers['X-API-Key'] = MCP_API_KEY
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

    # Expose bot instance for optional integrations/tests
    app["bot"] = bot
    
    app.router.add_post("/slack/events", bot.handle_event)
    app.router.add_post("/slack/interactive", bot.handle_interactive)
    app.router.add_post("/slack/commands", bot.handle_command)
    app.router.add_post("/api/private-alerts", bot.handle_private_alert)

    # Ops endpoints
    app.router.add_get("/health", bot.handle_health)
    app.router.add_get("/", bot.handle_root)
    
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
