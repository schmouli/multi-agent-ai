#!/bin/bash

# Function to install dependencies with retry
install_deps() {
    echo "Installing dependencies..."
    for i in {1..3}; do
        if uv add fastapi uvicorn python-dotenv httpx pydantic websockets; then
            echo "Dependencies installed successfully"
            return 0
        else
            echo "Attempt $i failed, retrying..."
            sleep 2
        fi
    done
    echo "Failed to install dependencies after 3 attempts"
    exit 1
}

# Set default service type
SERVICE_TYPE=${SERVICE_TYPE:-web-client}

echo "Starting service: $SERVICE_TYPE"
echo "Current directory: $(pwd)"
echo "Directory contents:"
ls -la

case $SERVICE_TYPE in
    "orchestrator")
        echo "Starting AI Agent Orchestrator on port 7500..."
        cd /app
        # Install AutoGen and WebSockets
        uv add pyautogen websockets
        # Use the correct filename
        uv run python server/agent_orchestrator.py
        ;;
    "mcp-server")
        echo "Starting MCP Server on port 8333..."
        cd /app
        install_deps
        uv add mcp
        uv run python server/mcpserver.py
        ;;
    "fastapi-server")
        echo "Starting FastAPI Server on port 7000..."
        cd /app
        install_deps
        uv run python server/fastapi_agent_server.py
        ;;
    "insurance-server")
        echo "Starting Insurance Agent Server on port 7001..."
        cd /app
        install_deps
        uv add acp-sdk crewai crewai-tools openai
        uv run python server/insurance_agent_server.py
        ;;
    "web-client")
        echo "Starting Web Client on port 7080..."
        cd /app
        install_deps
        uv run python client/web_client.py
        ;;
    *)
        echo "Unknown service type: $SERVICE_TYPE"
        echo "Available types: orchestrator, mcp-server, fastapi-server, insurance-server, web-client"
        exit 1
        ;;
esac