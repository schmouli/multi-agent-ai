import os
import logging
import time
from typing import Dict, Any

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from mcp.server.fastmcp import FastMCP

# Load environment variables
load_dotenv()

# Configure logging with detailed format
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)

# Log startup information
logger.info("=== Healthcare MCP Server Starting ===")
logger.info(f"Python version: {os.sys.version}")
logger.info(f"Working directory: {os.getcwd()}")

# Debug: Print API key info with enhanced logging
api_key = os.getenv("OPENAI_API_KEY", "")
if api_key:
    masked_key = f"{api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else 'SHORT'}"
    logger.info(f"OpenAI API key configured: {masked_key}")
    logger.debug(f"API key length: {len(api_key)} characters")
    print(f"API Key loaded: {api_key[:20]}...{api_key[-4:] if len(api_key) > 24 else 'SHORT_KEY'}")
else:
    logger.warning("OPENAI_API_KEY not found in environment variables")
    print("No API Key found in environment")

# Initialize FastMCP with logging
logger.info("Initializing FastMCP server...")
try:
    mcp = FastMCP("doctor-search-server")
    logger.info("FastMCP server initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize FastMCP server: {str(e)}")
    logger.exception("Full traceback:")
    raise

# Doctor database initialization with logging
logger.info("Loading doctor database...")
doctors = {
    "DOC001": {
        "name": "Dr. Sarah Mitchell",
        "specialty": "Cardiology",
        "address": {
            "street": "1247 Medical Center Drive",
            "city": "Atlanta",
            "state": "GA",
            "zip_code": "30309",
        },
        "phone": "(404) 555-2847",
        "email": "s.mitchell@atlantaheart.com",
        "years_experience": 15,
        "board_certified": True,
        "hospital_affiliations": [
            "Emory University Hospital",
            "Piedmont Atlanta Hospital",
        ],
        "education": {
            "medical_school": "Duke University School of Medicine",
            "residency": "Johns Hopkins Hospital",
            "fellowship": "Cleveland Clinic",
        },
        "languages": ["English", "Spanish"],
        "accepts_new_patients": True,
        "insurance_accepted": [
            "Blue Cross Blue Shield",
            "Aetna",
            "Cigna",
            "UnitedHealth",
        ],
    },
    "DOC002": {
        "name": "Dr. James Rodriguez",
        "specialty": "Pediatrics",
        "address": {
            "street": "892 Children's Way, Suite 205",
            "city": "Phoenix",
            "state": "AZ",
            "zip_code": "85016",
        },
        "phone": "(602) 555-9134",
        "email": "j.rodriguez@phoenixpeds.com",
        "years_experience": 8,
        "board_certified": True,
        "hospital_affiliations": [
            "Phoenix Children's Hospital",
            "Banner Desert Medical Center",
        ],
        "education": {
            "medical_school": "University of Arizona College of Medicine",
            "residency": "Seattle Children's Hospital",
            "fellowship": None,
        },
        "languages": ["English", "Spanish"],
        "accepts_new_patients": True,
        "insurance_accepted": ["Medicaid", "CHIP", "Blue Cross Blue Shield", "Aetna"],
    },
    "DOC003": {
        "name": "Dr. Emily Chen",
        "specialty": "Dermatology",
        "address": {
            "street": "3401 Pacific Coast Highway",
            "city": "Los Angeles",
            "state": "CA",
            "zip_code": "90405",
        },
        "phone": "(310) 555-7623",
        "email": "e.chen@laskincare.com",
        "years_experience": 12,
        "board_certified": True,
        "hospital_affiliations": ["UCLA Medical Center", "Cedars-Sinai Medical Center"],
        "education": {
            "medical_school": "Stanford University School of Medicine",
            "residency": "UCSF Medical Center",
            "fellowship": "Memorial Sloan Kettering Cancer Center",
        },
        "languages": ["English", "Mandarin", "Cantonese"],
        "accepts_new_patients": False,
        "insurance_accepted": ["Blue Cross Blue Shield", "Cigna", "UnitedHealth"],
    },
    "DOC004": {
        "name": "Dr. Michael Thompson",
        "specialty": "Orthopedic Surgery",
        "address": {
            "street": "1156 Sports Medicine Plaza",
            "city": "Denver",
            "state": "CO",
            "zip_code": "80206",
        },
        "phone": "(303) 555-4892",
        "email": "m.thompson@denverortho.com",
        "years_experience": 22,
        "board_certified": True,
        "hospital_affiliations": [
            "National Jewish Health",
            "Presbyterian/Saint Joseph Hospital",
        ],
        "education": {
            "medical_school": "University of Colorado School of Medicine",
            "residency": "Mayo Clinic",
            "fellowship": "Hospital for Special Surgery",
        },
        "languages": ["English"],
        "accepts_new_patients": True,
        "insurance_accepted": [
            "Blue Cross Blue Shield",
            "Aetna",
            "Cigna",
            "Workers' Compensation",
        ],
    },
    "DOC005": {
        "name": "Dr. Priya Patel",
        "specialty": "Internal Medicine",
        "address": {
            "street": "2847 Medical Arts Building",
            "city": "Houston",
            "state": "TX",
            "zip_code": "77030",
        },
        "phone": "(713) 555-3651",
        "email": "p.patel@houstoninternal.com",
        "years_experience": 6,
        "board_certified": True,
        "hospital_affiliations": [
            "Houston Methodist Hospital",
            "MD Anderson Cancer Center",
        ],
        "education": {
            "medical_school": "Baylor College of Medicine",
            "residency": "Massachusetts General Hospital",
            "fellowship": None,
        },
        "languages": ["English", "Hindi", "Gujarati"],
        "accepts_new_patients": True,
        "insurance_accepted": [
            "Medicare",
            "Medicaid",
            "Blue Cross Blue Shield",
            "Humana",
        ],
    },
    "DOC006": {
        "name": "Dr. Robert Kim",
        "specialty": "Neurology",
        "address": {
            "street": "567 Brain & Spine Center",
            "city": "Seattle",
            "state": "WA",
            "zip_code": "98104",
        },
        "phone": "(206) 555-8274",
        "email": "r.kim@seattleneuro.com",
        "years_experience": 18,
        "board_certified": True,
        "hospital_affiliations": [
            "University of Washington Medical Center",
            "Swedish Medical Center",
        ],
        "education": {
            "medical_school": "University of Washington School of Medicine",
            "residency": "UCSF Medical Center",
            "fellowship": "Mayo Clinic",
        },
        "languages": ["English", "Korean"],
        "accepts_new_patients": False,
        "insurance_accepted": ["Blue Cross Blue Shield", "Aetna", "UnitedHealth"],
    },
    "DOC007": {
        "name": "Dr. Lisa Johnson",
        "specialty": "Obstetrics & Gynecology",
        "address": {
            "street": "4392 Women's Health Plaza, Floor 3",
            "city": "Miami",
            "state": "FL",
            "zip_code": "33156",
        },
        "phone": "(305) 555-1847",
        "email": "l.johnson@miamiwomenshealth.com",
        "years_experience": 14,
        "board_certified": True,
        "hospital_affiliations": [
            "Jackson Memorial Hospital",
            "Baptist Hospital of Miami",
        ],
        "education": {
            "medical_school": "University of Miami Miller School of Medicine",
            "residency": "New York-Presbyterian Hospital",
            "fellowship": "Brigham and Women's Hospital",
        },
        "languages": ["English", "Spanish", "French"],
        "accepts_new_patients": True,
        "insurance_accepted": ["Blue Cross Blue Shield", "Aetna", "Cigna", "Medicaid"],
    },
    "DOC008": {
        "name": "Dr. David Wilson",
        "specialty": "Emergency Medicine",
        "address": {
            "street": "789 Emergency Services Drive",
            "city": "Chicago",
            "state": "IL",
            "zip_code": "60611",
        },
        "phone": "(312) 555-9567",
        "email": "d.wilson@chicagoemergency.com",
        "years_experience": 11,
        "board_certified": True,
        "hospital_affiliations": [
            "Northwestern Memorial Hospital",
            "Rush University Medical Center",
        ],
        "education": {
            "medical_school": "Northwestern University Feinberg School of Medicine",
            "residency": "Cook County Hospital",
            "fellowship": None,
        },
        "languages": ["English"],
        "accepts_new_patients": True,
        "insurance_accepted": ["All major insurances accepted", "Self-pay"],
    },
    "DOC009": {
        "name": "Dr. Amanda Foster",
        "specialty": "Psychiatry",
        "address": {
            "street": "1523 Mental Health Boulevard, Suite 401",
            "city": "Boston",
            "state": "MA",
            "zip_code": "02115",
        },
        "phone": "(617) 555-7412",
        "email": "a.foster@bostonpsych.com",
        "years_experience": 9,
        "board_certified": True,
        "hospital_affiliations": ["Massachusetts General Hospital", "McLean Hospital"],
        "education": {
            "medical_school": "Harvard Medical School",
            "residency": "Massachusetts General Hospital",
            "fellowship": "McLean Hospital",
        },
        "languages": ["English", "Portuguese"],
        "accepts_new_patients": True,
        "insurance_accepted": [
            "Blue Cross Blue Shield",
            "Harvard Pilgrim",
            "Tufts Health Plan",
        ],
    },
    "DOC010": {
        "name": "Dr. Christopher Lee",
        "specialty": "Oncology",
        "address": {
            "street": "2156 Cancer Treatment Center",
            "city": "Nashville",
            "state": "TN",
            "zip_code": "37232",
        },
        "phone": "(615) 555-6284",
        "email": "c.lee@nashvillecancer.com",
        "years_experience": 16,
        "board_certified": True,
        "hospital_affiliations": [
            "Vanderbilt University Medical Center",
            "Sarah Cannon Cancer Institute",
        ],
        "education": {
            "medical_school": "Vanderbilt University School of Medicine",
            "residency": "Memorial Sloan Kettering Cancer Center",
            "fellowship": "MD Anderson Cancer Center",
        },
        "languages": ["English"],
        "accepts_new_patients": False,
        "insurance_accepted": [
            "Blue Cross Blue Shield",
            "Cigna",
            "UnitedHealth",
            "Medicare",
        ],
    },
}

# Log database statistics
total_doctors = len(doctors)
states_covered = set(doc["address"]["state"] for doc in doctors.values())
specialties = set(doc["specialty"] for doc in doctors.values())

logger.info(f"Doctor database loaded successfully:")
logger.info(f"  Total doctors: {total_doctors}")
logger.info(f"  States covered: {len(states_covered)} ({', '.join(sorted(states_covered))})")
logger.info(f"  Specialties available: {len(specialties)}")
logger.debug(f"  Specialties: {', '.join(sorted(specialties))}")

# Log doctors per state
state_counts = {}
for doc in doctors.values():
    state = doc["address"]["state"]
    state_counts[state] = state_counts.get(state, 0) + 1

logger.debug("Doctors per state:")
for state, count in sorted(state_counts.items()):
    logger.debug(f"  {state}: {count} doctors")


# Build server function with enhanced logging
@mcp.tool()
def doctor_search(state: str) -> str:
    """This tool returns doctors that may be near you.
    Args:
        state: the two letter state code that you live in.
        Example payload: "CA"

    Returns:
        str: a list of doctors that may be near you
        Example Response "{"DOC001":{"name":"Dr John James",
        "specialty":"Cardiology"...}...}"
    """
    logger.info(f"Doctor search initiated for state: '{state}'")
    start_time = time.time()
    
    # Input validation and logging
    if not state:
        logger.warning("Empty state parameter provided")
        return "No doctors found: state parameter is required"
    
    # Normalize state input
    state_upper = state.upper().strip()
    logger.debug(f"Normalized state code: '{state_upper}'")
    
    if len(state_upper) != 2:
        logger.warning(f"Invalid state code length: '{state_upper}' (expected 2 characters)")
        return f"Invalid state code: {state}. Please provide a 2-letter state code."
    
    # Search for doctors
    logger.debug(f"Searching doctors in database for state: {state_upper}")
    filtered_doctors = {}
    
    for doc_id, doc_info in doctors.items():
        doc_state = doc_info["address"]["state"]
        if doc_state == state_upper:
            filtered_doctors[doc_id] = doc_info
            logger.debug(f"Found doctor: {doc_id} - {doc_info['name']} ({doc_info['specialty']})")
    
    # Log search results
    search_time = time.time() - start_time
    result_count = len(filtered_doctors)
    
    logger.info(f"Doctor search completed in {search_time:.3f}s")
    logger.info(f"Found {result_count} doctors in state '{state_upper}'")
    
    if filtered_doctors:
        # Log summary of found doctors
        specialties_found = set(doc["specialty"] for doc in filtered_doctors.values())
        logger.debug(f"Specialties found: {', '.join(sorted(specialties_found))}")
        
        # Log accepting new patients count
        accepting_new = sum(1 for doc in filtered_doctors.values() if doc.get("accepts_new_patients", False))
        logger.debug(f"Doctors accepting new patients: {accepting_new}/{result_count}")
        
        result = str(filtered_doctors)
        logger.debug(f"Result string length: {len(result)} characters")
        return result
    else:
        logger.info(f"No doctors found in state: {state_upper}")
        # Suggest nearby states if available
        available_states = sorted(set(doc["address"]["state"] for doc in doctors.values()))
        logger.debug(f"Available states: {', '.join(available_states)}")
        return f"No doctors found in state: {state}. Available states: {', '.join(available_states)}"


# Create FastAPI app for HTTP transport with enhanced logging
logger.info("Initializing FastAPI application...")
app = FastAPI(
    title="Healthcare MCP Server",
    version="1.0.0",
    description="MCP server providing healthcare tools",
)
logger.info("FastAPI application initialized successfully")


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


@app.get("/")
async def get_server_info():
    """Return MCP server information."""
    logger.debug("Server info requested")
    server_info = {
        "name": "doctor-search-server",
        "version": "1.0.0",
        "description": "Healthcare MCP Server",
        "total_doctors": len(doctors),
        "states_covered": sorted(set(doc["address"]["state"] for doc in doctors.values())),
        "specialties": sorted(set(doc["specialty"] for doc in doctors.values())),
    }
    logger.debug(f"Returning server info: {server_info}")
    return server_info


@app.post("/")
async def handle_jsonrpc(request: Request):
    """Handle MCP JSON-RPC calls."""
    request_id = id(request)
    logger.info(f"[JSONRPC {request_id}] Received JSON-RPC request")
    start_time = time.time()
    
    try:
        body = await request.json()
        logger.debug(f"[JSONRPC {request_id}] Request body: {body}")
    except Exception as e:
        logger.error(f"[JSONRPC {request_id}] Failed to parse JSON: {str(e)}")
        return JSONResponse(
            status_code=200,
            content={
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32600,
                    "message": "Invalid Request",
                },
            },
        )

    # Check if request has required JSON-RPC fields
    if "method" not in body:
        logger.warning(f"[JSONRPC {request_id}] Missing 'method' field in request")
        return {
            "jsonrpc": "2.0",
            "id": body.get("id"),
            "error": {
                "code": -32600,
                "message": "Invalid Request - missing method field",
            },
        }

    method = body.get("method")
    params = body.get("params", {})
    json_request_id = body.get("id")
    
    logger.info(f"[JSONRPC {request_id}] Method: {method}")
    logger.debug(f"[JSONRPC {request_id}] Params: {params}")
    logger.debug(f"[JSONRPC {request_id}] Request ID: {json_request_id}")

    if method == "tools/list":
        logger.debug(f"[JSONRPC {request_id}] Handling tools/list request")
        tools_response = {
            "jsonrpc": "2.0",
            "id": json_request_id,
            "result": {
                "tools": [
                    {
                        "name": "doctor_search",
                        "description": "Search for doctors by state",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "state": {
                                    "type": "string",
                                    "description": "Two letter state code",
                                }
                            },
                            "required": ["state"],
                        },
                    }
                ]
            },
        }
        process_time = time.time() - start_time
        logger.info(f"[JSONRPC {request_id}] tools/list completed in {process_time:.3f}s")
        return tools_response
        
    elif method == "tools/call":
        logger.debug(f"[JSONRPC {request_id}] Handling tools/call request")
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        logger.info(f"[JSONRPC {request_id}] Tool call: {tool_name}")
        logger.debug(f"[JSONRPC {request_id}] Tool arguments: {arguments}")

        if tool_name == "doctor_search":
            state = arguments.get("state", "")
            logger.info(f"[JSONRPC {request_id}] Calling doctor_search with state: '{state}'")
            
            try:
                result = doctor_search(state)
                logger.debug(f"[JSONRPC {request_id}] doctor_search result length: {len(result)} chars")
                
                response = {
                    "jsonrpc": "2.0",
                    "id": json_request_id,
                    "result": {"content": [{"type": "text", "text": result}]},
                }
                
                process_time = time.time() - start_time
                logger.info(f"[JSONRPC {request_id}] doctor_search completed successfully in {process_time:.3f}s")
                return response
                
            except Exception as e:
                logger.error(f"[JSONRPC {request_id}] Error in doctor_search: {str(e)}")
                logger.exception(f"[JSONRPC {request_id}] doctor_search exception:")
                return {
                    "jsonrpc": "2.0",
                    "id": json_request_id,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error in doctor_search: {str(e)}",
                    },
                }
        else:
            logger.warning(f"[JSONRPC {request_id}] Unknown tool requested: {tool_name}")
            return {
                "jsonrpc": "2.0",
                "id": json_request_id,
                "error": {
                    "code": -32601,
                    "message": f"Tool not found: {tool_name}",
                },
            }
    else:
        logger.warning(f"[JSONRPC {request_id}] Unknown method requested: {method}")
        return {
            "jsonrpc": "2.0",
            "id": json_request_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }


@app.post("/doctor_search")
async def api_doctor_search(request: dict):
    """Direct API endpoint for doctor search."""
    request_id = id(request)
    logger.info(f"[API {request_id}] Direct doctor_search API call")
    logger.debug(f"[API {request_id}] Request: {request}")
    
    start_time = time.time()
    
    try:
        state = request.get("state", "")
        logger.info(f"[API {request_id}] Searching for doctors in state: '{state}'")
        
        result = doctor_search(state)
        
        response = {"result": result}
        process_time = time.time() - start_time
        
        logger.info(f"[API {request_id}] Direct API call completed in {process_time:.3f}s")
        logger.debug(f"[API {request_id}] Response: {response}")
        
        return JSONResponse(response)
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"[API {request_id}] Error in direct API call after {process_time:.3f}s: {str(e)}")
        logger.exception(f"[API {request_id}] Exception details:")
        return JSONResponse(
            status_code=500,
            content={"error": f"Internal server error: {str(e)}"}
        )


@app.get("/health")
async def health_check():
    """Enhanced health check endpoint."""
    logger.debug("Health check requested")
    
    health_info = {
        "status": "healthy", 
        "service": "MCP Doctor Server",
        "version": "1.0.0",
        "database": {
            "total_doctors": len(doctors),
            "states_covered": len(set(doc["address"]["state"] for doc in doctors.values())),
            "specialties": len(set(doc["specialty"] for doc in doctors.values())),
        },
        "timestamp": time.time()
    }
    
    logger.debug(f"Health check response: {health_info}")
    return health_info


@app.on_event("startup")
async def startup_event():
    """Log startup completion."""
    logger.info("=== Healthcare MCP Server Ready ===")
    logger.info("Available endpoints:")
    logger.info("  GET  /           - Server information")
    logger.info("  POST /           - JSON-RPC endpoint")
    logger.info("  POST /doctor_search - Direct API endpoint")
    logger.info("  GET  /health     - Health check")
    logger.info("Server is ready to accept requests")


@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown."""
    logger.info("=== Healthcare MCP Server Shutting Down ===")


# Kick off server if file is run
if __name__ == "__main__":
    logger.info("Starting MCP server with uvicorn...")
    logger.info("Server configuration:")
    logger.info("  Host: 0.0.0.0")
    logger.info("  Port: 8333")
    logger.info("  Log level: info")
    
    try:
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8333,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
    except Exception as e:
        logger.error(f"Server failed to start: {str(e)}")
        logger.exception("Full traceback:")
        raise
    finally:
        logger.info("=== Healthcare MCP Server Stopped ===")
