# AI Agents Guide: Roman Galactic Exoplanet Survey Slack Bot

## Project Overview

This repository contains a **RAG-powered Slack bot** designed to support participants in the **Roman Galactic Exoplanet Survey - Project Infrastructure Team data challenge**. The bot serves as an intelligent assistant that can answer questions about microlensing analysis, data challenge procedures, and related tools by leveraging a comprehensive knowledge base of microlensing resources.

> Nancy is pre-release and there is no requirement for maintaining backwards compatanility.

## Current Status (v0.4 - Make Nancy Smarter)

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

### 🚀 **New Requirements (v0.5)**

#### Refactor for separately run RAG service (local or remote)

#### Cull unused depedencies.

## Repository Structure

```
slack-bot/
├── ref/                         # Repos for agent context (not installing from source)
│   ├── txtai/                   # Embeddings database and RAG framework
│   ├── nb4llm/                  # ipynb2txt conversion tool
│   ├── nancy-brain/             # Modular RAG service
│   └── slack-machine/           # Slack bot framework
├── knowledge_base/              # Knowledge base pipeline
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

## Current Status and Next Steps

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
- **Pipeline Modularization**: Refactor scripts into importable package
- **Embedding Model Updates**: Evaluate newer models for improved retrieval
- **Chunking Strategy**: Consider document vs. chunk-level embeddings for very large files

## Development Workflow (v3.0)

1. **Configure sources** in `config/repositories.yml` and `config/articles.yml`
2. **Build knowledge base**: `python scripts/build_knowledge_base.py --category microlens_submit --dirty`
   - Clones/updates repositories  
   - Downloads PDF articles from URLs
   - Converts notebooks via nb4llm (with .nb.txt extension)
   - Extracts PDF text via Tika
   - Creates dual txtai embedding indices (general + code models)
   - Comprehensive failure tracking and pipeline summary
3. **Test queries**: `python scripts/demo_query.py "your question here"`
4. **Deploy bot**: Configure Slack tokens, set dual embedding environment variables, and run Nancy

## Technical Considerations (v3.0)

- **Dual Embedding Models**: Complementary general and code-specific models for comprehensive coverage
- **File Type Intelligence**: Automatic categorization drives optimal model weighting
- **Large Candidate Pools**: 50x search limits enable effective reweighting without compromising accuracy
- **GitHub Integration**: Direct source links enhance user experience and source verification
- **Environment-Driven**: All features controllable via environment variables for deployment flexibility
- **Performance Optimized**: Nancy is "super fast" - large candidate pools don't impact user experience

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

- Track only the embeddings database config, source code, and configuration files.
- Ignore raw data, indexed embeddings, local settings, and model caches.

## Important Notes

- All libraries are modifiable.
- Focus on accuracy and user experience.
- Continuous improvement based on feedback and retrieval quality.

---

This guide reflects the current state of the project as of the latest development cycle. See README.md for user-facing details and scripts/demo_query.py for the latest RAG/LLM workflow. 

## MCP Adapter Refactor Plan

Purpose
-------
Add a small adapter layer so the bot can call a running MCP server (local or remote) using the exact same surface the code expects from the current `RAGService`. This minimizes code changes in `bot/plugins/llm` and allows a staged rollout with a fallback to the existing local RAG implementation.

Quick checklist (hand-off friendly)
----------------------------------
- [ ] Create `bot/plugins/rag/mcp_adapter.py` implementing the adapter contract below
- [ ] Wire `bot/plugins/llm/llm_service.py` to instantiate `MCPRAGAdapter` when `MCP_BASE_URL` is present
- [ ] Add unit tests: `tests/test_mcp_adapter.py` (mock MCP responses)
- [ ] Add integration/smoke test gated by env var `MCP_INTEGRATION_TEST=true`
- [ ] Add `.env` keys to `bot/config/.env.example`: `MCP_BASE_URL`, `MCP_API_KEY`
- [ ] Stage rollout: enable MCP usage with env flag; keep fallback to local `RAGService`

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