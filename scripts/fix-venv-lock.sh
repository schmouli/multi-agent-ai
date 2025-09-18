#!/bin/bash
# filepath: /home/danny/code/multi-agent-ai/scripts/fix-venv-lock.sh

echo "🔧 Fixing .venv lock file permission issues..."

# Change to project root
cd "$(dirname "$0")/.."

# Remove the problematic lock file
if [ -f ".venv/.lock" ]; then
    echo "Removing .venv/.lock file..."
    sudo rm -f .venv/.lock
fi

# Fix permissions on the entire .venv directory
if [ -d ".venv" ]; then
    echo "Fixing .venv directory permissions..."
    sudo chown -R $USER:$USER .venv
    chmod -R u+w .venv
fi

echo "✅ .venv permissions fixed!"