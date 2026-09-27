
"""
Phase 6.3.3 - Real Research Agent.

Pipeline:

    Real Company MCP
        -> Company Discovery
        -> News / Recruitment Discovery
        -> Original HTML Verification
        -> Literal Evidence Extraction
        -> Structured Research Output

No mock data.
No CRM access.
No outbound messages.
No LLM-generated enterprise facts.
"""

import json

from collections.abc import Mapping
from typing import Any

from app.mcp.adapter import (
    load_company_langchain_tools_sync,
)

from app.tools.source_verifier import (
    verify_company_sources,
)

from app.tools.company_verifier import (
    verify_company,
)


DATA_MODE = "real_source_page"

REQUIRED_TOOLS = {
    "search_company",
    "get_company_news",
    "get_company_jobs",
}


class RealResearchError(RuntimeError):
    pass


# ============================================================
# 1. Decode MCP output
# ============================================================

def _decode_result(value: Any) -> Any:

    if isinstance(value, str):

        try:

            value = json.loads(
                value.strip()
            )

        except json.JSONDecodeError:

            raise RealResearchError(
                "Company MCP returned non-JSON text"
            )

    if (
        isinstance(value, dict)
        and set(value.keys()) == {"result"}
    ):

        value = value["result"]

    return value


def _invoke_real_tool(
    tool,
    arguments: dict,
) -> dict:

    try:

        result = _decode_result(
            tool.invoke(arguments)
        )

    except Exception as exc:

        raise RealResearchError(
            f"Real MCP tool {tool.name} failed"
        ) from exc

    if not isinstance(result, dict):

        raise RealResearchError(
            f"{tool.name} returned malformed data"
        )

    if result.get("success") is not True:

        raise RealResearchError(
            f"{tool.name} did not report success"
        )

    if result.get("data_mode") != "real_web_search":

        raise RealResearchError(
            f"{tool.name} returned non-real data"
        )

    if result.get("mock_fallback_used", False) is not False:

        raise RealResearchError(
            "Mock fallback is forbidden"
        )

    return result


# ============================================================
# 2. Parse SalesGoal
# ============================================================

def _goal_dict(state: Mapping[str, Any]) -> dict:

    goal = state.get("goal")

    if hasattr(goal, "model_dump"):

        goal = goal.model_dump()

    if not isinstance(goal, Mapping):

        raise ValueError(
            "Research requires a valid SalesGoal"
        )

    industry = str(
        goal.get("target_industry") or ""
    ).strip()

    region = str(
        goal.get("target_region") or ""
    ).strip()

    target_count = goal.get(
        "target_count",
        3,
    )

    if not industry or not region:

        raise ValueError(
            "Target industry and region are required"
        )

    if (
        isinstance(target_count, bool)
        or not isinstance(target_count, int)
        or not 1 <= target_count <= 20
    ):

        raise ValueError(
            "target_count must be between 1 and 20"
        )

    return {
        "industry": industry,
        "region": region,
        "target_count": target_count,
    }


# ============================================================
# 3. Validate real company discovery
# ============================================================

def _real_company_candidates(
    discovery: dict,
) -> list[dict]:

    if discovery.get("verification_status") != (
        "search_result_only"
    ):

        raise RealResearchError(
            "Unexpected discovery verification status"
        )

    companies = discovery.get("companies")

    if not isinstance(companies, list):

        raise RealResearchError(
            "Malformed real company candidates"
        )

    candidates = []
    seen_names = set()

    for item in companies:

        if not isinstance(item, dict):
            continue

        name = item.get("name")

        sources = item.get(
            "discovery_sources"
        )

        if (
            not isinstance(name, str)
            or not name.strip()
            or not isinstance(sources, list)
            or not sources
        ):
            continue

        name = name.strip()

        # At least one actual search result must
        # explicitly mention the complete company name.

        valid_sources = []

        for source in sources:

            if not isinstance(source, dict):
                continue

            if source.get("verification_status") != (
                "search_result_only"
            ):
                continue

            title = str(
                source.get("title") or ""
            )

            snippet = str(
                source.get("snippet") or ""
            )

            url = source.get(
                "source_url"
            )

            if not isinstance(url, str):
                continue

            if not url.startswith(
                ("http://", "https://")
            ):
                continue

            if name not in (
                title + "\n" + snippet
            ):
                continue

            valid_sources.append(source)

        if not valid_sources:
            continue

        if name in seen_names:
            continue

        seen_names.add(name)

        candidates.append({
            "company": name,
            "profile": {
                "name": name,
                "identity_status": (
                    "name_mentioned_in_search_result"
                ),
                "requested_industry": item.get(
                    "requested_industry"
                ),
                "requested_region": item.get(
                    "requested_region"
                ),
                "discovery_sources": valid_sources,
            },
        })

    return candidates


# ============================================================
# 4. Validate source evidence
# ============================================================

def _extract_verified_evidence(
    company: str,
    verification_report: dict,
) -> list[dict]:

    evidence = []
    seen = set()

    pages = verification_report.get(
        "results",
        [],
    )

    if not isinstance(pages, list):

        raise RealResearchError(
            "Malformed source verification report"
        )

    for page in pages:

        if not isinstance(page, dict):
            continue

        # Both checks must pass. Body-only company mentions
        # never become verified article evidence.

        if page.get("source_fetch_status") != (
            "article_name_match"
        ):
            continue

        if page.get("category_check") != (
            "category_consistent"
        ):
            continue

        source_url = page.get(
            "final_url"
        ) or page.get(
            "source_url"
        )

        if not isinstance(source_url, str):
            continue

        if not source_url.startswith(
            ("http://", "https://")
        ):
            continue

        date_conflict = bool(
            page.get(
                "date_conflict_with_url_hint"
            )
        )

        # A conflicting publication date is never
        # promoted as a trusted publication field.

        publication_date = (
            None
            if date_conflict
            else page.get("page_published_at")
        )

        for candidate in page.get(
            "candidate_quotes",
            [],
        ):

            if not isinstance(candidate, dict):
                continue

            quote = candidate.get(
                "quote"
            )

            signal_types = candidate.get(
                "signal_types"
            )

            if (
                not isinstance(quote, str)
                or company not in quote
                or not isinstance(signal_types, list)
                or not signal_types
            ):
                continue

            if candidate.get("quote_status") != (
                "literal_page_excerpt_requires_review"
            ):
                continue

            key = (
                source_url,
                quote,
            )

            if key in seen:
                continue

            seen.add(key)

            evidence.append({
                "company": company,

                "quote": quote,

                "signal_types": signal_types,

                "source_url": source_url,

                "source_title": page.get(
                    "page_title"
                ),

                "source_type": page.get(
                    "requested_type"
                ),

                "published_at": publication_date,

                "date_origin": (
                    None
                    if date_conflict
                    else page.get(
                        "page_date_origin"
                    )
                ),

                "url_date_hint": page.get(
                    "url_date_hint"
                ),

                "date_conflict": date_conflict,

                "article_selector": page.get(
                    "article_selector"
                ),

                "verification_status": (
                    "literal_quote_from_article"
                ),

                # This is a page-level text match,
                # not verified company registration,
                # purchase intention or buying budget.
                "requires_human_review": True,
            })

    return evidence


# ============================================================
# 5. Real Research execution
# ============================================================

def run_real_research(
    state: Mapping[str, Any],
    *,
    tools=None,
    max_companies: int = 3,
    max_news_per_company: int = 3,
    max_jobs_per_company: int = 2,
) -> dict:

    if (
        isinstance(max_companies, bool)
        or not isinstance(max_companies, int)
        or max_companies < 1
    ):

        raise ValueError(
            "max_companies must be positive"
        )

    if (
        max_news_per_company < 0
        or max_jobs_per_company < 0
    ):

        raise ValueError(
            "Source limits must be nonnegative"
        )

    goal = _goal_dict(
        state
    )

    # --------------------------------------------------------
    # 1. Load real Company MCP tools
    # --------------------------------------------------------

    loaded_tools = (
        list(tools)
        if tools is not None
        else load_company_langchain_tools_sync()
    )

    tool_map = {
        tool.name: tool
        for tool in loaded_tools
    }

    if not REQUIRED_TOOLS.issubset(
        tool_map
    ):

        missing = REQUIRED_TOOLS - set(
            tool_map
        )

        raise RealResearchError(
            f"Missing Company MCP tools: {sorted(missing)}"
        )

    # --------------------------------------------------------
    # 2. Discover actual enterprises
    # --------------------------------------------------------

    discovery = _invoke_real_tool(
        tool_map["search_company"],
        {
            "industry": goal["industry"],
            "region": goal["region"],
        },
    )

    candidates = _real_company_candidates(
        discovery
    )

    target_limit = min(
        goal["target_count"],
        max_companies,
    )

    selected_candidates = candidates[
        :target_limit
    ]
    # --------------------------------------------------------
    # 2.5 Company identity verification
    # --------------------------------------------------------

    verified_candidates = []

    for candidate in selected_candidates:

        verification = verify_company(
            candidate["profile"]
        )


        if (
            verification.get(
                "verification_status"
            )
            != "verified_company"
        ):
            continue


        candidate["company_verification"] = (
            verification
        )


        verified_candidates.append(
            candidate
        )


    selected_candidates = verified_candidates
    company_records = []
    all_evidence = []
    review_only_sources = []

    tool_trace = [{
        "tool": "search_company",
        "source": "real_company_mcp",
        "candidate_count": len(candidates),
    }]

    # --------------------------------------------------------
    # 3. Query news and recruitment per company
    # --------------------------------------------------------

    for candidate in selected_candidates:

        company = candidate["company"]

        news = _invoke_real_tool(
            tool_map["get_company_news"],
            {
                "company": company,
            },
        )

        jobs = _invoke_real_tool(
            tool_map["get_company_jobs"],
            {
                "company": company,
            },
        )

        if (
            news.get("company") != company
            or jobs.get("company") != company
        ):

            raise RealResearchError(
                "Company identity mismatch in MCP detail result"
            )

        tool_trace.extend([
            {
                "tool": "get_company_news",
                "company": company,
                "source": "real_company_mcp",
                "result_count": news.get(
                    "result_count"
                ),
            },
            {
                "tool": "get_company_jobs",
                "company": company,
                "source": "real_company_mcp",
                "result_count": jobs.get(
                    "result_count"
                ),
            },
        ])

        # ----------------------------------------------------
        # 4. Verify the original HTML pages
        # ----------------------------------------------------

        report = verify_company_sources(
            company,
            news,
            jobs,
            max_news=max_news_per_company,
            max_jobs=max_jobs_per_company,
        )

        if report.get("data_mode") != DATA_MODE:

            raise RealResearchError(
                "Invalid source-page verification mode"
            )

        if report.get("mock_fallback_used") is not False:

            raise RealResearchError(
                "Source verifier used mock fallback"
            )

        verified_evidence = (
            _extract_verified_evidence(
                company,
                report,
            )
        )

        all_evidence.extend(
            verified_evidence
        )

        # Preserve failed/body-only pages for review,
        # but never place them into verified evidence.

        for page in report["results"]:

            if not (
                page.get("source_fetch_status")
                == "article_name_match"
                and page.get("category_check")
                == "category_consistent"
            ):

                review_only_sources.append({
                    "company": company,
                    "source_url": page.get(
                        "source_url"
                    ),
                    "source_fetch_status": page.get(
                        "source_fetch_status"
                    ),
                    "category_check": page.get(
                        "category_check"
                    ),
                    "error": page.get(
                        "error"
                    ),
                })

        company_records.append({

            "company": company,


            "company_verification":
                candidate.get(
                    "company_verification"
                ),


            "profile":
                candidate["profile"],

            # These are structured, source-backed records.
            # They are NOT Phase 5's mock text lists.
            "verified_evidence": verified_evidence,

            "verification_report": report,

            "evidence_count": len(
                verified_evidence
            ),

            "identity_status": (
                "source_article_name_match"
                if report["article_match_count"] > 0
                else "search_result_only"
            ),
        })

        tool_trace.append({
            "tool": "verify_company_sources",
            "company": company,
            "source": "real_original_html",
            "pages_checked": report["pages_checked"],
            "article_match_count": report[
                "article_match_count"
            ],
            "evidence_count": len(
                verified_evidence
            ),
        })

    # --------------------------------------------------------
    # 5. Research output
    # --------------------------------------------------------

    verified_companies = {
        item["company"]
        for item in all_evidence
    }

    status = (

    "complete"

    if selected_candidates
       and all_evidence

    else "insufficient_evidence"

    )

    return {
        "research_output": {
            "status": status,

            "data_mode": DATA_MODE,

            "provider": "bocha_via_company_mcp",

            "mock_fallback_used": False,

            "company_records": company_records,

            "verified_evidence": all_evidence,

            "review_only_sources": review_only_sources,

            "tool_trace": tool_trace,

            "discovered_company_count": len(
                candidates
            ),
            
            "identity_verified_company_count":len(
                selected_candidates
            ),

            "researched_company_count": len(
                company_records
            ),

            "verified_company_count": len(
                verified_companies
            ),

            "verified_evidence_count": len(
                all_evidence
            ),

            "requested_target_count": goal[
                "target_count"
            ],

            "target_met": (
                len(verified_companies)
                >= goal["target_count"]
            ),

            "independent_source_count": None,

            "requires_human_review": True,

            "crm_write_performed": False,

            "send_performed": False,
        }
    }


# ============================================================
# 6. LangGraph Worker entrypoint
# ============================================================

def real_research_agent_node(
    state: Mapping[str, Any],
) -> dict:

    return run_real_research(
        state
    )
