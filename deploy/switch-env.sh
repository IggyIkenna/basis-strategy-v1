#!/bin/bash
# Environment Switching Script
# Usage: ./switch-env.sh [local|staging|prod]

set -e

ENV=${1:-local}

echo "🔄 Switching to $ENV environment..."

# Update backend/env.unified based on environment
case $ENV in
    local)
        echo "📋 Configuring for local development..."
        sed -i.bak 's/BASIS_ENVIRONMENT=.*/BASIS_ENVIRONMENT=dev/' ../backend/env.unified
        sed -i.bak 's/BASIS_DEPLOYMENT=.*/BASIS_DEPLOYMENT=local/' ../backend/env.unified
        sed -i.bak 's/BASIS_API__RELOAD=.*/BASIS_API__RELOAD=true/' ../backend/env.unified
        sed -i.bak 's/BASIS_DEBUG=.*/BASIS_DEBUG=true/' ../backend/env.unified
        sed -i.bak 's/BASIS_MONITORING__LOG_LEVEL=.*/BASIS_MONITORING__LOG_LEVEL=DEBUG/' ../backend/env.unified
        cp .env.local .env
        echo "✅ Switched to local development"
        ;;
    staging)
        echo "📋 Configuring for staging..."
        sed -i.bak 's/BASIS_ENVIRONMENT=.*/BASIS_ENVIRONMENT=staging/' ../backend/env.unified
        sed -i.bak 's/BASIS_DEPLOYMENT=.*/BASIS_DEPLOYMENT=cloud/' ../backend/env.unified
        sed -i.bak 's/BASIS_API__RELOAD=.*/BASIS_API__RELOAD=false/' ../backend/env.unified
        sed -i.bak 's/BASIS_DEBUG=.*/BASIS_DEBUG=false/' ../backend/env.unified
        sed -i.bak 's/BASIS_MONITORING__LOG_LEVEL=.*/BASIS_MONITORING__LOG_LEVEL=INFO/' ../backend/env.unified
        cp .env.staging .env
        echo "✅ Switched to staging"
        ;;
    prod)
        echo "📋 Configuring for production..."
        sed -i.bak 's/BASIS_ENVIRONMENT=.*/BASIS_ENVIRONMENT=production/' ../backend/env.unified
        sed -i.bak 's/BASIS_DEPLOYMENT=.*/BASIS_DEPLOYMENT=cloud/' ../backend/env.unified
        sed -i.bak 's/BASIS_API__RELOAD=.*/BASIS_API__RELOAD=false/' ../backend/env.unified
        sed -i.bak 's/BASIS_DEBUG=.*/BASIS_DEBUG=false/' ../backend/env.unified
        sed -i.bak 's/BASIS_MONITORING__LOG_LEVEL=.*/BASIS_MONITORING__LOG_LEVEL=INFO/' ../backend/env.unified
        cp .env.prod .env
        echo "✅ Switched to production"
        ;;
    *)
        echo "❌ Invalid environment: $ENV"
        echo "Usage: $0 [local|staging|prod]"
        exit 1
        ;;
esac

# Clean up backup files
rm -f ../backend/env.unified.bak

echo ""
echo "🔧 Current configuration:"
echo "   Environment: $(grep '^BASIS_ENVIRONMENT=' ../backend/env.unified | cut -d'=' -f2)"
echo "   Deployment: $(grep '^BASIS_DEPLOYMENT=' ../backend/env.unified | cut -d'=' -f2)"
echo "   API Reload: $(grep '^BASIS_API__RELOAD=' ../backend/env.unified | cut -d'=' -f2)"
echo "   Debug: $(grep '^BASIS_DEBUG=' ../backend/env.unified | cut -d'=' -f2)"
echo "   Log Level: $(grep '^BASIS_MONITORING__LOG_LEVEL=' ../backend/env.unified | cut -d'=' -f2)"
echo ""
echo "🚀 To apply changes:"
echo "   docker compose restart backend"
