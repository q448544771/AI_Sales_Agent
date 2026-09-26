import sys


from mcp import (
    Client,
    StdioServerParameters,
)



# ============================================================
# Company MCP Server
# ============================================================

COMPANY_SERVER_PARAMS = StdioServerParameters(

    command=sys.executable,

    args=[
        "-m",
        "app.mcp.company_server",
    ],

)



# ============================================================
# CRM MCP Server
# ============================================================

CRM_SERVER_PARAMS = StdioServerParameters(

    command=sys.executable,

    args=[
        "-m",
        "app.mcp.crm_server",
    ],

)



# ============================================================
# Knowledge MCP Server
# ============================================================

KNOWLEDGE_SERVER_PARAMS = StdioServerParameters(

    command=sys.executable,

    args=[
        "-m",
        "app.mcp.knowledge_server",
    ],

)



# ============================================================
# 通用 MCP Tool List
# ============================================================

async def _get_mcp_tools(
    server_params
):

    """
    获取指定MCP Server提供的全部Tools。

    server_params可以是：

    - Company MCP Server
    - CRM MCP Server
    - Knowledge MCP Server

    后续新增其他MCP Server时也可以继续复用。
    """


    async with Client(
        server_params
    ) as client:

        result = (
            await client.list_tools()
        )


        return result.tools



# ============================================================
# 通用 MCP Tool Call
# ============================================================

async def _call_mcp_tool(
    server_params,
    tool_name: str,
    arguments: dict
):

    """
    调用指定MCP Server中的Tool。
    """


    async with Client(
        server_params
    ) as client:

        result = (
            await client.call_tool(

                tool_name,

                arguments

            )
        )


        return result



# ============================================================
# Company MCP
# ============================================================

async def get_company_mcp_tools():

    """
    获取Company MCP Server的Tools。

    当前应包含：

    search_company
    get_company_news
    get_company_jobs
    """


    return await _get_mcp_tools(
        COMPANY_SERVER_PARAMS
    )



async def call_company_mcp_tool(
    tool_name: str,
    arguments: dict
):

    """
    调用Company MCP Tool。
    """


    return await _call_mcp_tool(

        COMPANY_SERVER_PARAMS,

        tool_name,

        arguments

    )



# ============================================================
# CRM MCP
# ============================================================

async def get_crm_mcp_tools():

    """
    获取CRM MCP Server的Tools。

    当前应包含：

    query_leads
    create_lead
    update_lead_stage
    """


    return await _get_mcp_tools(
        CRM_SERVER_PARAMS
    )



async def call_crm_mcp_tool(
    tool_name: str,
    arguments: dict
):

    """
    调用CRM MCP Tool。
    """


    return await _call_mcp_tool(

        CRM_SERVER_PARAMS,

        tool_name,

        arguments

    )



# ============================================================
# Knowledge MCP
# ============================================================

async def get_knowledge_mcp_tools():

    """
    获取Knowledge MCP Server的Tools。

    当前应包含：

    search_product_knowledge
    """


    return await _get_mcp_tools(
        KNOWLEDGE_SERVER_PARAMS
    )



async def call_knowledge_mcp_tool(
    tool_name: str,
    arguments: dict
):

    """
    调用Knowledge MCP Tool。
    """


    return await _call_mcp_tool(

        KNOWLEDGE_SERVER_PARAMS,

        tool_name,

        arguments

    )