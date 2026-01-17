#!/bin/bash
# Validate Docker Implementation
set -e

echo "🔍 Validating Docker Implementation"
echo "===================================="
echo ""

ERRORS=0

# Check function
check_file() {
    if [ -f "$1" ]; then
        echo "✅ $1"
    else
        echo "❌ Missing: $1"
        ERRORS=$((ERRORS + 1))
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo "✅ $1"
    else
        echo "❌ Missing directory: $1"
        ERRORS=$((ERRORS + 1))
    fi
}

# Task 1: MCP Server Files
echo "📦 Task 1: MCP Server Dockerization"
check_file "ref/nancy-brain/Dockerfile"
check_file "ref/nancy-brain/.dockerignore"
check_file "ref/nancy-brain/build_docker.sh"
echo ""

# Task 2: Slack Bot Docker Files
echo "🤖 Task 2: Slack Bot Docker Setup"
check_file "Dockerfile"
check_file ".dockerignore"
check_file "docker-compose.yml"
check_file ".env.example"
check_file "setup-docker.sh"
check_file "DOCKER.md"
echo ""

# Task 3: Configuration Files
echo "🔑 Task 3: API Key Configuration"
check_file "bot/plugins/rag/mcp_adapter.py"
check_file "bot/plugins/llm/llm_service.py"
check_file "ref/nancy-brain/connectors/mcp_server/server.py"
echo ""

# Check for required directories
echo "📂 Required Directories"
check_dir "ref/nancy-brain/config"
check_dir "bot/config"
echo ""

# Check for executables
echo "🔧 Executable Scripts"
if [ -x "setup-docker.sh" ]; then
    echo "✅ setup-docker.sh (executable)"
else
    echo "⚠️  setup-docker.sh (not executable - run: chmod +x setup-docker.sh)"
fi

if [ -x "ref/nancy-brain/build_docker.sh" ]; then
    echo "✅ ref/nancy-brain/build_docker.sh (executable)"
else
    echo "⚠️  ref/nancy-brain/build_docker.sh (not executable - run: chmod +x ref/nancy-brain/build_docker.sh)"
fi
echo ""

# Check for Docker
echo "🐳 Docker Environment"
if command -v docker &> /dev/null; then
    echo "✅ Docker installed ($(docker --version))"
else
    echo "❌ Docker not found"
    ERRORS=$((ERRORS + 1))
fi

if command -v docker-compose &> /dev/null; then
    echo "✅ docker-compose installed ($(docker-compose --version))"
elif docker compose version &> /dev/null; then
    echo "✅ Docker Compose V2 installed ($(docker compose version))"
else
    echo "❌ docker-compose not found"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check for API key authentication in code
echo "🔐 Checking API Key Implementation"
if grep -q "X-API-Key" bot/plugins/rag/mcp_adapter.py; then
    echo "✅ MCPRAGAdapter uses X-API-Key header"
else
    echo "❌ MCPRAGAdapter missing X-API-Key header"
    ERRORS=$((ERRORS + 1))
fi

if grep -q "X-API-Key" bot/plugins/llm/llm_service.py; then
    echo "✅ LLMService health check uses X-API-Key header"
else
    echo "❌ LLMService health check missing X-API-Key header"
    ERRORS=$((ERRORS + 1))
fi

if grep -q "verify_api_key" ref/nancy-brain/connectors/mcp_server/server.py; then
    echo "✅ MCP server has API key verification"
else
    echo "❌ MCP server missing API key verification"
    ERRORS=$((ERRORS + 1))
fi

if grep -q "/rebuild" ref/nancy-brain/connectors/mcp_server/server.py; then
    echo "✅ MCP server has /rebuild endpoint"
else
    echo "❌ MCP server missing /rebuild endpoint"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Summary
echo "=================================="
if [ $ERRORS -eq 0 ]; then
    echo "✅ All checks passed! Docker implementation is complete."
    echo ""
    echo "Next steps:"
    echo "  1. Create .env file: cp .env.example .env"
    echo "  2. Fill in your secrets in .env"
    echo "  3. Run: ./setup-docker.sh"
    exit 0
else
    echo "❌ Found $ERRORS error(s). Please review the output above."
    exit 1
fi
