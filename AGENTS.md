# AI Agents Guide: Roman Galactic Exoplanet Survey Slack Bot

## Project Overview

This repository contains a **RAG-powered Slack bot** designed to support participants in the **Roman Galactic Exoplanet Survey - Project Infrastructure Team data challenge**. The bot serves as an intelligent assistant that can answer questions about microlensing analysis, data challenge procedures, and related tools by leveraging a comprehensive knowledge base of microlensing resources.

## Repository Structure

```
slack-bot/
├── src/
│   ├── txtai/                    # Embeddings database and RAG framework
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
├── scripts/                     # Build and maintenance scripts
├── docs/                        # Documentation
├── tests/                       # Testing scripts and environment
├── pyproject.toml               # Dependencies
├── local_settings.py            # Bot configuration (not in git)
├── .gitignore                   # Git ignore rules (includes knowledge_base/raw)
└── AGENTS.md                    # This file - AI agent guide
```

## Data Pipeline (Current - v2.0)

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

### Stage 3: Unified Embedding Pipeline
- All processed content (notebooks, PDFs, code, docs) embedded via txtai
- No intermediate chunking - whole files/documents preserved
- Extension-based weighting for relevance (configurable via `config/weights.yaml`)
- Comprehensive vector database for semantic search across all content types
- **txtai** is used to generate embeddings and build the vector database for semantic search.

## Retrieval and Weighting Improvements

- Retrieval was previously polluted by build artifacts and irrelevant files.
- Introduced extension- and path-based weighting rules (e.g., prioritizing `.py`, `.md`, files with "tutorial" in the path).
- The LLM is given a tool to dynamically adjust file weights, which has proven effective in practice.
- Despite improvements, retrieval of code and notebook content is still being refined.

## Key Components

- **txtai**: Embeddings database for semantic search and RAG
- **slack-machine**: Slack bot framework with plugin system  
- **nb4llm**: Jupyter notebook to plain text converter for improved semantic retrieval
- **Apache Tika** (via tika package): PDF text extraction for journal articles
- **Unified pipeline**: Single build process handles repositories + PDFs + notebooks

## Current Status and Capabilities

### ✅ **Fully Implemented**
- **Complete PDF processing**: Both repository-embedded and standalone articles
- **Notebook conversion**: nb4llm integration for all `.ipynb` files
- **Multi-source indexing**: Repositories, PDFs, and GitHub Pages sites
- **Java dependency handling**: Optional PDF processing with graceful fallback
- **Unified search**: All content types searchable through single txtai index

### 🔄 **Current Limitations and Next Steps**
- **Retrieval optimization**: Fine-tuning semantic search relevance
- **Chunking evaluation**: Consider document-level vs. chunk-level embeddings
- **Pipeline modularization**: Refactor scripts into importable package
- **Build artifact filtering**: Continue improving file relevance weighting

## Development Workflow (Updated v2.0)

1. **Configure sources** in `config/repositories.yml` and `config/articles.yml`
2. **Build knowledge base**: `python scripts/build_knowledge_base.py --config config/repositories.yml --articles-config config/articles.yml`
   - Clones/updates repositories
   - Downloads PDF articles from URLs
   - Converts notebooks via nb4llm  
   - Extracts PDF text via Tika
   - Creates unified txtai embeddings index
3. **Test queries**: `python scripts/demo_query.py "your question here"`
4. **Deploy bot**: Configure Slack tokens and run Nancy

## Technical Considerations

- **Dynamic weighting**: Both static (extension/path) and LLM-driven dynamic weighting are used to improve retrieval relevance.
- **No intermediate chunking**: All files are embedded as a whole for now.
- **Continuous improvement**: Ongoing evaluation of retrieval quality, especially for code and notebook content.

## Git Strategy

- Track only the embeddings database, source code, and configuration files.
- Ignore raw data, local settings, and model caches.

## Important Notes

- All libraries are modifiable.
- Focus on accuracy and user experience.
- Continuous improvement based on feedback and retrieval quality.

---

This guide reflects the current state of the project as of the latest development cycle. See README.md for user-facing details and scripts/demo_query.py for the latest RAG/LLM workflow. 