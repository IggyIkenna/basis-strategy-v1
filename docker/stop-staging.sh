#!/bin/bash
# Stop Staging Docker Deployment
# Usage: ./stop-staging.sh

set -e

echo "🛑 Stopping staging Docker deployment..."

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found. Please run this script from the deploy/ directory."
    exit 1
fi

echo ""
echo "🔍 Checking running containers..."
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(deploy-|NAMES)" || echo "No deploy containers running"

echo ""
echo "🛑 Stopping and removing containers..."
docker compose down

echo ""
echo "⚠️  Staging data management:"
echo "   Data volumes are preserved by default for safety"
echo "   Results and logs remain in Docker volumes"

echo ""
echo "🧹 Advanced cleanup options:"
read -p "Remove ALL data volumes? ⚠️  This will delete all staging data! (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚨 Removing staging volumes..."
    docker compose down -v
    echo "✅ All staging data removed"
else
    echo "📦 Staging volumes preserved (recommended)"
fi

echo ""
echo "🧹 Clean up unused images? (optional)"
read -p "Remove unused Docker images to free space? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker image prune -f
    echo "✅ Unused images removed"
else
    echo "🖼️ Images preserved"
fi

echo ""
echo "✅ Staging deployment stopped!"
echo ""
echo "🔧 To restart staging:"
echo "   ./deploy-staging.sh"
echo ""
echo "📊 Check remaining containers:"
echo "   docker ps"
echo ""
echo "📝 Note: SSL certificates and domain configuration preserved"
