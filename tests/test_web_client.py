"""Tests for the web client functionality with FastAPI backend."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the project root to the Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "client"))

from client.web_client import app, QueryRequest, QueryResponse


class TestWebClient:
    """Test cases for web client functionality."""

    @pytest.fixture
    def client(self):
        """Create a test client for the web client app."""
        return TestClient(app)

    @pytest.fixture
    def mock_httpx_client(self):
        """Mock httpx client for orchestrator communication."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "result": "Test AI response from orchestrator",
            "agent_used": "health_doctor",
            "confidence": 0.9,
            "reasoning": "Health keywords detected"
        }
        mock_client.post.return_value = mock_response
        mock_client.get.return_value = mock_response
        mock_client_class = MagicMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        return mock_client_class

    def test_index_page(self, client):
        """Test that the index page loads successfully."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            response = client.get("/")
            assert response.status_code == 404

    def test_health_endpoint(self, client):
        """Test the health check endpoint."""
        with patch('client.web_client.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            response = client.get("/health")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "web-client"
            assert "orchestrator_url" in data

    def test_query_endpoint_success(self, client, mock_httpx_client):
        """Test the query endpoint with successful response."""
        with patch('client.web_client.httpx.AsyncClient', mock_httpx_client):
            response = client.post("/query", json={
                "location": "atlanta",
                "query": "I need a cardiologist",
                "agent": "auto"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "Test AI response from orchestrator" in data["result"]
            assert data["agent_used"] == "health_doctor"

    def test_query_endpoint_orchestrator_error(self, client):
        """Test query endpoint when orchestrator returns error."""
        with patch('client.web_client.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            response = client.post("/query", json={
                "location": "atlanta",
                "query": "I need a cardiologist",
                "agent": "auto"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "Orchestrator error" in data["error"]

    def test_query_endpoint_connection_error(self, client):
        """Test query endpoint when connection fails."""
        with patch('client.web_client.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.side_effect = Exception("Connection failed")
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            response = client.post("/query", json={
                "location": "atlanta",
                "query": "I need a cardiologist",
                "agent": "auto"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "Connection error" in data["error"]

    def test_query_endpoint_validation_error(self, client):
        """Test the query endpoint with validation errors."""
        # Empty location
        response = client.post("/query", json={
            "location": "",
            "query": "I need a cardiologist"
        })
        assert response.status_code == 422

        # Empty query
        response = client.post("/query", json={
            "location": "atlanta",
            "query": ""
        })
        assert response.status_code == 422

        # Missing fields
        response = client.post("/query", json={
            "location": "atlanta"
        })
        assert response.status_code == 422

    def test_agents_status_endpoint(self, client):
        """Test the agents status endpoint."""
        with patch('client.web_client.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "health_agent": {"status": "healthy"},
                "insurance_agent": {"status": "healthy"}
            }
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            response = client.get("/agents/status")
            assert response.status_code == 200
            
            data = response.json()
            assert "health_agent" in data
            assert "insurance_agent" in data


class TestWebClientCurlCommands:
    """Test curl-equivalent commands for web client."""

    @pytest.fixture
    def client(self):
        """Create a test client for the web client app."""
        return TestClient(app)

    @pytest.fixture
    def mock_httpx_client(self):
        """Mock httpx client for orchestrator communication."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "result": "Dr. Sarah Mitchell - Cardiology - Atlanta, GA",
            "agent_used": "health_doctor",
            "confidence": 0.9,
            "reasoning": "Health keywords detected"
        }
        mock_client.post.return_value = mock_response
        mock_client.get.return_value = mock_response
        mock_client_class = MagicMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        return mock_client_class

    def test_curl_query_cardiologist_atlanta(self, client, mock_httpx_client):
        """
        Test equivalent of:
        curl -X POST http://localhost:7080/query \
             -H "Content-Type: application/json" \
             -d '{"location": "atlanta", "query": "I need to find a cardiologist"}'
        """
        with patch('client.web_client.httpx.AsyncClient', mock_httpx_client):
            response = client.post(
                "/query",
                json={
                    "location": "atlanta",
                    "query": "I need to find a cardiologist",
                    "agent": "auto"
                },
                headers={"Content-Type": "application/json"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "Dr. Sarah Mitchell" in data["result"]

    def test_curl_query_different_locations(self, client, mock_httpx_client):
        """Test queries for different locations and agent types."""
        test_cases = [
            {"location": "california", "query": "I need a dermatologist", "agent": "doctor"},
            {"location": "texas", "query": "I need a pediatrician", "agent": "auto"},
            {"location": "florida", "query": "Is my insurance covering this?", "agent": "insurance"},
            {"location": "GA", "query": "I need an emergency doctor", "agent": "doctor"}
        ]
        
        with patch('client.web_client.httpx.AsyncClient', mock_httpx_client):
            for test_case in test_cases:
                response = client.post(
                    "/query",
                    json=test_case,
                    headers={"Content-Type": "application/json"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True

    def test_curl_health_check(self, client):
        """
        Test equivalent of:
        curl -s http://localhost:7080/health
        """
        with patch('client.web_client.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            response = client.get("/health")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "web-client"

    def test_curl_malformed_requests(self, client):
        """Test various malformed requests."""
        # Missing required fields
        response = client.post(
            "/query",
            json={"location": "atlanta"},  # Missing query
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

        # Empty required fields
        response = client.post(
            "/query",
            json={"location": "", "query": "test"},  # Empty location
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
