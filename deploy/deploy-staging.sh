#!/bin/bash
# Staging Deployment Script for DeFi Yield Optimization Platform
# Usage: ./deploy-staging.sh

set -e  # Exit on any error

echo "🚀 Starting staging deployment..."
echo ""
echo "📍 Deployment Environment:"
echo "   Platform: Staging (UAT)"
echo "   Domain: defi-project-uat.odum-research.com"
echo "   Environment: backend/env.unified"
echo ""

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found. Please run this script from the deploy/ directory."
    exit 1
fi

# Set up staging environment
echo "📋 Setting up staging environment..."
./switch-env.sh staging

echo "📋 Staging deployment configuration:"
echo "   Domain: defi-project-uat.odum-research.com"
echo "   Backend Port: 8001 (Docker internal)"
echo "   Frontend Port: 80/443 (via Caddy)"
echo "   Redis: Internal Docker network"
echo "   Environment: backend/env.unified"

echo ""
echo "🛑 Stopping existing containers..."
docker compose down

echo ""
echo "🧹 Cleaning up unused images (optional)..."
docker image prune -f

echo ""
echo "🔨 Building and starting staging containers..."

# Enable BuildKit and optimizations automatically
export DOCKER_BUILDKIT=1
export BUILDKIT_PROGRESS=plain
export COMPOSE_DOCKER_CLI_BUILD=1

# Use optimized build process
docker compose build --parallel
docker compose up -d

echo ""
echo "⏳ Waiting for containers to start..."
sleep 10

echo ""
echo "📊 Container status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "🏥 Health checks..."
echo "Backend health:"
docker exec deploy-backend-1 curl -sf http://localhost:8001/health/ || echo "❌ Backend health check failed"

echo ""
echo "Caddy status:"
docker logs --tail 5 deploy-caddy-1 | grep -E "(server running|certificate obtained|error)" || echo "Check caddy logs manually"

echo ""
echo "🌐 Testing staging endpoints..."
echo "HTTP redirect (should return 301/308):"
curl -I http://defi-project-uat.odum-research.com/ 2>/dev/null | head -1 || echo "❌ HTTP test failed"

echo ""
echo "HTTPS health (with auth):"
if [ -n "$BASIC_AUTH_HASH" ]; then
    echo "   (Note: Basic Auth is enabled - test manually with: curl -u admin:password https://defi-project-uat.odum-research.com/health/detailed)"
else
    curl -I https://defi-project-uat.odum-research.com/health/detailed 2>/dev/null | head -1 || echo "❌ HTTPS health test failed"
fi

echo ""
echo "🎉 Staging deployment complete!"
echo ""
echo "📍 Your DeFi platform is available at:"
echo "   🔗 https://defi-project-uat.odum-research.com/"
echo ""
echo "🔧 Useful commands:"
echo "   View logs:     docker compose logs"
echo "   Restart:       docker compose restart"
echo "   Stop:          ./stop-staging.sh"
echo "   Quick stop:    docker compose down"
echo "   Update:        git pull && ./deploy-staging.sh"
echo ""
echo "📚 For troubleshooting, check:"
echo "   Backend logs:  docker logs deploy-backend-1"
echo "   Caddy logs:    docker logs deploy-caddy-1"
echo "   Redis logs:    docker logs deploy-redis-1"
