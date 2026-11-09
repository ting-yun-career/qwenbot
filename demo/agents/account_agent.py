from pathlib import Path
from fastmcp import Client
from fastmcp.exceptions import ToolError
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

from MCP.account_manager.schemas import Account

ACCOUNT_MANAGER = Path(__file__).parent.parent / "MCP/account_manager/server.py"


class AgentState(TypedDict):
    prompt: str | None
    userId: str | None
    tool: str | None
    arguments: dict | None
    result: Account | list[Account] | None
    error: str | None


async def get_tool_descriptions() -> str:
    async with Client(ACCOUNT_MANAGER) as client:
        tools = await client.list_tools()
    return "\n".join(
        f"- {tool.name}({', '.join(tool.input_schema.get('properties', {}))}): "
        f"{tool.description}"
        for tool in tools
    )


async def execute_action(state: AgentState) -> dict:
    if not state.get("tool"):
        return {"error": "No tool matches the request"}
    async with Client(ACCOUNT_MANAGER) as client:
        try:
            result = await client.call_tool(state["tool"], state["arguments"])
        except ToolError as error:
            return {"error": str(error)}
    content = result.structured_content
    if "result" in content:
        return {"result": [Account.model_validate(item) for item in content["result"]]}
    return {"result": Account.model_validate(content)}


def has_user_id(state: AgentState) -> str:
    return "plan_action" if state.get("userId") else END


def create_account_agent(llm):
    async def needs_user_id(state: AgentState) -> str:
        async with Client(ACCOUNT_MANAGER) as client:
            tools = await client.list_tools()
        names = ", ".join(tool.name for tool in tools)
        response = await llm.ainvoke(
            f"These tools are available:\n{await get_tool_descriptions()}\n\n"
            f"Which tool handles the request? Answer with one tool name from: {names}.\n"
            f"Request: {state['prompt']}"
        )
        chosen = response.content.strip()
        for tool in tools:
            if tool.name == chosen and "user_id" in tool.input_schema.get("properties", {}):
                return "extract_user_id"
        return "plan_action"

    async def extract_user_id(state: AgentState) -> dict:
        response = await llm.ainvoke(
            "Extract the user ID from the request. "
            "Answer with the user ID only. If there is none, answer: NONE.\n"
            f"Request: {state['prompt']}"
        )
        user_id = response.content.strip()
        if user_id.upper() == "NONE":
            return {"userId": None, "error": "No user ID found in the request"}
        return {"userId": user_id}

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
        user = f"The user ID is {state['userId']}. " if state.get("userId") else ""
        response = await llm_with_tools.ainvoke(
            f"{user}Pick the tool for this request: {state['prompt']}"
        )
        if not response.tool_calls:
            return {"tool": None, "arguments": None}
        call = response.tool_calls[0]
        return {"tool": call["name"], "arguments": call["args"]}

    graph = StateGraph(AgentState)

    graph.add_node("extract_user_id", extract_user_id)
    graph.add_node("plan_action", plan_action)
    graph.add_node("execute_action", execute_action)

    graph.add_conditional_edges(
        START,
        needs_user_id,
        ["extract_user_id", "plan_action"],
    )
    graph.add_conditional_edges("extract_user_id", has_user_id, ["plan_action", END])
    graph.add_edge("plan_action", "execute_action")
    graph.add_edge("execute_action", END)

    return graph.compile()
