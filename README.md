# Multi-Agent AI Project

## Project Structure

```
multi-agent-ai/
├── server/                 # Server components
│   ├── mcpserver.py       # MCP tools server
│   └── acpmcp_server.py   # ACP server with health agent
├── client/                 # Client components
│   ├── web_client.py      # FastAPI web interface
│   └── templates/         # HTML templates
│       └── index.html     # Web UI
├── scripts/               # Utility scripts
│   ├── build.sh          # Docker build script
│   ├── format.sh         # Code formatting script
│   ├── test.sh           # Test runner script
│   └── verify-config.sh  # Configuration validation
├── tests/                 # Test files
│   ├── test_mcpserver.py # MCP server tests
│   ├── test_acpmcp_server.py # ACP server tests
│   └── test_web_client_simple.py # Web client tests
├── pyproject.toml         # Project dependencies
├── Dockerfile             # Multi-service Docker build
├── docker-compose.yml     # Orchestration
├── .env.example          # Environment template
├── .gitignore            # Git exclusions
└── README.md             # This file
```

## Services

### 1. Server (`server/acpmcp_server.py`)
- Main ACP server with health agent using OpenAI GPT-4o-mini
- Internally spawns MCP server (`mcpserver.py`) as subprocess
- Contains doctor search functionality via MCP tools
- Runs on port 8000

### 2. Web Client (`client/web_client.py`)
- FastAPI web interface
- Connects to ACP server
- Provides HTML form for location and health queries
- Runs on port 8080

## Architecture

The application uses a simplified two-service architecture:
- **Server**: Single ACP server that includes MCP tools internally
- **Client**: Web interface that communicates with the server

The MCP server (`mcpserver.py`) is automatically started as a subprocess when the main server runs, eliminating the need for separate container orchestration.

## Scripts

The project includes several utility scripts in the `scripts/` directory:

### Development Scripts
- **`build.sh`** - Build Docker images for the application
- **`test.sh`** - Run comprehensive test suite with coverage
- **`format.sh`** - Format code with black, isort, and flake8
- **`verify-config.sh`** - Validate Docker Compose and environment configuration

### Git Scripts
- **`merge-to-github.sh`** - Interactive script to stage, commit, and push to GitHub
- **`quick-push.sh`** - Quick commit and push with optional message

All scripts are executable and can be run from the project root:
```bash
# Development
./scripts/build.sh      # Build Docker images
./scripts/test.sh       # Run tests
./scripts/format.sh     # Format code
./scripts/verify-config.sh  # Verify configuration

# Git operations
./scripts/merge-to-github.sh        # Interactive GitHub merge
./scripts/quick-push.sh "message"   # Quick push with message
```

## Quick Start

1. **Setup environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

2. **Build and run:**
   ```bash
   ./scripts/build.sh
   docker-compose up
   ```
   
   The docker-compose will automatically read your OpenAI API key from the `.env` file.

3. **Access:**
   - Web UI: http://localhost:8080
   - API docs: http://localhost:8080/docs

## Development

Run locally with uv:
```bash
# Install dependencies
uv sync

# Run ACP server
uv run server/acpmcp_server.py

# Run web client (in another terminal)
uv run client/web_client.py
```

## Testing

The project includes comprehensive unit tests using pytest:

```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=server --cov=client --cov-report=html:htmlcov

# Run specific test files
uv run pytest tests/test_mcpserver.py
uv run pytest tests/test_acpmcp_server.py
uv run pytest tests/test_web_client_simple.py

# Use the test script for comprehensive testing
./scripts/test.sh
```

### Test Coverage
- **MCP Server**: Tests for doctor database, search functionality, data validation
- **ACP Server**: Tests for health agent, server configuration, model setup
- **Web Client**: Tests for API models, endpoints, and configuration
- **Integration**: Tests for complete request flows

View detailed coverage reports in `htmlcov/index.html` after running tests with coverage.

## Code Quality

The project follows strict code quality standards:

```bash
# Format code
./scripts/format.sh

# Or run formatters individually
uv run black server/ client/
uv run isort server/ client/
uv run flake8 server/ client/
```
