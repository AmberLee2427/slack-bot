# AI Agents Guide: Roman Galactic Exoplanet Survey Slack Bot

## MCP Adapter Backend (v0.4.x baseline)

**As of v0.4.x, Nancy uses the MCPRAGAdapter as the *sole* supported RAG backend.**

- All legacy fallback logic and the old RAGService are removed.
- MCP configuration is required for all knowledge-base and RAG features.
- The adapter contract is:
  - `MCPRAGAdapter(base_url: str, api_key: Optional[str] = None)`
  - `search(query: str, limit: int = 5) -> list[dict]`
  - `get_context_for_query(query: str) -> str`
  - `_get_github_url(doc_id: str) -> Optional[str>`
  - `embeddings.database.search(sql: str) -> list[dict]`

**No fallback to legacy RAGService or txtai is available.**

All tests and docs assume MCP only. In this repo, MCP integration tests start a local server on `http://localhost:8123` without `MCP_INTEGRATION_TEST` toggles.
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

## v0.5.0 Implementation Plan

Purpose
-------
`v0.4.x` established the MCP-only architecture and Docker deployment baseline.
`v0.5.0` focuses on beta-readiness, reliability, and clearer operational UX.

Completed in v0.4.x
-------------------
- [x] `MCPRAGAdapter` implemented in `bot/plugins/rag/mcp_adapter.py`
- [x] `LLMService` wired to MCP-only backend in `bot/plugins/llm/llm_service.py`
- [x] Unit tests for adapter behavior in `tests/test_mcp_adapter.py`
- [x] Slash-command tests for `/status` and `/mcp_api_key` in `tests/test_slash_command_handler.py`
- [x] Integration tests auto-start local MCP in `tests/conftest.py`
- [x] `/status` slash command registered in `manifest.json`

Remaining for v0.5.0
--------------------
- [ ] Add RAG health block injection into App Home (`InteractiveHandler.handle_home_opened`)
- [ ] Add periodic MCP `/health` re-check task and refresh App Home on status change
- [ ] Improve reconnect/health diagnostics for operators (timestamps + failure reason history)
- [ ] Validate NancyGPT + Actions with live hosted MCP and document working setup
- [ ] Resolve outstanding MCP tool reliability issues (retrieve/tree/search edge cases)

Testing notes
-------------
- MCP integration tests run against local `http://localhost:8123` via `tests/conftest.py`.
- Slack command tests use form-encoded POSTs to `/slack/commands`.
- Keep `MCP_BASE_URL` and `MCP_API_KEY` configured for local manual testing.
