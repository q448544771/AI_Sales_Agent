"""Phase 7.1 - Real Company MCP tools.

Company discovery uses multi-region real search.

News and recruitment use live Web Search.

All returned search entries retain their original URLs.
No hard-coded companies and no mock fallback.
"""


from langchain_core.tools import tool


from app.tools.real_company_discovery import (
    discover_companies,
    make_source,
    search_checked,
    source_text,
)


DATA_MODE = "real_web_search"

DETAIL_RESULT_COUNT = 8


# ============================================================
# 1. Discover real candidate companies
# ============================================================


@tool
def search_companies(
    industry: str,
    region: str,
) -> dict:

    """
    使用多地区真实网页搜索发现企业候选，
    并返回来源链接与搜索记录。
    """

    result = discover_companies(
        industry=industry,
        region=region,
    )


    # 保证 MCP 层不会丢失审计字段
    return {

        "success": result.get(
            "success",
            True
        ),

        "data_mode": result.get(
            "data_mode",
            DATA_MODE
        ),

        "provider": result.get(
            "provider",
            "bocha"
        ),

        "strategy_version": result.get(
            "strategy_version",
            "phase7_multi_region_discovery"
        ),

        "mock_fallback_used": result.get(
            "mock_fallback_used",
            False
        ),

        "verification_status": result.get(
            "verification_status",
            "search_result_only"
        ),

        "requested_industry": result.get(
            "requested_industry",
            industry
        ),

        "requested_region": result.get(
            "requested_region",
            region
        ),

        "search_queries": result.get(
            "search_queries",
            []
        ),

        "query_log": result.get(
            "query_log",
            []
        ),

        "search_call_count": result.get(
            "search_call_count",
            0
        ),

        "search_result_count": result.get(
            "search_result_count",
            0
        ),

        "accepted_source_hits": result.get(
            "accepted_source_hits",
            0
        ),

        "company_count": result.get(
            "company_count",
            0
        ),

        "companies": result.get(
            "companies",
            []
        ),
    }



# ============================================================
# 2. Shared real detail search
# ============================================================


def _search_company_details(
    company: str,
    query: str,
    evidence_type: str,
) -> dict:


    company = (
        company or ""
    ).strip()


    if not company:

        raise ValueError(
            "Company cannot be empty"
        )


    pages = search_checked(
        query,
        DETAIL_RESULT_COUNT,
    )


    evidence = []

    seen_urls = set()



    for page in pages:


        source = make_source(
            page,
            evidence_type=evidence_type,
            query=query,
        )


        if source is None:
            continue



        # 企业名称必须真实出现在搜索结果中
        if company not in source_text(source):
            continue



        url = source[
            "source_url"
        ]



        if url in seen_urls:
            continue



        seen_urls.add(url)

        evidence.append(
            source
        )



    return {

        "success": True,


        "data_mode": DATA_MODE,


        "provider": "bocha",


        "strategy_version":
            "phase7_real_detail_search",


        "mock_fallback_used": False,


        "company": company,


        "verification_status":
            "search_result_only",


        "search_query": query,


        "result_count":
            len(evidence),


        "results": evidence,
    }





# ============================================================
# 3. Search company news
# ============================================================


@tool
def search_company_news(
    company: str,
) -> dict:


    """
    搜索指定企业的真实扩产、
    产线及自动化新闻，
    保留网页来源。
    """


    company = (
        company or ""
    ).strip()



    if not company:

        raise ValueError(
            "Company cannot be empty"
        )



    query = (
        f'"{company}" '
        "扩产 新建产线 自动化升级 质量检测"
    )



    return _search_company_details(

        company=company,

        query=query,

        evidence_type="company_news",

    )





# ============================================================
# 4. Search company recruitment
# ============================================================


@tool
def search_company_jobs(
    company: str,
) -> dict:


    """
    搜索指定企业的真实机器视觉、
    自动化及质量检测招聘线索。
    """



    company = (
        company or ""
    ).strip()



    if not company:

        raise ValueError(
            "Company cannot be empty"
        )



    query = (
        f'"{company}" '
        "招聘 机器视觉 自动化 质量工程师"
    )



    return _search_company_details(

        company=company,

        query=query,

        evidence_type="company_job_search",

    )