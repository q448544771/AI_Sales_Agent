import logging
import sys


from mcp.server.mcpserver import MCPServer


from app.tools.crm_tools import (

    query_leads as query_leads_tool,

    create_lead as create_lead_tool,

    update_lead_stage as update_lead_stage_tool,

)



# ============================================================
# Logging
# ============================================================
#
# MCP stdio模式下：
#
# stdout
#     必须留给JSON-RPC协议
#
# stderr
#     可以用于日志
#
# 所以绝对不要在这个文件使用普通print()。
# ============================================================

logging.basicConfig(

    level=logging.INFO,

    stream=sys.stderr,

    format=(
        "%(asctime)s "
        "[CRM MCP Server] "
        "%(levelname)s: "
        "%(message)s"
    )

)


logger = logging.getLogger(
    "crm_server"
)



# ============================================================
# 创建MCP Server
# ============================================================

server = MCPServer(
    name="crm-server"
)



# ============================================================
# Tool 1：查询CRM客户
# ============================================================

@server.tool()
def query_leads(
    industry: str = "",
    min_score: float = 0.0
):

    """
    查询CRM客户。

    支持行业父子匹配和最低评分过滤。
    """


    logger.info(

        "query_leads called: "
        "industry=%s, min_score=%s",

        industry,

        min_score

    )


    result = query_leads_tool.invoke(

        {

            "industry":
                industry,

            "min_score":
                min_score,

        }

    )


    logger.info(

        "query_leads completed: "
        "%s leads returned",

        len(result)

        if isinstance(result, list)

        else "unknown"

    )


    return result



# ============================================================
# Tool 2：创建CRM客户
# ============================================================

@server.tool()
def create_lead(
    company: str,
    industry: str,
    region: str,
    score: float = 0.0,
    level: str = "",
    evidence: list[str] | None = None,
    action: str = "",
    next_action: str = "",
    owner: str = ""
):

    """
    创建一个新的CRM客户。

    新客户统一以new阶段进入CRM。
    """


    logger.info(

        "create_lead called: "
        "company=%s",

        company

    )


    result = create_lead_tool.invoke(

        {

            "company":
                company,

            "industry":
                industry,

            "region":
                region,

            "score":
                score,

            "level":
                level,

            "evidence":
                evidence,

            "action":
                action,

            "next_action":
                next_action,

            "owner":
                owner,

        }

    )


    logger.info(

        "create_lead completed: "
        "company=%s, success=%s",

        company,

        (
            result.get(
                "success"
            )

            if isinstance(
                result,
                dict
            )

            else None
        )

    )


    return result



# ============================================================
# Tool 3：更新销售阶段
# ============================================================

@server.tool()
def update_lead_stage(
    company: str,
    stage: str,
    next_action: str = ""
):

    """
    更新已有CRM客户销售阶段及下一步动作。
    """


    logger.info(

        "update_lead_stage called: "
        "company=%s, stage=%s",

        company,

        stage

    )


    result = (
        update_lead_stage_tool.invoke(

            {

                "company":
                    company,

                "stage":
                    stage,

                "next_action":
                    next_action,

            }

        )
    )


    logger.info(

        "update_lead_stage completed: "
        "company=%s, success=%s",

        company,

        (
            result.get(
                "success"
            )

            if isinstance(
                result,
                dict
            )

            else None
        )

    )


    return result



# ============================================================
# Main
# ============================================================

if __name__ == "__main__":

    logger.info(
        "CRM MCP Server Starting..."
    )


    server.run()