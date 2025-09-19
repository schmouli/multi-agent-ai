#!/bin/bash

# Enhanced Quick Push Script - accepts custom commit message
# Usage: ./enhanced-quick-push.sh [commit-message]

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Get commit message from parameter or use default
COMMIT_MESSAGE="${1:-chore: quick update}"

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)

print_status "Committing and pushing changes..."
print_status "Branch: $CURRENT_BRANCH"
print_status "Message: $COMMIT_MESSAGE"

# Add all changes
git add .

# Check if there are changes to commit
if git diff --cached --quiet; then
    print_status "No changes to commit"
    exit 0
fi

# Commit changes
git commit -m "$COMMIT_MESSAGE"
print_success "Changes committed"

# Check current git remote
git remote -v

# If it's using HTTPS, switch to SSH (for GitHub)
git remote set-url origin git@github.com:schmouli/multi-agent-ai.git
print_status "Switched remote to SSH"

# Push to remote
git push origin "$CURRENT_BRANCH"
print_success "Changes pushed to $CURRENT_BRANCH"

print_success "Quick push completed!"