import os
import uuid
from strands import Agent
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager
from mcp_client.client import get_streamable_http_mcp_client
from model.load import load_model

app = BedrockAgentCoreApp()
log = app.logger

MEMORY_ID = os.getenv("BEDROCK_AGENTCORE_MEMORY_ID")
REGION = os.getenv("AWS_REGION", "us-east-1")

mcp_client = get_streamable_http_mcp_client()

# ---------- helpers ----------

def _get_headers(context) -> dict:
    for attr in ("request_headers", "headers"):
        h = getattr(context, attr, None)
        if isinstance(h, dict):
            return h
    return {}

def _resolve_session_id(payload, context) -> str:
    """
    Correct resolution order:

    1) agentcore invoke --dev      -> payload["session_id"]
    2) real AgentCore runtime      -> context.session_id
    3) headers (edge cases)
    4) dev fallback (UUID, never 'default')
    """

    # 1️⃣ DEV MODE (agentcore invoke --dev)
    if isinstance(payload, dict):
        sid = payload.get("session_id") or payload.get("sessionId")
        if sid:
            return str(sid)

    # 2️⃣ REAL RUNTIME
    sid = getattr(context, "session_id", None)
    if sid:
        return str(sid)

    # 3️⃣ HEADERS (rare)
    headers = _get_headers(context)
    sid = (
        headers.get("X-Session-Id")
        or headers.get("x-session-id")
        or headers.get("X-Amzn-Bedrock-AgentCore-Runtime-Session-Id")
        or headers.get("x-amzn-bedrock-agentcore-runtime-session-id")
    )
    if sid:
        return str(sid)

    # 4️⃣ SAFE DEV FALLBACK
    return f"dev-{uuid.uuid4()}"

def _resolve_actor_id(payload, context) -> str:
    headers = _get_headers(context)

    actor = (
        headers.get("X-Amzn-Bedrock-AgentCore-Runtime-User-Id")
        or headers.get("x-amzn-bedrock-agentcore-runtime-user-id")
    )
    if actor:
        return str(actor)

    if isinstance(payload, dict) and payload.get("user_id"):
        return str(payload["user_id"])

    return "user"

# ---------- entrypoint ----------

@app.entrypoint
async def invoke(payload, context):
    print("payload", payload)
    payload = payload or {}

    print("context", context)

    prompt = payload.get("prompt", "")

    session_id = _resolve_session_id(payload, context)
    actor_id = _resolve_actor_id(payload, context)

    log.info(f"runtime session_id={session_id} actor_id={actor_id}")

    session_manager = None
    if MEMORY_ID:
        session_manager = AgentCoreMemorySessionManager(
            agentcore_memory_config=AgentCoreMemoryConfig(
                memory_id=MEMORY_ID,
                session_id=session_id,
                actor_id=actor_id,
            ),
            region_name=REGION,
        )

    with mcp_client as client:
        tools = client.list_tools_sync()

        agent = Agent(
            model=load_model(),
            session_manager=session_manager,
            system_prompt=(
                "You are a helpful assistant name Jeni, you like to say your name alot.\n"
                "Use memory when it helps personalize answers.\n"
                "Do not store or repeat highly sensitive identifiers."
            ),
            tools=tools,
        )

        stream = agent.stream_async(prompt)
        async for event in stream:
            if "data" in event and isinstance(event["data"], str):
                yield event["data"]

if __name__ == "__main__":
    app.run()
