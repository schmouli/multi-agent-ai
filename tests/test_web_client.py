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

from client.web_client import app, query_hospital_agent


class TestWebClient:
    """Test cases for web client functionality."""

    @pytest.fixture
    def client(self):
        """Create a test client for the web client app."""
        return TestClient(app)

    @pytest.fixture
    def mock_httpx_client(self):
        """Mock httpx client for FastAPI server communication."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "output": [{"parts": [{"content": "Test AI response from doctor search"}]}]
        }
        mock_client.post.return_value = mock_response
        mock_client_class = MagicMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        return mock_client_class

    def test_index_page(self, client):
        """Test that the index page loads successfully."""
        response = client.get("/")
        assert response.status_code == 200
        assert "Hospital Agent Client" in response.text
        assert "form" in response.text.lower()

    @pytest.mark.asyncio
    async def test_query_hospital_agent_success(self, mock_httpx_client):
        """Test successful query to hospital agent."""
        with patch('httpx.AsyncClient', mock_httpx_client):
            result = await query_hospital_agent("atlanta", "I need a cardiologist")
            assert "Test AI response from doctor search" in result

    @pytest.mark.asyncio
    async def test_query_hospital_agent_server_error(self):
        """Test query when server returns error."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            with pytest.raises(Exception):  # Should raise HTTPException
                await query_hospital_agent("atlanta", "I need a cardiologist")

    @pytest.mark.asyncio
    async def test_query_hospital_agent_api_error(self):
        """Test query when API returns error response."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": False,
                "error": "API Error occurred"
            }
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            with pytest.raises(Exception):  # Should raise HTTPException
                await query_hospital_agent("atlanta", "I need a cardiologist")

    @pytest.mark.asyncio
    async def test_query_hospital_agent_connection_error(self):
        """Test query when connection fails."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.side_effect = Exception("Connection failed")
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            with pytest.raises(Exception):  # Should raise HTTPException
                await query_hospital_agent("atlanta", "I need a cardiologist")

    def test_query_endpoint_success(self, client, mock_httpx_client):
        """Test the query endpoint with successful response."""
        with patch('httpx.AsyncClient', mock_httpx_client):
            response = client.post("/query", json={
                "location": "atlanta",
                "query": "I need a cardiologist"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "Test AI response from doctor search" in data["result"]

    def test_query_endpoint_missing_fields(self, client):
        """Test the query endpoint with missing fields."""
        # Missing location
        response = client.post("/query", json={
            "query": "I need a cardiologist"
        })
        assert response.status_code == 422  # Validation error

        # Missing query
        response = client.post("/query", json={
            "location": "atlanta"
        })
        assert response.status_code == 422  # Validation error

    def test_query_endpoint_empty_fields(self, client):
        """Test the query endpoint with empty fields."""
        response = client.post("/query", json={
            "location": "",
            "query": ""
        })
        assert response.status_code == 422 or response.status_code == 500


class TestWebClientCurlCommands:
    """Test curl-equivalent commands for web client."""

    @pytest.fixture
    def client(self):
        """Create a test client for the web client app."""
        return TestClient(app)

    @pytest.fixture
    def mock_httpx_client(self):
        """Mock httpx client for FastAPI server communication."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "output": [{"parts": [{"content": "Dr. Sarah Mitchell - Cardiology - Atlanta, GA"}]}]
        }
        mock_client.post.return_value = mock_response
        mock_client_class = MagicMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        return mock_client_class

    def test_curl_get_index(self, client):
        """Test equivalent of: curl -s http://localhost:7080/"""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_curl_query_cardiologist_atlanta(self, client, mock_httpx_client):
        """
        Test equivalent of:
        curl -X POST http://localhost:7080/query \
             -H "Content-Type: application/json" \
             -d '{"location": "atlanta", "query": "I need to find a cardiologist"}'
        """
        with patch('httpx.AsyncClient', mock_httpx_client):
            response = client.post(
                "/query",
                json={
                    "location": "atlanta",
                    "query": "I need to find a cardiologist"
                },
                headers={"Content-Type": "application/json"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "Dr. Sarah Mitchell" in data["result"]

    def test_curl_query_different_locations(self, client, mock_httpx_client):
        """
        Test queries for different locations:
        curl -X POST http://localhost:7080/query \
             -H "Content-Type: application/json" \
             -d '{"location": "california", "query": "I need a dermatologist"}'
        """
        test_cases = [
            {"location": "california", "query": "I need a dermatologist"},
            {"location": "texas", "query": "I need a pediatrician"},
            {"location": "florida", "query": "I need an orthopedic surgeon"},
            {"location": "GA", "query": "I need an emergency doctor"}
        ]
        
        with patch('httpx.AsyncClient', mock_httpx_client):
            for test_case in test_cases:
                response = client.post(
                    "/query",
                    json=test_case,
                    headers={"Content-Type": "application/json"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True

    def test_curl_query_with_verbose_output(self, client, mock_httpx_client):
        """
        Test equivalent of:
        curl -v -X POST http://localhost:7080/query \
             -H "Content-Type: application/json" \
             -d '{"location": "atlanta", "query": "I need urgent care"}'
        """
        with patch('httpx.AsyncClient', mock_httpx_client):
            response = client.post(
                "/query",
                json={
                    "location": "atlanta",
                    "query": "I need urgent care"
                },
                headers={"Content-Type": "application/json"}
            )
            
            # Check response details (equivalent to verbose curl output)
            assert response.status_code == 200
            assert "application/json" in response.headers["content-type"]
            
            data = response.json()
            assert "success" in data
            assert "result" in data or "error" in data

    def test_curl_malformed_requests(self, client):
        """
        Test various malformed requests:
        curl -X POST http://localhost:7080/query -H "Content-Type: application/json" -d '{invalid json}'
        """
        # Invalid JSON
        response = client.post(
            "/query",
            data="{invalid json}",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

        # Missing content-type
        response = client.post(
            "/query",
            json={"location": "atlanta", "query": "test"}
        )
        # Should still work as TestClient handles this
        assert response.status_code in [200, 422, 500]
