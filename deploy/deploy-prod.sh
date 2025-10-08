#!/bin/bash
# Production Deployment Script for DeFi Yield Optimization Platform
# Usage: ./deploy-prod.sh

set -e  # Exit on any error

echo "🚀 Starting production deployment..."
echo ""
echo "📍 Deployment Environment:"
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "   Platform: macOS (local testing)"
    echo "   Note: Ensure your domain DNS points to this machine's IP"
    echo "   Note: Router/firewall must allow ports 80/443 from internet"
else
    echo "   Platform: Linux (likely GCloud VM)"
    echo "   Note: Ensure GCloud firewall allows ports 80/443"
    echo "   Note: Static IP should be assigned and DNS configured"
fi
echo "   Environment: backend/env.unified"
echo ""

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found. Please run this script from the deploy/ directory."
    exit 1
fi

# Set up production environment
echo "📋 Setting up production environment..."
./switch-env.sh prod

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found. Creating template..."
    cat > .env << 'EOF'
# Production Environment Configuration
APP_DOMAIN=defi-project.odum-research.com
ACME_EMAIL=ikenna@odum-research.com
BASIS_API__CORS_ORIGINS=["https://defi-project.odum-research.com"]

# Generated hash for admin/password
BASIC_AUTH_HASH=\$2a\$14\$0.4F1fiBLFTO7XEtL9FiMuvno5m4wADn9sF6hTydjc5.02zFiS5vq

# Backend Configuration
BASIS_API__PORT=8001
BASIS_API__REDIS__URL=redis://redis:6379/0
EOF
    echo "✅ Created .env template with your domain configuration"
    echo ""
echo "🔧 Next steps:"
echo "1. Configure backend/env.unified with production settings:"
echo "   - BASIS_ENVIRONMENT=production"
echo "   - BASIS_DEPLOYMENT=cloud"
echo "   - BASIS_API__CORS_ORIGINS=[\"https://defi-project.odum-research.com\"]"
echo "2. Ensure DNS points to this machine:"
echo "   - Production: defi-project.odum-research.com → [GCloud VM IP]"
echo "   - Or for Mac testing: defi-project.odum-research.com → $(curl -s ifconfig.me)"
echo "3. Ensure ports 80/443 are accessible from internet"
echo "4. Run ./deploy-prod.sh again"
    echo ""
    echo "🔐 Authentication: admin/password (hash pre-configured)"
    echo ""
    echo "📝 Note: The .env file is configured for your domain: defi-project.odum-research.com"
    exit 0
fi

echo "📋 Checking environment configuration..."
source .env
echo "   Domain: ${APP_DOMAIN}"
echo "   Email: ${ACME_EMAIL}"
echo "   Basic Auth: $([ -n "$BASIC_AUTH_HASH" ] && echo "✅ Configured" || echo "❌ Not set")"

echo ""
echo "🛑 Stopping existing containers..."
docker compose down

echo ""
echo "🧹 Cleaning up unused images (optional)..."
docker image prune -f

echo ""
echo "🔨 Building and starting production containers..."

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
echo "🌐 Testing production endpoints..."
echo "HTTP redirect (should return 301/308):"
curl -I http://${APP_DOMAIN}/ 2>/dev/null | head -1 || echo "❌ HTTP test failed"

echo ""
echo "HTTPS health (with auth):"
if [ -n "$BASIC_AUTH_HASH" ]; then
    echo "   (Note: Basic Auth is enabled - test manually with: curl -u admin:password https://${APP_DOMAIN}/health/detailed)"
else
    curl -I https://${APP_DOMAIN}/health/detailed 2>/dev/null | head -1 || echo "❌ HTTPS health test failed"
fi

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "📍 Your DeFi platform is available at:"
echo "   🔗 https://${APP_DOMAIN}/"
echo ""
echo "🔧 Useful commands:"
echo "   View logs:     docker compose logs"
echo "   Restart:       docker compose restart"
echo "   Stop:          ./stop-prod.sh"
echo "   Quick stop:    docker compose down"
echo "   Update:        git pull && ./deploy-prod.sh"
echo ""
echo "📚 For troubleshooting, check:"
echo "   Backend logs:  docker logs deploy-backend-1"
echo "   Caddy logs:    docker logs deploy-caddy-1"
echo "   Redis logs:    docker logs deploy-redis-1"
