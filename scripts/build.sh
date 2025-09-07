#!/bin/bash
set -e

echo "Building multi-agent-ai Docker images..."

# Check if docker command requires sudo
if ! docker info >/dev/null 2>&1; then
    echo "Docker requires sudo access. Using sudo for Docker commands..."
    DOCKER_CMD="sudo docker"
else
    DOCKER_CMD="docker"
fi

# Build MCP Server image
echo "Building MCP Server image..."
$DOCKER_CMD build --build-arg SERVICE_TYPE=mcpserver -t multi-agent-ai:mcpserver .

# Build FastAPI Agent Server image
echo "Building FastAPI Agent Server image..."
$DOCKER_CMD build --build-arg SERVICE_TYPE=fastapi-server -t multi-agent-ai:server .

# Build Web Client image
echo "Building Web Client image..."
$DOCKER_CMD build --build-arg SERVICE_TYPE=webclient -t multi-agent-ai:webclient .

echo "Build complete!"
echo ""
echo "Available images:"
echo "  - multi-agent-ai:mcpserver (MCP server with doctor search on port 8333)"
echo "  - multi-agent-ai:server (FastAPI agent server on port 7000)"
echo "  - multi-agent-ai:webclient (Web UI client on port 7080)"
echo ""
echo "Usage:"
echo "  Run MCP Server: docker run -p 8333:8333 multi-agent-ai:mcpserver"
echo "  Run Agent Server: docker run -p 7000:7000 -e OPENAI_API_KEY=your_key multi-agent-ai:server"
echo "  Run Web Client: docker run -p 7080:7080 multi-agent-ai:webclient"
echo "  Or use: docker-compose up  (reads OPENAI_API_KEY from .env file)"
echo ""
echo "Note: Services communicate via Docker networking in docker-compose setup."
