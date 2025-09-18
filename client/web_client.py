import os
import logging
import time

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("=== Web Client Starting ===")

app = FastAPI(
    title="Healthcare & Insurance AI Client", 
    description="Web client for healthcare and insurance AI agents"
)

# Server URL configuration - use orchestrator
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://orchestrator:7500")
logger.info(f"Orchestrator URL: {ORCHESTRATOR_URL}")

class QueryRequest(BaseModel):
    location: str = Field(..., min_length=1, description="Location cannot be empty")
    query: str = Field(..., min_length=1, description="Query cannot be empty")
    agent: str = Field(default="auto", description="Agent type: auto, doctor, insurance")

class QueryResponse(BaseModel):
    success: bool
    result: str = None
    error: str = None
    agent_used: str = ""
    confidence: float = 0.0
    reasoning: str = ""

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log requests"""
    start_time = time.time()
    request_id = id(request)
    
    logger.info(f"[WebClient {request_id}] {request.method} {request.url}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"[WebClient {request_id}] Response: {response.status_code} in {process_time:.3f}s")
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"[WebClient {request_id}] Error after {process_time:.3f}s: {str(e)}")
        raise

@app.get("/", response_class=HTMLResponse)
async def get_index():
    """Serve the main web interface"""
    logger.debug("Serving main web interface")
    try:
        with open("client/templates/index.html", "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        logger.error("index.html not found")
        raise HTTPException(status_code=404, detail="Web interface not found")

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Query the orchestrator to route to appropriate agent"""
    request_id = id(request)
    logger.info(f"[Query {request_id}] Received query request")
    logger.info(f"[Query {request_id}] Location: {request.location}")
    logger.info(f"[Query {request_id}] Query: {request.query[:100]}{'...' if len(request.query) > 100 else ''}")
    logger.info(f"[Query {request_id}] Agent preference: {request.agent}")
    
    start_time = time.time()
    
    try:
        # Forward the request to the orchestrator
        async with httpx.AsyncClient(timeout=45.0) as client:
            payload = {
                "location": request.location,
                "query": request.query,
                "agent": request.agent
            }
            
            logger.debug(f"[Query {request_id}] Sending to orchestrator: {payload}")
            response = await client.post(f"{ORCHESTRATOR_URL}/query", json=payload)
            
            if response.status_code == 200:
                result = response.json()
                process_time = time.time() - start_time
                
                logger.info(f"[Query {request_id}] Orchestrator response received in {process_time:.3f}s")
                logger.info(f"[Query {request_id}] Agent used: {result.get('agent_used', 'unknown')}")
                logger.info(f"[Query {request_id}] Success: {result.get('success', False)}")
                
                return QueryResponse(
                    success=result.get("success", True),
                    result=result.get("result", "No response received"),
                    agent_used=result.get("agent_used", "unknown"),
                    confidence=result.get("confidence", 0.0),
                    reasoning=result.get("reasoning", "")
                )
            else:
                process_time = time.time() - start_time
                logger.error(f"[Query {request_id}] Orchestrator error after {process_time:.3f}s: {response.status_code}")
                logger.error(f"[Query {request_id}] Error response: {response.text}")
                
                error_detail = response.text if response.text else f"HTTP {response.status_code}"
                return QueryResponse(
                    success=False, 
                    error=f"Orchestrator error: {error_detail}",
                    agent_used="error"
                )

    except httpx.RequestError as e:
        process_time = time.time() - start_time
        logger.error(f"[Query {request_id}] Connection error after {process_time:.3f}s: {str(e)}")
        return QueryResponse(
            success=False, 
            error=f"Connection error: {str(e)}",
            agent_used="error"
        )
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"[Query {request_id}] Unexpected error after {process_time:.3f}s: {str(e)}")
        logger.exception(f"[Query {request_id}] Exception details:")
        return QueryResponse(
            success=False, 
            error=f"Unexpected error: {str(e)}",
            agent_used="error"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.debug("Health check requested")
    
    health_info = {
        "status": "healthy",
        "service": "web-client",
        "version": "1.0.0",
        "orchestrator_url": ORCHESTRATOR_URL
    }
    
    # Test orchestrator connectivity
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{ORCHESTRATOR_URL}/health")
            health_info["orchestrator_status"] = "reachable" if response.status_code == 200 else "unreachable"
    except Exception as e:
        health_info["orchestrator_status"] = f"unreachable: {str(e)}"
    
    return health_info

@app.get("/agents/status")
async def get_agents_status():
    """Get status of all agents through orchestrator"""
    logger.debug("Getting agent status")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{ORCHESTRATOR_URL}/agents/status")
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Failed to get agent status: {response.status_code}"}
    except Exception as e:
        logger.error(f"Error getting agent status: {str(e)}")
        return {"error": f"Connection error: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Web Client with uvicorn...")
    logger.info("Server configuration:")
    logger.info("  Host: 0.0.0.0")
    logger.info("  Port: 7080")
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=7080)
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
    except Exception as e:
        logger.error(f"Server failed to start: {str(e)}")
        raise
    finally:
        logger.info("=== Web Client Stopped ===")
