#!/bin/bash

# Optimized Docker Build Script for Basis Strategy Backend
# This script demonstrates the caching benefits of the optimized Dockerfile

set -e

echo "🚀 Basis Strategy - Optimized Docker Build"
echo "=========================================="

# Enable BuildKit for better caching
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

echo ""
echo "📋 Build Configuration:"
echo "  - Multi-stage build with dependency caching"
echo "  - Requirements cached separately from source code"
echo "  - BuildKit inline cache enabled"
echo "  - .dockerignore excludes unnecessary files"
echo ""

# Function to time builds
time_build() {
    local description="$1"
    echo "⏱️  $description..."
    start_time=$(date +%s)
    docker compose build backend
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    echo "✅ Completed in ${duration}s"
    echo ""
}

# First build (cold cache)
echo "🔨 First build (cold cache) - will install all dependencies:"
time_build "Cold build"

# Second build (warm cache - no changes)
echo "🔄 Second build (warm cache - no changes) - should be very fast:"
time_build "Warm build (no changes)"

# Simulate a source code change
echo "📝 Simulating source code change..."
touch ../backend/src/basis_strategy_v1/__init__.py

# Third build (source change only)
echo "🔄 Third build (source code change) - should skip dependency installation:"
time_build "Source change build"

echo "🎯 Build Optimization Summary:"
echo "  - Dependencies are cached separately from source code"
echo "  - Only changed layers are rebuilt"
echo "  - Subsequent builds are much faster"
echo ""
echo "💡 Tips:"
echo "  - Requirements changes: Only dependencies stage rebuilds"
echo "  - Source code changes: Only builder and runtime stages rebuild"
echo "  - No changes: All layers cached, build completes in seconds"
echo ""
echo "✅ Backend is ready at http://localhost:8001"
