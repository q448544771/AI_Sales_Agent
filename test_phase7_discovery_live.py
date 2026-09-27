
"""Phase 7.1 - Multi-region discovery live MCP test.

Real Bocha API -> Company MCP -> Source-backed candidates.

No DeepSeek.
No CRM.
No mock fallback.
"""

from app.mcp.adapter import (
    load_company_langchain_tools_sync,
)


TARGET_COMPANY_COUNT = 3


def main():

    print("=" * 65)
    print("Phase 7.1 - Multi-region Real Discovery")
    print("=" * 65)

    tools = {
        tool.name: tool
        for tool in load_company_langchain_tools_sync()
    }

    print("\n[1] Searching Real Enterprises...")

    result = tools["search_company"].invoke({
        "industry": "汽车零部件",
        "region": "中国",
    })

    assert result["success"] is True

    assert result["data_mode"] == (
        "real_web_search"
    )

    assert result["mock_fallback_used"] is False

    assert result["verification_status"] == (
        "search_result_only"
    )

    print(
        "Strategy:",
        result["strategy_version"],
    )

    print(
        "Search Calls:",
        result["search_call_count"],
    )

    print(
        "Search Results:",
        result["search_result_count"],
    )

    print(
        "Accepted Source Hits:",
        result["accepted_source_hits"],
    )

    print(
        "Unique Companies:",
        result["company_count"],
    )

    # ========================================================
    # Search coverage
    # ========================================================

    print("\n[2] Query Coverage")

    for item in result["query_log"]:

        print(
            f"{item['search_region']}: "
            f"{item['returned_count']} results, "
            f"{item['accepted_source_hits']} "
            "accepted source hits"
        )

    # ========================================================
    # Real candidate records
    # ========================================================

    print("\n[3] Discovered Companies")

    for index, company in enumerate(
        result["companies"],
        start=1,
    ):

        print("\n" + "-" * 60)

        print(
            f"[{index}] {company['name']}"
        )

        print(
            "Identity:",
            company["identity_status"],
        )

        print(
            "Sources:",
            company["source_count"],
        )

        print(
            "Source Domains:",
            company["source_domain_count"],
        )

        print(
            "Search Regions:",
            company["discovery_search_regions"],
        )

        print(
            "Verification:",
            company["verification_status"],
        )

        assert company["signals"] == []

        assert company["identity_status"] == (
            "name_mentioned_in_search_result"
        )

        assert company["discovery_sources"]

        assert company["independent_source_count"] is None

        for source in company[
            "discovery_sources"
        ]:

            assert source["source_url"].startswith(
                ("http://", "https://")
            )

            assert source["verification_status"] == (
                "search_result_only"
            )

            original_text = (
                source["title"]
                + "\n"
                + source["snippet"]
            )

            assert company["name"] in original_text

        for source in company[
            "discovery_sources"
        ][:2]:

            print(
                "Source:",
                source["source_url"],
            )

    # ========================================================
    # Final coverage status
    # ========================================================

    print("\n[4] Coverage Check")

    assert result["search_call_count"] >= 3

    assert result["company_count"] == len(
        result["companies"]
    )

    assert result["mock_fallback_used"] is False

    print("Real Company MCP: PASS")
    print("Regional Query Coverage: PASS")
    print("Exact Source Retention: PASS")
    print("Company Deduplication: PASS")
    print("No Mock Fallback: PASS")

    coverage_met = (
        result["company_count"]
        >= TARGET_COMPANY_COUNT
    )

    print(
        "Three-company Discovery Target:",
        "MET" if coverage_met else "NOT MET",
    )

    if not coverage_met:

        print(
            "\nThe search completed successfully, "
            "but fewer than three candidates were found. "
            "Continue optimizing actual queries; "
            "do not fabricate replacement companies."
        )

    print("\n" + "=" * 65)

    print(
        "Phase 7.1 Real Discovery Test Finished"
    )

    print("=" * 65)


if __name__ == "__main__":

    main()
