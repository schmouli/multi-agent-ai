#!/bin/bash
set -e

echo "Building multi-agent-ai Docker images..."

# Build Server image (includes MCP server internally)
echo "Building Server image..."
docker build --build-arg SERVICE_TYPE=server -t multi-agent-ai:server .

# Build Web Client image
echo "Building Web Client image..."
docker build --build-arg SERVICE_TYPE=webclient -t multi-agent-ai:webclient .

echo "Build complete!"
echo ""
echo "Available images:"
echo "  - multi-agent-ai:server (ACP server with health agent + MCP tools on port 8000)"
echo "  - multi-agent-ai:webclient (Web UI client on port 8080)"
echo ""
echo "Usage:"
echo "  Run Server: docker run -p 8000:8000 -e OPENAI_API_KEY=your_key multi-agent-ai:server"
echo "  Run Web Client: docker run -p 8080:8080 multi-agent-ai:webclient"
echo "  Or use: docker-compose up  (reads OPENAI_API_KEY from .env file)"
echo ""
echo "Note: The server automatically starts the MCP server internally as a subprocess."
