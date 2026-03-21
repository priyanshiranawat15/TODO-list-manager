import os
from contextvars import ContextVar
import httpx
from agents import Agent, Runner, function_tool
from dotenv import load_dotenv

from models import AgentSession

load_dotenv()

BASE_URL = os.getenv("APP_BASE_URL", "http://127.0.0.1:8000")
AUTH_HEADER_CTX: ContextVar[str] = ContextVar("AUTH_HEADER_CTX", default="")


MODEL = os.getenv("OPENAI_MODEL", "gpt-5.1")

def _headers() -> dict:
    auth_header = AUTH_HEADER_CTX.get()
    if not auth_header:
        raise ValueError("Authorization header not set in context")
    return {"Authorization": auth_header}

def _safe_json(resp: httpx.Response):
    try:
        return resp.json()
    except Exception:
        return {"error": "Invalid JSON response", "status_code": resp.status_code, "text": resp.text}

@function_tool
async def create_task_tool(description: str, status: str = "pending", assignee_id: int | None = None):
    params = {"description": description, "status": status}
    if assignee_id is not None:
        params["assignee_id"] = assignee_id
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(f"{BASE_URL}/tasks", params=params, headers=_headers())
        return {"status_code": resp.status_code, "data": _safe_json(resp)}

@function_tool
async def list_my_tasks_tool() -> dict:
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(f"{BASE_URL}/tasks/mine", headers=_headers())
        return {"status_code": resp.status_code, "data": _safe_json(resp)}

@function_tool
async def update_task_status_tool(task_id: int, status: str) -> dict:
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.put(f"{BASE_URL}/tasks/{task_id}", params={"status": status}, headers=_headers())
        return {"status_code": resp.status_code, "data": _safe_json(resp)}

@function_tool
async def delete_task_tool(task_id: int) -> dict:
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.delete(f"{BASE_URL}/tasks/{task_id}", headers=_headers())
        return {"status_code": resp.status_code, "data": _safe_json(resp)}

@function_tool
async def list_all_users_tool() -> dict:
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(f"{BASE_URL}/users/list", headers=_headers())
        return {"status_code": resp.status_code, "data": _safe_json(resp)}


tool_agent = Agent(
    name="Todo Automation Agent",
    model=MODEL,
    instructions=(
        "You are a Todo Automation Agent. "
        "Always use function tools to perform actions. "
        "Never fabricate API results."
    ),
    tools=[create_task_tool, list_my_tasks_tool, update_task_status_tool, delete_task_tool, list_all_users_tool],
)

async def run_agent_for_session(
    session_id: int,
    user_id: int,
    auth_header: str,
    instruction: str,
    db
):
    token = AUTH_HEADER_CTX.set(auth_header)

    try:
        
        session = (
            db.query(AgentSession)
            .filter_by(id=session_id, user_id=user_id)
            .first()
        )
        if not session:
            raise ValueError("Session not found for this user")

        last_response_id = session.last_response_id
        result = await Runner.run(
            tool_agent,
            instruction,
            previous_response_id=last_response_id
        )

        session.last_response_id = result.last_response_id

        db.commit()

        return result.final_output

    finally:
        AUTH_HEADER_CTX.reset(token)