#!/bin/bash
# Simple Local Docker Deployment (No Build)
# Usage: ./deploy-local-simple.sh

set -e

echo "🚀 Starting simple local Docker deployment (no build)..."
echo "   - Uses unified environment file: backend/env.unified"

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found. Please run this script from the deploy/ directory."
    exit 1
fi

# Set up local environment
./switch-env.sh local

echo ""
echo "🛑 Stopping existing containers..."
docker compose down

echo ""
echo "🔨 Starting containers (using existing images)..."
export DOCKER_BUILDKIT=0
export COMPOSE_DOCKER_CLI_BUILD=0
docker compose up -d

echo ""
echo "⏳ Waiting for containers to start..."
sleep 10

echo ""
echo "📊 Container status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "🎉 Simple deployment complete!"
echo "   If containers failed to start, you may need to build them first:"
echo "   ./deploy-local.sh (with build)"
echo ""
echo "📍 Your platform should be available at:"
echo "   🔗 http://localhost/ (Firefox/Safari)"
echo "   🔗 http://localhost:8080/ (Chrome - avoids HSTS cache)"
echo ""
echo "🔧 Useful commands:"
echo "   View logs:    docker compose logs"
echo "   Stop:         ./stop-local.sh"
echo "   Quick stop:   docker compose down"
