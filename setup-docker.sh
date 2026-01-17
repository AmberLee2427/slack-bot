#!/bin/bash
# Nancy Docker Setup Script
set -e

echo "🤖 Nancy Docker Setup"
echo "===================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first:"
    echo "   https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install docker-compose first:"
    echo "   https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and docker-compose are installed"
echo ""

# Check for .env file
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and fill in your secrets:"
    echo "   - MCP_API_KEY (generate a random key)"
    echo "   - NB_SECRET_KEY (generate a random key)"
    echo "   - SLACK_BOT_TOKEN"
    echo "   - SLACK_APP_TOKEN"
    echo "   - SLACK_SIGNING_SECRET"
    echo "   - OPENAI_API_KEY"
    echo ""
    read -p "Press Enter after you've filled in .env..."
fi

echo "✅ .env file exists"
echo ""

# Check for embeddings
if [ ! -d "ref/nancy-brain/knowledge_base/embeddings" ] || [ -z "$(ls -A ref/nancy-brain/knowledge_base/embeddings 2>/dev/null)" ]; then
    echo "📦 Embeddings not found. Building embeddings..."
    echo "   This may take several minutes..."
    cd ref/nancy-brain
    python -m nancy_brain.cli build config/repositories.yml knowledge_base || {
        echo "❌ Failed to build embeddings"
        echo "   Make sure you have:"
        echo "   - Python 3.11+ installed"
        echo "   - nancy-brain dependencies installed (pip install -e .)"
        echo "   - config/repositories.yml configured"
        exit 1
    }
    cd ../..
fi

echo "✅ Embeddings are ready"
echo ""

# Build Docker images
echo "🐳 Building Docker images..."
docker-compose build || {
    echo "❌ Failed to build Docker images"
    exit 1
}

echo "✅ Docker images built successfully"
echo ""

# Start services
echo "🚀 Starting Nancy services..."
docker-compose up -d || {
    echo "❌ Failed to start services"
    exit 1
}

echo ""
echo "✅ Nancy is now running!"
echo ""
echo "📊 Service Status:"
docker-compose ps
echo ""
echo "📝 Next steps:"
echo "   - View logs: docker-compose logs -f"
echo "   - Check health: curl http://localhost:8000/health"
echo "   - Stop services: docker-compose down"
echo ""
echo "📖 For more information, see DOCKER.md"
