#!/bin/bash
# Local Docker Deployment Script for DeFi Yield Optimization Platform
# Usage: ./deploy-local.sh

set -e  # Exit on any error

echo "🚀 Starting local Docker deployment..."

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found. Please run this script from the deploy/ directory."
    exit 1
fi

# Set up local environment
echo "📋 Setting up local environment..."
./switch-env.sh local

echo "📋 Local deployment configuration:"
echo "   Domain: localhost"
echo "   Backend Port: 8001 (Docker internal)"
echo "   Frontend Port: 80 (via Caddy)"
echo "   Redis: Internal Docker network"
echo "   Environment: backend/env.unified"

echo ""
echo "🛑 Stopping existing containers..."
docker compose down

echo ""
echo "🧹 Cleaning up unused images (optional)..."
docker image prune -f

echo ""
echo "🔨 Building and starting local containers..."
echo "   Note: If you encounter Docker credential issues, try:"
echo "   - Ensure Docker Desktop is running"
echo "   - Run: docker login"
echo "   - Or set DOCKER_BUILDKIT=0 to use legacy builder"
echo ""

# Enable BuildKit and optimizations automatically
export DOCKER_BUILDKIT=1
export BUILDKIT_PROGRESS=plain
export COMPOSE_DOCKER_CLI_BUILD=1

# Try optimized build first, fallback to legacy builder if needed
if ! docker compose build --parallel && docker compose up -d; then
    echo ""
    echo "⚠️  Build failed with BuildKit. Trying fixes..."
    
    # Always fix Docker credential issues for local deployment
    echo "🔧 Fixing Docker credential issues..."
    
    # Backup and fix Docker config
    if [ -f ~/.docker/config.json ]; then
        cp ~/.docker/config.json ~/.docker/config.json.deploy-backup
        echo '{"auths": {}}' > ~/.docker/config.json
        echo "   Temporarily disabled Docker credential store"
    fi
    
    # Try with legacy builder
    export DOCKER_BUILDKIT=0
    export COMPOSE_DOCKER_CLI_BUILD=0
    
    if ! docker compose up -d --build; then
        echo "❌ Build failed even with legacy builder. Please check:"
        echo "   1. Docker Desktop is running"
        echo "   2. Docker daemon is accessible"
        echo "   3. No port conflicts (lsof -i :80)"
        exit 1
    fi
    
    # Restore Docker config if we backed it up
    if [ -f ~/.docker/config.json.deploy-backup ]; then
        mv ~/.docker/config.json.deploy-backup ~/.docker/config.json
        echo "🔧 Restored original Docker config"
    fi
fi

echo ""
echo "⏳ Waiting for containers to start..."
sleep 15

echo ""
echo "📊 Container status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "🏥 Health checks..."
echo "Backend health:"
docker exec deploy-backend-1 curl -sf http://localhost:8001/health/ || echo "❌ Backend health check failed"

echo ""
echo "Redis connection test:"
docker exec deploy-redis-1 redis-cli ping || echo "❌ Redis connection failed"

echo ""
echo "Caddy status:"
docker logs --tail 5 deploy-caddy-1 | grep -E "(server running|started|error)" || echo "Check caddy logs manually"

echo ""
echo "🌐 Testing local endpoints..."
echo "Frontend (via Caddy):"
curl -I http://localhost/ 2>/dev/null | head -1 || echo "❌ Frontend test failed"

echo ""
echo "Backend health (direct):"
curl -sf http://localhost/health/ | jq '.status' 2>/dev/null || echo "❌ Backend health via Caddy failed"

echo ""
echo "Backend API (strategies):"
curl -sf http://localhost/api/v1/strategies/ | jq '.success' 2>/dev/null || echo "❌ Strategies API test failed"

echo ""
echo "🎉 Local deployment complete!"
echo ""
echo "📍 Your DeFi platform is available at:"
echo "   🔗 http://localhost/ (Firefox/Safari)"
echo "   🔗 http://localhost:8080/ (Chrome - avoids HSTS cache)"
echo "   🔗 Backend API: http://localhost/api/v1/"
echo "   🔗 API Docs: http://localhost/docs"
echo "   🔗 Health Check: http://localhost/health/"
echo ""
echo "🔧 Useful commands:"
echo "   View logs:        docker compose logs"
echo "   Follow logs:      docker compose logs -f"
echo "   Restart:          docker compose restart"
echo "   Stop:             ./stop-local.sh"
echo "   Quick stop:       docker compose down"
echo "   Rebuild:          ./deploy-local.sh"
echo ""
echo "🐛 Debug commands:"
echo "   Backend logs:     docker logs deploy-backend-1"
echo "   Backend shell:    docker exec -it deploy-backend-1 /bin/bash"
echo "   Caddy logs:       docker logs deploy-caddy-1"
echo "   Redis logs:       docker logs deploy-redis-1"
echo "   Redis CLI:        docker exec -it deploy-redis-1 redis-cli"
echo ""
echo "🧪 Test endpoints:"
echo "   curl http://localhost/health/"
echo "   curl http://localhost/api/v1/strategies/"
echo "   curl http://localhost/api/v1/results/"
echo ""
echo "📝 Note: This is a local dev deployment."
echo "   - No HTTPS/SSL certificates"
echo "   - No authentication required"
echo "   - Data persisted in Docker volumes"
echo "   - Configs mounted read-only from ../configs/"
echo "   - Environment: backend/env.unified"
echo ""
echo "🔧 Troubleshooting:"
echo "   If Chrome redirects to HTTPS:"
echo "     1. Use port 8080: http://localhost:8080/"
echo "     2. Clear HSTS cache: chrome://net-internals/#hsts → Delete 'localhost'"
echo "     3. Use incognito mode"
echo "   If build fails with credential errors:"
echo "     1. Ensure Docker Desktop is running"
echo "     2. Try: docker login"
echo "     3. Or run with: DOCKER_BUILDKIT=0 ./deploy-local.sh"
echo "   If containers won't start:"
echo "     1. Check ports aren't in use: lsof -i :80"
echo "     2. Check Docker daemon: docker system info"
echo "     3. View detailed logs: docker compose logs"
