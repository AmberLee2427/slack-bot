# Docker Implementation Summary

## Completed Tasks

### ✅ Task 1: MCP Server Dockerization
**Location:** `ref/nancy-brain/`

**Files Created:**
- `Dockerfile` - MCP server container with embeddings support
- `.dockerignore` - Excludes unnecessary files from build
- `build_docker.sh` - Helper script for building the image

**Features Implemented:**
- Python 3.12 base image with all dependencies
- Embeddings baked into image (or mounted via volume)
- HTTP API on port 8000
- Health check endpoint
- `/rebuild` API endpoint for triggering embedding updates
- Simple API key authentication via `X-API-Key` header

**Server Endpoints:**
- `GET /health` - Health check (no auth)
- `GET /search` - Search knowledge base (auth required)
- `POST /retrieve` - Retrieve document passages (auth required)
- `POST /embeddings/sql` - SQL-like queries (auth required)
- `GET /doc/{doc_id}/url` - Get GitHub URL (auth required)
- `POST /rebuild` - Trigger embeddings rebuild (auth required)

**Authentication:**
- All endpoints except `/health` require `X-API-Key` header
- API key configured via `MCP_API_KEY` environment variable

---

### ✅ Task 2: Slack Bot Docker Setup
**Location:** Root directory

**Files Created:**
- `Dockerfile` - Slack bot container
- `.dockerignore` - Excludes unnecessary files
- `docker-compose.yml` - Orchestrates both services
- `.env.example` - Environment variable template
- `setup-docker.sh` - Automated setup script
- `DOCKER.md` - Complete deployment documentation

**Docker Compose Services:**
1. **nancy-brain** (MCP Server)
   - Port: 8000
   - Volumes: config (ro), knowledge_base, cache
   - Health check with 60s start period
   
2. **nancy-bot** (Slack Bot)
   - Port: 3000
   - Depends on nancy-brain (waits for healthy)
   - Connects via internal network
   - Health check with 30s start period

**Features:**
- Internal Docker network for service communication
- Volume persistence for embeddings and cache
- Health checks for both services
- Automatic restart unless stopped
- Named volumes for better management

---

### ✅ Task 3: API Key Configuration
**Files Modified:**
- `bot/plugins/rag/mcp_adapter.py` - Updated to use `X-API-Key` header
- `bot/plugins/llm/llm_service.py` - Updated health check to use `X-API-Key`
- `ref/nancy-brain/connectors/mcp_server/server.py` - Added API key auth and `/rebuild` endpoint

**Environment Variables:**
```env
# MCP Server
MCP_API_KEY=your-secret-api-key-here
NB_SECRET_KEY=your-jwt-secret-key-here

# Slack Bot
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
SLACK_SIGNING_SECRET=your-signing-secret
OPENAI_API_KEY=sk-your-openai-key

# Connection (automatic in Docker)
MCP_BASE_URL=http://nancy-brain:8000
```

**Authentication Flow:**
1. Slack bot reads `MCP_API_KEY` from environment
2. MCPRAGAdapter adds `X-API-Key: <key>` header to all requests
3. MCP server validates header before processing requests
4. `/health` endpoint is exempt from authentication

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Docker Host                          │
│                                                              │
│  ┌──────────────────────┐         ┌───────────────────────┐ │
│  │   nancy-slack-bot    │         │   nancy-brain-mcp     │ │
│  │   (Port 3000)        │         │   (Port 8000)         │ │
│  │                      │         │                       │ │
│  │ - Slack Events       │ ──────► │ - Search API          │ │
│  │ - Message Handler    │ X-API-Key│ - Embeddings         │ │
│  │ - LLM Service        │ ◄────── │ - /rebuild endpoint   │ │
│  │                      │         │                       │ │
│  └──────────────────────┘         └───────────────────────┘ │
│           │                                    │             │
│           │                                    │             │
│  ┌────────▼────────┐              ┌───────────▼──────────┐  │
│  │  Config Volume  │              │  Knowledge Base Vol  │  │
│  │  /app/bot/config│              │  /app/knowledge_base │  │
│  └─────────────────┘              └──────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
         │                                    │
         │                                    │
         ▼                                    ▼
    Slack API                        GitHub Repositories
```

---

## Deployment Options

### Option 1: Docker Compose (Recommended)
```bash
./setup-docker.sh
```

### Option 2: Manual Docker Commands
```bash
# Build images
docker build -t nancy-brain-mcp ref/nancy-brain/
docker build -t nancy-slack-bot .

# Run services
docker network create nancy-network

docker run -d --name nancy-brain \
  --network nancy-network \
  -p 8000:8000 \
  -e MCP_API_KEY=your-key \
  -v $(pwd)/ref/nancy-brain/config:/app/config:ro \
  -v $(pwd)/ref/nancy-brain/knowledge_base:/app/knowledge_base \
  nancy-brain-mcp

docker run -d --name nancy-bot \
  --network nancy-network \
  -p 3000:3000 \
  -e SLACK_BOT_TOKEN=your-token \
  -e MCP_BASE_URL=http://nancy-brain:8000 \
  -e MCP_API_KEY=your-key \
  nancy-slack-bot
```

### Option 3: Kubernetes (Future)
- Helm charts to be added
- Persistent volume claims for embeddings
- ConfigMaps for configuration
- Secrets for API keys

---

## Security Features

1. **API Key Authentication**
   - Required for all MCP endpoints except `/health`
   - Configurable via environment variables
   - No default/hardcoded keys

2. **Network Isolation**
   - Internal Docker network for service communication
   - Only necessary ports exposed to host

3. **Read-only Configuration**
   - Config files mounted as read-only volumes
   - Prevents accidental modification

4. **Secure Secrets Management**
   - All secrets via environment variables
   - `.env` excluded from git
   - Template provided in `.env.example`

---

## Testing

### Health Checks
```bash
# MCP Server
curl http://localhost:8000/health

# Slack Bot
curl http://localhost:3000/health
```

### API Authentication Test
```bash
# Without auth (should fail)
curl http://localhost:8000/search?query=test

# With auth (should succeed)
curl -H "X-API-Key: your-key" http://localhost:8000/search?query=test
```

### Rebuild Endpoint Test
```bash
curl -X POST \
  -H "X-API-Key: your-key" \
  http://localhost:8000/rebuild
```

---

## Production Deployment Guide

See **[DOCKER.md](DOCKER.md)** for complete production deployment instructions including:
- Proxmox VM setup
- Cloudflare Tunnel configuration
- Systemd service setup
- Resource requirements
- Backup procedures
- Monitoring and maintenance

---

## Files Structure

```
slack-bot/
├── Dockerfile                      # Slack bot container
├── .dockerignore                   # Slack bot build exclusions
├── docker-compose.yml              # Service orchestration
├── .env.example                    # Environment template
├── setup-docker.sh                 # Automated setup
├── DOCKER.md                       # Deployment documentation
│
├── ref/nancy-brain/
│   ├── Dockerfile                  # MCP server container
│   ├── .dockerignore               # MCP build exclusions
│   ├── build_docker.sh             # MCP build helper
│   ├── config/
│   │   ├── repositories.yml        # KB repositories
│   │   └── index_weights.yaml      # Search weights
│   └── knowledge_base/
│       └── embeddings/             # Pre-built embeddings
│
└── bot/
    ├── plugins/
    │   ├── rag/
    │   │   └── mcp_adapter.py      # Updated with X-API-Key
    │   └── llm/
    │       └── llm_service.py      # Updated health check
    └── config/
        └── .env                    # Bot secrets (gitignored)
```

---

## Next Steps

### Immediate
- [ ] Test Docker deployment locally
- [ ] Verify health checks work
- [ ] Test /rebuild endpoint
- [ ] Verify API key authentication

### Short-term
- [ ] Deploy to production VM
- [ ] Set up Cloudflare Tunnel
- [ ] Configure systemd service
- [ ] Set up log rotation

### Long-term
- [ ] Kubernetes Helm charts
- [ ] CI/CD pipeline for Docker builds
- [ ] Automated testing in containers
- [ ] Monitoring and alerting setup

---

## Troubleshooting

Common issues and solutions documented in **[DOCKER.md](DOCKER.md)**:
- MCP server not starting
- Slack bot can't connect
- Permission errors
- Embeddings rebuild failures

---

## Summary

All three tasks completed successfully:

1. ✅ **MCP Server Dockerization** - Full containerization with API, auth, and rebuild endpoint
2. ✅ **Slack Bot Docker Setup** - Complete docker-compose orchestration of both services
3. ✅ **API Key Configuration** - Secure authentication implemented throughout

The implementation follows Docker best practices:
- Minimal base images
- Health checks
- Volume persistence
- Network isolation
- Security by default
- Comprehensive documentation
