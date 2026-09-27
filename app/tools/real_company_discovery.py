
"""Phase 7.1 - Multi-query real company discovery.

Uses the existing Bocha search provider.

No hard-coded company database.
No mock fallback.
No inferred registration region.
No claim that distinct URLs are independent evidence.

Discovery results remain search_result_only until original
web pages are fetched and verified by Phase 6 source_verifier.
"""

import re

from datetime import datetime
from urllib.parse import urlsplit

from app.tools.real_web_search import search_real_web


DATA_MODE = "real_web_search"
MAX_CANDIDATES = 12
RESULTS_PER_QUERY = 8


INDUSTRY_TERMS = (
    "汽车",
    "汽配",
    "零部件",
    "车身",
    "新能源汽车",
    "车辆",
)

SIGNAL_TERMS = (
    "扩产",
    "扩建",
    "产能",
    "产线",
    "生产线",
    "自动化",
    "智能制造",
    "新工厂",
    "生产基地",
    "投产",
    "技改",
    "质量检测",
    "品检",
    "质检",
    "机器视觉",
    "招聘",
)

COMPANY_PATTERN = re.compile(
    r"[\u4e00-\u9fffA-Za-z0-9·（）()]{2,42}?"
    r"(?:股份有限公司|有限责任公司|集团有限公司|有限公司)"
)

SPLIT_PATTERN = re.compile(
    r"[，,。；;：:\n\r\t【】\[\]“”\"'!?！？]"
    r"|(?:20\d{2}年)?\d{1,2}月\d{1,2}日"
)

NOISE_PREFIXES = (
    "连日来",
    "据了解",
    "据悉",
    "近日",
    "日前",
    "目前",
    "工作人员",
    "记者看到",
    "记者",
    "企业名称",
    "公司名称",
    "该企业",
    "该公司",
    "图为",
    "位于",
    "在",
    "由",
    "与",
    "向",
    "为",
    "是",
)

INVALID_NAMES = (
    "研究报告",
    "发展报告",
    "咨询报告",
    "规划方案",
    "官方网站",
)


# ============================================================
# 1. Search-provider validation
# ============================================================

def search_checked(query: str, count: int = 8) -> list[dict]:

    response = search_real_web(
        query=query,
        count=count,
        freshness="oneYear",
    )

    if not isinstance(response, dict):
        raise RuntimeError(
            "Real search returned invalid data"
        )

    if response.get("success") is not True:
        raise RuntimeError(
            f"Real search failed: {query}"
        )

    if response.get("data_mode") != DATA_MODE:
        raise RuntimeError(
            "Unexpected company search data mode"
        )

    if response.get("mock_fallback_used") is not False:
        raise RuntimeError(
            "Mock fallback is forbidden"
        )

    results = response.get("results")

    if not isinstance(results, list):
        raise RuntimeError(
            "Search results must be a list"
        )

    return results


# ============================================================
# 2. Source normalization
# ============================================================

def make_source(
    page: dict,
    *,
    evidence_type: str,
    query: str,
    search_region: str = "",
) -> dict | None:

    if not isinstance(page, dict):
        return None

    url = page.get("source_url")

    if not isinstance(url, str):
        return None

    try:
        parsed = urlsplit(url.strip())

    except ValueError:
        return None

    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
    ):
        return None

    return {
        "evidence_type": evidence_type,

        "title": str(
            page.get("title") or ""
        ),

        "source_url": url.strip(),

        "publisher": str(
            page.get("publisher") or ""
        ),

        "snippet": str(
            page.get("snippet") or ""
        ),

        "published_at": page.get(
            "published_at"
        ),

        "retrieved_at": page.get(
            "retrieved_at"
        ),

        "search_query": (
            page.get("search_query")
            or query
        ),

        "provider": page.get(
            "provider",
            "bocha",
        ),

        "search_region": search_region,

        "verification_status": (
            "search_result_only"
        ),
    }


def source_text(source: dict) -> str:

    return (
        str(source.get("title") or "")
        + "\n"
        + str(source.get("snippet") or "")
    )


# ============================================================
# 3. Extract only literally present company names
# ============================================================

def _clean_name(raw: str) -> str:
    """
    清洗搜索结果中的企业名称。

    目标:
    1. 删除网页标题噪声
    2. 删除语义前缀
    3. 保留真实企业主体名称
    """

    if not raw:
        return ""

    name = raw.strip()


    # --------------------------------
    # 1. 删除编号
    # --------------------------------

    name = re.sub(
        r"^[\d０-９一二三四五六七八九十]+[\.\、\s\-：:]*",
        "",
        name,
    )


    # --------------------------------
    # 2. 删除标题噪声和语义前缀
    # --------------------------------

    prefixes = [

        "审批公示",
        "项目公示",
        "环评公示",
        "建设项目",

        "公告",
        "通知",
        "图文",
        "新闻",
        "招聘",
        "招工",

        "企业",

        # 新增
        "在",
        "位于",
        "来自",
        "据了解",
        "据悉",
        "近日",
        "日前",
        "目前",
        "记者",
        "工作人员",
        "其中",
    ]


    changed = True

    while changed:

        changed = False

        for prefix in prefixes:

            if name.startswith(prefix):

                name = (
                    name[len(prefix):]
                    .strip()
                )

                changed = True



    # --------------------------------
    # 3. 截断到企业主体
    # --------------------------------

    match = re.search(
        r".*?(股份有限公司|有限责任公司|集团有限公司|有限公司)",
        name,
    )

    if match:

        name = match.group(0)



    # --------------------------------
    # 4. 去除残余空格
    # --------------------------------

    name = re.sub(
        r"\s+",
        "",
        name,
    )


    return name

def extract_company_names(text: str) -> list[str]:

    if not isinstance(text, str):
        return []

    names = []


    segments = SPLIT_PATTERN.split(
        text
    )


    for segment in segments:

        for match in COMPANY_PATTERN.finditer(segment):

            name = _clean_name(
                match.group()
            )


            if not 5 <= len(name) <= 45:
                continue


            if any(
                invalid in name
                for invalid in INVALID_NAMES
            ):
                continue


            # 企业主体必须完整出现在文本
            if name not in text:
                continue


            if name not in names:
                names.append(name)


    return names


# ============================================================
# 4. Multi-region search strategy
# ============================================================

def build_discovery_queries(
    industry: str,
    region: str,
) -> list[tuple[str, str]]:

    industry = (
        industry or ""
    ).strip()

    region = (
        region or ""
    ).strip()

    if not industry or not region:

        raise ValueError(
            "Industry and region are required"
        )

    year = datetime.now().year

    nationwide = {
        "中国",
        "全国",
        "全国范围",
    }

    if region not in nationwide:

        return [
            (
                region,
                f"{region} {industry} {year} "
                "企业 扩产 新建生产线",
            ),
            (
                region,
                f"{region} {industry} {year} "
                "企业 自动化升级 智能制造 技改",
            ),
            (
                region,
                f"{region} 汽车零部件 企业 "
                "新工厂 投产 质量检测 招聘",
            ),
        ]

    # Phase 7.1:
    # Regional diversification rather than searching
    # the same nationwide wording repeatedly.
    #
    # These are search scopes, NOT confirmed company
    # registration locations.

    return [
        (
            "全国",
            f"中国 {industry} {year} "
            "企业 新建生产线 扩产",
        ),
        (
            "全国",
            f"汽车零部件企业 {year} "
            "智能制造 自动化改造 新工厂",
        ),
        (
            "浙江",
            f"浙江 汽车零部件 {year} "
            "扩产 新建产线 企业",
        ),
        (
            "广东",
            f"广东 汽车零部件 {year} "
            "智能制造 自动化升级 企业",
        ),
        (
            "江苏",
            f"江苏 汽车零部件 {year} "
            "新工厂 新建生产线 企业",
        ),
        (
            "湖北",
            f"湖北 汽车零部件 {year} "
            "扩产 智能生产线 企业",
        ),
        (
            "安徽",
            f"安徽 汽车零部件 {year} "
            "生产基地 技改 自动化 企业",
        ),
        (
            "广西",
            f"广西 汽车零部件 {year} "
            "生产基地 产线 扩建 企业",
        ),
    ]


# ============================================================
# 5. Candidate discovery and deduplication
# ============================================================

def discover_companies(
    industry: str,
    region: str,
    *,
    max_candidates: int = MAX_CANDIDATES,
) -> dict:

    if (
        isinstance(max_candidates, bool)
        or not isinstance(max_candidates, int)
        or max_candidates < 1
    ):
        raise ValueError(
            "max_candidates must be positive"
        )

    queries = build_discovery_queries(
        industry,
        region,
    )

    companies = {}
    search_queries = []
    query_log = []

    search_result_count = 0
    accepted_source_hits = 0

    for search_region, query in queries:

        pages = search_checked(
            query,
            RESULTS_PER_QUERY,
        )

        search_queries.append(
            query
        )

        search_result_count += len(
            pages
        )

        accepted_this_query = 0

        for page in pages:

            source = make_source(
                page,
                evidence_type="company_discovery",
                query=query,
                search_region=search_region,
            )

            if source is None:
                continue

            text = source_text(
                source
            )

            # Search results must visibly mention
            # the target industry and at least one
            # buying-signal-related expression.
            #
            # This is a discovery heuristic, not
            # article-level confirmation.
            if not any(
                term in text
                for term in INDUSTRY_TERMS
            ):
                continue

            if not any(
                term in text
                for term in SIGNAL_TERMS
            ):
                continue

            names = extract_company_names(
                text
            )

            for name in names:

                if name not in companies:

                    companies[name] = {
                        "name": name,

                        # Do not infer registration facts
                        # from the query or article alone.
                        "industry": None,
                        "region": None,

                        "requested_industry": industry,
                        "requested_region": region,

                        "signals": [],

                        "identity_status": (
                            "name_mentioned_in_search_result"
                        ),

                        "discovery_sources": [],

                        "discovery_queries": [],

                        "discovery_search_regions": [],
                    }

                candidate = companies[
                    name
                ]

                existing_urls = {
                    item["source_url"]
                    for item in candidate[
                        "discovery_sources"
                    ]
                }

                # Every URL is kept only once per company.
                if source["source_url"] not in existing_urls:

                    candidate[
                        "discovery_sources"
                    ].append(source)

                    accepted_source_hits += 1
                    accepted_this_query += 1

                if query not in candidate[
                    "discovery_queries"
                ]:

                    candidate[
                        "discovery_queries"
                    ].append(query)

                if search_region not in candidate[
                    "discovery_search_regions"
                ]:

                    candidate[
                        "discovery_search_regions"
                    ].append(search_region)

        query_log.append({
            "search_region": search_region,
            "query": query,
            "returned_count": len(pages),
            "accepted_source_hits": accepted_this_query,
        })

    # Prefer repeated discovery across search queries
    # and retain all source URLs.
    #
    # This does NOT mean that a republished report
    # provides independent corroboration.

    results = sorted(
        companies.values(),
        key=lambda item: (
            -len(item["discovery_queries"]),
            -len(item["discovery_sources"]),
            item["name"],
        ),
    )[:max_candidates]

    for item in results:

        domains = {
            urlsplit(
                source["source_url"]
            ).hostname
            for source in item["discovery_sources"]
        }

        item["source_count"] = len(
            item["discovery_sources"]
        )

        item["source_domain_count"] = len(
            domains
        )

        item["independent_source_count"] = None

        item["verification_status"] = (
            "search_result_only"
        )

    return {
        "success": True,

        "data_mode": DATA_MODE,

        "provider": "bocha",

        "strategy_version":
            "phase7_multi_region_discovery",

        "mock_fallback_used": False,

        "verification_status":
            "search_result_only",

        "requested_industry": industry,

        "requested_region": region,

        "search_queries": search_queries,

        "query_log": query_log,

        "search_call_count":
            len(search_queries),

        "search_result_count":
            search_result_count,

        "accepted_source_hits":
            accepted_source_hits,

        "company_count":
            len(results),

        "companies": results,
    }
