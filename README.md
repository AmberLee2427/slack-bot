# Roman Galactic Exoplanet Survey - AI Assistant Bot

> AKA: Nancy

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](h5. **Create configuration**
   Create `bot/config/.env` with your tokens:
   ```env
   # Slack Configuration
   SLACK_BOT_TOKEN=xoxb-your-bot-token-from-step-4
   SLACK_SIGNING_SECRET=your-signing-secret-from-slack-app
   
   # LLM Configuration  
   GEMINI_API_KEY=your-gemini-api-key
   GEMINI_MODEL=gemini-2.0-flash-lite
   
   # Logging
   LOG_LEVEL=INFO
   DEBUG_LLM=True
   
   # Knowledge Base
   KNOWLEDGE_BASE_PATH=knowledge_base/embeddings
   ```/opensource.org/licenses/MIT)

An intelligent Slack bot designed to support participants in the **Roman Galactic Exoplanet Survey - Project Infrastructure Team data challenge**. This bot leverages advanced AI techniques to provide context-aware assistance with microlensing analysis, data challenge procedures, and related tools.

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

### 🔧 Technical Capabilities
- **Semantic search** using advanced embeddings
- **RAG (Retrieval Augmented Generation)** for accurate responses
- **Slack integration** with rich message formatting
- **Thread support** for extended conversations
- **Slash commands** for quick access to common functions

## 🏗️ Architecture

This bot is built using a sophisticated three-stage data pipeline:

```
Raw Sources          →     Multi-Format Processing     →      Unified Embeddings
     ↓                            ↓                            ↓
Git repositories              nb4llm (notebooks)            txtai vector database
PDF articles                 Apache Tika (PDFs)                    ↓
GitHub Pages sites           Direct text (code/docs)          Semantic search
```
1. **Raw Stage**: Git repositories, downloaded PDFs, documentation sites
2. **Processing Stage**: Format-specific conversion (nb4llm, Tika, direct text)
3. **Embeddings Stage**: Unified txtai vector database for fast semantic search

## 🛠️ Setup & Installation

### Prerequisites
- Python 3.12 or higher
- Git
- Slack workspace with admin permissions
- **Java 8+ (for PDF processing)** - required for processing journal articles

### Quick Start

1. **Install Java (for PDF processing)**
   ```bash
   # macOS (using Homebrew)
   brew install openjdk
   
   # Ubuntu/Debian
   sudo apt-get install openjdk-11-jdk
   
   # Windows (using Chocolatey)
   choco install openjdk
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
   
   # Copy the public URL (e.g., https://abc123.ngrok-free.app)
   ```

4. **Install dependencies**
   ```bash
   # Using uv (recommended)
   uv sync
   
   # Or using pip
   pip install -e .
   
   # For PDF processing capabilities (optional)
   pip install -e .[pdf]
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
   ```python
   SLACK_BOT_TOKEN = "xoxb-your-bot-token"
   PLUGINS = ["bot.plugins.llm", "bot.plugins.rag"]
   ```

5. **Build the knowledge base**
   ```bash
   # Process repositories only (no PDF processing)
   python scripts/build_knowledge_base.py --config config/repositories.yml
   
   # Process both repositories and PDF articles (requires Java + Tika)
   python scripts/build_knowledge_base.py --config config/repositories.yml --articles-config config/articles.yml
   ```

7. **Start Nancy**
   ```bash
   # Make sure ngrok is running in another terminal first!
   python nancy_bot.py
   ```

   Nancy will start on port 3000. You should see:
   ```
   Starting Nancy Bot...
   Nancy Bot ready on http://0.0.0.0:3000
   Loading embeddings from knowledge_base/embeddings/index
   Embeddings loaded successfully
   ```

### 🚨 Troubleshooting Setup

**"Sending messages to this app has been turned off"**
- Go to your Slack app settings → **App Home**
- Enable **Messages Tab** and **Allow users to send messages**
- Reinstall the app to your workspace

**Nancy doesn't respond to direct messages**
- Check that `message.im` is in your Event Subscriptions
- Verify your ngrok URL is correct in the manifest
- Restart Slack client after app changes

**Java/PDF processing errors**
- Install Java: `brew install openjdk` (macOS) or equivalent
- Verify with: `java -version`
- PDF processing is optional - Nancy works without it

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
The bot's knowledge base can be customized in `config/knowledge_base.yml`:
```yaml
repositories:
  - name: microlens-submit
    url: https://github.com/roman-telescope/microlens-submit
    type: submission_tool
  
  - name: example-analysis-tool
    url: https://github.com/example/microlensing-tool
    type: analysis_tool
```

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