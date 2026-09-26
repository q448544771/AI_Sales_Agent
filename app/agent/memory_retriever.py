from app.mcp.adapter import (
    load_crm_langchain_tools_sync,
)


# ============================================================
# 加载 CRM MCP LangChain Tools
# ============================================================
#
# 当前 CRM MCP 提供：
#
# query_leads
# create_lead
# update_lead_stage
#
# Memory Retrieval 这里只使用 query_leads。
#
# 注意：
# 不再直接 import app.tools.crm_tools
#
# 数据链路变成：
#
# memory_retriever
#       ↓
# LangChain StructuredTool
#       ↓
# MCP Adapter
#       ↓
# MCP Client
#       ↓
# CRM MCP Server
#       ↓
# crm_tools.py
#       ↓
# SQLite
#
# ============================================================

crm_tools = (
    load_crm_langchain_tools_sync()
)


crm_tool_map = {

    tool.name:
        tool

    for tool in crm_tools

}



# ============================================================
# 检查 query_leads 是否存在
# ============================================================

if "query_leads" not in crm_tool_map:

    raise RuntimeError(

        "CRM MCP Server 未提供 query_leads 工具。"

        f"当前CRM工具: "
        f"{list(crm_tool_map.keys())}"

    )



query_leads_tool = (
    crm_tool_map[
        "query_leads"
    ]
)



# ============================================================
# Memory Retrieval Node
# ============================================================

def memory_retrieval_node(
    state
):

    """
    Memory Retrieval Node


    根据当前SalesGoal，
    通过CRM MCP查询历史客户。


    查询结果写入：

        state["memory_context"]


    数据链路：

        LangGraph
            ↓
        memory_retrieval_node
            ↓
        query_leads LangChain Tool
            ↓
        CRM MCP Adapter
            ↓
        CRM MCP Client
            ↓
        CRM MCP Server
            ↓
        crm_tools.query_leads
            ↓
        SQLite
    """


    # ========================================================
    # 获取当前Sales Goal
    # ========================================================

    goal = state.get(
        "goal"
    )


    # ========================================================
    # 没有Goal时不查询CRM
    # ========================================================

    if not goal:

        return {

            "memory_context":
                []

        }



    # ========================================================
    # 获取目标行业
    # ========================================================

    industry = getattr(

        goal,

        "target_industry",

        ""

    )


    # ========================================================
    # 输出调试信息
    # ========================================================

    print(
        "\n===== Memory Retrieval ====="
    )


    print(
        "查询行业:",
        industry
    )



    # ========================================================
    # 通过CRM MCP查询历史客户
    # ========================================================
    #
    # 这里已经不是：
    #
    # app.tools.crm_tools.query_leads.invoke(...)
    #
    # 而是：
    #
    # LangChain StructuredTool
    #       ↓
    # CRM MCP
    #
    # Adapter已经保证结果恢复为：
    #
    # list[dict]
    #
    # 而不是JSON字符串。
    # ========================================================

    history = (
        query_leads_tool.invoke(

            {

                "industry":
                    industry,

                "min_score":
                    0.0,

            }

        )
    )



    # ========================================================
    # 数据类型保护
    # ========================================================

    if history is None:

        history = []


    elif not isinstance(
        history,
        list
    ):

        raise TypeError(

            "CRM MCP query_leads 返回类型异常，"

            f"期望 list，实际为 "
            f"{type(history).__name__}: "

            f"{history}"

        )



    # ========================================================
    # 输出历史客户
    # ========================================================

    print(
        "历史客户:",
        history
    )



    # ========================================================
    # 注入LangGraph State
    # ========================================================

    return {

        "memory_context":
            history

    }