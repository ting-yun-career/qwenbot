from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from agents.account_agent import execute_action
from agents.main_agent import main_agent
from MCP.account_manager.schemas import Account

app = FastAPI(title="Account Manager API")


class ChatRequest(BaseModel):
    prompt: str


class SubtaskOut(BaseModel):
    id: int
    agent: str
    prompt: str
    status: str
    result: str | None


class ChatResponse(BaseModel):
    answer: str
    subtasks: list[SubtaskOut]


class StateUpdate(BaseModel):
    active: bool


@app.get("/accounts")
async def list_accounts() -> list[Account]:
    output = await execute_action({"tool": "list_subscriptions", "arguments": {}})
    if "error" in output:
        raise HTTPException(status_code=502, detail=output["error"])
    return output["result"]


@app.patch("/accounts/{user_id}")
async def set_account_state(user_id: str, update: StateUpdate) -> Account:
    output = await execute_action(
        {
            "tool": "set_subscription_state",
            "arguments": {"user_id": user_id, "active": update.active},
        }
    )
    if "error" in output:
        raise HTTPException(status_code=404, detail=output["error"])
    return output["result"]


@app.post("/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    final = await main_agent.ainvoke({"prompt": request.prompt})
    return ChatResponse(answer=final["answer"], subtasks=final["subtasks"])
