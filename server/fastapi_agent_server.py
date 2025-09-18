import os
import sys
import re
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional
from contextlib import asynccontextmanager

# Load environment variables first, before other imports
from dotenv import load_dotenv

# Load environment variables from .env file
# Try different possible locations for .env file
env_paths = [
    Path.cwd() / ".env",                    # Current working directory
    Path(__file__).parent / ".env",         # Server directory
    Path(__file__).parent.parent / ".env",  # Project root
]

env_loaded = False
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path)
        env_loaded = True
        print(f"Loaded environment variables from: {env_path}")
        break

if not env_loaded:
    print("Warning: No .env file found. Using system environment variables only.")

# Now check for required environment variables
required_env_vars = ["OPENAI_API_KEY"]
missing_vars = []

for var in required_env_vars:
    if not os.getenv(var):
        missing_vars.append(var)

if missing_vars:
    print(f"Warning: Missing required environment variables: {missing_vars}")
    print("Make sure your .env file contains these variables or set them in your environment.")

# Import external dependencies after environment setup
try:
    import httpx
except ImportError as e:
    print(f"Error importing httpx: {e}")
    print("Please install httpx: pip install httpx")
    sys.exit(1)

try:
    from fastapi import FastAPI, HTTPException, Request
    from pydantic import BaseModel
except ImportError as e:
    print(f"Error importing FastAPI dependencies: {e}")
    print("Please install FastAPI: pip install fastapi uvicorn")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)

# Log startup information
logger.info("=== FastAPI Healthcare Agent Server Starting ===")
logger.info(f"Python version: {sys.version}")  # Fixed: use sys.version instead of os.sys.version
logger.info(f"Working directory: {os.getcwd()}")

# Environment variable configuration with defaults
mcp_server_url = os.getenv("MCP_SERVER_URL", "http://mcpserver:8333")
server_url = os.getenv("SERVER_URL", "http://server:7000")

logger.info(f"MCP Server URL: {mcp_server_url}")
logger.info(f"Server URL: {server_url}")

# Environment variable logging with better security
if os.getenv("OPENAI_API_KEY"):
    api_key = os.getenv("OPENAI_API_KEY")
    if len(api_key) > 8:
        masked_key = api_key[:8] + "*" * (len(api_key) - 8)
    else:
        masked_key = "***"
    logger.info(f"OpenAI API key configured: {masked_key}")
    
    # Validate API key format
    if not api_key.startswith("sk-"):
        logger.warning("OpenAI API key doesn't start with 'sk-' - this may be invalid")
else:
    logger.error("OPENAI_API_KEY not found in environment variables!")
    logger.error("Please check your .env file or environment configuration")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("=== FastAPI Healthcare Agent Server Ready ===")
    logger.info("Available endpoints:")
    logger.info("  GET  /health     - Health check")
    logger.info("  POST /query      - Main query endpoint")
    logger.info("  POST /run_sync   - Legacy sync endpoint")
    logger.info("Server is ready to accept requests")
    
    yield
    
    # Shutdown
    logger.info("=== FastAPI Healthcare Agent Server Shutting Down ===")

# Create FastAPI app
try:
    app = FastAPI(
        title="Healthcare Agent Server", 
        version="1.0.0",
        description="Healthcare agent server with state extraction and MCP integration",
        lifespan=lifespan
    )
    logger.info("FastAPI application initialized")
except Exception as e:
    logger.error(f"Failed to initialize FastAPI app: {e}")
    sys.exit(1)

class QueryRequest(BaseModel):
    location: str
    query: str
    agent: str = "hospital"

class QueryResponse(BaseModel):
    result: str
    success: bool = True

def extract_state_from_prompt(prompt: str) -> Optional[str]:
    """Extract US state code from user prompt.

    Args:
        prompt: User input text

    Returns:
        Two-letter state code if found, None otherwise
    """
    if not prompt:
        logger.debug("Empty prompt provided, returning None")
        return None
        
    logger.debug(f"Starting state extraction from prompt: '{prompt[:100]}{'...' if len(prompt) > 100 else ''}'")
    start_time = time.time()
    
    # State name to code mapping (complete list)
    state_names = {
        "california": "CA", "texas": "TX", "florida": "FL", "new york": "NY",
        "pennsylvania": "PA", "illinois": "IL", "ohio": "OH", "georgia": "GA",
        "north carolina": "NC", "michigan": "MI", "new jersey": "NJ", "virginia": "VA",
        "washington": "WA", "arizona": "AZ", "massachusetts": "MA", "tennessee": "TN",
        "indiana": "IN", "missouri": "MO", "maryland": "MD", "wisconsin": "WI",
        "colorado": "CO", "minnesota": "MN", "south carolina": "SC", "alabama": "AL",
        "louisiana": "LA", "kentucky": "KY", "oregon": "OR", "oklahoma": "OK",
        "connecticut": "CT", "utah": "UT", "iowa": "IA", "nevada": "NV",
        "arkansas": "AR", "mississippi": "MS", "kansas": "KS", "new mexico": "NM",
        "nebraska": "NE", "west virginia": "WV", "idaho": "ID", "hawaii": "HI",
        "new hampshire": "NH", "maine": "ME", "montana": "MT", "rhode island": "RI",
        "delaware": "DE", "south dakota": "SD", "north dakota": "ND", "alaska": "AK",
        "vermont": "VT", "wyoming": "WY",
    }

    # Valid state codes for validation
    valid_state_codes = set(state_names.values())
    logger.debug(f"Loaded {len(state_names)} state names and {len(valid_state_codes)} state codes")

    # Words that should not be considered state codes even if they match
    excluded_words = {
        "me", "us", "am", "is", "it", "to", "in", "or", "at", "an", "as", "be", "by",
        "do", "go", "he", "if", "my", "no", "of", "on", "so", "up", "we",
    }

    prompt_lower = prompt.lower()
    logger.debug(f"Searching in lowercase prompt: '{prompt_lower}'")

    # Check for full state names first (longer matches first)
    logger.debug("Checking for full state names...")
    sorted_states = sorted(state_names.items(), key=lambda x: len(x[0]), reverse=True)
    
    for state_name, state_code in sorted_states:
        if state_name in prompt_lower:
            execution_time = time.time() - start_time
            logger.info(f"Found state name '{state_name}' -> '{state_code}' in {execution_time:.3f}s")
            logger.debug(f"State found using full name matching")
            return state_code

    logger.debug("No full state names found, checking state code patterns...")

    # Check for state code patterns - look for 2-letter codes
    state_code_patterns = [
        r"\bin\s+([A-Z]{2})\b",  # "in CA", "in NY"
        r"\bfrom\s+([A-Z]{2})\b",  # "from CA", "from NY"
        r"\bstate\s+([A-Z]{2})\b",  # "state CA", "state NY"
        r"\bof\s+([A-Z]{2})\b",  # "state of CA"
        r"\blive\s+in\s+([A-Z]{2})\b",  # "live in CA"
        r"\bdoctors?\s+in\s+([A-Z]{2})\b",  # "doctors in CA"
        r"\b([A-Z]{2})\s+doctors?\b",  # "CA doctors"
        r"\b([A-Z]{2})\s+area\b",  # "CA area"
        r"\b([A-Z]{2})\s+state\b",  # "CA state"
    ]

    try:
        prompt_upper = prompt.upper()
        logger.debug(f"Checking {len(state_code_patterns)} regex patterns against uppercase prompt")

        for i, pattern in enumerate(state_code_patterns, 1):
            logger.debug(f"Testing pattern {i}: {pattern}")
            matches = re.findall(pattern, prompt_upper)
            logger.debug(f"Pattern {i} matches: {matches}")
            
            for match in matches:
                if match in valid_state_codes and match.lower() not in excluded_words:
                    execution_time = time.time() - start_time
                    logger.info(f"Found state code '{match}' using pattern {i} in {execution_time:.3f}s")
                    logger.debug(f"Pattern used: {pattern}")
                    return match

        logger.debug("No pattern matches found, trying standalone state codes...")

        # Last resort: standalone state codes at word boundaries
        standalone_pattern = r"\b([A-Z]{2})\b"
        matches = re.findall(standalone_pattern, prompt_upper)
        logger.debug(f"Standalone pattern matches: {matches}")
        
        prompt_words = prompt.split()
        logger.debug(f"Prompt word count: {len(prompt_words)}")
        
        for match in matches:
            if (
                match in valid_state_codes
                and match.lower() not in excluded_words
                and len(prompt_words) <= 5
            ):
                execution_time = time.time() - start_time
                logger.info(f"Found standalone state code '{match}' in {execution_time:.3f}s")
                logger.debug(f"Match found in short prompt ({len(prompt_words)} words)")
                return match

    except re.error as e:
        logger.error(f"Regex error in state extraction: {e}")
    except Exception as e:
        logger.error(f"Error in state extraction: {e}")

    execution_time = time.time() - start_time
    logger.debug(f"No state found in prompt after {execution_time:.3f}s")
    return None


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log all HTTP requests and responses."""
    start_time = time.time()
    request_id = id(request)
    
    # Log incoming request
    logger.info(f"[Request {request_id}] {request.method} {request.url}")
    logger.debug(f"[Request {request_id}] Headers: {dict(request.headers)}")
    
    # Log client info
    client_host = request.client.host if request.client else "unknown"
    logger.debug(f"[Request {request_id}] Client: {client_host}")
    
    # Process request
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log response
        logger.info(f"[Request {request_id}] Response: {response.status_code} in {process_time:.3f}s")
        
        # Add timing header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"[Request {request_id}] Error after {process_time:.3f}s: {str(e)}")
        logger.exception(f"[Request {request_id}] Exception details:")
        raise


@app.get("/health")
async def health_check():
    """Health check endpoint with detailed system info."""
    logger.debug("Health check requested")
    
    health_info = {
        "status": "healthy", 
        "service": "healthcare-agent-server",
        "version": "1.0.0",
        "mcp_server_url": mcp_server_url,
        "timestamp": time.time()
    }
    
    # Test MCP server connectivity
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            test_response = await client.get(f"{mcp_server_url.rstrip('/')}/")
            health_info["mcp_server_status"] = "reachable"
            logger.debug(f"MCP server health check successful: {test_response.status_code}")
    except Exception as e:
        health_info["mcp_server_status"] = f"unreachable: {str(e)}"
        logger.warning(f"MCP server health check failed: {str(e)}")
    
    logger.debug(f"Health check response: {health_info}")
    return health_info


@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest) -> QueryResponse:
    """Main query endpoint that the frontend calls"""
    request_id = id(request)
    logger.info(f"[Query {request_id}] Received query request")
    logger.info(f"[Query {request_id}] Location: '{request.location}'")
    logger.info(f"[Query {request_id}] Query: '{request.query[:100]}{'...' if len(request.query) > 100 else ''}'")
    logger.info(f"[Query {request_id}] Agent: '{request.agent}'")
    logger.debug(f"[Query {request_id}] Full request: {request}")
    
    start_time = time.time()
    
    # Validate inputs
    if not request.query or not request.query.strip():
        logger.warning(f"[Query {request_id}] Empty query provided")
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    if request.agent not in ["hospital", "doctor"]:
        logger.warning(f"[Query {request_id}] Invalid agent: '{request.agent}'")
        raise HTTPException(
            status_code=400, detail="Agent must be 'hospital' or 'doctor'"
        )

    logger.debug(f"[Query {request_id}] Input validation passed")

    try:
        # Extract state from location or query
        logger.info(f"[Query {request_id}] Starting state extraction...")
        combined_text = f"{request.location} {request.query}"
        logger.debug(f"[Query {request_id}] Combined text for extraction: '{combined_text}'")
        
        state = extract_state_from_prompt(combined_text)
        
        if state:
            logger.info(f"[Query {request_id}] Extracted state: '{state}'")
        else:
            logger.info(f"[Query {request_id}] No state extracted from input")

        # Prepare MCP server request
        mcp_url = f"{mcp_server_url.rstrip('/')}/"
        logger.debug(f"[Query {request_id}] MCP server URL: {mcp_url}")
        
        # Use extracted state or default query
        search_args = {"state": state} if state else {"query": request.query}
        logger.debug(f"[Query {request_id}] Search arguments: {search_args}")

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "doctor_search",
                "arguments": search_args,
            },
        }
        
        logger.info(f"[Query {request_id}] Sending request to MCP server...")
        logger.debug(f"[Query {request_id}] MCP payload: {payload}")

        # Forward to MCP server
        async with httpx.AsyncClient(timeout=30.0) as client:
            mcp_start_time = time.time()
            
            try:
                mcp_response = await client.post(mcp_url, json=payload)
                mcp_time = time.time() - mcp_start_time
                
                logger.info(f"[Query {request_id}] MCP server responded in {mcp_time:.3f}s with status {mcp_response.status_code}")
                logger.debug(f"[Query {request_id}] MCP response headers: {dict(mcp_response.headers)}")
                
                if mcp_response.status_code == 200:
                    result = mcp_response.json()
                    logger.debug(f"[Query {request_id}] MCP response JSON: {result}")
                    
                    if "result" in result and result["result"] and "content" in result["result"]:
                        content_list = result["result"]["content"]
                        if content_list and len(content_list) > 0 and "text" in content_list[0]:
                            content = content_list[0]["text"]
                            logger.info(f"[Query {request_id}] Successfully extracted content, length: {len(content)} chars")
                            logger.debug(f"[Query {request_id}] Content preview: {content[:200]}...")
                            
                            total_time = time.time() - start_time
                            logger.info(f"[Query {request_id}] Query completed successfully in {total_time:.3f}s")
                            
                            return QueryResponse(result=content, success=True)
                        else:
                            logger.warning(f"[Query {request_id}] Invalid content structure in MCP response")
                            return QueryResponse(result="Invalid response format from MCP server", success=False)
                    else:
                        logger.warning(f"[Query {request_id}] No 'result' field in MCP response")
                        logger.debug(f"[Query {request_id}] Available fields: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
                        return QueryResponse(result="No results found", success=False)
                else:
                    logger.error(f"[Query {request_id}] MCP server error: {mcp_response.status_code}")
                    logger.error(f"[Query {request_id}] MCP error response: {mcp_response.text}")
                    raise HTTPException(status_code=500, detail="MCP server error")
                    
            except httpx.TimeoutException:
                mcp_time = time.time() - mcp_start_time
                logger.error(f"[Query {request_id}] MCP server timeout after {mcp_time:.3f}s")
                raise HTTPException(status_code=504, detail="MCP server timeout")
                
            except httpx.RequestError as e:
                mcp_time = time.time() - mcp_start_time
                logger.error(f"[Query {request_id}] MCP server connection error after {mcp_time:.3f}s: {str(e)}")
                raise HTTPException(
                    status_code=503, detail=f"Cannot connect to MCP server: {str(e)}"
                )

    except HTTPException:
        # Re-raise HTTP exceptions (already logged above)
        total_time = time.time() - start_time
        logger.error(f"[Query {request_id}] Query failed with HTTP exception after {total_time:.3f}s")
        raise
        
    except Exception as e:
        total_time = time.time() - start_time
        logger.error(f"[Query {request_id}] Unexpected error after {total_time:.3f}s: {str(e)}")
        logger.error(f"[Query {request_id}] Error type: {type(e).__name__}")
        logger.exception(f"[Query {request_id}] Full traceback:")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/run_sync")
async def run_sync(request: Dict[str, Any]):
    """Legacy endpoint for synchronous agent execution."""
    request_id = id(request)
    logger.info(f"[RunSync {request_id}] Received run_sync request")
    logger.debug(f"[RunSync {request_id}] Payload: {request}")
    
    start_time = time.time()
    
    # Validate agent
    valid_agents = ["hospital", "doctor"]
    
    if "agent" not in request:
        logger.warning(f"[RunSync {request_id}] Missing 'agent' field in request")
        raise HTTPException(
            status_code=400,
            detail="Missing 'agent' field in request"
        )
    
    if request["agent"] not in valid_agents:
        logger.warning(f"[RunSync {request_id}] Invalid agent: '{request['agent']}'")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid agent specified. Valid agents are: {', '.join(valid_agents)}",
        )
    
    agent = request["agent"]
    logger.info(f"[RunSync {request_id}] Agent validation passed: '{agent}'")
    
    # Log additional request fields
    if "input" in request:
        input_preview = str(request["input"])[:100] + "..." if len(str(request["input"])) > 100 else str(request["input"])
        logger.debug(f"[RunSync {request_id}] Input: {input_preview}")
    
    response = {"status": "completed", "agent": agent}
    
    execution_time = time.time() - start_time
    logger.info(f"[RunSync {request_id}] Request completed in {execution_time:.3f}s")
    logger.debug(f"[RunSync {request_id}] Response: {response}")
    
    return response


if __name__ == "__main__":
    try:
        import uvicorn
    except ImportError as e:
        logger.error(f"Error importing uvicorn: {e}")
        logger.error("Please install uvicorn: pip install uvicorn")
        sys.exit(1)
    
    port = int(os.getenv("PORT", "7000"))
    logger.info(f"Starting FastAPI Healthcare Agent Server on port {port}...")
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=port)
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
    except Exception as e:
        logger.error(f"Server failed to start: {str(e)}")
        raise
    finally:
        logger.info("=== FastAPI Healthcare Agent Server Stopped ===")
