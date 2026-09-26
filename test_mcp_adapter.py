import asyncio


from app.mcp.adapter import (
    load_company_langchain_tools
)



async def main():


    # ========================================================
    # 加载MCP -> LangChain Tools
    # ========================================================

    tools = await load_company_langchain_tools()



    print(
        "\n========== LangChain MCP Tools =========="
    )



    for tool in tools:

        print(
            f"\nTool Name: {tool.name}"
        )

        print(
            f"Description: {tool.description}"
        )

        print(
            f"Args: {tool.args}"
        )



    # ========================================================
    # 找到 search_company
    # ========================================================

    search_tool = next(

        tool

        for tool in tools

        if tool.name == "search_company"

    )



    print(
        "\n========== MCP Tool Call Test =========="
    )



    # 注意：
    #
    # MCP转换后的StructuredTool是异步工具，
    # 所以这里使用 ainvoke()

    result = await search_tool.ainvoke(

        {

            "industry":
                "汽车零部件",

            "region":
                "中国"

        }

    )



    print(
        "Tool Result:"
    )


    print(
        result
    )



if __name__ == "__main__":

    asyncio.run(
        main()
    )