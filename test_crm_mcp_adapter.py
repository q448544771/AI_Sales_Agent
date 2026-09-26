import asyncio


from app.mcp.adapter import (
    load_crm_langchain_tools,
)



async def main():

    # ========================================================
    # 加载CRM LangChain Tools
    # ========================================================

    tools = await (
        load_crm_langchain_tools()
    )


    print(
        "\n========== CRM LangChain MCP Tools ==========\n"
    )


    for tool in tools:

        print(
            f"Tool Name: {tool.name}"
        )

        print(
            f"Description: {tool.description}"
        )

        print(
            f"Args Schema: {tool.args_schema}"
        )

        print()



    # ========================================================
    # Tool Map
    # ========================================================

    tool_map = {

        tool.name:
            tool

        for tool in tools

    }



    # ========================================================
    # query_leads真实调用测试
    # ========================================================

    print(
        "\n========== query_leads Adapter Test ==========\n"
    )


    query_result = await (

        tool_map[
            "query_leads"
        ].ainvoke(

            {

                "industry":
                    "汽车零部件",

                "min_score":
                    0.0,

            }

        )

    )


    print(
        query_result
    )


    print(
        "\nResult Type:"
    )

    print(
        type(
            query_result
        )
    )



    # ========================================================
    # 检查第一个结果
    # ========================================================

    if isinstance(
        query_result,
        list
    ) and query_result:

        print(
            "\nFirst Lead:"
        )

        print(
            query_result[0]
        )

        print(
            "\nFirst Lead Type:"
        )

        print(
            type(
                query_result[0]
            )
        )



if __name__ == "__main__":

    asyncio.run(
        main()
    )