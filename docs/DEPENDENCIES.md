# Dependencies & Requirements

## Python Dependencies

Nancy uses Python 3.12+ and the following key packages:

### Core Dependencies (required)
- `txtai>=7.0.0` - Vector embeddings and semantic search
- `slack-sdk>=3.18.0` - Slack API integration  
- `torch>=1.12.1` - PyTorch for ML models
- `faiss-cpu>=1.7.1.post2` - Fast similarity search
- `transformers>=4.45.0` - Hugging Face transformer models

### Optional Dependencies

#### PDF Processing (`pip install .[pdf]`)
- `tika>=2.6.0` - Python wrapper for Apache Tika

## System Dependencies

### Java Runtime (for PDF processing)

**Why Java is needed:**
Nancy can process journal articles in PDF format to include them in the knowledge base. This functionality uses Apache Tika (via the `tika` Python package) which requires a Java Runtime Environment.

**What version:**
- Java 8 or higher (OpenJDK recommended)
- Tested with OpenJDK 11, 17, and 24

**Installation:**

#### macOS
```bash
# Using Homebrew (recommended)
brew install openjdk

# Or using MacPorts
sudo port install openjdk11
```

#### Ubuntu/Debian
```bash
# Install OpenJDK 11
sudo apt-get update
sudo apt-get install openjdk-11-jdk

# Or OpenJDK 17
sudo apt-get install openjdk-17-jdk
```

#### Windows
```bash
# Using Chocolatey
choco install openjdk

# Using Scoop
scoop bucket add java
scoop install openjdk
```

#### Verification
```bash
java -version
```

You should see output like:
```
openjdk version "11.0.x" 2021-xx-xx
OpenJDK Runtime Environment (build ...)
OpenJDK 64-Bit Server VM (build ...)
```

## Feature Matrix

| Feature | Required Dependencies | Notes |
|---------|----------------------|-------|
| Basic Q&A | Python core deps | Works without Java |
| Repository indexing | Python core deps | Git repos, code files |
| PDF article processing | Python core deps + Java + Tika | Journal articles |
| Slack integration | `slack-sdk` | Bot functionality |
| Vector search | `txtai`, `faiss-cpu` | Semantic search |

## Optional Features

### Without Java/Tika
- Nancy works fully for repository-based knowledge
- Can answer questions about code, documentation, tutorials
- No PDF journal article processing

### With Java/Tika  
- Full PDF processing capabilities
- Journal article indexing from `config/articles.yml`
- Enhanced knowledge base with research papers

## Troubleshooting

### Java Issues
**Problem**: `Failed to initialize Tika VM`
**Solution**: Ensure Java is installed and `java` command is in PATH

**Problem**: Java version conflicts
**Solution**: Use OpenJDK 11+ and ensure JAVA_HOME is set correctly

### Tika Issues  
**Problem**: Tika startup warnings
**Solution**: These are normal and don't affect functionality

**Problem**: PDF parsing failures
**Solution**: Check PDF file permissions and ensure file isn't corrupted
