#!/bin/bash
# filepath: /home/danny/code/multi-agent-ai/scripts/service-manager.sh

# Service Manager Script - Manage individual services
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check docker-compose command
check_compose_cmd() {
    if ! docker-compose version >/dev/null 2>&1; then
        if ! sudo docker-compose version >/dev/null 2>&1; then
            print_error "docker-compose not found or not accessible"
        fi
        echo "sudo docker-compose"
    else
        echo "docker-compose"
    fi
}

# Show usage
show_usage() {
    echo "Usage: $0 <command> [service_name]"
    echo ""
    echo "Commands:"
    echo "  start [service]    Start service(s)"
    echo "  stop [service]     Stop service(s)"
    echo "  restart [service]  Restart service(s)"
    echo "  logs [service]     Show logs for service(s)"
    echo "  status             Show all service status"
    echo "  build [service]    Build service(s)"
    echo "  list               List available services"
    echo ""
    echo "Available services:"
    echo "  - mcpserver        MCP Server (port 8333)"
    echo "  - server           FastAPI Agent Server (port 7000)"
    echo "  - insurance-server Insurance Agent Server (port 7001)"
    echo "  - webclient        Web Client (port 7080)"
    echo ""
    echo "Examples:"
    echo "  $0 start insurance-server"
    echo "  $0 logs server"
    echo "  $0 restart"
    echo "  $0 status"
}

# Main function
main() {
    COMPOSE_CMD=$(check_compose_cmd)
    
    if [ $# -eq 0 ]; then
        show_usage
        exit 1
    fi
    
    command=$1
    service=${2:-""}
    
    case "$command" in
        "start")
            if [ -n "$service" ]; then
                print_status "Starting service: $service"
                $COMPOSE_CMD up -d "$service"
                print_success "Service $service started"
            else
                print_status "Starting all services"
                $COMPOSE_CMD up -d
                print_success "All services started"
            fi
            ;;
        "stop")
            if [ -n "$service" ]; then
                print_status "Stopping service: $service"
                $COMPOSE_CMD stop "$service"
                print_success "Service $service stopped"
            else
                print_status "Stopping all services"
                $COMPOSE_CMD down
                print_success "All services stopped"
            fi
            ;;
        "restart")
            if [ -n "$service" ]; then
                print_status "Restarting service: $service"
                $COMPOSE_CMD restart "$service"
                print_success "Service $service restarted"
            else
                print_status "Restarting all services"
                $COMPOSE_CMD restart
                print_success "All services restarted"
            fi
            ;;
        "logs")
            if [ -n "$service" ]; then
                print_status "Showing logs for: $service"
                $COMPOSE_CMD logs -f "$service"
            else
                print_status "Showing logs for all services"
                $COMPOSE_CMD logs -f
            fi
            ;;
        "status")
            print_status "Service status:"
            $COMPOSE_CMD ps
            ;;
        "build")
            if [ -n "$service" ]; then
                print_status "Building service: $service"
                $COMPOSE_CMD build "$service"
                print_success "Service $service built"
            else
                print_status "Building all services"
                $COMPOSE_CMD build
                print_success "All services built"
            fi
            ;;
        "list")
            echo "Available services:"
            echo "  - mcpserver        MCP Server (port 8333)"
            echo "  - server           FastAPI Agent Server (port 7000)"
            echo "  - insurance-server Insurance Agent Server (port 7001)"
            echo "  - webclient        Web Client (port 7080)"
            ;;
        *)
            print_error "Unknown command: $command"
            show_usage
            ;;
    esac
}

main "$@"