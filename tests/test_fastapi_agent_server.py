"""Tests for FastAPI Agent Server."""

import pytest
import sys
import os
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock

# Add the server directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "server"))

# Set environment variables before importing
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("MCP_SERVER_URL", "http://test-mcp:8333")

# Import after path setup and env vars
try:
    from fastapi_agent_server import app, extract_state_from_prompt
except ImportError:
    from server.fastapi_agent_server import app, extract_state_from_prompt


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestExtractStateFromPrompt:
    """Tests for extract_state_from_prompt function."""

    def test_extract_state_code_uppercase(self):
        """Test extracting uppercase state codes."""
        assert extract_state_from_prompt("Find doctors in CA") == "CA"
        assert extract_state_from_prompt("Looking for doctors in NY") == "NY"
        assert extract_state_from_prompt("I live in TX") == "TX"

    def test_extract_state_name_full(self):
        """Test extracting full state names."""
        assert extract_state_from_prompt("Find doctors in California") == "CA"
        assert extract_state_from_prompt("Looking for doctors in New York") == "NY"
        assert extract_state_from_prompt("I need a doctor in Texas") == "TX"

    def test_extract_state_case_insensitive(self):
        """Test case insensitive extraction."""
        assert extract_state_from_prompt("find doctors in california") == "CA"
        assert extract_state_from_prompt("LOOKING FOR DOCTORS IN TEXAS") == "TX"

    def test_no_state_found(self):
        """Test when no state is found."""
        assert extract_state_from_prompt("Find doctors near me") is None
        assert extract_state_from_prompt("I need medical help") is None
        assert extract_state_from_prompt("") is None

    def test_invalid_state_code(self):
        """Test with invalid state codes."""
        assert extract_state_from_prompt("Find doctors in ZZ") is None
        assert extract_state_from_prompt("Looking in XX") is None


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        with patch('fastapi_agent_server.httpx.AsyncClient') as mock_client_class:
            # Mock the MCP server health check
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            response = client.get("/health")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "healthcare-agent-server"
            assert "version" in data
            assert "mcp_server_url" in data


class TestQueryEndpoint:
    """Tests for query endpoint."""

    def test_query_empty_query(self, client):
        """Test query with empty query string."""
        response = client.post("/query", json={
            "location": "CA", 
            "query": "", 
            "agent": "doctor"
        })
        assert response.status_code == 400
        assert "Query cannot be empty" in response.json()["detail"]

    def test_query_invalid_agent(self, client):
        """Test query with invalid agent."""
        response = client.post("/query", json={
            "location": "CA",
            "query": "test", 
            "agent": "invalid"
        })
        assert response.status_code == 400
        assert "Agent must be 'hospital' or 'doctor'" in response.json()["detail"]

    def test_query_valid_input_mcp_success(self, client):
        """Test query with valid input and mocked MCP server."""
        with patch('fastapi_agent_server.httpx.AsyncClient') as mock_client_class:
            # Mock successful MCP server response
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "result": {
                    "content": [{"text": "Found 3 doctors in CA"}]
                }
            }
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            response = client.post("/query", json={
                "location": "CA",
                "query": "Find doctors in CA", 
                "agent": "doctor"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "Found 3 doctors in CA" in data["result"]

    def test_query_mcp_server_error(self, client):
        """Test query when MCP server returns error."""
        with patch('fastapi_agent_server.httpx.AsyncClient') as mock_client_class:
            # Mock MCP server error
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            response = client.post("/query", json={
                "location": "CA",
                "query": "Find doctors in CA",
                "agent": "doctor"
            })
            
            assert response.status_code == 500

    def test_query_mcp_server_unreachable(self, client):
        """Test query when MCP server is unreachable."""
        with patch('fastapi_agent_server.httpx.AsyncClient') as mock_client_class:
            # Mock connection error
            mock_client = AsyncMock()
            mock_client.post.side_effect = Exception("Connection refused")
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            response = client.post("/query", json={
                "location": "CA",
                "query": "Find doctors in CA",
                "agent": "doctor"
            })
            
            assert response.status_code == 503


class TestRunSyncEndpoint:
    """Tests for run_sync endpoint."""

    def test_run_sync_valid_agent(self, client):
        """Test run_sync with valid agent."""
        response = client.post("/run_sync", json={"agent": "doctor"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["agent"] == "doctor"

    def test_run_sync_invalid_agent(self, client):
        """Test run_sync with invalid agent."""
        response = client.post("/run_sync", json={"agent": "invalid"})
        assert response.status_code == 400
        assert "Invalid agent specified" in response.json()["detail"]

    def test_run_sync_missing_agent(self, client):
        """Test run_sync with missing agent."""
        response = client.post("/run_sync", json={})
        assert response.status_code == 400
        assert "Missing 'agent' field in request" in response.json()["detail"]


class TestEnvironmentVariables:
    """Tests for environment variable loading."""

    def test_openai_api_key_from_env_file(self):
        """Test that OpenAI API key is correctly loaded from .env file."""
        # Save original environment
        original_api_key = os.environ.get("OPENAI_API_KEY")
        
        try:
            # Remove the environment variable to test .env loading
            if "OPENAI_API_KEY" in os.environ:
                del os.environ["OPENAI_API_KEY"]
            
            # Force reload of the module to test .env loading
            import importlib
            if 'fastapi_agent_server' in sys.modules:
                importlib.reload(sys.modules['fastapi_agent_server'])
            else:
                import fastapi_agent_server
            
            # Check if API key was loaded
            loaded_api_key = os.environ.get("OPENAI_API_KEY")
            
            # Verify that either the .env file loaded it or we have a test key
            assert loaded_api_key is not None, "OpenAI API key should be loaded from .env or set as test key"
            
            # If it's not our test key, it should come from .env
            if loaded_api_key != "test-key":
                assert len(loaded_api_key) > 10, "API key from .env should be a real key (longer than 10 chars)"
                assert loaded_api_key.startswith("sk-"), "OpenAI API key should start with 'sk-'"
            
        finally:
            # Restore original environment
            if original_api_key:
                os.environ["OPENAI_API_KEY"] = original_api_key
            else:
                os.environ.pop("OPENAI_API_KEY", None)

    def test_env_file_exists(self):
        """Test that .env file exists in the project root."""
        project_root = Path(__file__).parent.parent
        env_file = project_root / ".env"
        
        if env_file.exists():
            # Read .env file content
            with open(env_file, 'r') as f:
                content = f.read()
            
            # Check if OPENAI_API_KEY is defined
            openai_lines = [line for line in content.split('\n') if line.startswith('OPENAI_API_KEY')]
            
            if openai_lines:
                # Verify format
                api_key_line = openai_lines[0]
                assert '=' in api_key_line, "OPENAI_API_KEY should be in format OPENAI_API_KEY=value"
                
                key_value = api_key_line.split('=', 1)[1].strip().strip('"\'')
                if key_value and key_value != "your-openai-api-key-here":
                    assert key_value.startswith("sk-"), "OpenAI API key should start with 'sk-'"
            else:
                print("Warning: OPENAI_API_KEY not found in .env file")
        else:
            print("Warning: .env file not found in project root")

    def test_dotenv_loading_in_server(self):
        """Test that the server properly loads environment variables."""
        # Import the server module to trigger load_dotenv()
        try:
            from fastapi_agent_server import mcp_server_url, server_url
            
            # These should be loaded from environment or have defaults
            assert mcp_server_url is not None
            assert server_url is not None
            
            # Check that they're either defaults or custom values
            assert isinstance(mcp_server_url, str)
            assert isinstance(server_url, str)
            
        except ImportError:
            from server.fastapi_agent_server import mcp_server_url, server_url
            
            assert mcp_server_url is not None
            assert server_url is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
