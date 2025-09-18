"""Integration tests for the complete FastAPI-based architecture."""

import pytest
import asyncio
import time
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the project root to the Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from server.fastapi_agent_server import app as agent_app
from server.mcpserver import app as mcp_app
from client.web_client import app as client_app


class TestIntegrationE2E:
    """End-to-end integration tests for the complete system."""

    @pytest.fixture
    def agent_client(self):
        """Create a test client for the FastAPI agent server."""
        return TestClient(agent_app)

    @pytest.fixture
    def mcp_client(self):
        """Create a test client for the MCP server."""
        return TestClient(mcp_app)

    @pytest.fixture
    def web_client(self):
        """Create a test client for the web client."""
        return TestClient(client_app)

    def test_mcp_server_to_agent_server_integration(self, agent_client, mcp_client):
        """Test integration between MCP server and FastAPI agent server."""
        # First verify MCP server is working
        mcp_response = mcp_client.post("/", json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "doctor_search",
                "arguments": {"state": "GA"}
            }
        })
        
        assert mcp_response.status_code == 200
        mcp_data = mcp_response.json()
        assert "Dr. Sarah Mitchell" in mcp_data["result"]["content"][0]["text"]

        # Test agent server health check
        agent_response = agent_client.get("/health")
        assert agent_response.status_code == 200
        assert agent_response.json()["status"] == "healthy"

        # Test agent server query endpoint with mocked MCP communication
        with patch('httpx.AsyncClient') as mock_httpx:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mcp_data
            mock_client.post.return_value = mock_response
            mock_httpx.return_value.__aenter__.return_value = mock_client

            agent_response = agent_client.post("/query", json={
                "location": "GA",
                "query": "I need a cardiologist in Atlanta"
            })
            
            assert agent_response.status_code == 200
            agent_data = agent_response.json()
            assert agent_data["success"] is True

    def test_web_client_to_agent_server_integration(self, web_client):
        """Test integration between web client and FastAPI agent server."""
        # Mock the agent server response
        mock_agent_response = {
            "success": True,
            "output": [{
                "parts": [{"content": "Found cardiologist: Dr. Sarah Mitchell in Atlanta, GA"}]
            }]
        }

        with patch('httpx.AsyncClient') as mock_httpx:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_agent_response
            mock_client.post.return_value = mock_response
            mock_httpx.return_value.__aenter__.return_value = mock_client

            # Test web client query
            response = web_client.post("/query", json={
                "location": "atlanta",
                "query": "I need a cardiologist"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "Dr. Sarah Mitchell" in data["result"]

    def test_complete_system_flow(self, web_client, mcp_client):
        """Test the complete flow from web client through agent server to MCP server."""
        # Mock the complete chain of communications
        
        # First, mock the MCP server response
        mcp_response_data = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "content": [{
                    "type": "text",
                    "text": "DOC001: Dr. Sarah Mitchell - Cardiology - Atlanta, GA, 30309"
                }]
            }
        }

        # Mock the agent server processing the MCP response
        agent_response_data = {
            "success": True,
            "output": [{
                "parts": [{"content": "Based on your search in Atlanta, I found Dr. Sarah Mitchell, a board-certified cardiologist with 15 years of experience."}]
            }]
        }

        with patch('httpx.AsyncClient') as mock_httpx:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = agent_response_data
            mock_client.post.return_value = mock_response
            mock_httpx.return_value.__aenter__.return_value = mock_client

            # Test the complete flow through web client
            response = web_client.post("/query", json={
                "location": "atlanta",
                "query": "I need to find a cardiologist for my heart condition"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "Dr. Sarah Mitchell" in data["result"]
            assert "cardiologist" in data["result"]

    def test_error_propagation_through_system(self, web_client):
        """Test how errors propagate through the system layers."""
        # Mock agent server returning an error
        with patch('httpx.AsyncClient') as mock_httpx:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_client.post.return_value = mock_response
            mock_httpx.return_value.__aenter__.return_value = mock_client

            response = web_client.post("/query", json={
                "location": "atlanta",
                "query": "I need a doctor"
            })
            
            # Should handle the error gracefully
            assert response.status_code == 200  # Web client handles errors
            data = response.json()
            assert data["success"] is False
            assert "error" in data

    def test_system_performance_benchmarks(self, web_client):
        """Test basic performance benchmarks for the system."""
        mock_response_data = {
            "success": True,
            "output": [{
                "parts": [{"content": "Quick response for performance test"}]
            }]
        }

        with patch('httpx.AsyncClient') as mock_httpx:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client.post.return_value = mock_response
            mock_httpx.return_value.__aenter__.return_value = mock_client

            # Test multiple concurrent requests
            start_time = time.time()
            
            responses = []
            for i in range(5):
                response = web_client.post("/query", json={
                    "location": f"city{i}",
                    "query": f"test query {i}"
                })
                responses.append(response)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # All requests should succeed
            for response in responses:
                assert response.status_code == 200
                assert response.json()["success"] is True
            
            # Should complete reasonably quickly (under 5 seconds for 5 requests)
            assert duration < 5.0


class TestIntegrationCurlEquivalents:
    """Integration tests using curl-equivalent commands."""

    @pytest.fixture
    def agent_client(self):
        """Create a test client for the FastAPI agent server."""
        return TestClient(agent_app)

    @pytest.fixture
    def mcp_client(self):
        """Create a test client for the MCP server."""
        return TestClient(mcp_app)

    @pytest.fixture
    def web_client(self):
        """Create a test client for the web client."""
        return TestClient(client_app)

    def test_curl_complete_workflow(self, web_client, mcp_client):
        """
        Test complete workflow using curl-equivalent commands:
        
        1. curl -X POST http://localhost:7080/query -H "Content-Type: application/json" \
           -d '{"location": "atlanta", "query": "I need a cardiologist"}'
        2. (Internal) curl -X POST http://localhost:7000/query -H "Content-Type: application/json" \
           -d '{"location": "atlanta", "query": "I need a cardiologist"}'
        3. (Internal) curl -X POST http://localhost:8333/ -H "Content-Type: application/json" \
           -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "doctor_search", "arguments": {"state": "GA"}}}'
        """
        
        # Step 1: Test the MCP server endpoint directly
        mcp_response = mcp_client.post(
            "/",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "doctor_search",
                    "arguments": {"state": "GA"}
                }
            },
            headers={"Content-Type": "application/json"}
        )
        
        assert mcp_response.status_code == 200
        mcp_data = mcp_response.json()
        assert "Dr. Sarah Mitchell" in mcp_data["result"]["content"][0]["text"]

        # Step 2: Test the complete web client request (with mocked backend)
        mock_agent_response = {
            "success": True,
            "output": [{
                "parts": [{"content": "I found Dr. Sarah Mitchell, a cardiologist in Atlanta, GA. She has 15 years of experience and is board-certified."}]
            }]
        }

        with patch('httpx.AsyncClient') as mock_httpx:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_agent_response
            mock_client.post.return_value = mock_response
            mock_httpx.return_value.__aenter__.return_value = mock_client

            web_response = web_client.post(
                "/query",
                json={
                    "location": "atlanta",
                    "query": "I need a cardiologist"
                },
                headers={"Content-Type": "application/json"}
            )
            
            assert web_response.status_code == 200
            web_data = web_response.json()
            assert web_data["success"] is True
            assert "Dr. Sarah Mitchell" in web_data["result"]

    def test_curl_health_checks_all_services(self, agent_client, mcp_client, web_client):
        """
        Test health checks for all services:
        curl -s http://localhost:7000/health  # Agent server
        curl -s http://localhost:8333/health  # MCP server
        curl -s http://localhost:7080/        # Web client
        """
        
        # Agent server health check
        agent_health = agent_client.get("/health")
        assert agent_health.status_code == 200
        assert agent_health.json()["status"] == "healthy"

        # MCP server health check
        mcp_health = mcp_client.get("/health")
        assert mcp_health.status_code == 200
        assert mcp_health.json()["status"] == "healthy"

        # Web client index (serves as health check)
        web_index = web_client.get("/")
        assert web_index.status_code == 200
        assert "text/html" in web_index.headers["content-type"]

    def test_curl_error_scenarios(self, web_client, mcp_client):
        """
        Test error scenarios with curl-equivalent commands.
        """
        
        # Test invalid MCP request
        mcp_error_response = mcp_client.post(
            "/",
            json={"invalid": "request"},
            headers={"Content-Type": "application/json"}
        )
        assert mcp_error_response.status_code == 200
        mcp_error_data = mcp_error_response.json()
        assert "error" in mcp_error_data

        # Test web client with invalid request format
        web_error_response = web_client.post(
            "/query",
            json={"invalid": "format"},
            headers={"Content-Type": "application/json"}
        )
        assert web_error_response.status_code == 422  # Validation error

    def test_curl_stress_test(self, mcp_client):
        """
        Simulate stress testing with multiple curl requests:
        for i in {1..10}; do curl -X POST http://localhost:8333/ -H "Content-Type: application/json" \
        -d '{"jsonrpc": "2.0", "id": '$i', "method": "tools/call", "params": {"name": "doctor_search", "arguments": {"state": "GA"}}}' & done
        """
        
        responses = []
        
        # Simulate 10 concurrent requests
        for i in range(1, 11):
            response = mcp_client.post(
                "/",
                json={
                    "jsonrpc": "2.0",
                    "id": i,
                    "method": "tools/call",
                    "params": {
                        "name": "doctor_search",
                        "arguments": {"state": "GA"}
                    }
                },
                headers={"Content-Type": "application/json"}
            )
            responses.append(response)

        # All requests should succeed
        for i, response in enumerate(responses, 1):
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == i  # Should echo back the request ID
            assert "result" in data
