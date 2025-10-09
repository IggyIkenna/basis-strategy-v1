#!/bin/bash
# Stop All Docker Deployments
# Usage: ./stop-all.sh

set -e

echo "🛑 Stopping all Docker deployments..."

# Function to stop deployment if compose file exists
stop_deployment() {
    local compose_file=$1
    local deployment_name=$2
    
    if [ -f "$compose_file" ]; then
        echo ""
        echo "🛑 Stopping $deployment_name deployment..."
        docker compose -f "$compose_file" down
        echo "✅ $deployment_name stopped"
    else
        echo "⏭️  $deployment_name: No $compose_file found (skipping)"
    fi
}

# Check if we're in the right directory
if [ ! -d "." ] || [ ! -f "deploy-local.sh" ]; then
    echo "❌ Error: Please run this script from the deploy/ directory."
    exit 1
fi

echo ""
echo "🔍 Checking running containers..."
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(deploy-|NAMES)" || echo "No deploy containers running"

# Stop all deployments
stop_deployment "docker-compose.yml" "Unified"

echo ""
echo "🧹 Cleanup options:"
echo ""
echo "🔧 Remove all deploy-related containers and networks:"
read -p "Clean up all deployment containers and networks? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 Cleaning up deployment infrastructure..."
    
    # Remove any remaining deploy containers
    docker ps -a --format "table {{.Names}}" | grep "deploy-" | xargs -r docker rm -f 2>/dev/null || true
    
    # Remove deploy networks
    docker network ls --format "table {{.Name}}" | grep "deploy" | xargs -r docker network rm 2>/dev/null || true
    
    echo "✅ Deployment infrastructure cleaned"
fi

echo ""
echo "🧹 Remove unused images to free space:"
read -p "Remove unused Docker images? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker image prune -f
    echo "✅ Unused images removed"
else
    echo "🖼️ Images preserved"
fi

echo ""
echo "✅ All deployments stopped!"
echo ""
echo "📊 Remaining containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "🔧 To start deployments:"
echo "   ./deploy-local.sh        # Local dev"
echo "   ./deploy-local-simple.sh # Local (no build)"
echo "   ./deploy-prod.sh         # Production"
echo ""
echo "📝 Note: All deployments use single docker-compose.yml + backend/env.unified"

