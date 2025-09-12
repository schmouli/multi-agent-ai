#!/bin/bash
# filepath: /home/danny/code/multi-agent-ai/scripts/ci-pipeline.sh

# CI Pipeline Script - Format, Test, Build, Deploy
# Runs the complete development pipeline with intelligent commit messages

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

# Function to generate intelligent commit message
generate_commit_message() {
    local changes=""
    local message="chore: automated pipeline update"
    
    # Check for different types of changes
    if git diff --cached --name-only | grep -q "\.py$"; then
        if git diff --cached | grep -q "def \|class \|import "; then
            changes="${changes}feat: add new functionality, "
        elif git diff --cached | grep -q "fix\|bug\|error"; then
            changes="${changes}fix: resolve issues, "
        else
            changes="${changes}refactor: improve code quality, "
        fi
    fi
    
    if git diff --cached --name-only | grep -q "test_"; then
        changes="${changes}test: update tests, "
    fi
    
    if git diff --cached --name-only | grep -q "\.md$\|README\|CHANGELOG"; then
        changes="${changes}docs: update documentation, "
    fi
    
    if git diff --cached --name-only | grep -q "Dockerfile\|docker-compose\|\.yml$\|\.yaml$"; then
        changes="${changes}ci: update build configuration, "
    fi
    
    if git diff --cached --name-only | grep -q "requirements\|pyproject\|package"; then
        changes="${changes}deps: update dependencies, "
    fi
    
    # Check for insurance agent changes
    if git diff --cached --name-only | grep -q "insurance_agent_server\|data/"; then
        changes="${changes}feat: update insurance agent service, "
    fi
    
    # Check for server additions
    if git diff --cached --name-only | grep -q "server/.*\.py$"; then
        changes="${changes}feat: update server components, "
    fi
    
    # Remove trailing comma and space
    changes=$(echo "$changes" | sed 's/, $//')
    
    # If we detected specific changes, use them; otherwise use default
    if [ -n "$changes" ]; then
        message="$changes"
    fi
    
    # Add files changed summary
    local files_changed=$(git diff --cached --name-only | wc -l)
    if [ "$files_changed" -gt 0 ]; then
        message="${message} (${files_changed} files changed)"
    fi
    
    echo "$message"
}

# Function to check if we're in git repo
check_git_repo() {
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        print_error "Not in a git repository"
    fi
}

# Function to check for uncommitted changes
check_working_directory() {
    if ! git diff-index --quiet HEAD --; then
        print_warning "You have uncommitted changes. Staging all changes..."
        git add .
    elif git diff --cached --quiet; then
        print_warning "No changes to commit"
        return 1
    fi
    return 0
}

# Main pipeline function
run_pipeline() {
    local skip_format=false
    local skip_tests=false
    local skip_build=false
    local custom_message=""
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-format)
                skip_format=true
                shift
                ;;
            --skip-tests)
                skip_tests=true
                shift
                ;;
            --skip-build)
                skip_build=true
                shift
                ;;
            -m|--message)
                custom_message="$2"
                shift 2
                ;;
            -h|--help)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --skip-format    Skip code formatting step"
                echo "  --skip-tests     Skip testing step"
                echo "  --skip-build     Skip build step"
                echo "  -m, --message    Custom commit message"
                echo "  -h, --help       Show this help message"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                ;;
        esac
    done
    
    print_status "🚀 Starting CI Pipeline..."
    
    # Check prerequisites
    check_git_repo
    
    # Check for changes
    if ! check_working_directory; then
        print_status "No changes detected. Pipeline complete."
        exit 0
    fi
    
    # Step 1: Format Code
    if [ "$skip_format" = false ]; then
        print_status "📝 Step 1/4: Running code formatter..."
        if bash "$(dirname "$0")/format.sh"; then
            print_success "Code formatting completed successfully"
            # Stage any formatting changes
            git add .
        else
            print_error "Code formatting failed"
        fi
    else
        print_warning "Skipping code formatting step"
    fi
    
    # Step 2: Run Tests
    if [ "$skip_tests" = false ]; then
        print_status "🧪 Step 2/4: Running tests..."
        if bash "$(dirname "$0")/test.sh"; then
            print_success "All tests passed"
        else
            print_error "Tests failed"
        fi
    else
        print_warning "Skipping tests step"
    fi
    
    # Step 3: Build
    if [ "$skip_build" = false ]; then
        print_status "🔨 Step 3/4: Building project..."
        if bash "$(dirname "$0")/build.sh"; then
            print_success "Build completed successfully"
        else
            print_error "Build failed"
        fi
    else
        print_warning "Skipping build step"
    fi
    
    # Step 4: Push changes
    print_status "📤 Step 4/4: Pushing changes..."
    
    # Generate or use custom commit message
    local commit_message
    if [ -n "$custom_message" ]; then
        commit_message="$custom_message"
    else
        commit_message=$(generate_commit_message)
    fi
    
    print_status "Commit message: $commit_message"
    
    # Check if quick-push.sh exists and is executable
    local push_script="$(dirname "$0")/quick-push.sh"
    if [ -f "$push_script" ] && [ -x "$push_script" ]; then
        # Pass the commit message to quick-push.sh
        if bash "$push_script" "$commit_message"; then
            print_success "Changes pushed successfully"
        else
            print_error "Push failed"
        fi
    else
        # Fallback: manual git operations
        print_status "quick-push.sh not found, using manual git operations..."
        
        # Commit changes
        if git commit -m "$commit_message"; then
            print_success "Changes committed successfully"
        else
            print_error "Commit failed"
        fi
        
        # Push to remote
        local current_branch=$(git branch --show-current)
        if git push origin "$current_branch"; then
            print_success "Changes pushed to $current_branch"
        else
            print_error "Push to remote failed"
        fi
    fi
    
    print_success "🎉 CI Pipeline completed successfully!"
    print_status "Summary:"
    print_status "  ✅ Code formatted and validated"
    if [ "$skip_tests" = false ]; then
        print_status "  ✅ All tests passed"
    fi
    if [ "$skip_build" = false ]; then
        print_status "  ✅ Build successful"
    fi
    print_status "  ✅ Changes committed and pushed"
    print_status ""
    print_status "🌐 Services available:"
    print_status "  - MCP Server: http://localhost:8333"
    print_status "  - FastAPI Server: http://localhost:7000"
    print_status "  - Insurance Server: http://localhost:7001"
    print_status "  - Web Client: http://localhost:7080"
}

# Script entry point
main() {
    # Change to script directory
    cd "$(dirname "$0")"
    
    # Change to project root (assuming scripts are in scripts/ subdirectory)
    cd ..
    
    # Run the pipeline
    run_pipeline "$@"
}

# Run main function with all arguments
main "$@"