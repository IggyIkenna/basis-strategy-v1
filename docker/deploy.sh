#!/bin/bash
# Unified Docker Deployment Script
# Usage: ./deploy.sh [environment] [services] [action]
# 
# Examples:
#   ./deploy.sh local backend start
#   ./deploy.sh prod all start  
#   ./deploy.sh staging backend stop
#   ./deploy.sh local all restart

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT=${1:-local}
SERVICES=${2:-all}
ACTION=${3:-start}

show_help() {
    echo -e "${BLUE}🚀 Unified Docker Deployment Script${NC}"
    echo ""
    echo "Usage: $0 [ENVIRONMENT] [SERVICES] [ACTION]"
    echo ""
    echo -e "${GREEN}Parameters:${NC}"
    echo "  ENVIRONMENT    local|staging|prod (default: local)"
    echo "  SERVICES       backend|frontend|all (default: all)"
    echo "  ACTION         start|stop|restart|status|logs (default: start)"
    echo ""
    echo -e "${GREEN}Examples:${NC}"
    echo "  $0 local backend start     # Start backend in local environment"
    echo "  $0 prod all start          # Start all services in production"
    echo "  $0 staging backend stop    # Stop backend in staging"
    echo "  $0 local all restart       # Restart all services locally"
    echo "  $0 prod all status         # Check status of production deployment"
    echo "  $0 local backend logs      # View backend logs locally"
    echo ""
    echo -e "${YELLOW}Environment Files:${NC}"
    echo "  local    → docker/.env.dev"
    echo "  staging  → docker/.env.staging" 
    echo "  prod     → docker/.env.prod"
    echo ""
    echo -e "${YELLOW}Services:${NC}"
    echo "  backend  → Backend API + Redis"
    echo "  frontend → Backend + Caddy (reverse proxy)"
    echo "  all      → Backend + Caddy + Redis"
}

validate_environment() {
    case $ENVIRONMENT in
        local|staging|prod)
            return 0
            ;;
        *)
            echo -e "${RED}❌ Invalid environment: $ENVIRONMENT${NC}"
            echo "Valid environments: local, staging, prod"
            return 1
            ;;
    esac
}

validate_services() {
    case $SERVICES in
        backend|frontend|all)
            return 0
            ;;
        *)
            echo -e "${RED}❌ Invalid services: $SERVICES${NC}"
            echo "Valid services: backend, frontend, all"
            return 1
            ;;
    esac
}

validate_action() {
    case $ACTION in
        start|stop|restart|status|logs)
            return 0
            ;;
        *)
            echo -e "${RED}❌ Invalid action: $ACTION${NC}"
            echo "Valid actions: start, stop, restart, status, logs"
            return 1
            ;;
    esac
}

setup_environment() {
    echo -e "${BLUE}🔧 Setting up $ENVIRONMENT environment...${NC}"
    
    # Copy environment-specific file to .env (docker uses docker/.env.* files)
    case $ENVIRONMENT in
        local)
            cp .env.dev .env
            ;;
        staging)
            cp .env.staging .env
            ;;
        prod)
            cp .env.prod .env
            ;;
    esac
    
    echo -e "${GREEN}✅ Environment configured: $ENVIRONMENT${NC}"
}

get_compose_services() {
    case $SERVICES in
        backend)
            echo "redis backend"
            ;;
        frontend)
            echo "redis backend caddy"
            ;;
        all)
            echo "redis backend caddy"
            ;;
    esac
}

start_services() {
    echo -e "${BLUE}🚀 Starting $SERVICES services in $ENVIRONMENT environment...${NC}"
    
    setup_environment
    
    # Validate deployment configuration
    validate_deployment_config
    
    local compose_services=$(get_compose_services)
    
    echo -e "${BLUE}📦 Building and starting: $compose_services${NC}"
    docker compose up -d --build $compose_services
    
    # Wait for services to be healthy
    echo -e "${BLUE}⏳ Waiting for services to be healthy...${NC}"
    sleep 10
    
    # Health check backend
    if ! curl -f http://localhost:8001/health/ >/dev/null 2>&1; then
        echo -e "${RED}❌ Backend health check failed${NC}"
        return 1
    fi
    
    # Health check frontend (if deployed)
    if [[ "$SERVICES" == "frontend" || "$SERVICES" == "all" ]]; then
        # Test by IP
        if ! curl -f http://localhost/ >/dev/null 2>&1; then
            echo -e "${RED}❌ Frontend health check failed (localhost)${NC}"
            return 1
        fi
        
        # Test by domain (if not localhost)
        if [ "$APP_DOMAIN" != "localhost" ]; then
            if ! curl -f "http://$APP_DOMAIN/" >/dev/null 2>&1; then
                echo -e "${YELLOW}⚠️ Frontend not accessible via domain: $APP_DOMAIN${NC}"
                echo -e "${YELLOW}💡 Check DNS configuration${NC}"
            else
                echo -e "${GREEN}✅ Frontend accessible via domain: $APP_DOMAIN${NC}"
            fi
        fi
    fi
    
    show_status
}

validate_deployment_config() {
    # Validate required environment variables are set
    if [ -z "$BASIS_ENVIRONMENT" ]; then
        echo -e "${RED}❌ BASIS_ENVIRONMENT not set${NC}"
        return 1
    fi
    
    if [ -z "$BASIS_DEPLOYMENT_MACHINE" ]; then
        echo -e "${RED}❌ BASIS_DEPLOYMENT_MACHINE not set${NC}"
        return 1
    fi
    
    # Validate frontend vars if deploying frontend
    if [[ "$SERVICES" == "frontend" || "$SERVICES" == "all" ]]; then
        if [ -z "$APP_DOMAIN" ]; then
            echo -e "${RED}❌ APP_DOMAIN not set (required for frontend deployment)${NC}"
            return 1
        fi
        if [ -z "$ACME_EMAIL" ]; then
            echo -e "${RED}❌ ACME_EMAIL not set (required for frontend deployment)${NC}"
            return 1
        fi
    fi
}

stop_services() {
    echo -e "${BLUE}🛑 Stopping $SERVICES services...${NC}"
    
    local compose_services=$(get_compose_services)
    docker compose stop $compose_services
    
    echo -e "${GREEN}✅ Services stopped${NC}"
}

restart_services() {
    echo -e "${BLUE}🔄 Restarting $SERVICES services...${NC}"
    
    local compose_services=$(get_compose_services)
    docker compose restart $compose_services
    
    echo -e "${GREEN}✅ Services restarted${NC}"
    show_status
}

show_status() {
    echo -e "${BLUE}📊 Service Status:${NC}"
    echo ""
    
    # Show container status
    docker compose ps
    
    echo ""
    echo -e "${BLUE}🌐 Access Points:${NC}"
    
    # Check if backend is running
    if docker compose ps backend | grep -q "Up"; then
        echo "  ✅ Backend API: http://localhost:8001"
        echo "  ✅ API Docs: http://localhost:8001/docs"
        echo "  ✅ Health: http://localhost:8001/health/"
    else
        echo "  ❌ Backend: Not running"
    fi
    
    # Check if caddy is running
    if docker compose ps caddy | grep -q "Up"; then
        echo "  ✅ Frontend: http://localhost/"
        echo "  ✅ HTTPS: http://localhost:443/"
    else
        echo "  ❌ Frontend: Not running"
    fi
    
    echo ""
    echo -e "${BLUE}📋 Environment: $ENVIRONMENT${NC}"
    echo -e "${BLUE}🔧 Services: $SERVICES${NC}"
}

show_logs() {
    echo -e "${BLUE}📋 Showing logs for $SERVICES services...${NC}"
    
    local compose_services=$(get_compose_services)
    docker compose logs -f $compose_services
}

# Main script logic
if [ "$1" = "help" ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_help
    exit 0
fi

# Validate parameters
if ! validate_environment || ! validate_services || ! validate_action; then
    echo ""
    show_help
    exit 1
fi

# Execute action
case $ACTION in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
esac