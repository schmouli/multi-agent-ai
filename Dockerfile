# Multi-stage Dockerfile for multi-agent-ai project
FROM python:3.12-slim AS base

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

# Copy entrypoint script first
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Copy source code
COPY . .

# Build argument to determine which service to run
ARG SERVICE_TYPE=fastapi-server
ENV SERVICE_TYPE=${SERVICE_TYPE}

# Expose ports based on service type
# Port 7080 for web client, 7000 for FastAPI server, 8333 for MCP server
EXPOSE 7080 7000 8333

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
