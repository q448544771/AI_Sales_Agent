from mcp.server.mcpserver import MCPServer


import logging
import sys


from app.tools.company_tools import (
    search_companies,
    search_company_news,
    search_company_jobs
)



# ==================================================
# 日志配置
# ==================================================

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="%(asctime)s [Company MCP Server] %(levelname)s: %(message)s"
)


logger = logging.getLogger(
    "company_server"
)



# ==================================================
# 创建 MCP Server
# ==================================================

server = MCPServer(
    name="company-server"
)



# ==================================================
# 企业搜索工具
# ==================================================

@server.tool()
def search_company(
    industry: str,
    region: str
):
    """
    搜索企业信息
    """

    logger.info(
        f"调用 search_company: industry={industry}, region={region}"
    )


    result = search_companies.invoke(
        {
            "industry": industry,
            "region": region
        }
    )


    logger.info(
        "search_company 执行完成"
    )


    return result





# ==================================================
# 企业新闻查询
# ==================================================

@server.tool()
def get_company_news(
    company: str
):
    """
    查询企业新闻
    """


    logger.info(
        f"调用 get_company_news: company={company}"
    )


    result = search_company_news.invoke(
        {
            "company": company
        }
    )


    logger.info(
        "get_company_news 执行完成"
    )


    return result





# ==================================================
# 企业招聘查询
# ==================================================

@server.tool()
def get_company_jobs(
    company: str
):
    """
    查询企业招聘
    """


    logger.info(
        f"调用 get_company_jobs: company={company}"
    )


    result = search_company_jobs.invoke(
        {
            "company": company
        }
    )


    logger.info(
        "get_company_jobs 执行完成"
    )


    return result





# ==================================================
# MCP Server启动
# ==================================================

if __name__ == "__main__":


    logger.info(
        "Company MCP Server Starting..."
    )


    server.run()