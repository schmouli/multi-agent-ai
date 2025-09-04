from collections.abc import AsyncGenerator
import os

from acp_sdk.models import Message, MessagePart
from acp_sdk.server import Context, RunYield, RunYieldResume, Server
from mcp import StdioServerParameters
from smolagents import LiteLLMModel, ToolCallingAgent, ToolCollection

server = Server()

model = LiteLLMModel(
    model_id="gpt-4o-mini",
    api_key=os.getenv("OPENAI_API_KEY"),  # Get from environment variable
)

# Configure MCP server parameters for stdio transport
server_parameters = StdioServerParameters(
    command="uv",
    args=["run", "/app/server/mcpserver.py"],
    env=None,
)


@server.agent()
async def health_agent(
    input: list[Message], context: Context
) -> AsyncGenerator[RunYield, RunYieldResume]:
    """Health agent that supports hospital health-based questions.

    Current or prospective patients can use it to find answers about
    their health and hospital treatments.
    """
    # Use proper stdio MCP server connection
    try:
        with ToolCollection.from_mcp(
            server_parameters, trust_remote_code=True
        ) as tool_collection:
            agent = ToolCallingAgent(tools=[*tool_collection.tools], model=model)
            prompt = input[0].parts[0].content
            response = agent.run(prompt)
    except Exception as e:
        # Enhanced fallback with direct doctor search
        try:
            # Import the doctor search function directly as fallback
            import sys
            sys.path.append('/app')
            from server.mcpserver import doctor_search
            
            prompt = input[0].parts[0].content
            
            # Extract state from prompt (basic implementation)
            import re
            state_match = re.search(r'\b([A-Z]{2})\b', prompt)
            if not state_match:
                # Try common state names to abbreviations
                state_names = {
                    'georgia': 'GA', 'california': 'CA', 'texas': 'TX', 
                    'florida': 'FL', 'new york': 'NY', 'atlanta': 'GA',
                    'los angeles': 'CA', 'houston': 'TX', 'miami': 'FL'
                }
                for name, abbr in state_names.items():
                    if name.lower() in prompt.lower():
                        state_match = type('Match', (), {'group': lambda x, n: abbr})()
                        break
            
            if state_match:
                state = state_match.group(1) if hasattr(state_match, 'group') else state_match.group(0)
                doctor_data = doctor_search(state)
                
                # Create enhanced prompt with doctor data
                enhanced_prompt = f"""
User query: {prompt}

Available doctors in {state}: {doctor_data}

Please provide a helpful response about healthcare options based on the user's query and the available doctor information.
"""
                agent = ToolCallingAgent(tools=[], model=model)
                response = agent.run(enhanced_prompt)
            else:
                # No state detected, provide general response
                agent = ToolCallingAgent(tools=[], model=model)
                response = agent.run(f"Healthcare query: {prompt}. Please provide general healthcare guidance.")
                
        except Exception as fallback_error:
            # Final fallback
            prompt = input[0].parts[0].content
            response = f"I received your healthcare question: '{prompt}'. I'm currently experiencing technical difficulties. Please try again later or contact our support team."

    yield Message(parts=[MessagePart(content=str(response))])


if __name__ == "__main__":
    print("ACP Server starting on port 7000...")
    print("Using stdio MCP server transport")
    # Run server with port 7000
    server.run(port=7000)
