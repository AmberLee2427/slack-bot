# Nancy Docker Deployment Guide

This guide covers deploying Nancy (Slack bot + MCP server) using Docker and docker-compose.

## Architecture

Nancy consists of two services:

1. **nancy-brain-mcp**: Knowledge base MCP server with embeddings and search API
2. **nancy-slack-bot**: Slack bot that connects to the MCP server for RAG capabilities

```
┌─────────────────┐         HTTP API          ┌──────────────────┐
│                 │   ←─────────────────────→  │                  │
│  Slack Bot      │   (API Key Protected)      │   MCP Server     │
│  (Port 3000)    │                            │   (Port 8000)    │
│                 │                            │                  │
└─────────────────┘                            └──────────────────┘
        ↑                                              ↑
        │                                              │
        │ Slack Events                                 │ Embeddings
        ↓                                              ↓
    Slack API                              Knowledge Base Files
```

## Prerequisites

- Docker and docker-compose installed
- Built embeddings in `ref/nancy-brain/knowledge_base/embeddings/`
- Configuration files in `ref/nancy-brain/config/`

## Quick Start

### 1. Build Embeddings (First Time Only)

```bash
cd ref/nancy-brain
python -m nancy_brain.cli build config/repositories.yml knowledge_base
```

### 2. Create Environment File

Copy the example and fill in your secrets:

```bash
cp .env.example .env
# Edit .env with your actual keys
```

Required environment variables:

```env
# MCP Server Auth
MCP_API_KEY=your-secret-api-key-here
NB_SECRET_KEY=your-jwt-secret-key-here

# Slack Credentials
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
SLACK_SIGNING_SECRET=your-signing-secret

# OpenAI
OPENAI_API_KEY=sk-your-openai-key
```

### 3. Start Services

```bash
docker-compose up -d
```

This will:
- Build both Docker images
- Start nancy-brain-mcp on port 8000
- Start nancy-slack-bot on port 3000
- Connect them via internal network

### 4. Check Status

```bash
# View logs
docker-compose logs -f

# Check health
curl http://localhost:8000/health
curl http://localhost:3000/health
```

## Service Details

### Nancy Brain MCP Server

**Image:** Built from `ref/nancy-brain/Dockerfile`
**Port:** 8000
**Volumes:**
- `./ref/nancy-brain/config:/app/config:ro` - Configuration files (read-only)
- `./ref/nancy-brain/knowledge_base:/app/knowledge_base` - Embeddings and source files
- `nancy-brain-cache:/app/cache` - Cache directory

**Endpoints:**
- `GET /health` - Health check (no auth required)
- `GET /search?query=...&limit=5` - Search knowledge base
- `POST /retrieve` - Retrieve document passages
- `POST /rebuild` - Trigger embeddings rebuild
- All endpoints except `/health` require `X-API-Key` header

### Nancy Slack Bot

**Image:** Built from root `Dockerfile`
**Port:** 3000
**Volumes:**
- `./bot/config:/app/bot/config` - Bot configuration and cache

**Configuration:**
- Automatically connects to `nancy-brain` via internal network
- Receives Slack events on port 3000
- Uses MCP server for all RAG operations

## Rebuilding Embeddings

### Option 1: Via API (Recommended)

```bash
curl -X POST http://localhost:8000/rebuild \
  -H "X-API-Key: your-secret-api-key"
```

This triggers a background rebuild without downtime.

### Option 2: Manual Rebuild

```bash
# Stop services
docker-compose down

# Rebuild embeddings
cd ref/nancy-brain
python -m nancy_brain.cli build config/repositories.yml knowledge_base

# Restart services
cd ../..
docker-compose up -d
```

## Updating Configuration

### Update Weights

Edit `ref/nancy-brain/config/index_weights.yaml` and restart:

```bash
docker-compose restart nancy-brain
```

### Update Repository List

Edit `ref/nancy-brain/config/repositories.yml` and rebuild embeddings.

## Production Deployment

### Proxmox + Cloudflare

1. **Create VM on Proxmox:**
   ```bash
   # SSH into Proxmox host
   qm create <VMID> --name nancy-bot --memory 4096 --cores 2 --net0 virtio,bridge=vmbr0
   ```

2. **Install Docker on VM:**
   ```bash
   curl -fsSL https://get.docker.com | sh
   sudo usermod -aG docker $USER
   ```

3. **Clone and Deploy:**
   ```bash
   git clone <your-repo> nancy
   cd nancy
   cp .env.example .env
   # Edit .env with production keys
   docker-compose up -d
   ```

4. **Configure Cloudflare Tunnel:**
   ```bash
   # Install cloudflared
   curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o cloudflared.deb
   sudo dpkg -i cloudflared.deb
   
   # Authenticate
   cloudflared tunnel login
   
   # Create tunnel
   cloudflared tunnel create nancy-bot
   
   # Configure tunnel (config.yml)
   tunnel: <tunnel-id>
   credentials-file: /home/user/.cloudflared/<tunnel-id>.json
   ingress:
     - hostname: nancy-bot.yourdomain.com
       service: http://localhost:3000
     - service: http_status:404
   
   # Run tunnel
   cloudflared tunnel run nancy-bot
   ```

5. **Set up Systemd Service:**
   ```bash
   sudo nano /etc/systemd/system/nancy.service
   ```
   
   ```ini
   [Unit]
   Description=Nancy Slack Bot
   After=docker.service
   Requires=docker.service
   
   [Service]
   Type=oneshot
   RemainAfterExit=yes
   WorkingDirectory=/home/user/nancy
   ExecStart=/usr/local/bin/docker-compose up -d
   ExecStop=/usr/local/bin/docker-compose down
   
   [Install]
   WantedBy=multi-user.target
   ```
   
   ```bash
   sudo systemctl enable nancy
   sudo systemctl start nancy
   ```

### Resource Requirements

**Minimum:**
- CPU: 2 cores
- RAM: 4GB
- Disk: 10GB

**Recommended:**
- CPU: 4 cores
- RAM: 8GB
- Disk: 20GB (allows for knowledge base growth)

## Troubleshooting

### MCP Server Not Starting

Check embeddings exist:
```bash
ls -lh ref/nancy-brain/knowledge_base/embeddings/
```

Check config files:
```bash
ls -l ref/nancy-brain/config/repositories.yml
ls -l ref/nancy-brain/config/index_weights.yaml
```

### Slack Bot Can't Connect to MCP

Check network connectivity:
```bash
docker-compose exec nancy-bot curl http://nancy-brain:8000/health
```

Check API key is set:
```bash
docker-compose exec nancy-bot env | grep MCP_API_KEY
```

### Permission Errors

Fix volume permissions:
```bash
sudo chown -R $USER:$USER ref/nancy-brain/knowledge_base
sudo chown -R $USER:$USER bot/config
```

## Maintenance

### View Logs
```bash
docker-compose logs -f nancy-brain
docker-compose logs -f nancy-bot
```

### Restart Services
```bash
docker-compose restart
```

### Update Code
```bash
git pull
docker-compose build
docker-compose up -d
```

### Backup Embeddings
```bash
tar -czf embeddings-backup-$(date +%Y%m%d).tar.gz ref/nancy-brain/knowledge_base/embeddings/
```

## Security Notes

1. **Never commit `.env`** - Add it to `.gitignore`
2. **Rotate API keys regularly** - Update `MCP_API_KEY` in `.env` and restart
3. **Use strong secrets** - Generate random keys for `NB_SECRET_KEY` and `MCP_API_KEY`
4. **Limit network exposure** - Use Cloudflare Tunnel instead of exposing ports directly
5. **Keep Docker updated** - Regularly update base images

## Custom GPT Integration

To serve Nancy to a Custom GPT:

1. Deploy with HTTPS (via Cloudflare or reverse proxy)
2. Configure Custom GPT with OpenAPI schema
3. Set Authentication to "API Key" using your `MCP_API_KEY`
4. Point actions to `https://your-domain.com/search`, `/retrieve`, etc.

## Development Mode

For local development without Docker:

```bash
# Terminal 1: MCP Server
cd ref/nancy-brain
python run_mcp_server.py

# Terminal 2: Slack Bot
export MCP_BASE_URL=http://localhost:8000
export MCP_API_KEY=your-key
python nancy_bot.py
```
