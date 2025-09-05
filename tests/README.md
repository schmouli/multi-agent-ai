# Test Suite Documentation

## Overview

This document describes the comprehensive test suite for the FastAPI-based Multi-Agent Healthcare System. The test suite has been updated to reflect the migration from ACP SDK to FastAPI architecture and includes curl-equivalent tests for HTTP API validation.

## Architecture Changes Tested

The test suite validates the new architecture:

- **FastAPI Agent Server** (`server/fastapi_agent_server.py`) - Replaced ACP SDK server
- **HTTP-based Web Client** (`client/web_client.py`) - Uses httpx instead of ACP SDK client
- **MCP Server HTTP Transport** (`server/mcpserver.py`) - HTTP transport for doctor search
- **3-Container Architecture** - Web client → Agent server → MCP server

## Test Structure

### 1. Unit Tests

#### `test_fastapi_agent_server.py`
Tests the FastAPI agent server functionality:

- **Health checks** (`/health` endpoint)
- **Agent logic** (smolagents integration with LiteLLM)
- **Query endpoints** (`/query` and `/run_sync`)
- **MCP integration** (HTTP communication with MCP server)
- **Error handling** (connection failures, API errors)
- **Async functionality** (proper async/await patterns)

**Curl-equivalent tests:**
```python
def test_curl_health_check(self, client):
    """curl -s http://localhost:7000/health"""
    
def test_curl_query_cardiologist_atlanta(self, client, mock_mcp):
    """curl -X POST http://localhost:7000/query -H "Content-Type: application/json" 
       -d '{"location": "atlanta", "query": "I need a cardiologist"}'"""
```

#### `test_web_client.py`
Tests the web client HTTP-based functionality:

- **Frontend serving** (HTML page serving)
- **Query processing** (form submission handling)
- **HTTP communication** (httpx client to agent server)
- **Error propagation** (server errors, API failures)
- **Response handling** (JSON response processing)

**Curl-equivalent tests:**
```python
def test_curl_query_cardiologist_atlanta(self, client, mock_httpx_client):
    """curl -X POST http://localhost:7080/query -H "Content-Type: application/json"
       -d '{"location": "atlanta", "query": "I need to find a cardiologist"}'"""
```

#### `test_mcpserver.py`
Tests the MCP server with HTTP transport:

- **Doctor data integrity** (database validation)
- **Search functionality** (state-based doctor search)
- **HTTP transport** (JSON-RPC over HTTP)
- **Tool registration** (MCP protocol compliance)
- **Error handling** (invalid requests, malformed JSON)

**Curl-equivalent tests:**
```python
def test_curl_search_doctors_georgia(self, client):
    """curl -X POST http://localhost:8333/ -H "Content-Type: application/json"
       -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/call", 
            "params": {"name": "doctor_search", "arguments": {"state": "GA"}}}'"""
```

### 2. Integration Tests

#### `test_integration.py`
Tests end-to-end system functionality:

- **Service integration** (MCP ↔ Agent ↔ Web client)
- **Error propagation** (how errors flow through the system)
- **Performance benchmarks** (response time validation)
- **Complete workflow** (user query → doctor search → AI response)

**Curl-equivalent tests:**
```python
def test_curl_complete_workflow(self, web_client, mcp_client):
    """Complete workflow simulation using curl-equivalent commands"""
    
def test_curl_health_checks_all_services(self, agent_client, mcp_client, web_client):
    """curl -s http://localhost:7000/health  # Agent server
       curl -s http://localhost:8333/health  # MCP server
       curl -s http://localhost:7080/        # Web client"""
```

## Test Categories and Markers

### Pytest Markers

- `@pytest.mark.unit` - Unit tests for individual components
- `@pytest.mark.integration` - Integration tests across components
- `@pytest.mark.async` - Tests for async functionality
- `@pytest.mark.curl` - Tests that simulate curl commands
- `@pytest.mark.mcp` - MCP server specific tests
- `@pytest.mark.agent` - Agent server specific tests
- `@pytest.mark.web` - Web client specific tests
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.slow` - Tests that take longer to run

### Test Commands

```bash
# Run all tests
pytest tests/

# Run only fast tests
pytest tests/ -m "not slow"

# Run curl-equivalent tests
pytest tests/ -k "curl"

# Run async tests
pytest tests/ -k "async"

# Run with coverage
pytest tests/ --cov=server --cov=client --cov-report=html

# Run specific test file
pytest tests/test_fastapi_agent_server.py -v

# Run integration tests only
pytest tests/test_integration.py -v
```

## Mock Patterns

### HTTP Client Mocking
```python
@pytest.fixture
def mock_httpx_client(self):
    """Mock httpx client for FastAPI server communication."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"success": True, "data": "test"}
    mock_client.post.return_value = mock_response
    mock_client_class = MagicMock()
    mock_client_class.return_value.__aenter__.return_value = mock_client
    return mock_client_class
```

### MCP Server Mocking
```python
@pytest.fixture
def mock_mcp_server(self):
    """Mock MCP server responses."""
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "content": [{"type": "text", "text": "Dr. Sarah Mitchell - Cardiology"}]
        }
    }
```

### Agent Logic Mocking
```python
@pytest.fixture
def mock_smolagents(self):
    """Mock smolagents functionality."""
    with patch('smolagents.LiteLLMModel') as mock_model:
        mock_agent = MagicMock()
        mock_agent.run.return_value = "AI response about doctor search"
        yield mock_agent
```

## Test Data

### Sample Doctor Data
```python
test_doctor = {
    "name": "Dr. Sarah Mitchell",
    "specialty": "Cardiology",
    "address": {
        "street": "123 Medical Center Dr",
        "city": "Atlanta",
        "state": "GA",
        "zip_code": "30309"
    },
    "phone": "(404) 555-0123",
    "email": "sarah.mitchell@example.com",
    "years_experience": 15,
    "board_certified": True,
    "hospital_affiliations": ["Emory University Hospital"]
}
```

### Sample API Requests
```python
# Web client query
web_query = {
    "location": "atlanta",
    "query": "I need a cardiologist for my heart condition"
}

# MCP server request
mcp_request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "doctor_search",
        "arguments": {"state": "GA"}
    }
}

# Agent server query
agent_query = {
    "location": "atlanta",
    "query": "I need a cardiologist"
}
```

## Running Tests

### Using the Test Runner Script
```bash
# Run all tests
./tests/run_tests.sh

# Run only fast tests
./tests/run_tests.sh --fast

# Run with coverage
./tests/run_tests.sh --coverage

# Run in verbose mode
./tests/run_tests.sh --verbose

# Show help
./tests/run_tests.sh --help
```

### Manual Pytest Commands
```bash
# Basic test run
pytest tests/ -v

# Run with specific markers
pytest tests/ -m "unit and not slow"
pytest tests/ -m "integration"
pytest tests/ -m "curl"

# Run specific test classes
pytest tests/test_fastapi_agent_server.py::TestFastAPIAgentServer -v
pytest tests/test_integration.py::TestIntegrationE2E -v

# Run with coverage and HTML report
pytest tests/ --cov=server --cov=client --cov-report=html --cov-report=term

# Run tests matching pattern
pytest tests/ -k "test_curl" -v
pytest tests/ -k "test_async" -v
```

## Continuous Integration

The test suite is designed to work with CI/CD pipelines:

### GitHub Actions Example
```yaml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    - name: Install dependencies
      run: |
        pip install -e .[dev]
    - name: Run tests
      run: |
        ./tests/run_tests.sh --coverage
```

## Test Coverage Goals

- **Unit Tests**: >90% code coverage for individual modules
- **Integration Tests**: All major workflows covered
- **API Tests**: All endpoints tested with various scenarios
- **Error Cases**: All error conditions properly tested
- **Performance**: Response time benchmarks validated

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure project root is in Python path
2. **Async Test Failures**: Check `asyncio_mode = "auto"` in pytest config
3. **Mock Issues**: Verify proper async/await patterns in mocks
4. **HTTP Client Issues**: Check httpx version compatibility

### Debug Commands
```bash
# Run tests with maximum verbosity
pytest tests/ -vvv -s --tb=long

# Run single test with debugging
pytest tests/test_fastapi_agent_server.py::TestFastAPIAgentServer::test_health_endpoint -vvv -s

# Check test discovery
pytest --collect-only tests/
```

## Migration Notes

### Changes from ACP SDK Tests

1. **Removed ACP SDK mocks** - Replaced with httpx and FastAPI TestClient
2. **Added HTTP transport tests** - MCP server now uses HTTP instead of stdio
3. **Updated client tests** - Web client now uses httpx instead of ACP SDK client
4. **Added curl equivalents** - Each major API interaction has curl-equivalent test
5. **Enhanced async testing** - Proper async/await patterns throughout

### Breaking Changes

- Tests now require `fastapi` and `httpx` instead of `acp-sdk`
- Mock patterns changed from ACP SDK client mocks to HTTP client mocks
- MCP server tests now use HTTP transport instead of stdio transport
- Integration tests validate HTTP communication between services

This comprehensive test suite ensures the reliability and maintainability of the FastAPI-based healthcare agent system.
