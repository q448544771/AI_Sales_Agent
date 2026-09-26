import asyncio


from app.mcp.client import (
    get_knowledge_mcp_tools,
    call_knowledge_mcp_tool,
)



async def main():

    print(
        "\n========== Knowledge MCP Tools ==========\n"
    )


    tools = await get_knowledge_mcp_tools()


    for tool in tools:

        print(
            "Tool:",
            tool.name
        )


    print(
        "\n========== Call Knowledge MCP ==========\n"
    )


    result = await call_knowledge_mcp_tool(

        "search_product_knowledge",

        {
            "query":
                "新能源汽车结构件有哪些机器视觉检测方案"
        }

    )


    print(result)



if __name__ == "__main__":

    asyncio.run(
        main()
    )