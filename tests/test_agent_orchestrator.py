"""Tests for the Agent Orchestrator functionality."""

import pytest
import asyncio
import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

# Add the project root to the Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "server"))

# Set required environment variables before importing
os.environ.setdefault("OPENAI_API_KEY", "test-api-key")
os.environ.setdefault("FASTAPI_SERVER_URL", "http://test-server:7000")
os.environ.setdefault("INSURANCE_SERVER_URL", "ws://test-insurance:7001")
os.environ.setdefault("MCP_SERVER_URL", "http://test-mcp:8333")

# Import the orchestrator modules
try:
    from agent_orchestrator import AgentOrchestrator, QueryType, QueryRequest, QueryResponse, app, orchestrator
except ImportError:
    from server.agent_orchestrator import AgentOrchestrator, QueryType, QueryRequest, QueryResponse, app, orchestrator


class TestAgentOrchestrator:
    """Test cases for the Agent Orchestrator functionality."""

    @pytest.fixture
    def mock_openai_config(self):
        """Mock OpenAI configuration."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-api-key"}):
            yield

    @pytest.fixture
    def orchestrator_instance(self, mock_openai_config):
        """Create an orchestrator instance for testing."""
        # Mock both server.agent_orchestrator and agent_orchestrator imports
        with patch('server.agent_orchestrator.AssistantAgent') as mock_assistant, \
             patch('server.agent_orchestrator.UserProxyAgent') as mock_proxy, \
             patch('agent_orchestrator.AssistantAgent', mock_assistant), \
             patch('agent_orchestrator.UserProxyAgent', mock_proxy):
            mock_assistant.return_value = MagicMock()
            mock_proxy.return_value = MagicMock()
            return AgentOrchestrator()

    def test_orchestrator_initialization(self, mock_openai_config):
        """Test orchestrator initializes correctly."""
        with patch('server.agent_orchestrator.AssistantAgent') as mock_assistant, \
             patch('server.agent_orchestrator.UserProxyAgent') as mock_user, \
             patch('agent_orchestrator.AssistantAgent', mock_assistant), \
             patch('agent_orchestrator.UserProxyAgent', mock_user):
            orchestrator = AgentOrchestrator()
            
            # Check that agents were created
            assert mock_assistant.call_count >= 3  # router, health, insurance agents
            assert mock_user.call_count >= 1  # user proxy
            assert hasattr(orchestrator, 'router_agent')
            assert hasattr(orchestrator, 'health_agent')
            assert hasattr(orchestrator, 'insurance_agent')

    def test_orchestrator_missing_api_key(self):
        """Test orchestrator fails without API key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OPENAI_API_KEY is required"):
                AgentOrchestrator()

    def test_fallback_classify_health_keywords(self, orchestrator_instance):
        """Test fallback classification with health keywords."""
        test_cases = [
            # Provider seeking cases (should get 0.8 confidence)
            ("I need to find a doctor", 0.8, "provider seeking"),
            ("Looking for a cardiologist in Atlanta", 0.8, "provider seeking"),  
            ("Find me a hospital nearby", 0.8, "provider seeking"),
            
            # Health keyword cases (should get 0.7 confidence)
            ("What specialists are available?", 0.7, "health keywords"),
            ("I have symptoms and need medical help", 0.7, "health keywords"), 
            ("Need to see a pediatrician", 0.7, "health keywords")
        ]
        
        for query, expected_confidence, expected_reasoning_type in test_cases:
            query_type, confidence, reasoning = orchestrator_instance._fallback_classify(query)
            assert query_type == QueryType.HEALTH_DOCTOR, f"Failed for query: {query}"
            assert confidence == expected_confidence, f"Expected {expected_confidence}, got {confidence} for: {query}"
            assert expected_reasoning_type.lower() in reasoning.lower(), f"Expected '{expected_reasoning_type}' in reasoning '{reasoning}' for: {query}"

    def test_fallback_classify_insurance_keywords(self, orchestrator_instance):
        """Test fallback classification with insurance keywords."""
        test_cases = [
            # Strong insurance phrases (should get 0.8 confidence)
            ("What's my deductible?", 0.8, "strong insurance"),
            ("Check my policy coverage", 0.8, "strong insurance"),
            ("What are my insurance benefits?", 0.8, "strong insurance"),
            ("Check my insurance benefits", 0.8, "strong insurance"),
            
            # Regular insurance keywords (should get 0.7 confidence)
            ("Insurance reimbursement question", 0.7, "insurance keywords"),
        ]
        
        for query, expected_confidence, expected_reasoning_type in test_cases:
            query_type, confidence, reasoning = orchestrator_instance._fallback_classify(query)
            assert query_type == QueryType.INSURANCE, f"Failed for query: {query}"
            assert confidence == expected_confidence, f"Expected {expected_confidence}, got {confidence} for: {query}"
            assert expected_reasoning_type.lower() in reasoning.lower(), f"Expected '{expected_reasoning_type}' in reasoning '{reasoning}' for: {query}"

    def test_fallback_classify_provider_seeking(self, orchestrator_instance):
        """Test fallback classification prioritizes provider-seeking queries."""
        test_cases = [
            "find me a doctor that accepts my insurance",
            "looking for a specialist in my network",
            "need a doctor covered by my plan"
        ]
        
        for query in test_cases:
            query_type, confidence, reasoning = orchestrator_instance._fallback_classify(query)
            assert query_type == QueryType.HEALTH_DOCTOR
            assert confidence == 0.8  # Provider seeking gets 0.8 confidence
            assert "Provider seeking phrases found:" in reasoning

    def test_fallback_classify_unknown_query(self, orchestrator_instance):
        """Test fallback classification with ambiguous queries."""
        test_cases = [
            "Hello there",
            "What's the weather like?",
            "Random question about nothing specific", 
            "Just testing the system"
        ]
        
        for query in test_cases:
            query_type, confidence, reasoning = orchestrator_instance._fallback_classify(query)
            # Should default to HEALTH_DOCTOR for unclear queries
            assert query_type == QueryType.HEALTH_DOCTOR
            assert confidence == 0.3  # Match implementation
            assert "Default to health agent" in reasoning  # Match implementation

    @pytest.mark.asyncio
    async def test_route_to_health_agent_success(self, orchestrator_instance):
        """Test successful routing to health agent."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": True,
                "result": "Test response from health agent"
            }
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            result = await orchestrator_instance.route_to_health_agent("atlanta", "find cardiologist")
            
            assert result["success"] is True
            assert "result" in result

    @pytest.mark.asyncio
    async def test_route_to_health_agent_error(self, orchestrator_instance):
        """Test health agent routing with HTTP error."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            result = await orchestrator_instance.route_to_health_agent("atlanta", "find cardiologist")
            
            assert result["success"] is False
            assert "error" in result

    @pytest.mark.asyncio
    async def test_route_to_insurance_agent_error(self, orchestrator_instance):
        """Test insurance agent routing with connection error."""
        with patch('websockets.connect', side_effect=Exception("Connection failed")):
            result = await orchestrator_instance.route_to_insurance_agent("check coverage")
            
            assert result["success"] is False
            assert "error" in result or "Cannot reach insurance agent" in result["result"]

    @pytest.mark.asyncio 
    async def test_process_query_health_forced(self, orchestrator_instance):
        """Test process_query with forced health agent."""
        with patch.object(orchestrator_instance, 'route_to_health_agent') as mock_health:
            mock_health.return_value = {
                "success": True,
                "result": "Found cardiologist",
                "agent_used": "health_doctor"
            }
            
            result = await orchestrator_instance.process_query(
                "atlanta", "find cardiologist", force_agent="doctor"
            )
            
            assert result.success is True
            assert result.agent_used == "health_doctor"
            mock_health.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_query_insurance_forced(self, orchestrator_instance):
        """Test process_query with forced insurance agent."""
        with patch.object(orchestrator_instance, 'route_to_insurance_agent') as mock_insurance:
            mock_insurance.return_value = {
                "success": True,
                "result": "Coverage details",
                "agent_used": "insurance"
            }
            
            result = await orchestrator_instance.process_query(
                "", "check coverage", force_agent="insurance"
            )
            
            assert result.success is True
            assert result.agent_used == "insurance"
            mock_insurance.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_query_error_handling(self, orchestrator_instance):
        """Test process_query error handling."""
        with patch.object(orchestrator_instance, 'classify_query') as mock_classify:
            mock_classify.side_effect = Exception("Classification error")
            
            result = await orchestrator_instance.process_query("atlanta", "test query")
            
            assert result.success is False
            assert "Orchestration error" in result.result
            assert result.agent_used == "error"

    @pytest.mark.asyncio
    async def test_empty_query_handling(self, orchestrator_instance):
        """Test handling of empty queries."""
        # Empty queries are processed normally by the orchestrator
        with patch.object(orchestrator_instance, 'classify_query') as mock_classify, \
             patch.object(orchestrator_instance, 'route_to_health_agent') as mock_health:
            
            mock_classify.return_value = (QueryType.HEALTH_DOCTOR, 0.3, "Default to health agent")
            mock_health.return_value = {
                "success": True,
                "result": "No specific results for empty query",
                "agent_used": "health_doctor"
            }
            
            result = await orchestrator_instance.process_query("atlanta", "")
            
            # The orchestrator processes empty queries normally
            assert result.success is True


class TestOrchestratorAPI:
    """Test cases for orchestrator FastAPI endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client for the orchestrator app."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}), \
             patch('server.agent_orchestrator.orchestrator') as mock_orch, \
             patch('agent_orchestrator.orchestrator', mock_orch):
            mock_orch.process_query = AsyncMock()
            return TestClient(app)

    def test_health_endpoint(self, client):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "orchestrator-server"
        assert "agents" in data

    def test_query_endpoint_success(self, client):
        """Test successful query endpoint."""
        with patch('server.agent_orchestrator.orchestrator.process_query') as mock_process, \
             patch('agent_orchestrator.orchestrator.process_query', mock_process):
            mock_process.return_value = QueryResponse(
                success=True,
                result="Test response",
                agent_used="health_doctor",
                confidence=0.9,
                reasoning="Health keywords detected"
            )
            
            response = client.post("/query", json={
                "location": "atlanta",
                "query": "find cardiologist",
                "agent": "auto"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["result"] == "Test response"
            assert data["agent_used"] == "health_doctor"

    def test_query_endpoint_validation_error(self, client):
        """Test query endpoint with validation errors."""
        # Empty query should be caught by FastAPI validation
        response = client.post("/query", json={
            "location": "atlanta",
            "query": "",
            "agent": "auto"
        })
        assert response.status_code == 400  # Empty query validation

        # Missing required fields
        response = client.post("/query", json={
            "location": "atlanta"
            # Missing 'query' field
        })
        assert response.status_code == 422  # Pydantic validation error

    def test_agents_status_endpoint(self, client):
        """Test the agents status endpoint."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            response = client.get("/agents/status")
            assert response.status_code == 200
            
            data = response.json()
            assert "health_agent" in data
            assert "insurance_agent" in data
            assert "mcp_server" in data


class TestQueryClassificationScenarios:
    """Test specific query classification scenarios."""

    @pytest.fixture
    def orchestrator_instance(self):
        """Create orchestrator for classification testing."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}), \
             patch('server.agent_orchestrator.AssistantAgent') as mock_assistant, \
             patch('server.agent_orchestrator.UserProxyAgent') as mock_proxy, \
             patch('agent_orchestrator.AssistantAgent', mock_assistant), \
             patch('agent_orchestrator.UserProxyAgent', mock_proxy):
            mock_assistant.return_value = MagicMock()
            mock_proxy.return_value = MagicMock()
            return AgentOrchestrator()

    def test_provider_seeking_with_insurance_context(self, orchestrator_instance):
        """Test queries that seek providers but mention insurance."""
        test_cases = [
            "find me a doctor that accepts Blue Cross",
            "looking for cardiologist in my insurance network",
            "need specialist covered by my plan",
            "find doctor that takes my insurance"
        ]
        
        for query in test_cases:
            query_type, confidence, reasoning = orchestrator_instance._fallback_classify(query)
            assert query_type == QueryType.HEALTH_DOCTOR
            assert confidence == 0.8  # Provider seeking gets 0.8 confidence
            assert "Provider seeking phrases found:" in reasoning

    def test_pure_insurance_coverage_questions(self, orchestrator_instance):
        """Test pure insurance coverage questions."""
        test_cases = [
            ("does my insurance cover MRI scans?", "does my insurance cover"),
            ("what is my deductible for specialists?", "my deductible"), 
            ("is this procedure covered by my policy?", "covered by"),
            ("check my insurance benefits", "check my insurance benefits")
        ]
        
        for query, expected_phrase in test_cases:
            query_type, confidence, reasoning = orchestrator_instance._fallback_classify(query)
            assert query_type == QueryType.INSURANCE, f"Failed for query: {query}"
            assert confidence == 0.8, f"Expected 0.8, got {confidence} for: {query}"  # Strong insurance phrases get 0.8 confidence

    def test_mixed_context_prioritization(self, orchestrator_instance):
        """Test queries with both health and insurance keywords."""
        # Provider-seeking should win
        provider_seeking_queries = [
            "find cardiologist covered by insurance",
            "doctor near me that accepts my plan"
        ]
        
        for query in provider_seeking_queries:
            query_type, confidence, reasoning = orchestrator_instance._fallback_classify(query)
            assert query_type == QueryType.HEALTH_DOCTOR
        
        # Strong insurance phrases should win
        insurance_queries = [
            "does my plan cover cardiologist visits?",
            "my insurance benefits for heart doctor"
        ]
        
        for query in insurance_queries:
            query_type, confidence, reasoning = orchestrator_instance._fallback_classify(query)
            assert query_type == QueryType.INSURANCE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])