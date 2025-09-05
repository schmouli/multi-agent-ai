#!/bin/bash
set -e

case "$SERVICE_TYPE" in
  "server"|"fastapi-server")
    echo "Starting FastAPI Agent Server..."
    exec uv run server/fastapi_agent_server.py
    ;;
  "acp-server")
    echo "Starting ACP Server (deprecated)..."
    exec uv run server/acpmcp_server.py
    ;;
  "mcpserver")
    echo "Starting MCP Server on port ${MCP_PORT:-8333}..."
    export MCP_TRANSPORT=http
    export MCP_PORT=${MCP_PORT:-8333}
    exec uv run server/mcpserver.py
    ;;
  "webclient"|"client")
    echo "Starting Web Client..."
    exec uv run client/web_client.py
    ;;
  *)
    echo "Unknown service type: $SERVICE_TYPE"
    echo "Available options: server, fastapi-server, acp-server, mcpserver, client, webclient"
    exit 1
    ;;
esac
