import os

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

app = FastAPI(
    title="Hospital Agent Client", description="Web client for hospital agent queries"
)

# Server URL configuration - use environment variable or default to Docker service name
SERVER_URL = os.getenv("SERVER_URL", "http://server:7000")


class QueryRequest(BaseModel):
    location: str = Field(..., min_length=1, description="Location cannot be empty")
    query: str = Field(..., min_length=1, description="Query cannot be empty")


class QueryResponse(BaseModel):
    success: bool
    result: str = None
    error: str = None


@app.get("/", response_class=HTMLResponse)
async def get_index():
    with open("client/templates/index.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Query the hospital agent with location and health question"""
    try:
        # Forward the request to the FastAPI agent server
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{SERVER_URL}/query",  # Call /query endpoint, not /run_sync
                json={
                    "location": request.location,
                    "query": request.query,
                    "agent": "hospital"  # Use valid agent
                },
                timeout=30.0,
            )

            if response.status_code == 200:
                result = response.json()
                return QueryResponse(
                    success=result.get("success", True),
                    result=result.get("result", "No response received")
                )
            else:
                error_detail = response.text if response.text else f"HTTP {response.status_code}"
                return QueryResponse(
                    success=False, 
                    error=f"Server error: {error_detail}"
                )

    except httpx.RequestError as e:
        return QueryResponse(success=False, error=f"Connection error: {str(e)}")
    except Exception as e:
        return QueryResponse(success=False, error=f"Unexpected error: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7080)
