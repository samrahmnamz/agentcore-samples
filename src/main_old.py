import os
from strands import Agent, tool
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager
from mcp_client.client import get_streamable_http_mcp_client
from model.load import load_model
from user_extractor import UserInfoMemoryExtractor

app = BedrockAgentCoreApp()
log = app.logger

MEMORY_ID = os.getenv("BEDROCK_AGENTCORE_MEMORY_ID")
REGION = os.getenv("AWS_REGION", "us-east-1")

# Global user info extractor
user_extractor = UserInfoMemoryExtractor()

# Import AgentCore Gateway as Streamable HTTP MCP Client
mcp_client = get_streamable_http_mcp_client()

@tool
def get_user_info() -> dict:
    """Get the current extracted user information"""
    return user_extractor.extract("")

@app.entrypoint
async def invoke(payload, context):
    session_id = getattr(context, 'session_id', None) or 'default'
    prompt = payload.get("prompt", "")
    
    # Extract user info from the prompt
    extracted_data = user_extractor.extract(prompt)
    
    # Configure self-managed memory if MEMORY_ID is set
    session_manager = None
    if MEMORY_ID:
        session_manager = AgentCoreMemorySessionManager(
            AgentCoreMemoryConfig(
                memory_id=MEMORY_ID,
                session_id=session_id,
                actor_id="user",
                # Pass extracted user info as metadata
                metadata=extracted_data
            ),
            REGION
        )
    
    with mcp_client as client:
        # Get MCP Tools
        tools = client.list_tools_sync()

        # Create agent with memory
        agent = Agent(
            model=load_model(),
            session_manager=session_manager,
            system_prompt="""
                You are a helpful assistant that extracts and remembers user information.
                You can extract firstname, lastname, and SSN from conversations.
                Use the get_user_info tool to check what information you have about the user.
                Always be helpful and acknowledge when you learn new information about the user.
            """,
            tools=[get_user_info] + tools
        )

        # Execute and format response
        stream = agent.stream_async(prompt)

        async for event in stream:
            # Handle Text parts of the response
            if "data" in event and isinstance(event["data"], str):
                yield event["data"]

if __name__ == "__main__":
    app.run()