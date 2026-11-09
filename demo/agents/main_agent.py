import json
import os
from typing import Literal

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

from agents.account_agent import create_account_agent, get_tool_descriptions

load_dotenv()

llm = ChatOpenAI(
    model=os.getenv("MODEL"),
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY"),
    temperature=0,
)

account_graph = create_account_agent(llm)

SUBAGENT_NODES = {"account_agent": "account_agent"}


class Subtask(TypedDict):
    id: int
    agent: str
    prompt: str
    status: Literal["pending", "done", "failed"]
    result: str | None


class CoordinatorState(TypedDict):
    prompt: str
    subtasks: list[Subtask]
    current: int | None
    answer: str | None


async def describe_agents() -> dict[str, str]:
    tools = await get_tool_descriptions()
    return {
        "account_agent": f"Handles account subscription tasks. Its tools:\n{tools}",
        "coordinator": "Answers anything else directly, with no tools.",
    }


def update_subtask(state: CoordinatorState, status: str, result: str) -> dict:
    subtasks = state["subtasks"].copy()
    index = state["current"]
    subtasks[index] = {**subtasks[index], "status": status, "result": result}
    return {"subtasks": subtasks}


async def plan_subtasks(state: CoordinatorState) -> dict:
    agents = await describe_agents()
    listing = "\n".join(f"- {name}: {text}" for name, text in agents.items())
    response = await llm.ainvoke(
        "Break the request into the smallest independent subtasks. "
        "Put each subtask on its own line. "
        "Start each line with the agent name, a colon, then the subtask.\n"
        "Example output:\n"
        "account_agent: Show all subscriptions.\n"
        "coordinator: What is the capital of Italy?\n\n"
        "Rules: use only the request. "
        "Never add subtasks the request does not ask for. "
        "Write each subtask in plain English, not as a function call. "
        "Keep every detail that is in the request, such as user IDs. "
        "Choose the agent by topic, even when a detail is missing. "
        "Never invent details. If a detail, such as a user ID, is missing "
        "from the request, leave it out.\n"
        f"Agents:\n{listing}\n\nRequest: {state['prompt']}"
    )
    planned = []
    for line in response.content.splitlines():
        if ":" not in line:
            continue
        agent, prompt = line.split(":", 1)
        agent = agent.strip().strip("-*` ").lower()
        if prompt.strip():
            planned.append(
                {
                    "agent": agent if agent in agents else "coordinator",
                    "prompt": prompt.strip(),
                }
            )
    if not planned:
        planned = [{"agent": "coordinator", "prompt": state["prompt"]}]
    subtasks = [
        Subtask(
            id=index,
            agent=item["agent"],
            prompt=item["prompt"],
            status="pending",
            result=None,
        )
        for index, item in enumerate(planned)
    ]

    return {"subtasks": subtasks, "current": None, "answer": None}


def select_subtask(state: CoordinatorState) -> dict:
    for index, subtask in enumerate(state["subtasks"]):
        if subtask["status"] == "pending":
            print({"current": index})
            return {"current": index}
    return {"current": None}


def route_subtask(state: CoordinatorState) -> str:
    if state["current"] is None:
        return "synthesize"
    agent = state["subtasks"][state["current"]]["agent"]
    print(state["subtasks"][state["current"]])
    return SUBAGENT_NODES.get(agent, "answer_directly")


async def account_agent(state: CoordinatorState) -> dict:
    subtask = state["subtasks"][state["current"]]
    output = await account_graph.ainvoke({"prompt": subtask["prompt"]})
    if output.get("error"):
        return update_subtask(state, "failed", output["error"])
    result = output.get("result")
    if result is None:
        return update_subtask(state, "failed", "The agent returned no result")
    if isinstance(result, list):
        text = json.dumps([account.model_dump() for account in result])
    else:
        text = result.model_dump_json()
    return update_subtask(state, "done", text)


async def answer_directly(state: CoordinatorState) -> dict:
    subtask = state["subtasks"][state["current"]]
    response = await llm.ainvoke(subtask["prompt"])
    return update_subtask(state, "done", response.content)


async def synthesize(state: CoordinatorState) -> dict:
    lines = "\n".join(
        f"{subtask['id'] + 1}. {subtask['prompt']}\n"
        f"   status: {subtask['status']}\n   result: {subtask['result']}"
        for subtask in state["subtasks"]
    )
    response = await llm.ainvoke(
        "Write one final answer to the user's request. "
        "Use the subtask results. Say clearly which subtasks failed and why.\n"
        f"Request: {state['prompt']}\n\nSubtasks:\n{lines}"
    )
    return {"answer": response.content}


graph = StateGraph(CoordinatorState)

graph.add_node("plan_subtasks", plan_subtasks)
graph.add_node("select_subtask", select_subtask)
graph.add_node("account_agent", account_agent)
graph.add_node("answer_directly", answer_directly)
graph.add_node("synthesize", synthesize)

graph.add_edge(START, "plan_subtasks")
graph.add_edge("plan_subtasks", "select_subtask")
graph.add_conditional_edges(
    "select_subtask",
    route_subtask,
    ["account_agent", "answer_directly", "synthesize"],
)
graph.add_edge("account_agent", "select_subtask")
graph.add_edge("answer_directly", "select_subtask")
graph.add_edge("synthesize", END)

main_agent = graph.compile()
