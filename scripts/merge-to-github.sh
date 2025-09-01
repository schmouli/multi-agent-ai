#!/bin/bash

# 🚀 Multi-Agent AI Project - GitHub Merge Script
# This script stages, commits, and pushes changes to GitHub

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Multi-Agent AI GitHub Merge Script${NC}"
echo "============================================"

# Get to project root
cd "$(dirname "$0")/.."

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: Not in a git repository${NC}"
    exit 1
fi

# Check for uncommitted changes
echo -e "${YELLOW}📋 Checking git status...${NC}"
git status --porcelain

# Show current branch
CURRENT_BRANCH=$(git branch --show-current)
echo -e "${BLUE}📍 Current branch: ${CURRENT_BRANCH}${NC}"

# Check if remote exists
if ! git remote get-url origin > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: No remote 'origin' configured${NC}"
    exit 1
fi

REMOTE_URL=$(git remote get-url origin)
echo -e "${BLUE}🔗 Remote: ${REMOTE_URL}${NC}"

# Ask for commit message
echo ""
echo -e "${YELLOW}💬 Enter commit message (or press Enter for default):${NC}"
read -r COMMIT_MESSAGE

if [ -z "$COMMIT_MESSAGE" ]; then
    COMMIT_MESSAGE="feat: Add comprehensive testing, formatting, and project organization

- Added pytest test suite with 42 tests (70% coverage)
- Implemented black/isort/flake8 code formatting
- Organized shell scripts into scripts/ directory
- Added Docker containerization with multi-service setup
- Created comprehensive documentation and testing guides"
fi

echo -e "${BLUE}📝 Commit message: ${COMMIT_MESSAGE}${NC}"

# Ask for confirmation
echo ""
echo -e "${YELLOW}🤔 Do you want to proceed with the following actions?${NC}"
echo "1. Stage all changes (git add .)"
echo "2. Commit with message: \"$COMMIT_MESSAGE\""
echo "3. Push to origin/$CURRENT_BRANCH"
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}⏹️  Operation cancelled${NC}"
    exit 0
fi

# Stage all changes
echo -e "${BLUE}📦 Staging changes...${NC}"
git add .

# Show what will be committed
echo -e "${YELLOW}📋 Changes to be committed:${NC}"
git diff --cached --stat

# Commit changes
echo -e "${BLUE}💾 Committing changes...${NC}"
git commit -m "$COMMIT_MESSAGE"

# Push to remote
echo -e "${BLUE}🚀 Pushing to GitHub...${NC}"
git push origin "$CURRENT_BRANCH"

echo ""
echo -e "${GREEN}✅ Successfully merged to GitHub!${NC}"
echo -e "${BLUE}🔗 Repository: ${REMOTE_URL}${NC}"
echo -e "${BLUE}🌿 Branch: ${CURRENT_BRANCH}${NC}"

# Optional: Open GitHub repo in browser
echo ""
read -p "🌐 Open GitHub repository in browser? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Convert SSH URL to HTTPS for browser
    HTTPS_URL=$(echo "$REMOTE_URL" | sed 's/git@github.com:/https:\/\/github.com\//' | sed 's/\.git$//')
    echo -e "${BLUE}🌐 Opening: ${HTTPS_URL}${NC}"
    
    # Try different browser opening commands
    if command -v xdg-open > /dev/null; then
        xdg-open "$HTTPS_URL"
    elif command -v open > /dev/null; then
        open "$HTTPS_URL"
    elif command -v start > /dev/null; then
        start "$HTTPS_URL"
    else
        echo -e "${YELLOW}⚠️  Could not open browser automatically${NC}"
        echo -e "${BLUE}   Please visit: ${HTTPS_URL}${NC}"
    fi
fi

echo ""
echo -e "${GREEN}🎉 All done! Your code is now on GitHub!${NC}"
