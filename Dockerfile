# Multi-stage Dockerfile for multi-agent-ai project
FROM python:3.12-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen

# Copy source code
COPY . .

# Build argument to determine which service to run
ARG SERVICE_TYPE=webclient
ENV SERVICE_TYPE=${SERVICE_TYPE}

# Expose ports
# Port 7080 for web client, 7000 for ACP server
EXPOSE 7080 7000

# Create entrypoint script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
case "$SERVICE_TYPE" in\n\
  "server")\n\
    echo "Starting ACP Server (includes MCP server internally)..."\n\
    exec uv run server/acpmcp_server.py\n\
    ;;\n\
  "webclient"|"client")\n\
    echo "Starting Web Client..."\n\
    exec uv run client/web_client.py\n\
    ;;\n\
  *)\n\
    echo "Unknown service type: $SERVICE_TYPE"\n\
    echo "Available options: server, client, webclient"\n\
    exit 1\n\
    ;;\n\
esac\n' > /app/entrypoint.sh

# Make entrypoint script executable
RUN chmod +x /app/entrypoint.sh

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
