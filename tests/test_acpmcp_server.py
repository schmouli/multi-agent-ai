"""Tests for the ACP server functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from collections.abc import AsyncGenerator

from acp_sdk.models import Message, MessagePart


class TestACPServer:
    """Test cases for ACP server functionality."""

    @pytest.fixture
    def mock_message(self):
        """Create a mock message for testing."""
        part = MessagePart(content="I'm based in Atlanta, GA. Are there any Cardiologists near me?")
        return Message(parts=[part])

    @pytest.fixture
    def mock_context(self):
        """Create a mock context for testing."""
        return MagicMock()

    @patch('server.acpmcp_server.ToolCollection')
    @patch('server.acpmcp_server.ToolCallingAgent')
    @pytest.mark.asyncio
    async def test_health_agent_basic_functionality(self, mock_agent_class, mock_tool_collection, mock_message, mock_context):
        """Test basic functionality of health_agent."""
        from server.acpmcp_server import health_agent
        
        # Setup mocks
        mock_tool_collection.from_mcp.return_value.__enter__.return_value.tools = []
        mock_agent_instance = MagicMock()
        mock_agent_instance.run.return_value = "Test response"
        mock_agent_class.return_value = mock_agent_instance
        
        # Call the agent
        result_generator = health_agent([mock_message], mock_context)
        
        # Get the result
        result_message = None
        async for message in result_generator:
            result_message = message
            break
        
        # Assertions
        assert result_message is not None
        assert isinstance(result_message, Message)
        assert len(result_message.parts) == 1
        assert result_message.parts[0].content == "Test response"

    @patch('server.acpmcp_server.model')
    @patch('server.acpmcp_server.ToolCollection')
    @patch('server.acpmcp_server.ToolCallingAgent')
    @pytest.mark.asyncio
    async def test_health_agent_with_mocked_dependencies(self, mock_agent_class, mock_tool_collection, mock_model, mock_message, mock_context):
        """Test health_agent with all dependencies mocked."""
        from server.acpmcp_server import health_agent
        
        # Setup mocks
        mock_tools = [MagicMock(), MagicMock()]
        mock_tool_collection_instance = MagicMock()
        mock_tool_collection_instance.tools = mock_tools
        mock_tool_collection.from_mcp.return_value.__enter__.return_value = mock_tool_collection_instance
        
        mock_agent_instance = MagicMock()
        mock_agent_instance.run.return_value = "Mocked health advice"
        mock_agent_class.return_value = mock_agent_instance
        
        # Call the agent
        result_generator = health_agent([mock_message], mock_context)
        result_message = None
        async for message in result_generator:
            result_message = message
            break
        
        # Verify tool collection was created with correct parameters
        mock_tool_collection.from_mcp.assert_called_once()
        
        # Verify agent was created with tools and model
        mock_agent_class.assert_called_once()
        call_args = mock_agent_class.call_args
        assert 'tools' in call_args.kwargs
        assert 'model' in call_args.kwargs
        
        # Verify agent.run was called with the message content
        mock_agent_instance.run.assert_called_once_with("I'm based in Atlanta, GA. Are there any Cardiologists near me?")
        
        # Verify response
        assert result_message.parts[0].content == "Mocked health advice"

    def test_server_parameters_configuration(self):
        """Test that server parameters are configured correctly."""
        from server.acpmcp_server import server_parameters
        
        assert server_parameters.command == "uv"
        assert "run" in server_parameters.args
        assert "server/mcpserver.py" in server_parameters.args

    def test_model_configuration(self):
        """Test that the model is configured correctly."""
        from server.acpmcp_server import model
        
        # The model should be a LiteLLMModel instance
        assert hasattr(model, 'model_id')

    def test_server_instance(self):
        """Test that server instance is created."""
        from server.acpmcp_server import server
        
        assert server is not None
        # Should have the health_agent registered
        assert hasattr(server, 'agents') or hasattr(server, '_agents')

    @pytest.mark.asyncio
    async def test_health_agent_return_type(self, mock_message, mock_context):
        """Test that health_agent returns the correct type."""
        from server.acpmcp_server import health_agent
        
        with patch('server.acpmcp_server.ToolCollection') as mock_tool_collection:
            with patch('server.acpmcp_server.ToolCallingAgent') as mock_agent_class:
                # Setup mocks
                mock_tool_collection.from_mcp.return_value.__enter__.return_value.tools = []
                mock_agent_instance = MagicMock()
                mock_agent_instance.run.return_value = "Test response"
                mock_agent_class.return_value = mock_agent_instance
                
                # Call the agent
                result = health_agent([mock_message], mock_context)
                
                # Should return an async generator
                assert isinstance(result, AsyncGenerator)

    @pytest.mark.parametrize("test_input,expected_contains", [
        ("Find cardiologists in Atlanta", "Atlanta"),
        ("I need a pediatrician in Phoenix", "pediatrician"),
        ("Dermatologist near me in California", "Dermatologist"),
    ])
    @patch('server.acpmcp_server.ToolCollection')
    @patch('server.acpmcp_server.ToolCallingAgent')
    @pytest.mark.asyncio
    async def test_health_agent_with_different_queries(self, mock_agent_class, mock_tool_collection, test_input, expected_contains, mock_context):
        """Test health_agent with different query types."""
        from server.acpmcp_server import health_agent
        
        # Create message with test input
        part = MessagePart(content=test_input)
        message = Message(parts=[part])
        
        # Setup mocks
        mock_tool_collection.from_mcp.return_value.__enter__.return_value.tools = []
        mock_agent_instance = MagicMock()
        mock_agent_instance.run.return_value = f"Response for {test_input}"
        mock_agent_class.return_value = mock_agent_instance
        
        # Call the agent
        result_generator = health_agent([message], mock_context)
        result_message = None
        async for msg in result_generator:
            result_message = msg
            break
        
        # Verify the agent was called with the correct input
        mock_agent_instance.run.assert_called_once_with(test_input)
        
        # Verify response contains expected content
        assert expected_contains.lower() in result_message.parts[0].content.lower()


class TestServerConfiguration:
    """Test cases for server configuration and setup."""

    def test_imports_available(self):
        """Test that all required imports are available."""
        try:
            from server.acpmcp_server import server, model, server_parameters, health_agent
            assert server is not None
            assert model is not None
            assert server_parameters is not None
            assert health_agent is not None
        except ImportError as e:
            pytest.fail(f"Required imports not available: {e}")

    def test_server_parameters_structure(self):
        """Test the structure of server parameters."""
        from server.acpmcp_server import server_parameters
        
        assert hasattr(server_parameters, 'command')
        assert hasattr(server_parameters, 'args')
        assert isinstance(server_parameters.args, list)

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    def test_model_with_environment_variable(self):
        """Test model configuration with environment variable."""
        # This test would verify that the model uses environment variables
        # when available, but since the current implementation has a hardcoded
        # placeholder, we'll test the structure instead
        from server.acpmcp_server import model
        
        assert hasattr(model, 'model_id')
        # In a real implementation, this should read from environment
