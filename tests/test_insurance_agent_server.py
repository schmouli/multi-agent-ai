import os
import pytest
import asyncio
import tempfile
import shutil
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from collections.abc import AsyncGenerator

# Set up environment before any imports
os.environ.setdefault('OPENAI_API_KEY', 'test-api-key')

# Add the server directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "server"))


class TestOpenAILLM:
    """Test the OpenAILLM adapter class."""

    def setup_method(self):
        """Set up test fixtures."""
        os.environ['OPENAI_API_KEY'] = 'test-api-key'

    @patch('openai.api_key', 'test-api-key')
    @patch('openai.AsyncOpenAI')
    @patch('openai.OpenAI')
    def test_import_insurance_agent_server(self, mock_openai, mock_async_openai, mock_api_key):
        """Test that insurance_agent_server can be imported without errors."""
        with patch('crewai_tools.RagTool') as mock_rag_tool, \
             patch('crewai.Agent') as mock_agent, \
             patch('crewai.Crew') as mock_crew, \
             patch('crewai.Task') as mock_task, \
             patch('acp_sdk.server.Server') as mock_server:
            
            # Mock the RagTool and other dependencies
            mock_rag_instance = Mock()
            mock_rag_tool.return_value = mock_rag_instance
            
            try:
                import insurance_agent_server
                assert hasattr(insurance_agent_server, 'OpenAILLM')
                assert hasattr(insurance_agent_server, 'policy_agent')
                assert hasattr(insurance_agent_server, 'llm_adapter')
                assert hasattr(insurance_agent_server, 'insurance_agent')
            except Exception as e:
                pytest.fail(f"Failed to import insurance_agent_server: {e}")

    @patch('openai.api_key', 'test-api-key')
    @patch('crewai_tools.RagTool')
    @patch('crewai.Agent')
    @patch('acp_sdk.server.Server')
    def test_openai_llm_init(self, mock_server, mock_agent, mock_rag_tool, mock_api_key):
        """Test OpenAILLM initialization."""
        mock_rag_tool.return_value = Mock()
        mock_agent.return_value = Mock()
        mock_server.return_value = Mock()
        
        with patch('pathlib.Path') as mock_path:
            mock_path.return_value.exists.return_value = False
            
            # Import after mocking
            import insurance_agent_server
            
            llm = insurance_agent_server.OpenAILLM(model="gpt-4o-mini", max_tokens=1024, temperature=0.0)
            
            assert llm.model == "gpt-4o-mini"
            assert llm.max_tokens == 1024
            assert llm.temperature == 0.0

    @patch('openai.AsyncOpenAI')
    @patch('openai.api_key', 'test-api-key')
    @patch('crewai_tools.RagTool')
    @patch('crewai.Agent')
    @patch('acp_sdk.server.Server')
    async def test_acompletion(self, mock_server, mock_agent, mock_rag_tool, mock_api_key, mock_async_openai):
        """Test async completion method."""
        # Setup mocks
        mock_rag_tool.return_value = Mock()
        mock_agent.return_value = Mock()
        mock_server.return_value = Mock()
        
        # Mock response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"
        
        mock_client = Mock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_async_openai.return_value = mock_client
        
        with patch('pathlib.Path') as mock_path:
            mock_path.return_value.exists.return_value = False
            
            import insurance_agent_server
            
            llm = insurance_agent_server.OpenAILLM()
            
            messages = [{"role": "user", "content": "Test message"}]
            result = await llm.acompletion(messages)
            
            assert result == "Test response"
            mock_client.chat.completions.create.assert_called_once()

    @patch('openai.OpenAI')
    @patch('openai.api_key', 'test-api-key')
    @patch('crewai_tools.RagTool')
    @patch('crewai.Agent')
    @patch('acp_sdk.server.Server')
    def test_completion(self, mock_server, mock_agent, mock_rag_tool, mock_api_key, mock_openai_class):
        """Test sync completion method."""
        # Setup mocks
        mock_rag_tool.return_value = Mock()
        mock_agent.return_value = Mock()
        mock_server.return_value = Mock()
        
        # Mock response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        with patch('pathlib.Path') as mock_path:
            mock_path.return_value.exists.return_value = False
            
            import insurance_agent_server
            
            llm = insurance_agent_server.OpenAILLM()
            
            messages = [{"role": "user", "content": "Test message"}]
            result = llm.completion(messages)
            
            assert result == "Test response"
            mock_client.chat.completions.create.assert_called_once()


class TestInsuranceAgentServer:
    """Test the insurance agent server functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        os.environ['OPENAI_API_KEY'] = 'test-api-key'
        
        # Create temporary data directory
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir) / "data"
        self.data_dir.mkdir(exist_ok=True)
        
        # Create mock PDF file
        self.mock_pdf = self.data_dir / "test_policy.pdf"
        self.mock_pdf.write_text("Mock PDF content")

    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch('openai.api_key', 'test-api-key')
    @patch('crewai_tools.RagTool')
    @patch('pathlib.Path')
    @patch('crewai.Agent')
    @patch('acp_sdk.server.Server')
    def test_rag_tool_initialization_with_pdfs(self, mock_server, mock_agent, mock_path_class, mock_rag_tool, mock_api_key):
        """Test RAG tool initialization when PDFs exist."""
        # Mock Path behavior for /app/data
        mock_data_dir = Mock()
        mock_data_dir.exists.return_value = True
        mock_data_dir.glob.return_value = [Path("test1.pdf"), Path("test2.pdf")]
        
        # Mock Path constructor to return our mock for /app/data
        def path_constructor(path_str):
            if str(path_str) == "/app/data":
                return mock_data_dir
            return Mock()
        
        mock_path_class.side_effect = path_constructor
        
        # Mock other dependencies
        mock_rag_instance = Mock()
        mock_rag_tool.return_value = mock_rag_instance
        mock_agent.return_value = Mock()
        mock_server.return_value = Mock()
        
        # Import with mocked dependencies
        with patch('logging.getLogger') as mock_logger:
            # Force reimport to trigger initialization
            if 'insurance_agent_server' in sys.modules:
                del sys.modules['insurance_agent_server']
            import insurance_agent_server
            
            # Verify RagTool was created
            mock_rag_tool.assert_called_once()

    @patch('openai.api_key', 'test-api-key')
    @patch('crewai.Agent')
    @patch('crewai_tools.RagTool')
    @patch('acp_sdk.server.Server')
    @patch('pathlib.Path')
    def test_insurance_agent_creation(self, mock_path, mock_server, mock_rag_tool, mock_agent, mock_api_key):
        """Test insurance agent creation with correct parameters."""
        mock_rag_instance = Mock()
        mock_rag_tool.return_value = mock_rag_instance
        mock_server.return_value = Mock()
        mock_path.return_value.exists.return_value = False
        
        # Force reimport to trigger agent creation
        if 'insurance_agent_server' in sys.modules:
            del sys.modules['insurance_agent_server']
        import insurance_agent_server
        
        # Verify Agent was called
        mock_agent.assert_called_once()
        call_args = mock_agent.call_args
        
        assert call_args.kwargs['role'] == "Senior Insurance Coverage Assistant"
        assert call_args.kwargs['goal'] == "Determine whether something is covered or not"
        assert call_args.kwargs['verbose'] is True
        assert call_args.kwargs['allow_delegation'] is False
        assert call_args.kwargs['max_retry_limit'] == 5


class TestPolicyAgent:
    """Test the policy agent function."""

    def setup_method(self):
        """Set up test fixtures."""
        os.environ['OPENAI_API_KEY'] = 'test-api-key'

    @pytest.mark.asyncio
    @patch('openai.api_key', 'test-api-key')
    @patch('crewai.Crew')
    @patch('crewai.Task')
    @patch('crewai_tools.RagTool')
    @patch('crewai.Agent')
    @patch('acp_sdk.server.Server')
    @patch('pathlib.Path')
    async def test_policy_agent_success(self, mock_path, mock_server, mock_agent, mock_rag_tool, mock_task, mock_crew, mock_api_key):
        """Test successful policy agent execution."""
        # Setup all mocks
        mock_path.return_value.exists.return_value = False
        mock_server.return_value = Mock()
        mock_agent.return_value = Mock()
        mock_rag_tool.return_value = Mock()
        
        # Import after mocking
        from acp_sdk.models import Message, MessagePart
        from acp_sdk.server import Context
        
        # Force import
        if 'insurance_agent_server' in sys.modules:
            del sys.modules['insurance_agent_server']
        import insurance_agent_server
        
        # Create mock input
        mock_message = Message(parts=[MessagePart(content="Is dental cleaning covered?")])
        mock_context = Mock(spec=Context)
        
        # Mock task output
        mock_task_output = "Yes, dental cleaning is covered under your basic plan."
        mock_crew_instance = Mock()
        mock_crew_instance.kickoff_async = AsyncMock(return_value=mock_task_output)
        mock_crew.return_value = mock_crew_instance
        
        # Execute the agent
        result_generator = insurance_agent_server.policy_agent([mock_message], mock_context)
        
        # Get the result
        result = None
        async for message in result_generator:
            result = message
            break
        
        # Verify result
        assert isinstance(result, Message)
        assert len(result.parts) == 1
        assert result.parts[0].content == mock_task_output
        
        # Verify Task was created correctly
        mock_task.assert_called_once()
        task_call_args = mock_task.call_args
        assert task_call_args.kwargs['description'] == "Is dental cleaning covered?"

    @pytest.mark.asyncio
    @patch('openai.api_key', 'test-api-key')
    @patch('crewai.Crew')
    @patch('crewai.Task')
    @patch('logging.getLogger')
    @patch('crewai_tools.RagTool')
    @patch('crewai.Agent')
    @patch('acp_sdk.server.Server')
    @patch('pathlib.Path')
    async def test_policy_agent_error_handling(self, mock_path, mock_server, mock_agent, mock_rag_tool, mock_logger_class, mock_task, mock_crew, mock_api_key):
        """Test policy agent error handling."""
        # Setup all mocks
        mock_path.return_value.exists.return_value = False
        mock_server.return_value = Mock()
        mock_agent.return_value = Mock()
        mock_rag_tool.return_value = Mock()
        
        mock_logger = Mock()
        mock_logger_class.return_value = mock_logger
        
        # Import after mocking
        from acp_sdk.models import Message, MessagePart
        from acp_sdk.server import Context
        
        # Force import
        if 'insurance_agent_server' in sys.modules:
            del sys.modules['insurance_agent_server']
        import insurance_agent_server
        
        # Create mock input
        mock_message = Message(parts=[MessagePart(content="Test query")])
        mock_context = Mock(spec=Context)
        
        # Make crew.kickoff_async raise an exception
        mock_crew_instance = Mock()
        mock_crew_instance.kickoff_async = AsyncMock(side_effect=Exception("Test error"))
        mock_crew.return_value = mock_crew_instance
        
        # Execute the agent
        result_generator = insurance_agent_server.policy_agent([mock_message], mock_context)
        
        # Get the result
        result = None
        async for message in result_generator:
            result = message
            break
        
        # Verify error handling
        assert isinstance(result, Message)
        assert len(result.parts) == 1
        assert "Error processing your query: Test error" in result.parts[0].content


class TestServerIntegration:
    """Test server integration and startup."""

    def setup_method(self):
        """Set up test fixtures."""
        os.environ['OPENAI_API_KEY'] = 'test-api-key'

    @patch('openai.api_key', 'test-api-key')
    @patch('acp_sdk.server.Server')
    @patch('crewai_tools.RagTool')
    @patch('crewai.Agent')
    @patch('pathlib.Path')
    def test_server_creation(self, mock_path, mock_agent, mock_rag_tool, mock_server_class, mock_api_key):
        """Test server creation and agent registration."""
        mock_path.return_value.exists.return_value = False
        mock_agent.return_value = Mock()
        mock_rag_tool.return_value = Mock()
        
        mock_server_instance = Mock()
        mock_server_class.return_value = mock_server_instance
        
        # Force reimport to trigger server creation
        if 'insurance_agent_server' in sys.modules:
            del sys.modules['insurance_agent_server']
        import insurance_agent_server
        
        # Verify server was created
        mock_server_class.assert_called_once()


class TestEnvironmentAndConfiguration:
    """Test environment variables and configuration."""

    @patch('openai.api_key', 'test-api-key')
    @patch('crewai_tools.RagTool')
    @patch('crewai.Agent')
    @patch('acp_sdk.server.Server')
    @patch('pathlib.Path')
    def test_llm_adapter_configuration(self, mock_path, mock_server, mock_agent, mock_rag_tool, mock_api_key):
        """Test LLM adapter configuration."""
        mock_path.return_value.exists.return_value = False
        mock_server.return_value = Mock()
        mock_agent.return_value = Mock()
        mock_rag_tool.return_value = Mock()
        
        # Force reimport
        if 'insurance_agent_server' in sys.modules:
            del sys.modules['insurance_agent_server']
        import insurance_agent_server
        
        assert insurance_agent_server.llm_adapter.model == "gpt-4o-mini"
        assert insurance_agent_server.llm_adapter.max_tokens == 4096
        assert insurance_agent_server.llm_adapter.temperature == 0.0

    @patch('openai.api_key', 'test-api-key')
    @patch('crewai_tools.RagTool')
    @patch('crewai.Agent')
    @patch('acp_sdk.server.Server')
    @patch('pathlib.Path')
    def test_rag_tool_configuration(self, mock_path, mock_server, mock_agent, mock_rag_tool, mock_api_key):
        """Test RAG tool configuration."""
        mock_path.return_value.exists.return_value = False
        mock_server.return_value = Mock()
        mock_agent.return_value = Mock()
        
        # Force reimport
        if 'insurance_agent_server' in sys.modules:
            del sys.modules['insurance_agent_server']
        import insurance_agent_server
        
        # Verify RagTool was initialized with correct config
        mock_rag_tool.assert_called_once()
        call_args = mock_rag_tool.call_args
        config = call_args.kwargs['config']
        
        assert config['llm']['provider'] == 'openai'
        assert config['embedding_model']['provider'] == 'openai'
        assert config['embedding_model']['config']['model'] == 'text-embedding-3-small'


# Integration test
class TestFullWorkflow:
    """Test full workflow integration."""

    @pytest.mark.asyncio
    @patch('openai.api_key', 'test-api-key')
    @patch('crewai.Crew')
    @patch('crewai.Task')
    @patch('crewai_tools.RagTool')
    @patch('pathlib.Path')
    @patch('crewai.Agent')
    @patch('acp_sdk.server.Server')
    async def test_end_to_end_workflow(self, mock_server, mock_agent, mock_path_class, mock_rag_tool, mock_task, mock_crew, mock_api_key):
        """Test complete workflow from message to response."""
        # Setup mocks
        mock_data_dir = Mock()
        mock_data_dir.exists.return_value = True
        mock_data_dir.glob.return_value = [Path("policy.pdf")]
        
        def path_constructor(path_str):
            if str(path_str) == "/app/data":
                return mock_data_dir
            return Mock()
        
        mock_path_class.side_effect = path_constructor
        
        mock_server.return_value = Mock()
        mock_agent.return_value = Mock()
        mock_rag_instance = Mock()
        mock_rag_tool.return_value = mock_rag_instance
        
        mock_task_output = "Your prescription is covered with a $10 copay."
        mock_crew_instance = Mock()
        mock_crew_instance.kickoff_async = AsyncMock(return_value=mock_task_output)
        mock_crew.return_value = mock_crew_instance
        
        # Import and test
        from acp_sdk.models import Message, MessagePart
        from acp_sdk.server import Context
        
        if 'insurance_agent_server' in sys.modules:
            del sys.modules['insurance_agent_server']
        import insurance_agent_server
        
        # Create test input
        test_message = Message(parts=[MessagePart(content="Is my prescription covered?")])
        test_context = Mock(spec=Context)
        
        # Execute workflow
        result_generator = insurance_agent_server.policy_agent([test_message], test_context)
        
        result = None
        async for message in result_generator:
            result = message
            break
        
        # Verify end-to-end result
        assert isinstance(result, Message)
        assert result.parts[0].content == mock_task_output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])