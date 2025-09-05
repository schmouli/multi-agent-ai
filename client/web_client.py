from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os
import httpx

app = FastAPI(
    title="Hospital Agent Client", description="Web client for hospital agent queries"
)

# Server URL configuration - use environment variable or default to Docker service name
SERVER_URL = os.getenv("SERVER_URL", "http://server:7000")


class QueryRequest(BaseModel):
    location: str
    query: str


class QueryResponse(BaseModel):
    success: bool
    result: str = None
    error: str = None


async def query_hospital_agent(location: str, query: str) -> str:
    """Query the hospital agent asynchronously using direct HTTP"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{SERVER_URL}/run_sync",
                json={
                    "agent": "health_agent",
                    "input": f"I'm based in {location}. {query}"
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success") and result.get("output"):
                    return result["output"][0]["parts"][0]["content"]
                else:
                    raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
            else:
                raise HTTPException(status_code=response.status_code, detail=f"Server error: {response.text}")
                
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Connection error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/", response_class=HTMLResponse)
async def get_index():
    with open("client/templates/index.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Query the hospital agent with location and health question"""
    try:
        result = await query_hospital_agent(request.location, request.query)
        return QueryResponse(success=True, result=result)
    except HTTPException:
        raise
    except Exception as e:
        return QueryResponse(success=False, error=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7080)
