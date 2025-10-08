#!/bin/bash
# Fast dev Docker Deployment
# Usage: ./deploy-dev.sh

set -e

echo "🚀 Starting FAST dev Docker deployment..."

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found. Please run this script from the deploy/ directory."
    exit 1
fi

# Set up local environment
./switch-env.sh local

echo "⚡ Fast dev mode:"
echo "   - Uses existing images when possible"
echo "   - Only rebuilds if code changes detected"
echo "   - Optimized for rapid iteration"
echo "   - Uses unified environment file: backend/env.unified"

echo ""
echo "🔍 Checking for code changes..."

# Check if we need to rebuild based on file changes
NEED_REBUILD=false

# Check if images exist
if ! docker image inspect deploy-backend >/dev/null 2>&1; then
    echo "   Backend image not found - rebuild needed"
    NEED_REBUILD=true
fi

if ! docker image inspect deploy-caddy >/dev/null 2>&1; then
    echo "   Frontend image not found - rebuild needed"
    NEED_REBUILD=true
fi

# Check for recent changes (last 10 minutes)
if find ../backend ../frontend ../requirements.txt -newer docker-compose.yml 2>/dev/null | grep -q .; then
    echo "   Recent code changes detected - rebuild recommended"
    NEED_REBUILD=true
fi

echo ""
if [ "$NEED_REBUILD" = true ]; then
    echo "🔨 Rebuilding images (optimized)..."
    
    # Use BuildKit with optimized settings (automatic)
    export DOCKER_BUILDKIT=1
    export BUILDKIT_PROGRESS=plain
    export COMPOSE_DOCKER_CLI_BUILD=1
    
    # Stop containers first
    docker compose down
    
    # Build with cache and parallelism
    docker compose build --parallel
    
    # Start containers
    docker compose up -d
else
    echo "⚡ No rebuild needed - using existing images..."
    
    # Just restart containers
    docker compose down
    docker compose up -d
fi

echo ""
echo "⏳ Waiting for containers to start..."
sleep 5

echo ""
echo "📊 Container status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "🧪 Quick health check:"
curl -sf http://localhost/health/ | jq '.status' 2>/dev/null || echo "❌ Health check failed"

echo ""
echo "⚡ Fast deployment complete!"
echo ""
echo "📍 Your DeFi platform is available at:"
echo "   🔗 http://localhost/ (Firefox/Safari)"
echo "   🔗 http://localhost:8080/ (Chrome)"
echo ""
echo "🔧 dev workflow:"
echo "   Code changes: ./deploy-dev.sh (smart rebuild)"
echo "   Full rebuild: ./deploy-local.sh (clean build)"
echo "   Quick restart: ./deploy-local-simple.sh (no build)"
