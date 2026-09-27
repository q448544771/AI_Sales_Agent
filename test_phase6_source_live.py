
"""Phase 6.3 - Real source-page verification integration.

Execution:
    Real Company MCP
        -> Real Web Search
        -> Original Source URLs
        -> HTML Extraction
        -> Company Name Verification
        -> Publication Date Cross-check

No mock data.
No CRM writes.
No DeepSeek calls.
"""

from app.mcp.adapter import (
    load_company_langchain_tools_sync,
)

from app.tools.source_verifier import (
    verify_company_sources,
)


EXPECTED_TOOLS = {
    "search_company",
    "get_company_news",
    "get_company_jobs",
}


def main():

    print("=" * 65)
    print("Phase 6.3 - Real Source Verification")
    print("=" * 65)

    # ========================================================
    # 1. Load actual Company MCP tools
    # ========================================================

    tools = load_company_langchain_tools_sync()

    tool_map = {
        tool.name: tool
        for tool in tools
    }

    assert set(tool_map) == EXPECTED_TOOLS

    # ========================================================
    # 2. Discover a real enterprise
    # ========================================================

    print("\n[1] Real Enterprise Discovery...")

    discovery = tool_map["search_company"].invoke({
        "industry": "汽车零部件",
        "region": "中国",
    })

    assert isinstance(
        discovery,
        dict,
    )

    assert discovery["success"] is True

    assert discovery["data_mode"] == (
        "real_web_search"
    )

    assert discovery["mock_fallback_used"] is False

    companies = discovery["companies"]

    if not companies:

        raise RuntimeError(
            "No real company discovered; "
            "mock fallback is forbidden"
        )

    company = companies[0]["name"]

    print("Company:", company)

    print(
        "Discovery Sources:",
        len(
            companies[0]["discovery_sources"]
        ),
    )

    # ========================================================
    # 3. Retrieve news and recruitment search results
    # ========================================================

    print("\n[2] Querying Real Company MCP...")

    news = tool_map["get_company_news"].invoke({
        "company": company,
    })

    jobs = tool_map["get_company_jobs"].invoke({
        "company": company,
    })

    assert news["data_mode"] == (
        "real_web_search"
    )

    assert jobs["data_mode"] == (
        "real_web_search"
    )

    assert news["company"] == company

    assert jobs["company"] == company

    print(
        "News Search Results:",
        news["result_count"],
    )

    print(
        "Job Search Results:",
        jobs["result_count"],
    )

    # ========================================================
    # 4. Fetch original source pages
    # ========================================================

    print("\n[3] Fetching Original Web Pages...")

    report = verify_company_sources(
        company,
        news,
        jobs,
        max_news=3,
        max_jobs=2,
    )

    print(
        "Checked Pages:",
        report["pages_checked"],
    )

    print(
        "Article Name Matches:",
        report["article_match_count"],
    )

    print(
        "Date Conflicts:",
        report["date_conflict_count"],
    )

    # ========================================================
    # 5. Print source-level verification results
    # ========================================================

    for index, result in enumerate(
        report["results"],
        start=1,
    ):

        print("\n" + "-" * 60)

        print(
            f"Source #{index}"
        )

        print(
            "URL:",
            result["source_url"],
        )

        print(
            "Final URL:",
            result["final_url"],
        )

        print(
            "Page Title:",
            result["page_title"],
        )

        print(
            "Fetch Status:",
            result["source_fetch_status"],
        )

        print(
            "Identity Check:",
            result["identity_check"],
        )

        print(
            "Article Selector:",
            result["article_selector"],
        )

        print(
            "Detected Type:",
            result["detected_type"],
        )

        print(
            "Category Check:",
            result["category_check"],
        )

        print(
            "Page Date:",
            result["page_published_at"],
        )

        print(
            "Date Origin:",
            result["page_date_origin"],
        )

        print(
            "URL Date Hint:",
            result["url_date_hint"],
        )

        print(
            "Date Conflict:",
            result["date_conflict_with_url_hint"],
        )

        if result["error"]:

            print(
                "Error:",
                result["error"],
            )

        if result["candidate_quotes"]:

            print("\nLiteral Candidate Quotes:")

            for quote in result[
                "candidate_quotes"
            ][:3]:

                print(
                    "-",
                    quote["quote"],
                )

                print(
                    "  Signal Types:",
                    quote["signal_types"],
                )

                print(
                    "  Quote Status:",
                    quote["quote_status"],
                )

    # ========================================================
    # 6. Reliability assertions
    # ========================================================

    print("\n[4] Reliability Assertions")

    assert report["company"] == company

    assert report["data_mode"] == (
        "real_source_page"
    )

    assert report["mock_fallback_used"] is False

    assert report["pages_checked"] <= 5

    assert report["independent_source_count"] is None

    assert report["date_conflict_count"] == sum(
        bool(item["date_conflict_with_url_hint"])
        for item in report["results"]
    )

    assert all(
        item["source_url"]
        for item in report["results"]
    )

    # A quote must mention the selected company explicitly.
    for page in report["results"]:

        for quote in page["candidate_quotes"]:

            assert company in quote["quote"]

            assert quote["quote_status"] == (
                "literal_page_excerpt_requires_review"
            )

            assert quote["signal_types"]

    print("Real MCP Discovery: PASS")
    print("Actual HTML Fetch Attempt: PASS")
    print("Original URL Preservation: PASS")
    print("Publication Date Cross-check: PASS")
    print("Company-specific Quote Validation: PASS")
    print("News / Recruitment Classification: PASS")
    print("No Mock Fallback: PASS")

    # ========================================================
    # 7. Require at least one actual article match
    # ========================================================

    if report["article_match_count"] == 0:

        raise AssertionError(
            "No original article passed company-name "
            "and category verification. "
            "Inspect the extraction results; "
            "do not replace them with search snippets."
        )

    print(
        "\nAt least one original article contains "
        "the complete company name."
    )

    print("\n" + "=" * 65)

    print(
        "Phase 6.3 Source Verification Test Passed"
    )

    print("=" * 65)


if __name__ == "__main__":

    main()
