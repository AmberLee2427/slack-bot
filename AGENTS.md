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

## Data Pipeline (Current)

### Stage 1: Raw Resources (`knowledge_base/raw/`)
- **Source repositories**: Git clones of microlensing tools, notebooks, etc.
- **Web content**: Scraped or downloaded resources from Microlensing Source
- **Documents**: PDFs, markdown files, etc.
- **Purpose**: Original, unprocessed source material

### Stage 2: Notebook Conversion (via nb4llm)
- **Jupyter notebooks** (`.ipynb`) are converted to plain text files with fenced code blocks for each cell using `nb4llm`.
- This conversion strips metadata/outputs and preserves semantic intent for better retrieval.
- Currently, this is tested on generated notebooks; integration with real repo notebooks is planned.

### Stage 3: Embedding (No Chunking)
- All files (including converted notebooks) are embedded as whole files (no intermediate chunking step).
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

## Current Limitations and Next Steps

- **Jupyter notebook retrieval**: Notebooks are now converted, but this is not yet fully integrated/tested on real repo notebooks.
- **Multivector retrieval**: There is ongoing discussion about using additional code-centric embedding models to improve code/documentation retrieval.
- **Chunking**: The pipeline currently embeds whole files; chunking strategies may be revisited for better granularity.
- **Build artifacts**: Extension/path-based weighting helps, but further filtering or smarter indexing may be needed.
- **nb4llm integration**: The intent is to make nb4llm a standard part of the pipeline for all notebook sources.
- **Pipeline refactor needed**: Refactor pipeline logic (currently in scripts/) into an importable package/module for easier testing and reuse.

## Development Workflow (Updated)

1. **Clone repositories** into `knowledge_base/raw/`.
2. **Convert Jupyter notebooks** to plain text using `nb4llm` (planned for all repos).
3. **Embed all files** (including converted notebooks) using txtai.
4. **Run and test queries** using `scripts/demo_query.py`.

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