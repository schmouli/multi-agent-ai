from acp_sdk.client import Client
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(
    title="Hospital Agent Client", description="Web client for hospital agent queries"
)


class QueryRequest(BaseModel):
    location: str
    query: str


class QueryResponse(BaseModel):
    success: bool
    result: str = None
    error: str = None


async def query_hospital_agent(location: str, query: str) -> str:
    """Query the hospital agent asynchronously"""
    try:
        async with Client(base_url="http://localhost:8000") as hospital:
            run1 = await hospital.run_sync(
                agent="health_agent", input=f"I'm based in {location}. {query}"
            )
            content = run1.output[0].parts[0].content
            return content
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

    uvicorn.run(app, host="0.0.0.0", port=8080)
