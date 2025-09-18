FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# Copy all files
COPY . .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Create .venv directory
RUN uv venv

# Set environment variables - CORRECTED PATHS
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app:/app/server:$PYTHONPATH"

# Default service type
ARG SERVICE_TYPE=web-client
ENV SERVICE_TYPE=$SERVICE_TYPE

# Expose common ports
EXPOSE 7000 7001 7080 7500 8333

# Run entrypoint
CMD ["./entrypoint.sh"]