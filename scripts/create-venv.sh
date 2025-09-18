cd /home/danny/code/multi-agent-ai

# Remove the problematic .venv directory
sudo rm -rf .venv 2>/dev/null || rm -rf .venv

# Create a new virtual environment with python3
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Upgrade pip to latest version
pip install --upgrade pip

# Install all required dependencies
pip install pytest pytest-asyncio pytest-cov pytest-mock
pip install fastapi uvicorn python-dotenv httpx pydantic websockets
pip install pyautogen  # for agent orchestrator

# Verify installations
python --version
pip list

# Set environment variables for testing
export PYTHONPATH="/home/danny/code/multi-agent-ai:/home/danny/code/multi-agent-ai/server"
export OPENAI_API_KEY="test-api-key"

# Now run tests
python -m pytest tests/ -v --tb=short