#!/bin/bash
set -e

echo "Building multi-agent-ai services with docker-compose..."

# Check if docker-compose command requires sudo
if ! docker-compose version >/dev/null 2>&1; then
    if ! sudo docker-compose version >/dev/null 2>&1; then
        echo "❌ docker-compose not found or not accessible"
        exit 1
    fi
    echo "Docker-compose requires sudo access. Using sudo for docker-compose commands..."
    COMPOSE_CMD="sudo docker-compose"
else
    COMPOSE_CMD="docker-compose"
fi

# Step 1: Stop and remove existing containers
echo "🛑 Stopping and removing existing containers..."
$COMPOSE_CMD down --remove-orphans

# Step 2: Build all services
echo "🔨 Building all services..."
$COMPOSE_CMD build --no-cache

# Step 3: Start services in detached mode
echo "🚀 Starting services..."
$COMPOSE_CMD up -d

# Wait a moment for services to initialize
echo "⏳ Waiting for services to initialize..."
sleep 5

# Step 4: Show service status
echo "📊 Service status:"
$COMPOSE_CMD ps

echo ""
echo "✅ Build and deployment complete!"
echo ""
echo "🌐 Available services:"
echo "  - MCP Server: http://localhost:8333 (Doctor search API)"
echo "  - FastAPI Agent Server: http://localhost:7000 (Healthcare agent API)"
echo "  - Web Client: http://localhost:7080 (Healthcare chat interface)"
echo ""
echo "📋 Useful commands:"
echo "  View logs: $COMPOSE_CMD logs -f [service_name]"
echo "  Stop services: $COMPOSE_CMD down"
echo "  Restart service: $COMPOSE_CMD restart [service_name]"
echo "  View status: $COMPOSE_CMD ps"
echo ""
echo "🔧 Troubleshooting:"
echo "  Check logs: $COMPOSE_CMD logs"
echo "  Rebuild specific service: $COMPOSE_CMD build [service_name]"
echo "  Force recreate: $COMPOSE_CMD up --force-recreate -d"
echo ""
echo "💡 Note: Services use .env file for OPENAI_API_KEY configuration"