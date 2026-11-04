import asyncio

from agent.mcp_client import (
    connect,
    disconnect,
    discover_tools
)

from graph import build_graph


async def main():

    client = await connect()

    tools = await discover_tools(client)

    print("\nAvailable Tools")
    print("----------------")

    for tool in tools:
        print(tool.name)

    graph = build_graph(tools)

    user_request = input("\nUser : ")

    initial_state = {
        "user_request": user_request,
        "current_step": 0,
        "max_steps": 5,
        "actions": [],
        "observations": [],
        "finished": False,
        "final_answer": ""
    }

    result = graph.invoke(
        initial_state
    )

    print("\nFinal State")
    print("-----------")
    print(result)

    await disconnect(client)


if __name__ == "__main__":
    asyncio.run(main())
