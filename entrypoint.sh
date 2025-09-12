#!/bin/bash
set -e

echo "Starting service: $SERVICE_TYPE"

case "$SERVICE_TYPE" in
    "web-client")
        echo "Starting Web Client on port 7080..."
        cd /app
        uv run python client/web_client.py
        ;;
    "fastapi-server")
        echo "Starting FastAPI Agent Server on port 7000..."
        cd /app
        uv run python server/fastapi_agent_server.py
        ;;
    "mcp-server")
        echo "Starting MCP Server on port 8333..."
        cd /app
        uv run python server/mcpserver.py
        ;;
    "insurance-server")
        echo "Starting Insurance Agent Server on port 7001..."
        cd /app
        # Ensure data directory exists
        mkdir -p /app/data
        uv run python server/insurance_agent_server.py
        ;;
    *)
        echo "Unknown service type: $SERVICE_TYPE"
        echo "Available types: web-client, fastapi-server, mcp-server, insurance-server"
        exit 1
        ;;
esac