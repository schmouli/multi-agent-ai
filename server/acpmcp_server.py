from collections.abc import AsyncGenerator
import os
import httpx

from acp_sdk.models import Message, MessagePart
from acp_sdk.server import Context, RunYield, RunYieldResume, Server
from smolagents import LiteLLMModel, ToolCallingAgent

# Create server but delay startup to handle ACP SDK issues
server = Server()

# Initialize model
try:
    model = LiteLLMModel(
        model_id="gpt-4o-mini", 
        api_key=os.getenv("OPENAI_API_KEY")
    )
except Exception as e:
    print(f"Warning: Could not initialize LiteLLM model: {e}")
    model = None

# MCP server HTTP configuration
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://mcpserver:8333")


@server.agent()
async def health_agent(
    input: list[Message], context: Context
) -> AsyncGenerator[RunYield, RunYieldResume]:
    """Health agent that supports hospital health-based questions.

    Current or prospective patients can use it to find answers about
    their health and hospital treatments.
    """
    # Connect to MCP server via HTTP
    try:
        prompt = input[0].parts[0].content
        
        # Extract state from prompt
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
                    state = abbr
                    break
            else:
                state = "GA"  # Default to Georgia
        else:
            state = state_match.group(0)
        
        # Call MCP server via HTTP
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{MCP_SERVER_URL}/doctor_search",
                json={"state": state},
                timeout=10.0
            )
            
            if response.status_code == 200:
                doctor_data = response.json()["result"]
                
                # Create enhanced prompt with doctor data
                enhanced_prompt = f"""
User query: {prompt}

Available doctors in {state}: {doctor_data}

Please provide a helpful response about healthcare options based on the user's query and the available doctor information.
"""
                if model:
                    agent = ToolCallingAgent(tools=[], model=model)
                    llm_response = agent.run(enhanced_prompt)
                else:
                    llm_response = f"Found doctors in {state}: {doctor_data[:200]}... (AI assistant temporarily unavailable)"
            else:
                # MCP server error, provide general response
                if model:
                    agent = ToolCallingAgent(tools=[], model=model)
                    llm_response = agent.run(f"Healthcare query: {prompt}. Please provide general healthcare guidance.")
                else:
                    llm_response = "Healthcare query received. Our doctor database is temporarily unavailable."
                
    except Exception as e:
        # Fallback response if HTTP connection fails
        prompt = input[0].parts[0].content
        llm_response = f"I received your healthcare question: '{prompt}'. I'm currently experiencing technical difficulties connecting to our doctor database. Please try again later or contact our support team. (Error: {str(e)})"

    yield Message(parts=[MessagePart(content=str(llm_response))])


if __name__ == "__main__":
    print("ACP Server starting on port 7000...")
    print(f"MCP server configured at: {MCP_SERVER_URL}")
    
    # Start a simple HTTP server on 8333 to satisfy ACP SDK health checks
    import asyncio
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import threading
    import json
    
    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.startswith('/health') or self.path == '/':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok", "service": "ACP Health Check"}).encode())
            else:
                self.send_response(404)
                self.end_headers()
        
        def do_POST(self):
            self.do_GET()
        
        def log_message(self, format, *args):
            pass  # Suppress logs
    
    def start_health_server():
        try:
            health_server = HTTPServer(('127.0.0.1', 8333), HealthHandler)
            print("Started health check server on 127.0.0.1:8333")
            health_server.serve_forever()
        except Exception as e:
            print(f"Health server error: {e}")
    
    # Start health server in background thread
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    
    # Small delay to let health server start
    import time
    time.sleep(1)
    
    # Run server with port 7000
    server.run(port=7000)
