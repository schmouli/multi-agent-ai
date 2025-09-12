# insurance_agent_server.py
import os
import logging
import asyncio
from collections.abc import AsyncGenerator
from pathlib import Path

import openai
from acp_sdk.models import Message, MessagePart
from acp_sdk.server import Context, RunYield, RunYieldResume, Server
from crewai import Crew, Task, Agent
from crewai_tools import RagTool

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Configure OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")

class OpenAILLM:
    def __init__(self, model="gpt-4o-mini", max_tokens=1024, temperature=0.0):
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    async def acompletion(self, messages, **kwargs):
        client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        resp = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            temperature=kwargs.get("temperature", self.temperature),
        )
        return resp.choices[0].message.content

    def completion(self, messages, **kwargs):
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        resp = client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            temperature=kwargs.get("temperature", self.temperature),
        )
        return resp.choices[0].message.content

llm_adapter = OpenAILLM(model="gpt-4o-mini", max_tokens=4096, temperature=0.0)

# RAG tool configuration
config = {
    "llm": {
        "provider": "openai",
        "config": {"model": llm_adapter.model}
    },
    "embedding_model": {
        "provider": "openai",
        "config": {"model": "text-embedding-3-small"}
    }
}

# Initialize RAG tool
rag_tool = RagTool(config=config)

# Add documents if they exist
data_dir = Path("/app/data")
if data_dir.exists():
    pdf_files = list(data_dir.glob("*.pdf"))
    
    if pdf_files:
        logger.info(f"Found {len(pdf_files)} PDF files in data directory")
        for pdf_file in pdf_files:
            logger.info(f"Adding PDF: {pdf_file}")
            rag_tool.add(str(pdf_file), data_type="pdf_file")
    else:
        logger.warning("No PDF files found in /app/data directory")
else:
    logger.warning("/app/data directory does not exist")

# Create insurance agent
insurance_agent = Agent(
    role="Senior Insurance Coverage Assistant",
    goal="Determine whether something is covered or not",
    backstory="""You are an expert insurance agent designed to assist with coverage queries. 
    Whenever you call the knowledge base tool the tool input must follow the pattern
    {query: 'your query', kwargs:{}}""",
    verbose=True,
    allow_delegation=False,
    llm=llm_adapter,
    tools=[rag_tool],
    max_retry_limit=5
)

server = Server()

@server.agent()
async def policy_agent(input: list[Message], context: Context) -> AsyncGenerator[RunYield, RunYieldResume]:
    """Agent for policy coverage questions using RAG to consult policy docs."""
    user_text = input[0].parts[0].content
    logger.info(f"Received query: {user_text}")

    task1 = Task(
        description=user_text,
        expected_output="A comprehensive response as to the users question",
        agent=insurance_agent
    )
    
    crew = Crew(agents=[insurance_agent], tasks=[task1], verbose=True)
    
    try:
        task_output = await crew.kickoff_async()
        logger.info("Task completed successfully")
        logger.info(f"Output: {task_output}")
        
        yield Message(parts=[MessagePart(content=str(task_output))])
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        yield Message(parts=[MessagePart(content=f"Error processing your query: {str(e)}")])

if __name__ == "__main__":
    logger.info("Starting Insurance Agent Server on port 7001...")
    server.run(port=7001)
