import asyncio


from app.mcp.client import (
    get_crm_mcp_tools,
    call_crm_mcp_tool,
)



async def main():

    # ========================================================
    # 1. 获取CRM MCP Tools
    # ========================================================

    print(
        "\n========== CRM MCP Tools ==========\n"
    )


    tools = await get_crm_mcp_tools()


    for tool in tools:

        print(
            f"Tool Name: {tool.name}"
        )

        print(
            f"Description: {tool.description}"
        )

        print(
            f"Args: {tool.input_schema}"
        )

        print()



    # ========================================================
    # 2. 测试 query_leads
    # ========================================================

    print(
        "\n========== query_leads Test ==========\n"
    )


    result = await call_crm_mcp_tool(

        "query_leads",

        {

            "industry":
                "汽车零部件",

            "min_score":
                0.0,

        }

    )


    print(
        "Tool Result:"
    )

    print(
        result
    )



    # ========================================================
    # 3. 测试 create_lead 防重复
    # ========================================================

    print(
        "\n========== create_lead Duplicate Test ==========\n"
    )


    result = await call_crm_mcp_tool(

        "create_lead",

        {

            "company":
                "CRM_MCP测试企业",

            "industry":
                "汽车零部件",

            "region":
                "测试区域",

            "score":
                0.75,

            "level":
                "中",

            "evidence": [
                "测试新建生产线",
                "测试自动化升级",
            ],

            "action":
                "测试销售动作",

            "next_action":
                "测试下一步动作",

            "owner":
                "",

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