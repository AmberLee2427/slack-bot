# AI Agents Guide: Roman Galactic Exoplanet Survey Slack Bot

## Project Overview

This repository contains a **RAG-powered Slack bot** designed to support participants in the **Roman Galactic Exoplanet Survey - Project Infrastructure Team data challenge**. The bot serves as an intelligent assistant that can answer questions about microlensing analysis, data challenge procedures, and related tools by leveraging a comprehensive knowledge base of microlensing resources.

> Nancy is pre-release and there is no requirement for maintaining backwards compatanility.

## Current Stable Version (v0.4 - Make Nancy Smarter)

### ✅ **Recently Completed**

#### 1. **Enhanced Context Presentation**
- **Links in System Text**: Replace plain filenames with clickable GitHub links in LLM context
- **Stable GitHub URLs**: Switch from "main" to "master" branch links for better stability
- **Improved User Experience**: Make source attribution more discoverable and actionable

#### 2. **"Keep Cooking" Feature**
- **Interactive Continuation**: Add system message with button allowing Nancy to continue/expand responses
- **User Control**: Let users request deeper analysis or additional perspectives on demand
- **Seamless Flow**: Maintain conversation context while providing optional expansion

#### 3. **Daily Rate Limiting**
- **Per-User Limits**: Implement daily usage quotas to manage API costs and ensure fair access
- **Graceful Degradation**: Informative messages when limits are reached
- **Admin Overrides**: Configurable limits and bypass mechanisms for power users

## 🚀 New Requirements (v0.5)

### ✅ **Testing**

#### 1. Refactor for separately run RAG service (local or remote)

More details below in "Moved to Nancy Brain" section.

#### 2. Cull unused depedencies.

## Future Feature Additions (v0.6 - Nancy the Bouncer)

### Automated Team Onboarding and Private Channel Creation

**Overview**: This feature automates the process of adding new data challenge participants to the workspace and sorting them into private team channels. It uses an external webform to collect team information and a backend process triggered by new user joins to manage channel creation and invitations, ensuring teams are securely separated from the moment they arrive.

---

### Core Components

#### 1\. **External Webform**

-   **Purpose**: To collect team registration details before users join the Slack workspace.
    
-   **Fields**:
    
    -   `Team Name`: The desired name for the team and its private channel.
        
    -   `Team Member Emails`: A list of all emails for team members, including the captain.
        
-   **Implementation**: A simple Google Form or similar service that outputs responses to a Google Sheet. The confirmation message will direct users to the Slack workspace invite link.

#### 2\. **Automation Trigger: New User Joins**

-   **Event Listener**: The bot will listen for the `team_join` event from the Slack Events API.
    
-   **Trigger Action**: When a new user joins the workspace, the bot will immediately initiate the onboarding workflow.
    

#### 3\. **Conditional Onboarding Logic**

The bot's main logic will execute the following steps upon a new user joining:

1.  **Lookup User**: The bot will take the new user's email and look it up in the Google Sheet containing the webform responses.
    
2.  **Find Team**: From the sheet, it will identify the user's assigned **Team Name**.
    
3.  **Check for Existing Channel**: The bot will then search the Slack workspace to see if a private channel corresponding to the **Team Name** (e.g., `#team-data-divas`) already exists.
    
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
├── knowledge_base/              # Knowledge base pipeline (managed by `nancy-brain` in v>0.5)
│   ├── raw/                     # Original repositories and resources
│   │   ├── microlensing_tools/  # Open source microlensing analysis tools
│   │   ├── jupyter_notebooks/   # Microlensing analysis notebooks
│   │   ├── microlens_submit/    # Data challenge submission tool
│   │   ├── general_tools/       # Roman and general astronomy tools
│   │   ├── web_resources/       # Microlensing Source and other web content
│   │   └── journal_articles/    # Microlensing research papers
│   └── embeddings/              # txtai embeddings database
│       ├── embeddings.sqlite    # Vector database (txtai default)
│       ├── config.yml           # txtai configuration
│       └── models/              # Cached embedding models
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

## Data Pipeline (v0.2)

### Stage 1: Raw Resources (`knowledge_base/raw/`)
- **Git repositories**: Cloned microlensing tools, notebooks, documentation sites
- **PDF articles**: Downloaded from journal/arXiv URLs via `config/articles.yml`
- **GitHub Pages sites**: Cloned as repositories (e.g., rges-pit.github.io)
- **Purpose**: Original, unprocessed source material

### Stage 2: Multi-Format Processing
- **Jupyter notebooks** (`.ipynb`) → converted to plain text via `nb4llm` 
- **PDF files** → text extraction via Apache Tika (requires Java 8+)
  - Repository-embedded PDFs automatically discovered and processed
  - Standalone articles downloaded from URLs in `articles.yml`
- **Standard text files** → direct processing (.py, .md, .rst, .yml, etc.)

### Stage 3: Dual Embedding Pipeline
- **General Text Model**: sentence-transformers/all-MiniLM-L6-v2 for documentation and natural language
- **Code-Specific Model**: microsoft/codebert-base for code files and technical content
- **Smart Weighting**: File-type-aware scoring (code: 70% code model, mixed: 50/50, docs: 80% general)
- **Extension-based Weighting**: Configurable via `config/weights.yaml` for relevance optimization
- **Model Weights**: Individual document scoring stored in `config/model_weights.yaml`
- **Unified Search**: Merged dual scoring with comprehensive reweighting pipeline

## Technical Architecture (v0.3)

### Dual Embedding System
- **Two Embedding Indices**: 
  - `knowledge_base/embeddings/index/` - General model for text/docs
  - `knowledge_base/embeddings/code_index/` - Code model for technical content
- **Intelligent Merging**: Weighted mean scoring based on file type detection
- **Large Candidate Pools**: 50x limit for reweighting effectiveness  
- **Environment Configuration**: `USE_DUAL_EMBEDDING=true` and `CODE_EMBEDDING_MODEL=microsoft/codebert-base`

### Search Quality Improvements
- **File Type Categorization**: Automatic detection of code/mixed/docs content
- **Multi-Model Scoring**: Complementary embeddings provide better coverage
- **Advanced Reweighting**: Extension weights + model weights + dual scores
- **GitHub URL Integration**: Direct links to source files included in all results

## Key Components

- **txtai**: Embeddings database for semantic search and RAG
- **slack-machine**: Slack bot framework with plugin system  
- **nb4llm**: Jupyter notebook to plain text converter for improved semantic retrieval
- **Apache Tika** (via tika package): PDF text extraction for journal articles
- **Unified pipeline**: Single build process handles repositories + PDFs + notebooks

----------------------------------------------------------
----------------------------------------------------------

## Previous State

### ✅ **Fully Implemented (v0.3)**
- **Dual Embedding System**: General + code models with intelligent merging
- **Complete PDF Processing**: Both repository-embedded and standalone articles
- **Notebook Conversion**: nb4llm integration preventing duplicates with .nb.txt extension
- **Multi-Source Indexing**: Repositories, PDFs, and GitHub Pages sites
- **Advanced Weighting**: File-type detection, extension weights, model weights
- **Interactive Slack Interface**: Home tab with Block Kit UI and button navigation
- **Failure Tracking**: Comprehensive pipeline monitoring and reporting

### ✅ **Fully Implemented (v0.4)**

- **GitHub Link Integration**: Replace filenames with clickable links in system messages
- **Master Branch URLs**: Switch from `/blob/main/` to `/blob/master/` for stability
- **Implementation**: Modify `get_context_for_query()` and `get_detailed_context()` methods
- **Timeline**: 1-2 hours
- **Button Implementation**: Add "Continue Analysis" button to Nancy's responses
- **Context Preservation**: Maintain conversation state for follow-up expansions
- **Handler Extension**: Extend `InteractiveHandler` with new button action
- **Timeline**: 2-3 hours
- **User Tracking**: Implement per-user daily quota system
- **Storage Backend**: Redis or SQLite for rate limit persistence
- **Graceful Limits**: Informative messages when quotas exceeded
- **Admin Config**: Environment-based limit configuration
- **Timeline**: 3-4 hours

### 🔧 **Technical Debt and Optimizations**

> Now issues for the Nancy Brain package

- ✅ **Pipeline Modularization**: Refactor scripts into importable package
- **Embedding Model Updates**: Evaluate newer models for improved retrieval
- **Chunking Strategy**: Consider document vs. chunk-level embeddings for very large files

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