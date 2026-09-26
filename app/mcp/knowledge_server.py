import sys


from mcp.server.mcpserver import MCPServer


from app.tools.knowledge_tools import (
    search_product_knowledge as search_product_knowledge_tool,
)



# ============================================================
# Knowledge MCP Server
# ============================================================

server = MCPServer(
    "knowledge-server"
)



# ============================================================
# MCP Tool
# ============================================================

@server.tool()
def search_product_knowledge(
    query: str
):

    """
    查询企业内部产品知识库。

    可用于查询：

    - 产品能力
    - 产品参数
    - 行业解决方案
    - 检测场景
    - 客户案例
    - 产品优势
    - 销售切入方案

    Args:
        query:
            产品、行业、检测场景或解决方案相关问题。

    Returns:
        与查询最相关的企业内部知识。
    """


    # --------------------------------------------------------
    # 调用LangChain Knowledge Tool
    # --------------------------------------------------------

    result = search_product_knowledge_tool.invoke(

        {

            "query":
                query

        }

    )


    return result



# ============================================================
# Server Entry
# ============================================================

if __name__ == "__main__":


    # 注意：
    #
    # MCP stdio模式下，
    # stdout必须留给JSON-RPC协议。
    #
    # 所以调试信息只能打印到stderr。

    print(
        "Starting Knowledge MCP Server...",
        file=sys.stderr
    )


    server.run(
        transport="stdio"
    )