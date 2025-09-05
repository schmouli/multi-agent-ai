from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import httpx
import os
from smolagents import LiteLLMModel, ToolCallingAgent
import asyncio
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title="Hospital Agent Server",
    description="FastAPI-based agent server for hospital health queries",
    version="1.0.0"
)

# Initialize model
try:
    model = LiteLLMModel(
        model_id="gpt-4o-mini", 
        api_key=os.getenv("OPENAI_API_KEY")
    )
    print("✅ LiteLLM model initialized successfully")
except Exception as e:
    print(f"⚠️ Warning: Could not initialize LiteLLM model: {e}")
    model = None

# MCP server configuration
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://mcpserver:8333")

# Request/Response models
class MessagePart(BaseModel):
    content: str

class Message(BaseModel):
    parts: List[MessagePart]

class AgentRequest(BaseModel):
    agent: str
    input: str

class AgentResponse(BaseModel):
    success: bool
    output: List[Message]
    error: Optional[str] = None

async def extract_state_from_prompt(prompt: str) -> str:
    """Extract state from user prompt"""
    import re
    
    # Look for state abbreviations
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
                return abbr
        return "GA"  # Default to Georgia
    else:
        return state_match.group(0)

async def get_doctor_data(state: str) -> Optional[str]:
    """Get doctor data from MCP server"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{MCP_SERVER_URL}/doctor_search",
                json={"state": state},
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()["result"]
            else:
                print(f"MCP server error: {response.status_code}")
                return None
                
    except Exception as e:
        print(f"Error connecting to MCP server: {e}")
        return None

async def health_agent_logic(prompt: str) -> str:
    """Core health agent logic"""
    try:
        # Extract state from prompt
        state = await extract_state_from_prompt(prompt)
        print(f"Extracted state: {state} from prompt: {prompt[:50]}...")
        
        # Get doctor data
        doctor_data = await get_doctor_data(state)
        
        if doctor_data:
            # Create enhanced prompt with doctor data
            enhanced_prompt = f"""
User query: {prompt}

Available doctors in {state}: {doctor_data}

Please provide a helpful response about healthcare options based on the user's query and the available doctor information.
"""
            if model:
                agent = ToolCallingAgent(tools=[], model=model)
                response = agent.run(enhanced_prompt)
                return str(response)
            else:
                return f"Found doctors in {state}: {doctor_data[:200]}... (AI assistant temporarily unavailable)"
        else:
            # MCP server error, provide general response
            if model:
                agent = ToolCallingAgent(tools=[], model=model)
                response = agent.run(f"Healthcare query: {prompt}. Please provide general healthcare guidance.")
                return str(response)
            else:
                return "Healthcare query received. Our doctor database is temporarily unavailable."
                
    except Exception as e:
        return f"I received your healthcare question: '{prompt}'. I'm currently experiencing technical difficulties. Please try again later. (Error: {str(e)})"

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Hospital Agent Server",
        "status": "running",
        "mcp_server": MCP_SERVER_URL,
        "model_available": model is not None
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    mcp_status = "unknown"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MCP_SERVER_URL}/health", timeout=5.0)
            mcp_status = "healthy" if response.status_code == 200 else "unhealthy"
    except:
        mcp_status = "unreachable"
    
    return {
        "status": "healthy",
        "service": "Hospital Agent Server",
        "mcp_server": mcp_status,
        "model_available": model is not None
    }

@app.post("/run_sync", response_model=AgentResponse)
async def run_agent_sync(request: AgentRequest):
    """Run agent synchronously - compatible with ACP SDK client interface"""
    try:
        if request.agent != "health_agent":
            raise HTTPException(status_code=400, detail=f"Unknown agent: {request.agent}")
        
        # Process the request
        result = await health_agent_logic(request.input)
        
        # Return in ACP-compatible format
        return AgentResponse(
            success=True,
            output=[Message(parts=[MessagePart(content=result)])]
        )
        
    except Exception as e:
        return AgentResponse(
            success=False,
            output=[],
            error=str(e)
        )

@app.post("/query")
async def direct_query(request: dict):
    """Direct query endpoint for simple testing"""
    try:
        prompt = request.get("query", "")
        if not prompt:
            raise HTTPException(status_code=400, detail="Missing 'query' field")
        
        result = await health_agent_logic(prompt)
        return {"success": True, "result": result}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    print("🚀 Starting FastAPI Hospital Agent Server...")
    print(f"📍 MCP Server: {MCP_SERVER_URL}")
    print(f"🤖 Model Available: {model is not None}")
    
    # Run server
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=7000,
        log_level="info"
    )
