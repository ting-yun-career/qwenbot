import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from fastmcp import Client
from fastmcp.exceptions import ToolError
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, ValidationError
from typing_extensions import TypedDict

from MCP.account_manager.schemas import Account

load_dotenv()

ACCOUNT_MANAGER = Path(__file__).parent / "MCP/account_manager/account_manager.py"

llm = ChatOpenAI(
    model=os.getenv("MODEL"),
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY"),
    temperature=0,
)


class Action(BaseModel):
    tool: str
    arguments: dict


class ActionResult(BaseModel):
    success: bool
    error: str | None = None


class AgentState(TypedDict):
    prompt: str
    userId: str
    action: Action | None
    actionResult: ActionResult | None
    account: Account | None


async def plan_action(state: AgentState) -> dict:
    async with Client(ACCOUNT_MANAGER) as client:
        tools = await client.list_tools()
    llm_with_tools = llm.bind_tools(
        [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema,
                },
            }
            for tool in tools
        ]
    )
    response = await llm_with_tools.ainvoke(
        f"The user ID is {state['userId']}. "
        f"Pick the tool for this request: {state['prompt']}"
    )
    if not response.tool_calls:
        return {"action": None}
    call = response.tool_calls[0]
    return {"action": Action(tool=call["name"], arguments=call["args"])}


async def execute_action(state: AgentState) -> dict:
    action = state["action"]
    if action is None:
        return {
            "actionResult": ActionResult(
                success=False, error="No tool matches the request"
            )
        }
    async with Client(ACCOUNT_MANAGER) as client:
        try:
            result = await client.call_tool(action.tool, action.arguments)
        except ToolError as error:
            return {"actionResult": ActionResult(success=False, error=str(error))}
    update = {"actionResult": ActionResult(success=True)}
    try:
        update["account"] = Account.model_validate(result.structured_content)
    except ValidationError:
        pass
    return update


graph = StateGraph(AgentState)

graph.add_node("plan_action", plan_action)
graph.add_node("execute_action", execute_action)

graph.add_edge(START, "plan_action")
graph.add_edge("plan_action", "execute_action")
graph.add_edge("execute_action", END)

app = graph.compile()

if __name__ == "__main__":
    with open("demo.png", "wb") as f:
        f.write(app.get_graph().draw_mermaid_png())
    print("Graph saved to demo.png")

    final = asyncio.run(
        app.ainvoke({"prompt": input("Enter a prompt: "), "userId": "103"})
    )
    print('---')
    print(final.get("action"))
    print(final.get("actionResult"))
    print(final.get("account"))
