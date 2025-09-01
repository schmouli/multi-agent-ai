#!/bin/bash
# Test runner script for multi-agent-ai project

set -e

echo "🧪 Running pytest for multi-agent-ai project..."
echo "=============================================="

# Change to project directory (parent of scripts directory)
cd "$(dirname "$0")/.."

# Ensure we have the latest dependencies
echo "📦 Syncing dependencies..."
uv sync

# Run different test categories
echo ""
echo "🔬 Running unit tests..."
uv run pytest tests/ -v -m "not slow" --tb=short

echo ""
echo "📊 Running tests with coverage..."
uv run pytest tests/ --cov=server --cov=client --cov-report=term-missing --cov-report=html:htmlcov

echo ""
echo "🚀 Running all tests (including slow ones)..."
uv run pytest tests/ -v

echo ""
echo "✅ All tests completed!"
echo ""
echo "📈 Coverage report generated in htmlcov/"
echo "🔍 To view detailed coverage: open htmlcov/index.html"
