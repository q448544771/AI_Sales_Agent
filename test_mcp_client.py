import asyncio


from app.mcp.client import (
    get_company_tools
)



async def main():


    tools = await get_company_tools()


    print(
        "========== MCP Tools =========="
    )


    for tool in tools:

        print(
            tool.name
        )



if __name__=="__main__":

    asyncio.run(main())