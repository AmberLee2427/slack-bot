# AI Agents Guide: Roman Galactic Exoplanet Survey Slack Bot

## MCP Adapter Backend (v0.5+)

**As of v0.5, Nancy uses the MCPRAGAdapter as the *sole* supported RAG backend.**

- All legacy fallback logic and the old RAGService are removed.
- MCP configuration is required for all knowledge-base and RAG features.
- The adapter contract is:
  - `MCPRAGAdapter(base_url: str, api_key: Optional[str] = None)`
  - `search(query: str, limit: int = 5) -> list[dict]`
  - `get_context_for_query(query: str) -> str`
  - `_get_github_url(doc_id: str) -> Optional[str>`
  - `embeddings.database.search(sql: str) -> list[dict]`

**No fallback to legacy RAGService or txtai is available.**

All tests and docs assume MCP only. In this repo the MCP integration tests start a local server on `http://localhost:8123`; they no longer use `MCP_INTEGRATION_TEST` toggles.
4.  **Execute Conditional Path**:
    
    -   **If Channel Does NOT Exist**:
        
        -   The bot creates a new private channel using the team name.
            
        -   The bot invites the new user who triggered the workflow into the channel.
            
        -   This user is now the first member of their team in the workspace.
            
    -   **If Channel Already Exists**:
        
        -   The bot simply invites the new user to the existing private channel.
            
---

### User Experience

-   **For Participants**: The process is seamless. A user fills out a form, joins the workspace via a link, and is automatically invited to their private team channel moments later. There's no need to search for channels or wait for a manual invitation.
    
-   **For Admins**: The system is entirely hands-off after the initial setup. It eliminates the manual work of creating channels and managing permissions for dozens of participants, while ensuring team data remains private and secure. The fallback is the original manual process, so there's no risk if the automation fails.
    
### Future Enhancements

-   A slash command (`/team-admin`) for team captains to manage their team (edit name, add/remove members) without needing admin privileges. The bot would handle these requests by updating the Google Sheet and adjusting channel membership.

## Repository Structure

```
slack-bot/
├── ref/                         # Repos for agent context (not installing from source)
│   ├── txtai/                   # Embeddings database and RAG framework
│   ├── nb4llm/                  # ipynb2txt conversion tool
│   ├── nancy-brain/             # Modular RAG service
│   └── slack-machine/           # Slack bot framework
├── knowledge_base/              # Only cached artifacts; pipeline lives in ref/nancy-brain now
├── bot/                         # Bot implementation
│   ├── config/                  # Keys, tokens, cache
│   ├── home/                    # Slack block kit
│   ├── plugins/
│   │   └── llm/                 # llm service, tools, system prompt
│   ├── utils/.                  # Utility/Slack functions and handlers
│   └── __init__.py.             # Slack bot framework
├── scripts/                     # Build and maintenance scripts
├── docs/                        # Documentation
├── tests/                       # Testing scripts and environment
├── pyproject.toml               # Dependencies
├── manifest.json                # Bot configuration settings on Slack
├── .gitignore                   # Git ignore rules (includes knowledge_base/raw)
└── AGENTS.md                    # This file - AI agent guide
```
----------------------------------------------------------
Moved to nancy-brain
----------------------------------------------------------

## Knowledge Base Pipeline

The KB build and RAG implementation now live entirely in the `ref/nancy-brain` submodule (MCP server). This repo does not own txtai or embedding builds; it consumes the MCP server via `MCPRAGAdapter`.

----------------------------------------------------------
----------------------------------------------------------

## Current Integration Expectations (Slack bot)

- RAG: MCP only. `MCP_BASE_URL` must point to the MCP server; adapter is required.
- Tests: integration tests start a local MCP on `http://localhost:8123`; no env toggles required.
- Knowledge base: built/served by `ref/nancy-brain`; this repo should not rebuild embeddings.

## Admin Guide: Rate Limiting Management

### **Configuration**
```bash
# Add to .env file
DAILY_RATE_LIMIT=100  # Default: 100 queries per user per day

# For testing or cost control
DAILY_RATE_LIMIT=50

# To disable (not recommended for production)
DAILY_RATE_LIMIT=0
```

### **Admin Commands**
**System Overview**: Type `@nancy admin stats` or `@nancy rate stats` in any channel
```
📊 Rate Limit Statistics

Daily Limit: 100 queries per user
Active Users: 3

User Breakdown:
✅ <@U12345ABC>: 23/100 (23%)
🟡 <@U67890DEF>: 78/100 (78%)  
🚫 <@U54321GHI>: 100/100 (100%)

Quotas reset at midnight UTC
```

**Status Indicators**:
- ✅ Green: 0-69% usage (healthy)
- 🟡 Yellow: 70-89% usage (moderate)
- ⚠️ Orange: 90-99% usage (high)
- 🚫 Red: 100% usage (quota exceeded)

### **User Experience**
**Personal Stats**: Users can check their own usage with:
- `@nancy my quota`
- `@nancy my stats` 
- `@nancy usage`
- Home page "📊 Check My Usage" button

**When Quota Exceeded**:
```
🚫 Daily Limit Reached

You've used your 100 daily Nancy interactions. 
Your quota resets at midnight UTC.

Need more access? Contact your administrator or try again tomorrow!
```

### **Admin Override Methods**

#### **Method 1: Restart Nancy (Recommended)**
```bash
# Restarts Nancy and resets ALL user quotas instantly
sudo systemctl restart nancy-bot
# OR
docker restart nancy-container
# OR
pkill -f nancy_bot.py && python nancy_bot.py
```
**When to use**: Urgent situations, server maintenance, or when multiple users need resets

#### **Method 2: Adjust Daily Limit**
```bash
# Temporarily increase limit for everyone
export DAILY_RATE_LIMIT=200
# Restart Nancy to apply new limit
```
**When to use**: High-usage days, special events, or testing periods

### **Monitoring and Logging**

**Log Levels**:
- `INFO`: Normal usage tracking
- `WARNING`: Users approaching or hitting limits  
- `ERROR`: Rate limiting system failures

**Key Log Messages**:
```bash
# Normal operation
✅ User U12345ABC rate limit check passed: 23/100 used

# User getting low on quota
⚠️ User U12345ABC has 5 queries remaining today

# User hit limit
🚫 Rate limit exceeded for user U12345ABC: 100/100

# Last allowed query
🟡 User U12345ABC has reached their daily limit: 100/100
```

### **Best Practices**

1. **Start Conservative**: Begin with 50-100 queries per day
2. **Monitor Patterns**: Watch logs for usage trends
3. **Communication**: Inform users about limits upfront
4. **Escalation Path**: Provide clear admin contact info
5. **Regular Review**: Adjust limits based on actual usage

### **Troubleshooting**

**Problem**: User reports they can't ask questions
- Check logs for rate limit messages
- Verify user's quota with `@nancy admin stats`
- If legitimate need, restart Nancy for immediate reset

**Problem**: Rate limiting not working
- Check if `DAILY_RATE_LIMIT` environment variable is set
- Verify Nancy has write permissions for rate limit storage
- Check logs for rate limiter initialization messages

**Problem**: Usage stats showing incorrect data
- Rate limits are stored in memory - restart clears all data
- Quotas reset at midnight UTC (not user's local timezone)
- Keep Cooking feature also counts against quota

## Git Strategy

- KB stuff belongs in the Nancy Brain package.

## Important Notes

- All libraries are modifiable.
- Focus on accuracy and user experience.
- Continuous improvement based on feedback and retrieval quality.

---

## MCP Adapter Refactor Plan (v0.5)

Purpose
-------
Add a small adapter layer so the bot can call a running MCP server (local or remote) using the exact same surface the code expects from the current `RAGService`. This minimizes code changes in `bot/plugins/llm` and allows a staged rollout with a fallback to the existing local RAG implementation.

Quick checklist (hand-off friendly)
----------------------------------
- [x] Create `bot/plugins/rag/mcp_adapter.py` implementing the adapter contract below
- [x] Wire `bot/plugins/llm/llm_service.py` to instantiate `MCPRAGAdapter` when `MCP_BASE_URL` is present
- [ ] Add unit tests: `tests/test_mcp_adapter.py` (mock MCP responses)
- [ ] Add integration/smoke test gated by env var `MCP_INTEGRATION_TEST=true`
- [x] Add `.env` keys to `bot/config/.env.example`: `MCP_BASE_URL`, `MCP_API_KEY`

Additional immediate work (v0.5 - health/status & tests)
-----------------------------------------------
- [ ] Update Slack home view to include a RAG health block showing `LLMService.rag_status` and last-checked time. Implement dynamic injection in `InteractiveHandler.handle_home_opened`.
- [ ] Add a periodic background re-check (best-effort): small async task that polls MCP `/health` every N seconds (configurable), updates `LLMService.rag_status`, and triggers a home-view refresh when status changes.
- [ ] Add unit tests that simulate Slack slash command POSTs to `/slack/commands` (form-encoded). Place tests in `tests/test_slash_command_handler.py` and use aiohttp test utilities to call `NancyBot.handle_command`.
- [ ] Add integration/smoke test gated by env var `MCP_INTEGRATION_TEST=true` which will POST to a running MCP server and validate end-to-end reconnect flow.

Notes on Slack registration and manifest
--------------------------------------
- Add the `/status` slash command to the Slack app manifest (see `manifest.json`), pointing to the bot's `/slack/commands` endpoint. The command should be ephemeral by default and accept an optional `reconnect` argument.

Testing locally
---------------
- To simulate Slack during tests, send an application/x-www-form-urlencoded POST with fields `command`, `user_id`, and optional `text` to `/slack/commands` (the repository tests will cover this).

Priority
--------
1. Unit tests for slash command (fast feedback)
2. Home view health injection and publish (UI visible)
3. Periodic background poll + optional presence/emoji update
4. Integration test gated by env var and manifest changes

Adapter contract (minimal API)
------------------------------
- Class: MCPRAGAdapter(base_url: str, api_key: Optional[str] = None, fallback: Optional[RAGService] = None)
  - search(query: str, limit: int = 5) -> list[dict]
    - returns items: {id: str, text: str, score: float, extension_weight: float, model_score: float, adjusted_score: float}
  - get_context_for_query(query: str) -> str
  - _get_github_url(doc_id: str) -> Optional[str]
  - embeddings.database.search(sql: str) -> list[dict]  # maintains current SQL usage in tools.py
  - Behavior: normalize MCP responses, raise clear exceptions for network/auth issues, and allow optional fallback to local RAG

Files to add / update
---------------------
- Add: `bot/plugins/rag/mcp_adapter.py` (adapter implementation + lightweight `EmbeddingsDB` wrapper)
- Update: `bot/plugins/llm/llm_service.py` (instantiate adapter when configured; keep `rag_service` injection working)
- Update: `bot/plugins/llm/tools.py` tests to mock adapter behavior
- Add tests: `tests/test_mcp_adapter.py`, update existing llm tests to use adapter mocks

Testing and rollout notes
-------------------------
- Unit tests should mock the MCP endpoints and validate that adapter normalizes fields used by `tools.py` and `llm_service.py`.
- Add an env-gated integration test that runs against a dev MCP server (`MCP_INTEGRATION_TEST=true`) — keep it opt-in for CI.
- Default behavior: if `MCP_BASE_URL` unset or adapter fails on startup, fall back to local `RAGService` and log a warning.

Environment variables
---------------------
- `MCP_BASE_URL` — base URL of running MCP server (optional)
- `MCP_API_KEY` — API key / bearer token for MCP (optional)
- `MCP_TIMEOUT` — adapter HTTP timeout in seconds (default 5)

Estimated effort
----------------
- Adapter + unit tests: 0.5 - 1.5 days
- Wiring `llm_service.py` + smoke tests: 0.5 day
- Integration tests + staged rollout validation: 0.5 - 1 day

Handoff pointer
---------------
If you pick this up, begin by implementing `MCPRAGAdapter.search()` and `get_context_for_query()` as mocked endpoints and update `llm_service.py` to instantiate the adapter only when `MCP_BASE_URL` is present. Run unit tests and then enable the integration test if a dev MCP server is available.
