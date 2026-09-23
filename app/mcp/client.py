import asyncio


from mcp.client.stdio import (
    stdio_client,
    StdioServerParameters
)


from mcp import ClientSession



company_server = StdioServerParameters(

    command="python",

    args=[
        "-m",
        "app.mcp.company_server"
    ]

)



async def get_company_tools():

    """
    获取MCP Server工具列表
    """


    async with stdio_client(
        company_server
    ) as (
        read,
        write
    ):


        async with ClientSession(
            read,
            write
        ) as session:


            await session.initialize()


            response = await session.list_tools()


            return response.tools