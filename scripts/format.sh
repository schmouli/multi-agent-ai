#!/bin/bash
# Format all Python files with black, isort, and check with flake8

echo "🔧 Running isort..."
uv run isort server/ client/

echo "🎨 Running black..."
uv run black server/ client/

echo "🔍 Running flake8..."
uv run flake8 server/ client/ --statistics

echo "✅ All formatters completed!"
