import asyncio

from mcp_manager import (
    create_tool_registry,
    close_servers,
    run_tool
)


async def main():

    servers = [
        "time-mcp-server/server.py",
        "weather-mcp-server/server.py"
    ]

    clients, tool_registry = (
        await create_tool_registry(
            servers
        )
    )

    try:

        print("\nAvailable Tools")
        print("----------------")

        for tool_name in tool_registry:
            print(tool_name)

        result = await run_tool(
            tool_registry,
            "get_weather",
            {"city": "Delhi"}
        )

        print("\nTool Result:")
        print(result)

    finally:

        await close_servers(
            clients
        )


if __name__ == "__main__":
    asyncio.run(main())

