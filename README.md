# Roman Galactic Exoplanet Survey - AI Assistant Bot

> AKA: Nancy

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

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
Raw Repositories     →     Chunked Content     →      Embeddings Database
     ↓                            ↓                            ↓
  Git clones       TBD (currently chunking by file)     txtai embeddings
```
1. **Raw Stage**: Original repositories and resources
2. **Chunked Stage**: Semantic chunks ready for AI processing
3. **Embeddings Stage**: Vector database for fast semantic search

## 🛠️ Setup & Installation

### Prerequisites
- Python 3.9 or higher
- Git
- Slack workspace with admin permissions

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd slack-bot
   ```

2. **Install dependencies**
   ```bash
   # Using uv (recommended)
   uv sync
   
   # Or using pip
   pip install -r requirements.txt
   ```

3. **Configure Slack**
   - Create a new Slack app at api.slack.com/apps](https://api.slack.com/apps)
   - Add the following OAuth scopes:
     - `chat:write`
     - `app_mentions:read`
     - `channels:history`
     - `commands`
     - to do: fill in the rest of these, or create a manifest 
   - Copy your Bot Token and App Token

4. **Create configuration**
   Edit/Create `bot/config/.env`:
   ```python
   SLACK_BOT_TOKEN = "xoxb-your-bot-token"
   PLUGINS = ["bot.plugins.llm", "bot.plugins.rag"]
   ```

5. **Build the knowledge base**
   ```bash
   # This will process all microlensing repositories
   python scripts/build_knowledge_base.py
   ```

6**Start the bot**
   ```bash
   python -m bot.main
   ```

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