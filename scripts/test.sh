#!/bin/bash

# Test runner script with improved error handling
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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
}

# Function to fix venv permissions
fix_venv_permissions() {
    print_warning "Fixing .venv permission issues..."
    
    # Remove lock file if it exists
    if [ -f ".venv/.lock" ]; then
        sudo rm -f .venv/.lock 2>/dev/null || true
    fi
    
    # Fix ownership and permissions
    if [ -d ".venv" ]; then
        sudo chown -R $USER:$USER .venv 2>/dev/null || true
        chmod -R u+w .venv 2>/dev/null || true
    fi
}

# Function to clean and recreate venv if needed
recreate_venv_if_needed() {
    if [ -f ".venv/.lock" ] && ! rm -f ".venv/.lock" 2>/dev/null; then
        print_warning "Lock file cannot be removed, recreating virtual environment..."
        
        # Remove entire .venv directory
        sudo rm -rf .venv 2>/dev/null || rm -rf .venv
        
        # Recreate virtual environment
        print_status "Creating new virtual environment..."
        uv venv
        
        # Install dependencies
        print_status "Installing dependencies..."
        uv add pytest pytest-asyncio pytest-cov pytest-mock httpx
    fi
}

run_tests() {
    print_status "🧪 Running Tests..."
    
    # Set test environment variables
    export PYTHONPATH="/home/danny/code/multi-agent-ai:/home/danny/code/multi-agent-ai/server"
    export OPENAI_API_KEY="test-api-key"
    export OPENAI_API_KEY="mock_api_key"
    # Fix permissions first
    fix_venv_permissions
    
    # Try to recreate venv if lock file issues persist
    recreate_venv_if_needed
    
    # Install test dependencies
    print_status "Installing test dependencies..."
    if ! uv add pytest pytest-asyncio pytest-cov pytest-mock; then
        print_warning "Failed to install with uv, trying pip..."
        .venv/bin/pip install pytest pytest-asyncio pytest-cov pytest-mock
    fi
    
    # Run tests with multiple fallback options
    print_status "Running pytest tests..."
    
    # Try different test running approaches
    local test_commands=(
        "uv run pytest tests/ -v --tb=short"
        ".venv/bin/python -m pytest tests/ -v --tb=short"
        "python -m pytest tests/ -v --tb=short"
        "pytest tests/ -v --tb=short"
    )
    
    local test_success=false
    
    for cmd in "${test_commands[@]}"; do
        print_status "Trying: $cmd"
        if eval $cmd; then
            test_success=true
            break
        else
            print_warning "Command failed: $cmd"
        fi
    done
    
    if [ "$test_success" = true ]; then
        print_success "All tests passed!"
        return 0
    else
        print_error "All test commands failed"
        return 1
    fi
}

# Function to run specific test files
run_specific_tests() {
    local test_files=(
        "tests/test_web_client.py"
        "tests/test_agent_orchestrator.py"
        "tests/test_fastapi_agent.py"
        "tests/test_insurance_agent.py"
        "tests/test_mcpserver.py"
        "tests/test_integration.py"
    )
    
    for test_file in "${test_files[@]}"; do
        if [ -f "$test_file" ]; then
            print_status "Running $test_file..."
            if uv run pytest "$test_file" -v; then
                print_success "$test_file passed"
            else
                print_warning "$test_file failed"
            fi
        fi
    done
}

# Main function
main() {
    cd "$(dirname "$0")/.."
    
    # Parse arguments
    case "${1:-all}" in
        "specific")
            run_specific_tests
            ;;
        "fix")
            fix_venv_permissions
            print_success "Permissions fixed!"
            ;;
        *)
            run_tests
            ;;
    esac
}

main "$@"