"""Tests for the FastAPI Agent Server functionality."""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the project root to the Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from server.fastapi_agent_server import app, extract_state_from_prompt, get_doctor_data, health_agent_logic


class TestFastAPIAgentServer:
    """Test cases for FastAPI Agent Server functionality."""

    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app."""
        return TestClient(app)

    @pytest.fixture
    def mock_httpx_client(self):
        """Mock httpx client for MCP server communication."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": "{'DOC001': {'name': 'Dr. Test', 'specialty': 'Cardiology', 'address': {'city': 'Atlanta', 'state': 'GA'}}}"
        }
        mock_client.post.return_value = mock_response
        return mock_client

    def test_root_endpoint(self, client):
        """Test the root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Hospital Agent Server"
        assert data["status"] == "running"
        assert "mcp_server" in data
        assert "model_available" in data

    def test_health_endpoint(self, client):
        """Test the health check endpoint."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "Hospital Agent Server"

    @pytest.mark.asyncio
    async def test_extract_state_from_prompt(self):
        """Test state extraction from prompts."""
        # Test state abbreviation
        result = await extract_state_from_prompt("I'm in GA looking for a doctor")
        assert result == "GA"
        
        # Test city name mapping
        result = await extract_state_from_prompt("I live in atlanta and need help")
        assert result == "GA"
        
        # Test default case
        result = await extract_state_from_prompt("I need a doctor")
        assert result == "GA"

    @pytest.mark.asyncio
    async def test_get_doctor_data_success(self, mock_httpx_client):
        """Test successful doctor data retrieval."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_httpx_client
            
            result = await get_doctor_data("GA")
            assert result is not None
            assert "DOC001" in result

    @pytest.mark.asyncio
    async def test_get_doctor_data_failure(self):
        """Test failed doctor data retrieval."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            result = await get_doctor_data("GA")
            assert result is None

    @pytest.mark.asyncio
    async def test_health_agent_logic_with_model(self, mock_httpx_client):
        """Test health agent logic with model available."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_httpx_client
            
            with patch('server.fastapi_agent_server.model') as mock_model:
                mock_agent = MagicMock()
                mock_agent.run.return_value = "Test AI response"
                
                with patch('server.fastapi_agent_server.ToolCallingAgent', return_value=mock_agent):
                    result = await health_agent_logic("I need a cardiologist in Atlanta")
                    assert "Test AI response" in result

    @pytest.mark.asyncio
    async def test_health_agent_logic_without_model(self, mock_httpx_client):
        """Test health agent logic without model available."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_httpx_client
            
            with patch('server.fastapi_agent_server.model', None):
                result = await health_agent_logic("I need a cardiologist in Atlanta")
                assert "Found doctors in GA" in result
                assert "AI assistant temporarily unavailable" in result

    def test_run_sync_endpoint_success(self, client, mock_httpx_client):
        """Test the run_sync endpoint with successful response."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_httpx_client
            
            with patch('server.fastapi_agent_server.model') as mock_model:
                mock_agent = MagicMock()
                mock_agent.run.return_value = "Test AI response"
                
                with patch('server.fastapi_agent_server.ToolCallingAgent', return_value=mock_agent):
                    response = client.post("/run_sync", json={
                        "agent": "health_agent",
                        "input": "I need a cardiologist in Atlanta"
                    })
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True
                    assert len(data["output"]) > 0
                    assert data["output"][0]["parts"][0]["content"] == "Test AI response"

    def test_run_sync_endpoint_invalid_agent(self, client):
        """Test the run_sync endpoint with invalid agent."""
        response = client.post("/run_sync", json={
            "agent": "invalid_agent",
            "input": "test query"
        })
        
        assert response.status_code == 400

    def test_direct_query_endpoint(self, client, mock_httpx_client):
        """Test the direct query endpoint."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_httpx_client
            
            with patch('server.fastapi_agent_server.model') as mock_model:
                mock_agent = MagicMock()
                mock_agent.run.return_value = "Test AI response"
                
                with patch('server.fastapi_agent_server.ToolCallingAgent', return_value=mock_agent):
                    response = client.post("/query", json={
                        "query": "I need a cardiologist in Atlanta"
                    })
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True
                    assert "Test AI response" in data["result"]

    def test_direct_query_endpoint_missing_query(self, client):
        """Test the direct query endpoint with missing query."""
        response = client.post("/query", json={})
        assert response.status_code == 400


class TestCurlCommands:
    """Test curl-equivalent commands for FastAPI server."""

    @pytest.fixture
    def base_url(self):
        """Base URL for the FastAPI server."""
        return "http://localhost:7000"

    def test_curl_health_check(self, client):
        """Test equivalent of: curl -s http://localhost:7000/health"""
        response = client.get("/health")
        assert response.status_code == 200
        assert "healthy" in response.json()["status"]

    def test_curl_root_endpoint(self, client):
        """Test equivalent of: curl -s http://localhost:7000/"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Hospital Agent Server"

    def test_curl_direct_query(self, client, mock_httpx_client):
        """Test equivalent of: curl -X POST http://localhost:7000/query -H "Content-Type: application/json" -d '{"query": "I need a cardiologist"}'"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_httpx_client
            
            with patch('server.fastapi_agent_server.model') as mock_model:
                mock_agent = MagicMock()
                mock_agent.run.return_value = "Test AI response"
                
                with patch('server.fastapi_agent_server.ToolCallingAgent', return_value=mock_agent):
                    response = client.post(
                        "/query",
                        json={"query": "I need a cardiologist"},
                        headers={"Content-Type": "application/json"}
                    )
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True

    def test_curl_run_sync(self, client, mock_httpx_client):
        """Test equivalent of: curl -X POST http://localhost:7000/run_sync -H "Content-Type: application/json" -d '{"agent": "health_agent", "input": "test"}'"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_httpx_client
            
            with patch('server.fastapi_agent_server.model') as mock_model:
                mock_agent = MagicMock()
                mock_agent.run.return_value = "Test AI response"
                
                with patch('server.fastapi_agent_server.ToolCallingAgent', return_value=mock_agent):
                    response = client.post(
                        "/run_sync",
                        json={"agent": "health_agent", "input": "I need a cardiologist"},
                        headers={"Content-Type": "application/json"}
                    )
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True
                    assert len(data["output"]) > 0
