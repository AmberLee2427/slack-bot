## 🧪 MCP Integration Tests (auto-start)

Integration tests for the MCP server live in `tests/test_mcp_integration.py` and `tests/test_mcp_passage_retrieval.py`.

How it works:
- `tests/conftest.py` auto-starts the MCP server (from `ref/nancy-brain`) on `http://localhost:8123` before the test session.
- It waits for `/health` to report `ok`; after tests finish, the subprocess is terminated.
- No env flags are required; ensure the KB embeddings/configs exist under `ref/nancy-brain/knowledge_base/embeddings`.

# Roman Galactic Exoplanet Survey - AI Assistant Bot

> AKA: Nancy

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An intelligent Slack bot designed to support participants in the **Roman Galactic Exoplanet Survey - Project Infrastructure Team data challenge**. This bot leverages advanced AI techniques to provide context-aware assistance with microlensing analysis, data challenge procedures, and related tools.

## 📌 Release Status

- Current package version: `0.4.1` (`pyproject.toml`)
- `v0.4.x` baseline is complete: Dockerized bot+MCP deployment, MCP API key auth, MCP-only RAG adapter wiring.
- Next implementation target: `v0.5.0` (beta hardening and production-readiness work).

## 🚢 GitHub Releases

This project publishes releases on GitHub (not PyPI).

- Manual: run the `Release` workflow in Actions and provide a version (for example `0.5.0`).
- Tag-driven: push a tag like `v0.5.0`.
- The workflow validates that `pyproject.toml` version matches the release version before creating the release.

## 🎯 Purpose

The Roman mission will revolutionize our understanding of exoplanets through gravitational microlensing. This bot serves as an AI assistant that can:

- **Answer questions** about microlensing analysis techniques
- **Provide guidance** on data challenge procedures and submission
- **Explain tools** like `microlens-submit` and Roman Research Nexus
- **Share examples** from open-source microlensing analysis tools
- **Reference research** papers and documentation
- **Help with code** and data processing workflows

## 🚀 Features (under active development)

### 🤖 Intelligent Responses
- **Context-aware answers** based on comprehensive microlensing knowledge
- **Citation support** - always provides sources for information
- **Code assistance** with examples from real analysis tools
- **Multi-format responses** - text, code blocks, links, and rich formatting

### 📚 Comprehensive Knowledge Base
The bot has access to:
- **Open-source microlensing tools** and their documentation
- **Jupyter notebooks** demonstrating analysis techniques
- **Data challenge resources** including submission procedures
- **Roman Research Nexus** documentation and usage guides
- **Research papers** and journal articles on microlensing
- **Web resources** from Microlensing Source and related sites

**Note:** In the `v0.4.x` baseline, Nancy already uses `MCPRAGAdapter` as the sole supported RAG backend. Legacy `RAGService`/txtai fallback is not supported in this repo. MCP configuration is required for all knowledge-base features.

### 🔧 Technical Capabilities
- **Semantic search** via MCPRAGAdapter (MCP server required)
- **RAG (Retrieval Augmented Generation)** for accurate responses (MCP only)
- **Slack integration** with rich message formatting
- **Thread support** for extended conversations
- **Slash commands** for quick access to common functions

## 🧪 End-to-End Passage Retrieval Tests

- Coverage in `tests/test_mcp_passage_retrieval.py` (runs with the auto-started MCP server on `localhost:8123`).
- Validates passage retrieval metadata (line ranges, partial/full flag) and GitHub URL propagation.
- Requires the KB artifacts under `ref/nancy-brain/knowledge_base/embeddings`.

## 🏗️ Architecture

- **RAG backend:** MCPRAGAdapter talking to the MCP server in `ref/nancy-brain`.
- **Knowledge base:** Built/maintained in `ref/nancy-brain`; this repo does not build embeddings.
- **Tests:** Auto-start a local MCP server on `http://localhost:8123`.

## Commissioning alerts

Nexus can deliver evaluated, deduplicated commissioning alerts through Nancy:

```http
POST /api/commissioning/alerts
Authorization: Bearer $COMMISSIONING_ALERT_TOKEN
Content-Type: application/json

{
  "alert_id": "detector-temperature-001",
  "severity": "warning",
  "title": "Detector temperature drift",
  "summary": "Median residual exceeded the commissioning threshold.",
  "occurred_at": "2026-08-19T12:00:00Z",
  "dashboard_url": "https://roman.science.stsci.edu/..."
}
```

Set `COMMISSIONING_CHANNEL_ID` to the private Slack channel ID and invite Nancy
to that channel. The endpoint never accepts a destination channel from the
request, so alerts cannot be redirected elsewhere. Supported severities are
`info`, `warning`, `critical`, and `resolved`.

Threshold evaluation, hysteresis, and duplicate suppression belong on Nexus;
Nancy only authenticates, formats, and delivers the alert.

## 🔑 MCP API Keys (nancy-brain)

RGES-PIT Slack members can issue a personal MCP key with `/mcp_api_key`.
The invite-code endpoint is available for users outside that Slack workspace;
keep invite codes in your `.env` (not in git).

```bash
MCP_INVITE_CODES=code1,code2,code3
```

Issue a key:
```bash
curl -X POST https://mcp.rges-pit.com/v2/api-keys/request \
  -H "Content-Type: application/json" \
  -d '{"invite_code":"code1","contact":"you@example.com"}'
```

Use the key:
```bash
curl -H "X-API-Key: <key>" "https://mcp.rges-pit.com/search?query=roman&limit=3"
```

## 🛠️ Setup & Installation

### Docker Deployment (Recommended for Production)

For production deployment with Docker, see **[DOCKER.md](docs/DOCKER.md)** for complete instructions.

**Quick start:**
```bash
./setup-docker.sh
```

This will guide you through:
- Creating `.env` with your secrets
- Building embeddings (if needed)
- Building Docker images
- Starting both MCP server and Slack bot

### Manual Setup (Development)

### Prerequisites
- Python 3.12 or higher
- Git
- Slack workspace with admin permissions
- **Java 8+ (REQUIRED for PDF processing)** - needed for Apache Tika to process journal articles

### Quick Start

1. **Install Java (REQUIRED for PDF processing)**
   ```bash
   # macOS (using Homebrew) - RECOMMENDED
   brew install openjdk
   
   # Ubuntu/Debian
   sudo apt-get install openjdk-11-jdk
   
   # Windows (using Chocolatey)
   choco install openjdk
   
   # Verify installation
   java -version
   ```

2. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd slack-bot
   ```

3. **Set up ngrok for development**
   Nancy needs a public URL for Slack to send events. Install and start ngrok:
   ```bash
   # Install ngrok (if not already installed)
   # macOS: brew install ngrok
   # Or download from https://ngrok.com/download
   
   # Start ngrok tunnel (in a separate terminal)
   ngrok http 3000
   ```

   Then update your Slack app URLs to use the ngrok HTTPS address shown (e.g., https://abc123.ngrok-free.app):
   - Event Subscriptions → Request URL: `https://<ngrok>/slack/events`
   - Interactivity → Request URL: `https://<ngrok>/slack/interactive`
   - Slash commands (if any) → e.g., `https://<ngrok>/slack/commands`

4. **Install dependencies**
   ```bash
   # Using uv (recommended)
   uv sync
   
   # Or using pip
   pip install -e .
   ```

3. **Configure Slack**
   
   The easiest way to set up your Slack app is using the provided manifest:

   **Option A: Use the Provided Manifest (Recommended)**
   1. Go to [api.slack.com/apps](https://api.slack.com/apps)
   2. Click **"Create New App"**
   3. Select **"From an app manifest"**
   4. Choose your workspace
   5. Copy the entire contents of [`manifest.json`](manifest.json) and paste it
   6. **Important**: Update the `request_url` fields in the manifest to match your ngrok URL:
      ```json
      "request_url": "https://YOUR-NGROK-URL.ngrok-free.app/slack/events"
      ```
   7. Click **"Create"** and then **"Install to Workspace"**
   8. Copy your **Bot User OAuth Token** (starts with `xoxb-`)

   **Option B: Manual Setup**
   - Create a new Slack app at [api.slack.com/apps](https://api.slack.com/apps)
   - Add the following OAuth scopes:
     - `app_mentions:read`, `channels:history`, `chat:write`, `channels:read`
     - `files:read`, `groups:history`, `groups:read`, `im:history`, `im:read`, `im:write`
     - `reactions:read`, `links.embed:write`, `links:read`, `reactions:write`
     - `metadata.message:read`, `mpim:history`, `mpim:read`, `users:read`
   - Enable **Event Subscriptions** with these events:
     - `app_home_opened`, `app_mention`, `message.channels`, `message.groups`, `message.im`, `message.mpim`
   - Enable **Interactivity** and **App Home** with Messages Tab
   - Set your request URLs to your ngrok endpoints

4. **Create configuration**
   Edit/Create `bot/config/.env`:
   ```env
   # LLM Configuration
   ANTHROPIC_API_KEY=your-api-key
   CLAUDE_MODEL=claude-3-5-sonnet-latest

   # Nancy Bot Configuration
   SLACK_BOT_TOKEN="xoxb-your-bot-token"
   SLACK_SIGNING_SECRET="your-signing-secret"
   MCP_BASE_URL="http://localhost:8000"
   MCP_API_KEY="your-mcp-api-key"

   # Logging
   LOG_LEVEL=INFO
   DEBUG_LLM=False

   # Optional rate limit
   DAILY_RATE_LIMIT=100
   ```

5. **Build the knowledge base and start the MCP server**
   see `nancy-brain`

7. **Start Nancy**
   ```bash
   # Make sure ngrok is running in another terminal first!
   python nancy_bot.py
   ```

   Nancy will start on port 3000. You should see:
   ```
   Starting Nancy Bot...
   Nancy Bot ready on http://0.0.0.0:3000
   Using MCPRAGAdapter pointing to http://localhost:8000 (health OK)
   ```

### 🚨 Troubleshooting Setup

**"Unable to locate a Java Runtime" or Tika server errors**
- Ensure Java is installed: `brew install openjdk` (macOS)
- Set Java environment variables:
  ```bash
  export JAVA_HOME="/opt/homebrew/opt/openjdk"
  export PATH="/opt/homebrew/opt/openjdk/bin:$PATH"
  ```
- Use the provided `build_with_java.sh` script for automatic setup
- Check the troubleshooting notebook: `knowledge_base_troubleshooting.ipynb`

**"Sending messages to this app has been turned off"**
- Go to your Slack app settings → **App Home**
- Enable **Messages Tab** and **Allow users to send messages**
- Reinstall the app to your workspace

**Nancy doesn't respond to direct messages**
- Check that `message.im` is in your Event Subscriptions
- Verify your ngrok URL is correct in the manifest
- Restart Slack client after app changes

**PDF processing errors (optional feature)**
- Install Java: `brew install openjdk` (macOS) or equivalent
- Verify with: `java -version`
- PDF processing is optional - Nancy works without it, but with reduced knowledge base

## 📖 Usage

### For Data Challenge Participants

The bot responds to mentions and direct messages. Simply ask questions like:

- *"How do I submit my results using microlens-submit?"*
- *What arethe best practices for microlensing light curve analysis?"*
- *"Can you show me an example of using the Roman Research Nexus?"*
- *"What tools are available for microlensing data processing?"*

### For Developers

#### Adding New Knowledge Sources
```bash
# Add a new repository to the knowledge base
python scripts/add_repository.py --repo https://github.com/example/microlensing-tool --name tool_name

# Rebuild the entire knowledge base
python scripts/build_knowledge_base.py --rebuild
```

#### Creating Custom Plugins
```python
from bot.plugins.rag import rag_service
import bot.plugins.llm as llm

class CustomPlugin(MachineBasePlugin):
    @respond_to(rcustom command")
    async def handle_custom(self, msg):
        await msg.say("Custom response!")
```

## 🔧 Configuration

### Environment Variables
- `SLACK_BOT_TOKEN`: Your Slack bot token
- `KNOWLEDGE_BASE_PATH`: Path to knowledge base (default: `knowledge_base/`)
- `LOG_LEVEL`: Logging level (default: `INFO`)

### Knowledge Base Settings
The bot's knowledge base is now managed by the MCP server. All configuration and indexing is handled externally; Nancy connects to the MCP via the MCPRAGAdapter. See the MCP documentation for details.

## 🧪 Development

### Project Structure
```
slack-bot/
├── bot/                    # Bot implementation
│   ├── plugins/           # Slack bot plugins
│   ├── config/           # Configuration files
│   └── utils/            # Utility functions
├── knowledge_base/        # AI knowledge base
├── scripts/              # Build and maintenance scripts
├── docs/                 # Documentation
└── tests/                # Test suite
```

### Running Tests
```bash
# Make sure MCP_BASE_URL is set and the MCP server is running
pytest tests/
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📚 Documentation

- [AGENTS.md](AGENTS.md) - Technical guide for AI agents working on this project
- [API Documentation](docs/api.md) - Bot API reference
- [Plugin Development](docs/plugins.md) - How to create custom plugins
- [Knowledge Base Management](docs/knowledge_base.md) - Managing the AI knowledge base

## 🤝 Support

### For Data Challenge Participants
- Ask questions directly to the bot in your Slack workspace
- Check the [Roman Data Challenge documentation](https://roman.gsfc.nasa.gov/science/RRG_Data_Challenge.html)
- Join the [Roman Community Slack](https://roman.gsfc.nasa.gov/community.html)

### For Developers
- [Open an issue](https://github.com/your-repo/issues) for bugs or feature requests
- Check the [development documentation](docs/development.md)
- Join our [developer discussions](https://github.com/your-repo/discussions)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Roman Space Telescope Team** for the data challenge opportunity
- **Microlensing Community** for open-source tools and resources
- **Slack Machine** framework for the bot infrastructure
- **txtai** for the embeddings and RAG capabilities
- **pyragify** for repository processing

---

**Built with ❤️ for the Roman Galactic Exoplanet Survey community**
