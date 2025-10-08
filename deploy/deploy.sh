#!/bin/bash
# DeFi Platform Deployment Management
# Usage: ./deploy.sh [command]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

show_help() {
echo -e "${BLUE}🚀 DeFi Platform Deployment Management${NC}"
echo ""
echo "Usage: $0 [COMMAND]"
echo ""
echo -e "${GREEN}Deployment Commands:${NC}"
echo "  dev                Fast development deployment (smart rebuild)"
echo "  local              Deploy locally with Docker (full build)"
echo "  local-simple       Deploy locally with Docker (no build)"
echo "  staging            Deploy to staging (UAT environment)"
echo "  prod               Deploy to production (GCloud VM)"
echo ""
echo -e "${YELLOW}Environment:${NC}"
echo "  All deployments use: single docker-compose.yml + backend/env.unified"
echo ""
echo -e "${YELLOW}Stop Commands:${NC}"
echo "  stop-local         Stop local Docker deployment"
echo "  stop-staging       Stop staging Docker deployment"
echo "  stop-prod          Stop production deployment"
echo "  stop-all           Stop all deployments"
    echo ""
    echo -e "${BLUE}Utility Commands:${NC}"
    echo "  status             Show deployment status"
    echo "  logs [type]        Show logs (local, prod, or all)"
    echo "  clean              Clean up unused Docker resources"
    echo "  help               Show this help"
    echo ""
    echo -e "${GREEN}Examples:${NC}"
    echo "  $0 local           # Deploy locally"
    echo "  $0 stop-local      # Stop local deployment"
    echo "  $0 status          # Check what's running"
    echo "  $0 logs local      # View local deployment logs"
    echo ""
    echo -e "${BLUE}Access Points (Local):${NC}"
    echo "  Firefox/Safari: http://localhost/"
    echo "  Chrome:         http://localhost:8080/"
    echo "  API:            http://localhost/api/v1/"
    echo "  Docs:           http://localhost/docs"
}

show_status() {
    echo -e "${BLUE}📊 Docker Deployment Status:${NC}"
    echo ""
    
    # Check for running containers
    local containers=$(docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "deploy-" || echo "")
    
    if [ -n "$containers" ]; then
        echo "$containers"
        echo ""
        
        # Test endpoints if containers are running
        if docker ps --format "{{.Names}}" | grep -q "deploy-caddy-1"; then
            echo -e "${GREEN}🌐 Endpoint Tests:${NC}"
            
            # Test port 80
            if curl -sf http://localhost/health/ >/dev/null 2>&1; then
                echo "  ✅ http://localhost/ - Working"
            else
                echo "  ❌ http://localhost/ - Not responding"
            fi
            
            # Test port 8080
            if curl -sf http://localhost:8080/health/ >/dev/null 2>&1; then
                echo "  ✅ http://localhost:8080/ - Working"
            else
                echo "  ❌ http://localhost:8080/ - Not responding"
            fi
        fi
    else
        echo "No deployment containers running"
    fi
    
    echo ""
    echo -e "${BLUE}📦 Docker Resources:${NC}"
    echo "Images: $(docker images --format "table {{.Repository}}" | grep -c "deploy" || echo "0") deployment images"
    echo "Volumes: $(docker volume ls --format "table {{.Name}}" | grep -c "deploy" || echo "0") deployment volumes"
}

show_logs() {
    local type=${1:-all}
    
    case $type in
        local|prod|all|*)
            if [ -f "docker-compose.yml" ]; then
                echo -e "${BLUE}📋 Deployment Logs:${NC}"
                docker compose logs --tail=50
            else
                echo "❌ No deployment found"
            fi
            ;;
    esac
}

clean_resources() {
    echo -e "${YELLOW}🧹 Cleaning Docker Resources...${NC}"
    
    echo "Removing unused images..."
    docker image prune -f
    
    echo "Removing unused volumes..."
    docker volume prune -f
    
    echo "Removing unused networks..."
    docker network prune -f
    
    echo -e "${GREEN}✅ Cleanup complete!${NC}"
}

# Main script logic
case "${1:-help}" in
    dev)
        ./deploy-dev.sh
        ;;
    local)
        ./deploy-local.sh
        ;;
    local-simple)
        ./deploy-local-simple.sh
        ;;
    staging)
        ./deploy-staging.sh
        ;;
    prod)
        ./deploy-prod.sh
        ;;
    stop-local)
        ./stop-local.sh
        ;;
    stop-staging)
        ./stop-staging.sh
        ;;
    stop-prod)
        ./stop-prod.sh
        ;;
    stop-all)
        ./stop-all.sh
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "$2"
        ;;
    clean)
        clean_resources
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac

