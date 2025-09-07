#!/bin/bash

# Test runner script for the FastAPI-based multi-agent healthcare system.
# This script runs comprehensive tests including unit tests, integration tests, and curl-equivalent tests.

# Set script options
set -e  # Exit on any error
set -u  # Exit on undefined variables

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to run tests with proper error handling
run_test_suite() {
    local test_name="$1"
    local test_file="$2"
    local test_args="${3:-}"
    
    print_status "Running $test_name..."
    
    if uv run pytest "$test_file" $test_args -v --tb=short; then
        print_success "$test_name completed successfully"
        return 0
    else
        print_error "$test_name failed"
        return 1
    fi
}

# Main test execution
main() {
    print_status "Starting FastAPI Healthcare Agent Test Suite"
    
    # Check prerequisites
    if ! command_exists uv; then
        print_error "uv is not installed. Please install it from https://docs.astral.sh/uv/"
        exit 1
    fi
    
    # Get the directory of this script
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
    
    print_status "Project root: $PROJECT_ROOT"
    print_status "Test directory: $SCRIPT_DIR"
    
    # Change to project root for tests
    cd "$PROJECT_ROOT"
    
    # Initialize test result tracking
    local total_tests=0
    local passed_tests=0
    local failed_tests=0
    
    # Test configuration
    local test_suites=(
        "MCP Server Tests:tests/test_mcpserver.py:"
        "FastAPI Agent Server Tests:tests/test_fastapi_agent_server.py:"
        "Web Client Tests:tests/test_web_client.py:"
        "Integration Tests:tests/test_integration.py:"
    )
    
    print_status "Running individual test suites..."
    
    # Run each test suite
    for suite in "${test_suites[@]}"; do
        IFS=':' read -r name file args <<< "$suite"
        total_tests=$((total_tests + 1))
        
        if run_test_suite "$name" "$file" "$args"; then
            passed_tests=$((passed_tests + 1))
        else
            failed_tests=$((failed_tests + 1))
        fi
        echo ""
    done
    
    # Run curl-equivalent tests specifically
    print_status "Running curl-equivalent tests..."
    total_tests=$((total_tests + 1))
    
    if uv run pytest tests/ -k "curl" -v --tb=short; then
        print_success "Curl-equivalent tests completed successfully"
        passed_tests=$((passed_tests + 1))
    else
        print_error "Curl-equivalent tests failed"
        failed_tests=$((failed_tests + 1))
    fi
    echo ""
    
    # Run async tests specifically
    print_status "Running async tests..."
    total_tests=$((total_tests + 1))
    
    if uv run pytest tests/ -k "async" -v --tb=short; then
        print_success "Async tests completed successfully"
        passed_tests=$((passed_tests + 1))
    else
        print_error "Async tests failed"
        failed_tests=$((failed_tests + 1))
    fi
    echo ""
    
    # Run complete test suite
    print_status "Running complete test suite..."
    total_tests=$((total_tests + 1))
    
    if uv run pytest tests/ --tb=short --cov=server --cov=client --cov-report=term-missing; then
        print_success "Complete test suite passed"
        passed_tests=$((passed_tests + 1))
    else
        print_error "Complete test suite failed"
        failed_tests=$((failed_tests + 1))
    fi
    
    # Print summary
    echo ""
    print_status "Test Summary:"
    echo "  Total test suites: $total_tests"
    echo "  Passed: $passed_tests"
    echo "  Failed: $failed_tests"
    
    if [ "$failed_tests" -eq 0 ]; then
        print_success "All tests passed! 🎉"
        exit 0
    else
        print_error "Some tests failed. Please check the output above."
        exit 1
    fi
}

# Help function
show_help() {
    echo "FastAPI Healthcare Agent Test Runner"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -q, --quiet    Run tests in quiet mode"
    echo "  -v, --verbose  Run tests in verbose mode"
    echo "  -f, --fast     Run only fast tests (skip slow tests)"
    echo "  -c, --coverage Show test coverage report"
    echo ""
    echo "Test Categories:"
    echo "  - MCP Server Tests: Test the Model Context Protocol server"
    echo "  - FastAPI Agent Server Tests: Test the main agent server"
    echo "  - Web Client Tests: Test the web interface"
    echo "  - Integration Tests: Test end-to-end functionality"
    echo "  - Curl-equivalent Tests: Test HTTP API compatibility"
    echo ""
    echo "Examples:"
    echo "  $0                    # Run all tests"
    echo "  $0 --fast             # Run only fast tests"
    echo "  $0 --coverage         # Run tests with coverage report"
}

# Parse command line arguments
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    -q|--quiet)
        export PYTEST_ARGS="-q"
        main
        ;;
    -v|--verbose)
        export PYTEST_ARGS="-v -s"
        main
        ;;
    -f|--fast)
        export PYTEST_ARGS="-m 'not slow'"
        main
        ;;
    -c|--coverage)
        export PYTEST_ARGS="--cov=server --cov=client --cov-report=html --cov-report=term"
        main
        ;;
    "")
        main
        ;;
    *)
        print_error "Unknown option: $1"
        show_help
        exit 1
        ;;
esac
