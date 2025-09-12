"""Tests for FastAPI Agent Server."""

import pytest
from fastapi.testclient import TestClient

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
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {
            "status": "healthy",
            "service": "healthcare-agent-server"
        }


class TestQueryEndpoint:
    """Tests for query endpoint."""

    def test_query_empty_query(self, client):
        """Test query with empty query string."""
        response = client.post("/query", json={"query": "", "agent": "doctor"})
        assert response.status_code == 400
        assert "Query cannot be empty" in response.json()["detail"]

    def test_query_invalid_agent(self, client):
        """Test query with invalid agent."""
        response = client.post("/query", json={"query": "test", "agent": "invalid"})
        assert response.status_code == 400
        assert "Agent must be 'hospital' or 'doctor'" in response.json()["detail"]

    def test_query_valid_input(self, client):
        """Test query with valid input (will fail due to MCP server not running)."""
        response = client.post("/query", json={"query": "Find doctors in CA", "agent": "doctor"})
        # This will likely return a 503 since MCP server isn't running in tests
        assert response.status_code in [200, 503]


class TestRunSyncEndpoint:
    """Tests for run_sync endpoint."""

    def test_run_sync_valid_agent(self, client):
        """Test run_sync with valid agent."""
        response = client.post("/run_sync", json={"agent": "doctor"})
        assert response.status_code == 200
        assert response.json() == {"status": "completed", "agent": "doctor"}

    def test_run_sync_invalid_agent(self, client):
        """Test run_sync with invalid agent."""
        response = client.post("/run_sync", json={"agent": "invalid"})
        assert response.status_code == 400
        assert "Invalid agent specified" in response.json()["detail"]

    def test_run_sync_missing_agent(self, client):
        """Test run_sync with missing agent."""
        response = client.post("/run_sync", json={})
        assert response.status_code == 400
        assert "Invalid agent specified" in response.json()["detail"]
