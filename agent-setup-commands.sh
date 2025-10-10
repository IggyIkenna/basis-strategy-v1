#!/bin/bash

# Manual setup commands for Cursor Background Agents
# Run these commands in the agent environment terminal

echo "🚀 Setting up environment for Cursor Background Agents..."

# Update system packages
sudo apt-get update

# Install Python and pip
sudo apt-get install -y python3 python3-pip python3-venv

# Install Node.js and npm
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Python dependencies
pip3 install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..

# Verify installations
echo "✅ Python version: $(python3 --version)"
echo "✅ Node.js version: $(node --version)"
echo "✅ npm version: $(npm --version)"

echo "🎉 Environment setup complete!"
