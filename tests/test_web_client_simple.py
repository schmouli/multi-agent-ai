"""Simple tests for the web client functionality."""

import pytest
import sys
from pathlib import Path

# Add the project root to the Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from client.web_client import QueryRequest, QueryResponse


class TestWebClientModels:
    """Test cases for Pydantic models."""

    def test_query_request_model(self):
        """Test QueryRequest model validation."""
        # Valid request
        request = QueryRequest(location="Atlanta, GA", query="Find a cardiologist")
        assert request.location == "Atlanta, GA"
        assert request.query == "Find a cardiologist"

    def test_query_request_validation(self):
        """Test QueryRequest model field validation."""
        # Test with empty strings
        request = QueryRequest(location="", query="")
        assert request.location == ""
        assert request.query == ""

    def test_query_response_model_success(self):
        """Test QueryResponse model for successful response."""
        response = QueryResponse(success=True, result="Dr. Smith found")
        assert response.success is True
        assert response.result == "Dr. Smith found"
        assert response.error is None

    def test_query_response_model_error(self):
        """Test QueryResponse model for error response."""
        response = QueryResponse(success=False, error="Connection failed")
        assert response.success is False
        assert response.error == "Connection failed"
        assert response.result is None


class TestWebClientStructure:
    """Test cases for web client structure and configuration."""

    def test_app_exists(self):
        """Test that the FastAPI app exists and is configured."""
        from client.web_client import app
        assert app is not None
        assert app.title == "Hospital Agent Client"
        assert "hospital agent queries" in app.description.lower()

    def test_query_hospital_agent_exists(self):
        """Test that the query function exists."""
        from client.web_client import query_hospital_agent
        assert query_hospital_agent is not None
        assert callable(query_hospital_agent)

    def test_models_structure(self):
        """Test that models have the expected structure."""
        # Test QueryRequest fields
        request = QueryRequest(location="test", query="test")
        assert hasattr(request, 'location')
        assert hasattr(request, 'query')
        
        # Test QueryResponse fields
        response = QueryResponse(success=True)
        assert hasattr(response, 'success')
        assert hasattr(response, 'result')
        assert hasattr(response, 'error')


class TestWebClientConfiguration:
    """Test cases for web client configuration."""

    def test_imports_available(self):
        """Test that all required imports are available."""
        try:
            from client.web_client import app, QueryRequest, QueryResponse, query_hospital_agent
            assert app is not None
            assert QueryRequest is not None
            assert QueryResponse is not None
            assert query_hospital_agent is not None
        except ImportError as e:
            pytest.fail(f"Required imports not available: {e}")

    def test_fastapi_routes_configured(self):
        """Test that FastAPI routes are configured."""
        from client.web_client import app
        
        # Check that routes exist
        routes = [route.path for route in app.routes]
        assert "/" in routes
        assert "/query" in routes

    @pytest.mark.parametrize("location,query", [
        ("Atlanta, GA", "Find a cardiologist"),
        ("Phoenix, AZ", "Need a pediatrician"),
        ("Los Angeles, CA", "Dermatologist near me"),
        ("", ""),  # Test edge cases
    ])
    def test_query_request_with_various_inputs(self, location, query):
        """Test QueryRequest with various input combinations."""
        request = QueryRequest(location=location, query=query)
        assert request.location == location
        assert request.query == query

    def test_query_response_defaults(self):
        """Test QueryResponse default values."""
        # Test minimal response
        response = QueryResponse(success=True)
        assert response.success is True
        assert response.result is None
        assert response.error is None
        
        response = QueryResponse(success=False)
        assert response.success is False
        assert response.result is None
        assert response.error is None
