#!/bin/bash

# Frontend Setup Script for Cursor Background Agents
# This script ensures the frontend can be built on demand by background agents

set -e

echo "🚀 Setting up frontend for Cursor background agents..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Installing via Homebrew..."
    
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo "❌ Homebrew is not installed. Please install Homebrew first:"
        echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
    
    # Install Node.js via Homebrew
    brew install node
    echo "✅ Node.js installed successfully"
fi

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not available. Please ensure Node.js installation includes npm."
    exit 1
fi

echo "✅ Node.js version: $(node --version)"
echo "✅ npm version: $(npm --version)"

# Navigate to frontend directory
cd "$(dirname "$0")/../frontend"

# Install dependencies
echo "📦 Installing frontend dependencies..."
npm install

# Build the frontend
echo "🔨 Building frontend..."
npm run build

echo "✅ Frontend setup complete! Background agents can now build the frontend on demand."
echo ""
echo "📋 Available commands:"
echo "   npm run dev     - Start development server"
echo "   npm run build   - Build for production"
echo "   npm run lint    - Run linting"
echo "   npm run test    - Run tests"
