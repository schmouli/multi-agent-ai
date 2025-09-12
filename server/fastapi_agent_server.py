import re
from typing import Any, Dict, Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Load environment variables
load_dotenv()

app = FastAPI(title="Healthcare Agent Server", version="1.0.0")


class QueryRequest(BaseModel):
    query: str
    agent: str = "hospital"


class QueryResponse(BaseModel):
    response: str
    success: bool = True


def extract_state_from_prompt(prompt: str) -> Optional[str]:
    """Extract US state code from user prompt.

    Args:
        prompt: User input text

    Returns:
        Two-letter state code if found, None otherwise
    """
    # State name to code mapping (complete list)
    state_names = {
        "california": "CA",
        "texas": "TX",
        "florida": "FL",
        "new york": "NY",
        "pennsylvania": "PA",
        "illinois": "IL",
        "ohio": "OH",
        "georgia": "GA",
        "north carolina": "NC",
        "michigan": "MI",
        "new jersey": "NJ",
        "virginia": "VA",
        "washington": "WA",
        "arizona": "AZ",
        "massachusetts": "MA",
        "tennessee": "TN",
        "indiana": "IN",
        "missouri": "MO",
        "maryland": "MD",
        "wisconsin": "WI",
        "colorado": "CO",
        "minnesota": "MN",
        "south carolina": "SC",
        "alabama": "AL",
        "louisiana": "LA",
        "kentucky": "KY",
        "oregon": "OR",
        "oklahoma": "OK",
        "connecticut": "CT",
        "utah": "UT",
        "iowa": "IA",
        "nevada": "NV",
        "arkansas": "AR",
        "mississippi": "MS",
        "kansas": "KS",
        "new mexico": "NM",
        "nebraska": "NE",
        "west virginia": "WV",
        "idaho": "ID",
        "hawaii": "HI",
        "new hampshire": "NH",
        "maine": "ME",
        "montana": "MT",
        "rhode island": "RI",
        "delaware": "DE",
        "south dakota": "SD",
        "north dakota": "ND",
        "alaska": "AK",
        "vermont": "VT",
        "wyoming": "WY",
    }

    # Valid state codes for validation
    valid_state_codes = set(state_names.values())

    # Words that should not be considered state codes even if they match
    excluded_words = {
        "me",
        "us",
        "am",
        "is",
        "it",
        "to",
        "in",
        "or",
        "at",
        "an",
        "as",
        "be",
        "by",
        "do",
        "go",
        "he",
        "if",
        "my",
        "no",
        "of",
        "on",
        "so",
        "up",
        "we",
    }

    if not prompt:
        return None

    prompt_lower = prompt.lower()

    # Check for full state names first (longer matches first)
    # Sort by length descending to match longer names first
    sorted_states = sorted(state_names.items(), key=lambda x: len(x[0]), reverse=True)
    for state_name, state_code in sorted_states:
        if state_name in prompt_lower:
            return state_code

    # Check for state code patterns - look for 2-letter codes
    # More specific patterns to avoid false matches
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

    prompt_upper = prompt.upper()

    for pattern in state_code_patterns:
        matches = re.findall(pattern, prompt_upper)
        for match in matches:
            if match in valid_state_codes and match.lower() not in excluded_words:
                return match

    # Last resort: standalone state codes at word boundaries
    # But only if they're not common English words
    standalone_pattern = r"\b([A-Z]{2})\b"
    matches = re.findall(standalone_pattern, prompt_upper)
    for match in matches:
        if (
            match in valid_state_codes
            and match.lower() not in excluded_words
            and len(prompt.split()) <= 5
        ):  # Only for short prompts to avoid false positives
            return match

    return None


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "healthcare-agent-server"}


@app.post("/query", response_model=QueryResponse)
async def query_agent(request: QueryRequest) -> QueryResponse:
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    if request.agent not in ["hospital", "doctor"]:
        raise HTTPException(
            status_code=400, detail="Agent must be 'hospital' or 'doctor'"
        )

    try:
        # Extract state from query for better search
        state = extract_state_from_prompt(request.query)

        # Forward to MCP server
        async with httpx.AsyncClient() as client:
            mcp_url = "http://localhost:8333/"

            # Use extracted state or default query
            search_args = {"state": state} if state else {"query": request.query}

            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "doctor_search",
                    "arguments": search_args,
                },
            }
            mcp_response = await client.post(mcp_url, json=payload)

            if mcp_response.status_code == 200:
                result = mcp_response.json()
                if "result" in result:
                    content = result["result"]["content"][0]["text"]
                    return QueryResponse(response=content, success=True)
                else:
                    return QueryResponse(response="No results found", success=False)
            else:
                raise HTTPException(status_code=500, detail="MCP server error")

    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503, detail=f"Cannot connect to MCP server: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/run_sync")
async def run_sync(request: Dict[str, Any]):
    valid_agents = ["hospital", "doctor"]
    if "agent" not in request or request["agent"] not in valid_agents:
        raise HTTPException(status_code=400, detail="Invalid agent specified")

    return {"status": "completed", "agent": request["agent"]}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7000)
