# Journal Article Management

This directory contains tools for managing journal articles (PDFs) in Nancy's knowledge base. There are now **two approaches** for handling PDF articles:

## 🆕 **Integrated Pipeline Approach** (Recommended)

The main knowledge base build pipeline now supports downloading PDFs from URLs and integrating them into the embeddings, just like repositories.

### Setup

1. **Configure PDF articles** in `config/articles.yml`:
   ```yaml
   journal_articles:
     - name: "Paczynski_1986_ApJ_304_1"
       url: "https://ui.adsabs.harvard.edu/link_gateway/1986ApJ...304....1P/PUB_PDF"
       description: "Paczynski (1986) - Gravitational microlensing by the galactic halo"
   
   microlensing_reviews:
     - name: "Mao_2012_RAA_12_947"
       url: "https://ui.adsabs.harvard.edu/link_gateway/2012RAA....12..947M/PUB_PDF"
       description: "Mao (2012) - Introduction to gravitational microlensing"
   ```

2. **Build the complete knowledge base** (repos + PDFs):
   ```bash
   export KMP_DUPLICATE_LIB_OK=TRUE
   conda activate roman-slack-bot
   
   # Build everything (downloads repos and PDFs, creates embeddings, cleans up)
   python scripts/build_knowledge_base.py
   
   # Build only PDF articles
   python scripts/build_knowledge_base.py --category journal_articles
   
   # Keep raw files for inspection
   python scripts/build_knowledge_base.py --dirty
   ```

### Features

- ✅ **URL-based PDF downloads** - just like repositories, but for PDFs
- ✅ **Automatic cleanup** - downloads, processes, and cleans up PDFs
- ✅ **Integrated embeddings** - PDFs included in the same search index as code
- ✅ **Metadata preservation** - title, description, and URL included in search results
- ✅ **Categorized organization** - separate categories like `journal_articles`, `reviews`, etc.

## 📄 **Standalone PDF Manager**

For manual PDF management, there's also a dedicated tool:

```bash
# Download PDFs by category
python scripts/manage_pdf_articles.py --category journal_articles

# List all configured PDFs
python scripts/manage_pdf_articles.py --list

# Download all PDFs
python scripts/manage_pdf_articles.py

# Clean up orphaned PDFs
python scripts/manage_pdf_articles.py --clean
```

## 🔧 **Legacy Individual Article Manager**

The original `manage_articles.py` script for manually adding individual PDFs:

```bash
# Add a single PDF
python scripts/manage_articles.py add /path/to/paper.pdf

# List existing articles  
python scripts/manage_articles.py list
```

## 🏗️ **Architecture**

### Integrated Pipeline Flow:
1. **Download repos** → Clone git repositories  
2. **Download PDFs** → Fetch PDFs from configured URLs
3. **Extract text** → Use txtai Textractor + Apache Tika for PDF text extraction
4. **Build embeddings** → Index both code and PDF content together
5. **Cleanup** → Remove raw files, keep only embeddings

### File Organization:
```
knowledge_base/
├── raw/                           # Temporary downloads (cleaned up)
│   ├── journal_articles/          # PDF downloads by category
│   │   ├── Paczynski_1986.pdf
│   │   └── Mao_2012.pdf  
│   └── microlensing_tools/        # Git repo clones
│       ├── pyLIMA/
│       └── MulensModel/
└── embeddings/                    # Persistent search index
    └── index/                     # txtai FAISS index
```

## 🔧 **Setup Requirements**

```bash
# Ensure dependencies
conda activate roman-slack-bot
pip install "txtai[pipeline]"

# macOS users: handle OpenMP conflicts
export KMP_DUPLICATE_LIB_OK=TRUE

# Java required for PDF processing
java -version
```

## ⚠️ **Current Known Issues**

1. **Tika Server Issues**: Occasional startup problems with Apache Tika server for PDF processing
   - Workaround: Restart session or run with `--dirty` to inspect individual steps

2. **PDF URL Reliability**: Some publisher PDFs require authentication or have changing URLs
   - Use stable URLs like arXiv: `https://arxiv.org/pdf/1234.5678.pdf`

## 🎯 **Usage Patterns**

### For Development/Testing:
```bash
# Test the pipeline
python scripts/build_knowledge_base.py --dry-run

# Download specific category only
python scripts/build_knowledge_base.py --category roman_mission

# Keep files for debugging
python scripts/build_knowledge_base.py --dirty
```

### For Production:
```bash
# Full rebuild (everything)
python scripts/build_knowledge_base.py --force-update

# Regular update (only new content)
python scripts/build_knowledge_base.py
```

### For PDF Management:
```bash
# Quick PDF status check
python scripts/manage_pdf_articles.py --list

# Add individual PDF
python scripts/manage_articles.py add /path/to/new_paper.pdf
```
