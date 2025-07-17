# AI Agents Guide: Roman Galactic Exoplanet Survey Slack Bot

## Project Overview

This repository contains a **RAG-powered Slack bot** designed to support participants in the **Roman Galactic Exoplanet Survey - Project Infrastructure Team data challenge**. The bot will serve as an intelligent assistant that can answer questions about microlensing analysis, data challenge procedures, and related tools by leveraging a comprehensive knowledge base of microlensing resources.

## Repository Structure

```
slack-bot/
├── src/
│   ├── txtai/                    # Embeddings database and RAG framework
│   │   ├── src/txtai/           # Core txtai library (modifiable)
│   │   ├── examples/            # txtai examples and tutorials
│   │   └── docs/                # txtai documentation
│   ├── pyragify/                # Repository processing tool
│   │   ├── src/pyragify/        # Core pyragify library (modifiable)
│   │   └── config.yaml          # Processing configuration
│   └── slack-machine/           # Slack bot framework
│       ├── src/machine/         # Core slack-machine library (modifiable)
│       ├── docs/                # Framework documentation
│       ├── tests/               # Framework tests
│       └── pyproject.toml       # Framework dependencies
├── knowledge_base/              # Three-stage data pipeline
│   ├── raw/                     # Original repositories and resources
│   │   ├── microlensing_tools/  # Open source microlensing analysis tools
│   │   ├── jupyter_notebooks/   # Microlensing analysis notebooks
│   │   ├── microlens_submit/    # Data challenge submission tool
│   │   ├── roman_research_nexus/ # Roman Research Nexus documentation
│   │   ├── web_resources/       # Microlensing Source and other web content
│   │   └── journal_articles/    # Microlensing research papers
│   ├── chunked/                 # Output from pyragify processing
│   │   ├── microlensing_tools/  # Chunked Python code and docs
│   │   ├── jupyter_notebooks/   # Chunked notebooks and examples
│   │   ├── microlens_submit/    # Chunked submission tool docs
│   │   ├── roman_research_nexus/ # Chunked RRN documentation
│   │   ├── web_resources/       # Chunked web content
│   │   └── journal_articles/    # Chunked research papers
│   └── embeddings/              # txtai embeddings database
│       ├── embeddings.sqlite    # Vector database (txtai default)
│       ├── config.yml           # txtai configuration
│       └── models/              # Cached embedding models
├── bot/                         # Your bot implementation
│   ├── plugins/                 # Slack bot plugins
│   │   ├── rag_plugin.py        # RAG functionality
│   │   ├── microlensing_plugin.py # Microlensing-specific responses
│   │   └── challenge_plugin.py  # Data challenge procedures
│   ├── config/                  # Bot configuration
│   └── utils/                   # Utility functions
├── docs/                        # Your bot documentation
├── pyproject.toml               # Your bot dependencies
├── local_settings.py            # Bot configuration (not in git)
├── .gitignore                   # Git ignore rules (includes knowledge_base/raw and knowledge_base/chunked)
└── AGENTS.md                    # This file - AI agent guide
```

## Data Pipeline

### Stage 1: Raw Resources (`knowledge_base/raw/`)
- **Source repositories**: Git clones of microlensing tools, notebooks, etc.
- **Web content**: Scraped or downloaded resources from Microlensing Source
- **Documents**: PDFs, markdown files, etc.
- **Purpose**: Original, unprocessed source material

### Stage 2Chunked Content (`knowledge_base/chunked/`)
- **Processed by**: pyragify
- **Output**: Semantic chunks of code, documentation, and text
- **Format**: `.txt` files organized by content type (python/, markdown/, other/)
- **Purpose**: LLM-friendly chunks ready for embedding

### Stage 3: Embeddings Database (`knowledge_base/embeddings/`)
- **Processed by**: txtai
- **Output**: Vector embeddings and searchable database
- **Format**: SQLite database with vector indexes
- **Purpose**: Fast semantic search and retrieval

## Key Components

###1. Core Libraries (Modifiable)
- **txtai**: Embeddings database for semantic search and RAG
- **pyragify**: Processes repositories into LLM-friendly chunks
- **slack-machine**: Slack bot framework with plugin system

###2ledge Base Sources
The bot will ingest and process the following resources:

#### Microlensing Analysis Tools
- Open source microlensing analysis software repositories
- Code examples and documentation
- Best practices for microlensing data processing

#### Educational Resources
- Jupyter notebooks demonstrating microlensing analysis
- Tutorial materials and examples
- Data processing workflows

#### Data Challenge Specific
- `microlens-submit` repository (submission tool)
- Roman Research Nexus documentation and usage guides
- Challenge rules, procedures, and requirements

#### Research Context
- Microlensing Source web resources
- Journal articles on microlensing techniques
- Recent research papers and methodologies

### 3. Bot Architecture

#### RAG Pipeline
1. **Repository Processing**: Use pyragify to chunk repositories into semantic units
2. **Embedding Generation**: Use txtai to create embeddings for all chunks
3. **Query Processing**: Convert user questions to embeddings
4. **Semantic Search**: Find most relevant chunks from knowledge base
5. **Response Generation**: Use retrieved context to generate accurate responses

#### Slack Integration
- **Plugin System**: Modular plugins for different functionalities
- **Event Handling**: Respond to messages, slash commands, and interactions
- **Thread Support**: Maintain conversation context in threads
- **Rich Responses**: Support for blocks, attachments, and interactive elements

## Development Workflow

### 1. Repository Setup
```bash
# Clone and setup
git clone <your-repo>
cd slack-bot

# Install dependencies (when you create pyproject.toml)
uv sync
```

###2ge Base Population
```bash
# Stage 1: Clone raw repositories
git clone https://github.com/example/microlensing-tool knowledge_base/raw/microlensing_tools/
git clone https://github.com/example/microlens-submit knowledge_base/raw/microlens_submit/
# ... repeat for all repositories

# Stage 2Process with pyragify
python -m pyragify --repo-path knowledge_base/raw/microlensing_tools --output-dir knowledge_base/chunked/microlensing_tools
python -m pyragify --repo-path knowledge_base/raw/microlens_submit --output-dir knowledge_base/chunked/microlens_submit
# ... repeat for all repositories

# Stage 3: Create embeddings with txtai
python -c 
import txtai
embeddings = txtai.Embeddings()
embeddings.index([open(f).read() for f in glob.glob(knowledge_base/chunked/**/*.txt', recursive=true])
embeddings.save('knowledge_base/embeddings/')
```

###3. Bot Development
```python
# Example plugin structure
from machine.plugins.base import MachineBasePlugin
from txtai import Embeddings

class MicrolensingRAGPlugin(MachineBasePlugin):
    def __init__(self):
        self.embeddings = Embeddings()
        # Load the embeddings database
        self.embeddings.load('knowledge_base/embeddings/')
    
    async def handle_microlensing_question(self, msg, question):
        # RAG pipeline: search -> retrieve -> respond
        results = self.embeddings.search(question, 5
        context = self.build_context(results)
        response = self.generate_response(question, context)
        await msg.say(response)
```

## Key Features for Data Challenge Support

### 1. Context-Aware Responses
- Understand microlensing terminology and concepts
- Provide accurate information about data challenge procedures
- Reference specific tools and their usage

### 2. Code Assistance
- Help with microlensing analysis code
- Explain data processing workflows
- Provide examples from ingested repositories

### 3. Challenge Guidance
- Answer questions about submission procedures
- Explain Roman Research Nexus usage
- Provide links to relevant resources

### 4. Research Support
- Reference relevant journal articles
- Explain microlensing techniques
- Connect users to appropriate resources

## Technical Considerations

### 1. Knowledgege Base Management
- **Incremental Updates**: Process new repositories as they're added
- **Version Control**: Track changes to knowledge base
- **Quality Control**: Ensure processed content is accurate and relevant
- **Git Strategy**: Only commit embeddings database, ignore raw and chunked data

### 2. Response Quality
- **Citation Support**: Provide sources for responses
- **Confidence Scoring**: Indicate when responses are uncertain
- **Context Preservation**: Maintain conversation history

### 3. Performance
- **Embedding Caching**: Cache embeddings for faster responses
- **Search Optimization**: Optimize semantic search for large knowledge bases
- **Response Time**: Ensure responses are generated quickly

### 4. Quality Control

Ensuring the accuracy, relevance, and reliability of the bot's responses is critical for user trust and effective challenge support. Quality control will be systematically applied across the entire RAG pipeline.

#### 4.1. Raw Data Vetting (`knowledge_base/raw/`)

* **Source Reliability**: Rigorously vet all incoming source material. Only include official documentation, peer-reviewed journal articles, and actively maintained open-source tool repositories.
* **Content Relevance**: Ensure raw data directly pertains to microlensing analysis, data challenge procedures, Roman Research Nexus usage, or relevant scientific background.
* **Categorization**: Maintain clear distinctions between `microlensing_tools`, `journal_articles`, `web_resources`, etc., to facilitate targeted checks and content updates.

#### 4.2. Chunking Optimization (`knowledge_base/chunked/`)

* **Semantic Cohesion**: Tune `pyragify`'s configuration (`config.yaml`) to ensure that generated text chunks are semantically coherent and do not awkwardly split sentences, paragraphs, or code blocks.
* **Manual Review**: Conduct periodic manual spot-checks of sample `chunked` files to identify and correct any recurring structural or formatting issues introduced during processing.
* **Metadata Integrity**: Verify that essential metadata (e.g., source file, URL, title, section) is either carried into the chunk content or stored separately for accurate citation.

#### 4.3. Embeddings and Index Validation (`knowledge_base/embeddings/`)

* **Model Suitability**: Evaluate the chosen embeddings model (e.g., `all-MiniLM-L6-v2`) for its performance on microlensing-specific vocabulary and concepts. Consider fine-tuning or selecting a more domain-specific model if search relevance is insufficient.
* **Relevance Testing (Golden Queries)**: Develop a set of "golden" test queries with known expected relevant chunks. Regularly run these queries against the `txtai` embeddings database.
* **Search Result Evaluation**: Manually inspect the top-retrieved chunks for each test query to assess their relevance and identify any irrelevant or missing information. Iterate on chunking parameters or embedding models if necessary.

#### 4.4. Response Quality and Monitoring (Bot Output)

* **Prompt Engineering**: Craft precise LLM prompts that instruct the model to:
    * Strictly ground responses in the provided `txtai` retrieved context.
    * Clearly cite sources from the retrieved chunks.
    * Express uncertainty or state when information is not found within the knowledge base rather than fabricating.
* **Human Feedback Loop**: Implement mechanisms (e.g., simple Slack reactions like 👍/👎 or a dedicated feedback channel) to gather user input on the bot's responses.
* **Continuous Monitoring**: Regularly review bot interactions for:
    * Accuracy of answers.
    * Instances of hallucination or off-topic responses.
    * Repeated questions that the bot struggles with, indicating gaps in the knowledge base or prompt engineering.
* **Iterative Improvement**: Use monitoring and feedback to drive continuous improvement of the knowledge base, chunking strategy, embeddings models, and LLM prompts.

## Deployment Considerations

### 1. Setup
- Containerize the entire application
- Include all dependencies and knowledge base
- Easy deployment to cloud platforms

### 2. Environment Configuration
- Slack API tokens and configuration
- Knowledge base paths and settings
- Model configurations for txtai

### 3. Monitoring and Logging
- Track bot usage and performance
- Monitor response quality and user satisfaction
- Log errors and issues for debugging

## Git Strategy

### Files to Track
- `knowledge_base/embeddings/` - The final embeddings database
- `src/` - All modifiable library source code
- `bot/` - Your bot implementation
- Configuration files

### Files to Ignore
- `knowledge_base/raw/` - Large repository clones
- `knowledge_base/chunked/` - Intermediate processing output
- `local_settings.py` - Sensitive configuration
- Model caches and temporary files

## Next Steps for AI Agents

1. **Review the existing code structure** in `src/` directories
2. **Understand the RAG pipeline** by examining txtai and pyragify source
3. **Plan the knowledge base structure** for microlensing resources
4. **Design the bot plugins** for different types of interactions
5Implement the core RAG functionality** using the modified libraries
6. **Test with sample microlensing questions** and refine responses
7. **Deploy and monitor** the bot in the data challenge Slack workspace

## Important Notes

- **All libraries are modifiable**: You can customize txtai, pyragify, and slack-machine as needed
- **Focus on accuracy**: Microlensing is a specialized field, so responses must be precise
- **User experience**: The bot should be helpful and not overwhelming
- **Continuous improvement**: Update knowledge base and responses based on user feedback
- **Efficient storage**: Only commit the final embeddings database, not intermediate processing steps

This setup provides a powerful foundation for creating an intelligent assistant that can truly help data challenge participants navigate the complex world of microlensing analysis and Roman mission procedures. 