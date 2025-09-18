#!/bin/bash
# filepath: /home/danny/code/multi-agent-ai/scripts/clean-env.sh

echo "🧹 Cleaning up development environment..."

cd "$(dirname "$0")/.."

# Stop any running containers
echo "Stopping Docker containers..."
docker-compose down 2>/dev/null || true

# Remove virtual environment completely
echo "Removing virtual environment..."
sudo rm -rf .venv 2>/dev/null || rm -rf .venv

# Clean Python cache
echo "Cleaning Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# Remove any lock files
echo "Removing lock files..."
rm -f .venv/.lock 2>/dev/null || true
rm -f uv.lock 2>/dev/null || true

# Recreate virtual environment
echo "Creating fresh virtual environment..."
uv venv

# Install base dependencies
echo "Installing dependencies..."
uv add fastapi uvicorn python-dotenv httpx pydantic websockets

echo "✅ Environment cleaned and recreated!"
echo "Run './scripts/test.sh' to install test dependencies and run tests"