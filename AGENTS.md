# AI Agents Guide: Roman Galactic Exoplanet Survey Slack Bot

## Project Overview

This repository contains a **RAG-powered Slack bot** designed to support participants in the **Roman Galactic Exoplanet Survey - Project Infrastructure Team data challenge**. The bot serves as an intelligent assistant that can answer questions about microlensing analysis, data challenge procedures, and related tools by leveraging a comprehensive knowledge base of microlensing resources.

## Current Status (v3.0 - Dual Embedding System)

### ✅ **Recently Completed**
- **Dual Embedding Architecture**: General text model (sentence-transformers/all-MiniLM-L6-v2) + Code-specific model (microsoft/codebert-base)
- **Smart File Type Detection**: Automatic categorization of files as code/mixed/docs for optimal embedding model weighting
- **Enhanced Knowledge Base Pipeline**: 937 documents indexed with comprehensive failure tracking and monitoring
- **Model Weights System**: Dynamic document weighting with extension-based and path-based rules
- **Environment-Driven Configuration**: Dual embedding controlled via .env variables
- **Notebook Processing**: .nb.txt conversion preserving notebook identity while preventing duplicates
- **Interactive Slack Features**: Home tab with Block Kit UI, button-based navigation

### 🚀 **New Requirements (v3.1)**

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

### Stage 3: Dual Embedding Pipeline
- **General Text Model**: sentence-transformers/all-MiniLM-L6-v2 for documentation and natural language
- **Code-Specific Model**: microsoft/codebert-base for code files and technical content
- **Smart Weighting**: File-type-aware scoring (code: 70% code model, mixed: 50/50, docs: 80% general)
- **Extension-based Weighting**: Configurable via `config/weights.yaml` for relevance optimization
- **Model Weights**: Individual document scoring stored in `config/model_weights.yaml`
- **Unified Search**: Merged dual scoring with comprehensive reweighting pipeline

## Technical Architecture (v3.0)

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

### ✅ **Fully Implemented (v3.0)**
- **Dual Embedding System**: General + code models with intelligent merging
- **Complete PDF Processing**: Both repository-embedded and standalone articles
- **Notebook Conversion**: nb4llm integration preventing duplicates with .nb.txt extension
- **Multi-Source Indexing**: Repositories, PDFs, and GitHub Pages sites
- **Advanced Weighting**: File-type detection, extension weights, model weights
- **Interactive Slack Interface**: Home tab with Block Kit UI and button navigation
- **Failure Tracking**: Comprehensive pipeline monitoring and reporting

### 🔄 **Priority Implementation Plan (v3.1)**

#### **Phase 1: Enhanced Context Presentation (High Priority)**
- **GitHub Link Integration**: Replace filenames with clickable links in system messages
- **Master Branch URLs**: Switch from `/blob/main/` to `/blob/master/` for stability
- **Implementation**: Modify `get_context_for_query()` and `get_detailed_context()` methods
- **Timeline**: 1-2 hours

#### **Phase 2: "Keep Cooking" Interactive Feature (Medium Priority)**  
- **Button Implementation**: Add "Continue Analysis" button to Nancy's responses
- **Context Preservation**: Maintain conversation state for follow-up expansions
- **Handler Extension**: Extend `InteractiveHandler` with new button action
- **Timeline**: 2-3 hours

#### **Phase 3: Daily Rate Limiting (Medium Priority)**
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

## Immediate Next Steps (Recommended Priority Order)

### 1. **GitHub Link Enhancement** (Start Here - Quick Win)
**Why First**: Simple change with immediate UX improvement, affects core functionality
- Modify RAG service context methods to use links instead of filenames
- Switch to master branch for stability  
- Test with existing dual embedding system

### 2. **Master Branch URL Fix** (Coupled with #1)  
**Why Second**: Natural coupling with GitHub link work, addresses stability concerns
- Single line change in `_get_github_url()` method
- Immediate stability improvement for existing links

### 3. **"Keep Cooking" Feature** (High Impact)
**Why Third**: Leverages existing interactive infrastructure, major UX enhancement
- Extends existing `InteractiveHandler` capabilities
- Provides user control over response depth
- Maintains conversation context

### 4. **Daily Rate Limiting** (Resource Management)
**Why Fourth**: Important for cost control but requires new infrastructure
- Implement user tracking and quota system
- Add graceful degradation messaging
- Configure admin overrides

## Git Strategy

- Track only the embeddings database, source code, and configuration files.
- Ignore raw data, local settings, and model caches.

## Important Notes

- All libraries are modifiable.
- Focus on accuracy and user experience.
- Continuous improvement based on feedback and retrieval quality.

---

This guide reflects the current state of the project as of the latest development cycle. See README.md for user-facing details and scripts/demo_query.py for the latest RAG/LLM workflow. 