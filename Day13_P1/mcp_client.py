from fastmcp import Client


async def connect(server):

    client = Client(server)

    await client.__aenter__()

    print(
        f"Connected to: {server}"
    )

    return client


async def disconnect(client):

    await client.__aexit__(
        None,
        None,
        None
    )


async def discover_tools(client):

    return await client.list_tools()


async def execute_tool(
    client,
    tool_name,
    arguments=None
):

    if arguments is None:
        arguments = {}

    return await client.call_tool(
        tool_name,
        arguments
    )

