import os
import re
import logging
import time
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum

import uvicorn
import httpx
import websockets
import json
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from autogen import AssistantAgent, UserProxyAgent, GroupChatManager, GroupChat

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("=== AI Agent Orchestrator Starting ===")

# Environment configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
FASTAPI_SERVER_URL = os.getenv("FASTAPI_SERVER_URL", "http://server:7000")
INSURANCE_SERVER_URL = os.getenv("INSURANCE_SERVER_URL", "ws://insurance-server:7001")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://mcpserver:8333")

if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY not found in environment variables")
    raise ValueError("OPENAI_API_KEY is required")

logger.info(f"FastAPI Server URL: {FASTAPI_SERVER_URL}")
logger.info(f"Insurance Server URL: {INSURANCE_SERVER_URL}")
logger.info(f"MCP Server URL: {MCP_SERVER_URL}")

class QueryType(Enum):
    HEALTH_DOCTOR = "health_doctor"
    INSURANCE = "insurance"
    UNKNOWN = "unknown"

class QueryRequest(BaseModel):
    location: str
    query: str
    agent: str = "auto"  # auto, doctor, insurance

class QueryResponse(BaseModel):
    result: str
    success: bool = True
    agent_used: str = ""
    confidence: float = 0.0
    reasoning: str = ""

class AgentOrchestrator:
    """Main orchestrator class using AutoGen for agent coordination"""
    
    def __init__(self):
        logger.info("Initializing Agent Orchestrator...")
        self.setup_autogen_agents()
        
    def setup_autogen_agents(self):
        """Setup AutoGen agents for orchestration"""
        logger.info("Setting up AutoGen agents...")
        
        # Configuration for all agents
        llm_config = {
            "config_list": [{
                "model": "gpt-4o-mini",
                "api_key": OPENAI_API_KEY,
                "temperature": 0.1,
            }],
            "timeout": 30,
        }
        
        # Router Agent - decides which agent to use
        self.router_agent = AssistantAgent(
            name="QueryRouter",
            system_message="""You are an intelligent query router. Your job is to analyze user queries and determine which specialized agent should handle them.

AGENT TYPES:
1. HEALTH_DOCTOR: For medical questions, finding doctors, healthcare providers, symptoms, treatments, medical conditions, hospitals, clinics
2. INSURANCE: For insurance coverage questions, policy details, claims, benefits, deductibles, copays, insurance plans

KEYWORDS FOR HEALTH_DOCTOR:
- doctor, physician, medical, healthcare, hospital, clinic, specialist
- symptoms, treatment, diagnosis, medication, prescription
- cardiology, pediatrics, dermatology, neurology, orthopedic, etc.
- "find doctor", "medical help", "health issue", "see a doctor"

KEYWORDS FOR INSURANCE:
- insurance, coverage, policy, claim, benefits, deductible, copay
- "is covered", "covered by", "insurance pays", "out of pocket"
- premium, network, provider, plan, benefit

Respond with ONLY the agent type: HEALTH_DOCTOR or INSURANCE
If unclear, default to HEALTH_DOCTOR for medical-related queries.""",
            llm_config=llm_config,
        )
        
        # Health/Doctor Agent Proxy
        self.health_agent = AssistantAgent(
            name="HealthAgent",
            system_message="""You are a healthcare assistant that helps users find doctors and medical information. 
            You work with a healthcare API that can search for doctors by location and specialty.
            Always be helpful and provide accurate medical referral information.""",
            llm_config=llm_config,
        )
        
        # Insurance Agent Proxy  
        self.insurance_agent = AssistantAgent(
            name="InsuranceAgent", 
            system_message="""You are an insurance coverage specialist that helps users understand their insurance benefits.
            You work with an insurance system that has access to policy documents and coverage information.
            Always provide accurate insurance coverage information.""",
            llm_config=llm_config,
        )
        
        # User proxy for orchestration
        self.user_proxy = UserProxyAgent(
            name="UserProxy",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=1,
            is_termination_msg=lambda msg: "TERMINATE" in msg.get("content", ""),
        )
        
        logger.info("AutoGen agents setup completed")

    async def classify_query(self, query: str, location: str = "") -> Tuple[QueryType, float, str]:
        """Classify the query using AutoGen router agent"""
        logger.info(f"Classifying query: '{query[:100]}{'...' if len(query) > 100 else ''}'")
        start_time = time.time()
        
        try:
            # Combine query and location for better classification
            full_query = f"Location: {location}\nQuery: {query}" if location else query
            
            # Use AutoGen to classify the query
            classification_prompt = f"""Classify this user query: "{full_query}"
            
            Respond with ONLY one of: HEALTH_DOCTOR or INSURANCE"""
            
            # Get classification from router agent
            chat_result = self.user_proxy.initiate_chat(
                self.router_agent,
                message=classification_prompt,
                max_turns=1,
                silent=True
            )
            
            # Extract the classification from the response
            response = chat_result.chat_history[-1]["content"].strip().upper()
            
            # Parse the response
            if "HEALTH_DOCTOR" in response:
                query_type = QueryType.HEALTH_DOCTOR
                confidence = 0.8
                reasoning = "Query contains health/medical keywords"
            elif "INSURANCE" in response:
                query_type = QueryType.INSURANCE
                confidence = 0.8
                reasoning = "Query contains insurance-related keywords"
            else:
                # Fallback classification using keywords
                query_type, confidence, reasoning = self._fallback_classify(query)
            
            classification_time = time.time() - start_time
            logger.info(f"Query classified as {query_type.value} with confidence {confidence:.2f} in {classification_time:.3f}s")
            logger.debug(f"Classification reasoning: {reasoning}")
            
            return query_type, confidence, reasoning
            
        except Exception as e:
            logger.error(f"Error in AutoGen classification: {str(e)}")
            # Fallback to rule-based classification
            return self._fallback_classify(query)
    
    def _fallback_classify(self, query: str) -> Tuple[QueryType, float, str]:
        """Fallback classification using keyword matching"""
        logger.debug("Using fallback classification method")
        
        query_lower = query.lower()
        
        # Health/Doctor keywords - ADD THIS MISSING DEFINITION
        health_keywords = [
            'doctor', 'physician', 'medical', 'healthcare', 'hospital', 'clinic',
            'specialist', 'symptoms', 'treatment', 'diagnosis', 'medication',
            'prescription', 'find doctor', 'medical help', 'health issue',
            'cardiology', 'pediatrics', 'dermatology', 'neurology', 'orthopedic',
            'cardiologist', 'pediatrician', 'dermatologist', 'neurologist'
        ]
        
        # Check for provider-seeking phrases FIRST
        provider_seeking_phrases = [
            'find me a doctor', 'looking for a doctor', 'need a doctor',
            'find me a specialist', 'looking for a specialist', 'need a specialist', 
            'find doctor', 'find specialist', 'doctor that accepts',
            'specialist in my network', 'doctor in my area', 'find a doctor'
        ]

        provider_seeking_count = sum(1 for phrase in provider_seeking_phrases if phrase in query_lower)
        if provider_seeking_count > 0:
            return QueryType.HEALTH_DOCTOR, 0.8, f"Provider seeking phrases found: {provider_seeking_count}"

        # Then check for strong insurance indicators
        strong_insurance_phrases = [
            'covered by', 'insurance cover', 'insurance pay',
            'insurance benefits', 'policy coverage',
            'does my plan cover', 'will insurance pay', 'insurance reimbursement',
            'my deductible', 'insurance details', 'my insurance coverage',
            'what are my insurance', 'check my policy'
        ]

        strong_insurance_count = sum(1 for phrase in strong_insurance_phrases if phrase in query_lower)
        if strong_insurance_count > 0:
            return QueryType.INSURANCE, 0.8, f"Strong insurance indicators found: {strong_insurance_count}"
        
        # Insurance keywords - focused on coverage/benefits questions
        insurance_keywords = [
            'insurance', 'coverage', 'covered', 'policy', 'claim', 'benefits', 
            'deductible', 'copay', 'premium', 'plan', 'benefit',
            'pays for', 'reimburse', 'out of pocket', 'reimbursement'
        ]
        
        # Count individual keyword matches
        insurance_score = sum(1 for keyword in insurance_keywords if keyword in query_lower)
        health_score = sum(1 for keyword in health_keywords if keyword in query_lower)
        
        logger.debug(f"Insurance score: {insurance_score}, Health score: {health_score}")
        
        # If we have both types of keywords, prioritize based on context
        if insurance_score > 0 and health_score > 0:
            # Look for context clues
            if any(word in query_lower for word in ['find', 'looking for', 'need a', 'search for']):
                # User is looking for something - likely a provider
                return QueryType.HEALTH_DOCTOR, 0.7, f"Mixed query - provider seeking context: health={health_score}, insurance={insurance_score}"
            elif any(word in query_lower for word in ['covered', 'cover', 'pay', 'benefits', 'reimburse']):
                # User is asking about coverage
                return QueryType.INSURANCE, 0.7, f"Mixed query - coverage context: insurance={insurance_score}, health={health_score}"
    
        # Standard classification - prioritize insurance when found
        if insurance_score > 0:
            return QueryType.INSURANCE, 0.7, f"Insurance keywords found: {insurance_score}"
        elif health_score > 0:
            return QueryType.HEALTH_DOCTOR, 0.7, f"Health keywords found: {health_score}"
        else:
            return QueryType.HEALTH_DOCTOR, 0.3, "Default to health agent"

    async def route_to_health_agent(self, location: str, query: str) -> Dict[str, Any]:
        """Route query to FastAPI health agent"""
        logger.info(f"Routing to health agent - Location: {location}")
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "location": location,
                    "query": query,
                    "agent": "hospital"
                }
                
                logger.debug(f"Sending request to FastAPI server: {payload}")
                response = await client.post(f"{FASTAPI_SERVER_URL}/query", json=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    processing_time = time.time() - start_time
                    logger.info(f"Health agent responded successfully in {processing_time:.3f}s")
                    
                    return {
                        "success": True,
                        "result": result.get("result", "No response received"),
                        "agent_used": "health_doctor",
                        "processing_time": processing_time
                    }
                else:
                    logger.error(f"Health agent error: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "result": f"Health agent error: {response.status_code}",
                        "agent_used": "health_doctor"
                    }
                    
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error calling health agent after {processing_time:.3f}s: {str(e)}")
            return {
                "success": False,
                "result": f"Error contacting health agent: {str(e)}",
                "agent_used": "health_doctor"
            }

    async def route_to_insurance_agent(self, query: str) -> Dict[str, Any]:
        """Route query to insurance agent via WebSocket"""
        logger.info(f"Routing to insurance agent")
        start_time = time.time()
        
        try:
            # Convert ws:// to the format expected by websockets library
            ws_url = INSURANCE_SERVER_URL.replace("ws://", "")
            if not ws_url.startswith("ws://"):
                ws_url = f"ws://{ws_url}"
            
            logger.debug(f"Connecting to insurance agent: {ws_url}")
            
            async with websockets.connect(ws_url, timeout=30) as websocket:
                # Send query to insurance agent
                message = {
                    "type": "message",
                    "content": query
                }
                
                await websocket.send(json.dumps(message))
                logger.debug(f"Sent message to insurance agent: {message}")
                
                # Wait for response
                response = await websocket.recv()
                response_data = json.loads(response)
                
                processing_time = time.time() - start_time
                logger.info(f"Insurance agent responded successfully in {processing_time:.3f}s")
                
                return {
                    "success": True,
                    "result": response_data.get("content", "No response received"),
                    "agent_used": "insurance",
                    "processing_time": processing_time
                }
                
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error calling insurance agent after {processing_time:.3f}s: {str(e)}")
            
            # Try alternative method - direct HTTP if WebSocket fails
            try:
                logger.info("WebSocket failed, trying alternative routing...")
                return {
                    "success": False,
                    "result": f"Insurance agent temporarily unavailable: {str(e)}",
                    "agent_used": "insurance"
                }
            except Exception as e2:
                logger.error(f"All insurance agent connection methods failed: {str(e2)}")
                return {
                    "success": False,
                    "result": f"Cannot reach insurance agent: {str(e)}",
                    "agent_used": "insurance"
                }

    async def process_query(self, location: str, query: str, force_agent: str = None) -> QueryResponse:
        """Main orchestration method"""
        request_id = id(query)
        logger.info(f"[Orchestrator {request_id}] Processing query")
        logger.info(f"[Orchestrator {request_id}] Location: {location}")
        logger.info(f"[Orchestrator {request_id}] Query: {query[:100]}{'...' if len(query) > 100 else ''}")
        logger.info(f"[Orchestrator {request_id}] Force agent: {force_agent}")
        
        start_time = time.time()
        
        try:
            # Determine which agent to use
            if force_agent and force_agent in ['doctor', 'health']:
                query_type = QueryType.HEALTH_DOCTOR
                confidence = 1.0
                reasoning = "Forced to health agent"
            elif force_agent == 'insurance':
                query_type = QueryType.INSURANCE
                confidence = 1.0
                reasoning = "Forced to insurance agent"
            else:
                # Use AutoGen classification
                query_type, confidence, reasoning = await self.classify_query(query, location)
            
            logger.info(f"[Orchestrator {request_id}] Routing to: {query_type.value} (confidence: {confidence:.2f})")
            
            # Route to appropriate agent
            if query_type == QueryType.INSURANCE:
                result = await self.route_to_insurance_agent(query)
            else:  # Default to health agent
                result = await self.route_to_health_agent(location, query)
            
            total_time = time.time() - start_time
            logger.info(f"[Orchestrator {request_id}] Query completed in {total_time:.3f}s")
            
            return QueryResponse(
                result=result["result"],
                success=result["success"],
                agent_used=result["agent_used"],
                confidence=confidence,
                reasoning=reasoning
            )
            
        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"[Orchestrator {request_id}] Error after {total_time:.3f}s: {str(e)}")
            logger.exception(f"[Orchestrator {request_id}] Full traceback:")
            
            return QueryResponse(
                result=f"Orchestration error: {str(e)}",
                success=False,
                agent_used="error",
                confidence=0.0,
                reasoning="Error in orchestration"
            )


# Initialize orchestrator
orchestrator = AgentOrchestrator()

# FastAPI app
app = FastAPI(
    title="AI Agent Orchestrator",
    version="1.0.0",
    description="Intelligent agent orchestrator using AutoGen"
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log all HTTP requests and responses."""
    start_time = time.time()
    request_id = id(request)
    
    logger.info(f"[Request {request_id}] {request.method} {request.url}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"[Request {request_id}] Response: {response.status_code} in {process_time:.3f}s")
        response.headers["X-Process-Time"] = str(process_time)
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"[Request {request_id}] Error after {process_time:.3f}s: {str(e)}")
        raise

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.debug("Health check requested")
    return {
        "status": "healthy",
        "service": "orchestrator-server",
        "version": "1.0.0",
        "agents": {
            "health_agent": FASTAPI_SERVER_URL,
            "insurance_agent": INSURANCE_SERVER_URL,
            "mcp_server": MCP_SERVER_URL
        }
    }

@app.post("/query", response_model=QueryResponse)
async def orchestrate_query(request: QueryRequest) -> QueryResponse:
    """Main orchestration endpoint"""
    logger.info(f"Received orchestration request: {request}")
    
    # Validate inputs
    if not request.query.strip():
        logger.warning("Empty query provided")
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    # Process the query through orchestrator
    result = await orchestrator.process_query(
        location=request.location,
        query=request.query,
        force_agent=request.agent if request.agent != "auto" else None
    )
    
    logger.info(f"Orchestration completed: agent={result.agent_used}, success={result.success}")
    return result

@app.get("/agents/status")
async def get_agents_status():
    """Check status of all connected agents"""
    logger.debug("Checking agent status")
    
    status = {
        "health_agent": {"url": FASTAPI_SERVER_URL, "status": "unknown"},
        "insurance_agent": {"url": INSURANCE_SERVER_URL, "status": "unknown"},
        "mcp_server": {"url": MCP_SERVER_URL, "status": "unknown"}
    }
    
    # Check health agent
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{FASTAPI_SERVER_URL}/health")
            status["health_agent"]["status"] = "healthy" if response.status_code == 200 else "unhealthy"
    except Exception as e:
        status["health_agent"]["status"] = f"error: {str(e)}"
    
    # Check MCP server
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{MCP_SERVER_URL}/health")
            status["mcp_server"]["status"] = "healthy" if response.status_code == 200 else "unhealthy"
    except Exception as e:
        status["mcp_server"]["status"] = f"error: {str(e)}"
    
    # Insurance agent status check would need WebSocket connection test
    status["insurance_agent"]["status"] = "websocket - not tested"
    
    return status

if __name__ == "__main__":
    logger.info("Starting Orchestrator server with uvicorn...")
    logger.info("Server configuration:")
    logger.info("  Host: 0.0.0.0")
    logger.info("  Port: 7500")
    
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=7500,
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
        logger.info("=== AI Agent Orchestrator Stopped ===")