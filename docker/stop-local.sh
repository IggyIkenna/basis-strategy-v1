#!/bin/bash
# Stop Local Docker Deployment
# Usage: ./stop.sh

set -e

echo "🛑 Stopping local Docker deployment..."

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
echo "🧹 Cleaning up volumes (optional)..."
read -p "Remove data volumes? This will delete all stored data (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker compose down -v
    echo "✅ Volumes removed"
else
    echo "📦 Volumes preserved"
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
echo "✅ Local Docker deployment stopped!"
echo ""
echo "🔧 To start again:"
echo "   ./deploy-local.sh        # Full deployment with build"
echo "   ./deploy-local-simple.sh # Quick start with existing images"
echo ""
echo "📝 Note: Uses backend/env.unified for configuration"
echo ""
echo "📊 Check remaining containers:"
echo "   docker ps"

