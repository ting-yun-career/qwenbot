from mcp_client import (
    connect,
    disconnect,
    discover_tools,
    execute_tool
)


async def create_tool_registry(
    servers
):

    clients = []

    tool_registry = {}

    for server in servers:

        client = await connect(
            server
        )

        clients.append(client)

        tools = await discover_tools(
            client
        )

        for tool in tools:

            tool_registry[
                tool.name
            ] = {
                "client": client,
                "tool": tool
            }

    return clients, tool_registry


async def close_servers(clients):

    for client in clients:

        await disconnect(client)


async def run_tool(
    tool_registry,
    tool_name,
    arguments
):

    entry = tool_registry.get(
        tool_name
    )

    if entry is None:

        raise ValueError(
            f"Unknown tool: {tool_name}"
        )

    return await execute_tool(
        entry["client"],
        tool_name,
        arguments
    )

