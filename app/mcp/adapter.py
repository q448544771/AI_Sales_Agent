import asyncio

import json


from langchain_core.tools import StructuredTool

from mcp.types import TextContent


from app.mcp.client import (

    get_company_mcp_tools,
    call_company_mcp_tool,

    get_crm_mcp_tools,
    call_crm_mcp_tool,

    get_knowledge_mcp_tools,
    call_knowledge_mcp_tool,

)



# ============================================================
# MCP Result标准化
# ============================================================

def normalize_mcp_result(result):

    """
    将MCP CallToolResult转换成LangChain更容易使用的结果。


    当前MCP Server可能返回：

    1. structured_content
    2. 单个TextContent
    3. 多个TextContent
    4. 普通文本
    5. JSON文本


    目标：

    MCP
        ↓
    normalize_mcp_result
        ↓
    Python dict / list / str
        ↓
    LangChain Tool
    """


    # ========================================================
    # MCP执行失败
    # ========================================================

    if result.is_error:

        error_messages = []


        for block in result.content:

            if isinstance(
                block,
                TextContent
            ):

                error_messages.append(
                    block.text
                )


        error_text = "\n".join(
            error_messages
        )


        raise RuntimeError(

            error_text

            or

            "MCP Tool执行失败"

        )



    # ========================================================
    # 优先使用structured_content
    # ========================================================

    if result.structured_content is not None:

        data = (
            result.structured_content
        )


        # ----------------------------------------------------
        # 某些MCP实现会包装：
        #
        # {
        #     "result": ...
        # }
        #
        # 如果只有result一个字段，
        # 直接取内部数据。
        # ----------------------------------------------------

        if (

            isinstance(
                data,
                dict
            )

            and

            set(
                data.keys()
            )
            ==
            {"result"}

        ):

            return data["result"]


        return data



    # ========================================================
    # 提取TextContent
    # ========================================================

    text_blocks = []


    for block in result.content:

        if isinstance(
            block,
            TextContent
        ):

            text = (
                block.text
                or
                ""
            ).strip()


            if text:

                text_blocks.append(
                    text
                )



    # ========================================================
    # 没有任何TextContent
    # ========================================================

    if not text_blocks:

        return ""



    # ========================================================
    # 尝试把每个TextContent解析成JSON
    # ========================================================
    #
    # 例如query_leads当前返回：
    #
    # TextContent(
    #     text='{"company": "..."}'
    # )
    #
    # TextContent(
    #     text='{"company": "..."}'
    # )
    #
    # 应该转换为：
    #
    # [
    #     {"company": "..."},
    #     {"company": "..."}
    # ]
    #
    # 而不是：
    #
    # '{"company": "..."}\n{"company": "..."}'
    #
    # ========================================================

    parsed_results = []

    all_json = True


    for text in text_blocks:

        try:

            parsed = json.loads(
                text
            )


            parsed_results.append(
                parsed
            )


        except json.JSONDecodeError:

            all_json = False

            break



    # ========================================================
    # 所有TextContent都是JSON
    # ========================================================

    if all_json:


        # ----------------------------------------------------
        # 单个JSON结果
        # ----------------------------------------------------

        if len(parsed_results) == 1:

            return parsed_results[0]


        # ----------------------------------------------------
        # 多个JSON结果
        # ----------------------------------------------------

        return parsed_results



    # ========================================================
    # 普通文本
    # ========================================================

    return "\n".join(
        text_blocks
    )



# ============================================================
# MCP Tool -> LangChain Tool
# ============================================================

def create_langchain_tool(
    mcp_tool,
    call_mcp_tool
):

    """
    将一个MCP Tool转换为LangChain StructuredTool。


    Args:

        mcp_tool:
            MCP Server返回的Tool描述。


        call_mcp_tool:
            对应Server的调用函数。

            例如：

            call_company_mcp_tool

            call_crm_mcp_tool

            call_knowledge_mcp_tool
    """


    tool_name = (
        mcp_tool.name
    )



    # ========================================================
    # Async调用
    # ========================================================

    async def async_call_tool(
        **kwargs
    ):

        result = await call_mcp_tool(

            tool_name,

            kwargs

        )


        return normalize_mcp_result(
            result
        )



    # ========================================================
    # Sync调用
    # ========================================================

    def sync_call_tool(
        **kwargs
    ):

        return asyncio.run(

            async_call_tool(
                **kwargs
            )

        )



    # ========================================================
    # 创建LangChain StructuredTool
    # ========================================================

    langchain_tool = (

        StructuredTool.from_function(

            func=sync_call_tool,

            coroutine=async_call_tool,

            name=mcp_tool.name,

            description=(

                mcp_tool.description

                or

                f"MCP Tool: {mcp_tool.name}"

            ),

            args_schema=(
                mcp_tool.input_schema
            ),

            infer_schema=False,

        )

    )


    return langchain_tool



# ============================================================
# Company MCP -> LangChain
# ============================================================

async def load_company_langchain_tools():

    """
    加载Company MCP Tools。

    当前应包含：

    search_company
    get_company_news
    get_company_jobs
    """


    mcp_tools = (
        await get_company_mcp_tools()
    )


    langchain_tools = []


    for mcp_tool in mcp_tools:

        tool = create_langchain_tool(

            mcp_tool,

            call_company_mcp_tool

        )


        langchain_tools.append(
            tool
        )


    return langchain_tools



# ============================================================
# CRM MCP -> LangChain
# ============================================================

async def load_crm_langchain_tools():

    """
    加载CRM MCP Tools。

    当前应包含：

    query_leads
    create_lead
    update_lead_stage
    """


    mcp_tools = (
        await get_crm_mcp_tools()
    )


    langchain_tools = []


    for mcp_tool in mcp_tools:

        tool = create_langchain_tool(

            mcp_tool,

            call_crm_mcp_tool

        )


        langchain_tools.append(
            tool
        )


    return langchain_tools



# ============================================================
# Knowledge MCP -> LangChain
# ============================================================

async def load_knowledge_langchain_tools():

    """
    加载Knowledge MCP Tools。

    当前应包含：

    search_product_knowledge
    """


    mcp_tools = (
        await get_knowledge_mcp_tools()
    )


    langchain_tools = []


    for mcp_tool in mcp_tools:

        tool = create_langchain_tool(

            mcp_tool,

            call_knowledge_mcp_tool

        )


        langchain_tools.append(
            tool
        )


    return langchain_tools



# ============================================================
# 加载全部MCP Tools
# ============================================================

async def load_all_langchain_tools():

    """
    加载Agent当前全部MCP Tools。


    Company MCP：

        search_company
        get_company_news
        get_company_jobs


    CRM MCP：

        query_leads
        create_lead
        update_lead_stage


    Knowledge MCP：

        search_product_knowledge


    最终共：

        7个MCP Tools
    """


    # ========================================================
    # 并行获取三个MCP Server的Tool定义
    # ========================================================

    (

        company_tools,

        crm_tools,

        knowledge_tools,

    ) = await asyncio.gather(

        load_company_langchain_tools(),

        load_crm_langchain_tools(),

        load_knowledge_langchain_tools(),

    )



    all_tools = [

        *company_tools,

        *crm_tools,

        *knowledge_tools,

    ]



    # ========================================================
    # 检查Tool名称冲突
    # ========================================================

    tool_names = [

        tool.name

        for tool in all_tools

    ]


    if len(tool_names) != len(
        set(tool_names)
    ):

        raise ValueError(

            "MCP Tool名称存在冲突: "
            f"{tool_names}"

        )


    return all_tools



# ============================================================
# Sync Loader
# ============================================================

def load_company_langchain_tools_sync():

    return asyncio.run(
        load_company_langchain_tools()
    )



def load_crm_langchain_tools_sync():

    return asyncio.run(
        load_crm_langchain_tools()
    )



def load_knowledge_langchain_tools_sync():

    return asyncio.run(
        load_knowledge_langchain_tools()
    )



def load_all_langchain_tools_sync():

    return asyncio.run(
        load_all_langchain_tools()
    )