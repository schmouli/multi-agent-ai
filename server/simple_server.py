from collections.abc import AsyncGenerator
import os

from acp_sdk.models import Message, MessagePart
from acp_sdk.server import Context, RunYield, RunYieldResume, Server

server = Server()

@server.agent()
async def simple_agent(
    input: list[Message], context: Context
) -> AsyncGenerator[RunYield, RunYieldResume]:
    """Simple agent for testing."""
    prompt = input[0].parts[0].content
    response = f"Echo: {prompt}"
    yield Message(parts=[MessagePart(content=response)])

if __name__ == "__main__":
    print("Simple ACP Server starting on port 7000...")
    server.run(port=7000)
