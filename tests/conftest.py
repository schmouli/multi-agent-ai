"""Test configuration and fixtures for the multi-agent-ai project."""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_openai_key():
    """Provide a mock OpenAI API key for testing."""
    return "test-openai-api-key-for-testing"


@pytest.fixture
def mock_environment(mock_openai_key):
    """Mock environment variables for testing."""
    env_vars = {
        "OPENAI_API_KEY": mock_openai_key
    }
    
    # Store original values
    original_values = {}
    for key, value in env_vars.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield env_vars
    
    # Restore original values
    for key, original_value in original_values.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value


@pytest.fixture
def sample_doctor_data():
    """Provide sample doctor data for testing."""
    return {
        "DOC_TEST": {
            "name": "Dr. Test Smith",
            "specialty": "Cardiology",
            "address": {
                "street": "123 Test Street",
                "city": "Test City",
                "state": "GA",
                "zip_code": "12345",
            },
            "phone": "(555) 123-4567",
            "email": "test.smith@testhosp.com",
            "years_experience": 10,
            "board_certified": True,
            "hospital_affiliations": ["Test Hospital"],
            "education": {
                "medical_school": "Test Medical School",
                "residency": "Test Residency",
                "fellowship": "Test Fellowship",
            },
            "languages": ["English"],
            "accepts_new_patients": True,
            "insurance_accepted": ["Test Insurance"],
        }
    }


@pytest.fixture
def mock_acp_client():
    """Mock ACP client for testing."""
    mock_client = MagicMock()
    mock_client.run_sync = MagicMock()
    return mock_client


@pytest.fixture
def mock_message_part():
    """Mock message part for testing."""
    mock_part = MagicMock()
    mock_part.content = "Test message content"
    return mock_part


@pytest.fixture
def mock_message(mock_message_part):
    """Mock message for testing."""
    mock_msg = MagicMock()
    mock_msg.parts = [mock_message_part]
    return mock_msg


@pytest.fixture
def mock_server_response():
    """Mock server response for testing."""
    mock_response = MagicMock()
    mock_response.output = [MagicMock()]
    mock_response.output[0].parts = [MagicMock()]
    mock_response.output[0].parts[0].content = "Test server response"
    return mock_response


# Pytest configuration for async tests
def pytest_configure(config):
    """Configure pytest for the project."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
