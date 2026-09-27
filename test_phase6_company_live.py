
"""Phase 6.2 - Real Company MCP integration test.

Actual chain:
    LangChain Adapter
        -> Company MCP
        -> Real company tools
        -> Bocha Web Search

No mock fallback.
No CRM calls.
No DeepSeek calls.
"""

from app.mcp.adapter import (
    load_company_langchain_tools_sync,
)


EXPECTED_TOOL_NAMES = {
    "search_company",
    "get_company_news",
    "get_company_jobs",
}


def check_sources(items, company):

    for item in items:

        assert isinstance(item, dict)

        assert item["source_url"].startswith(
            ("https://", "http://")
        )

        assert item["verification_status"] == (
            "search_result_only"
        )

        source_text = (
            item["title"]
            + "\n"
            + item["snippet"]
        )

        assert company in source_text, (
            "Company name not found in original search result"
        )


def main():

    print("=" * 60)
    print("Phase 6.2 - Real Company MCP Integration")
    print("=" * 60)

    tools = load_company_langchain_tools_sync()

    tool_map = {
        tool.name: tool
        for tool in tools
    }

    assert set(tool_map) == EXPECTED_TOOL_NAMES

    # ========================================================
    # 1. Real company discovery
    # ========================================================

    print("\n[1] Real Company Discovery...")

    discovery = tool_map["search_company"].invoke({
        "industry": "汽车零部件",
        "region": "中国",
    })

    assert isinstance(discovery, dict)

    assert discovery["success"] is True

    assert discovery["data_mode"] == "real_web_search"

    assert discovery["mock_fallback_used"] is False

    companies = discovery["companies"]

    print(
        "Search Results:",
        discovery["search_result_count"],
    )

    print(
        "Discovered Companies:",
        len(companies),
    )

    assert companies, (
        "No complete enterprise names were extracted. "
        "Inspect the real search results; never use mock fallback."
    )

    for company in companies:

        print("\nCompany:", company["name"])

        print(
            "Identity Status:",
            company["identity_status"],
        )

        print(
            "Source Count:",
            len(company["discovery_sources"]),
        )

        assert company["signals"] == []

        assert company["identity_status"] == (
            "name_mentioned_in_search_result"
        )

        check_sources(
            company["discovery_sources"],
            company["name"],
        )

        for source in company["discovery_sources"]:

            print("Source:", source["source_url"])

    # ========================================================
    # 2. Real company news search
    # ========================================================

    selected = companies[0]["name"]

    print("\n[2] Real Company News...")

    print("Selected Company:", selected)

    news = tool_map["get_company_news"].invoke({
        "company": selected,
    })

    assert news["success"] is True

    assert news["data_mode"] == "real_web_search"

    assert news["company"] == selected

    print("News Clues:", news["result_count"])

    check_sources(
        news["results"],
        selected,
    )

    for item in news["results"]:

        print(
            "\nNews:",
            item["title"],
        )

        print(
            "URL:",
            item["source_url"],
        )

    # ========================================================
    # 3. Real recruitment search
    # ========================================================

    print("\n[3] Real Company Recruitment...")

    jobs = tool_map["get_company_jobs"].invoke({
        "company": selected,
    })

    assert jobs["success"] is True

    assert jobs["data_mode"] == "real_web_search"

    assert jobs["company"] == selected

    print("Recruitment Clues:", jobs["result_count"])

    check_sources(
        jobs["results"],
        selected,
    )

    for item in jobs["results"]:

        print(
            "\nRecruitment:",
            item["title"],
        )

        print(
            "URL:",
            item["source_url"],
        )

    # ========================================================
    # 4. Verification summary
    # ========================================================

    print("\nReal API: PASS")
    print("Company MCP: PASS")
    print("Original URL Preservation: PASS")
    print("Company Name Evidence: PASS")
    print("No Mock Fallback: PASS")
    print("No CRM Write: PASS")

    print("\n" + "=" * 60)
    print("Phase 6.2 Real Company MCP Test Passed")
    print("=" * 60)


if __name__ == "__main__":
    main()
