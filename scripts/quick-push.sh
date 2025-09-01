#!/bin/bash

# 🚀 Quick GitHub Push Script
# Simple script for quick commits and pushes

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

cd "$(dirname "$0")/.."

# Quick commit with timestamp if no message provided
if [ -z "$1" ]; then
    COMMIT_MESSAGE="Update $(date '+%Y-%m-%d %H:%M')"
else
    COMMIT_MESSAGE="$1"
fi

echo -e "${BLUE}🚀 Quick push: ${COMMIT_MESSAGE}${NC}"

git add .
git commit -m "$COMMIT_MESSAGE"
git push origin "$(git branch --show-current)"

echo -e "${GREEN}✅ Pushed to GitHub!${NC}"
