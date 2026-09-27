"""
Phase 6.1 - Live Real Search Test.

Requires a real BOCHA_API_KEY.
Does not use any mock company data.
"""

import json

from app.tools.real_web_search import search_real_web


def main():

    print("=" * 60)
    print("Phase 6.1 - Real Enterprise Search")
    print("=" * 60)

    result = search_real_web(
        query=(
            "2026 汽车零部件企业 "
            "扩产 新建生产线 自动化升级"
        ),
        count=5,
        freshness="oneYear",
    )

    print("\nProvider:", result["provider"])

    print("Data Mode:", result["data_mode"])

    print("Result Count:", result["result_count"])

    print(
        "Mock Fallback:",
        result["mock_fallback_used"],
    )

    print("\nActual Search Results:\n")

    for index, page in enumerate(
        result["results"],
        start=1,
    ):

        print(f"\n[{index}] {page['title']}")

        print("URL:", page["source_url"])

        print("Publisher:", page["publisher"])

        print("Published:", page["published_at"])

        print("Snippet:", page["snippet"])

        print(
            "Verification:",
            page["verification_status"],
        )

    assert result["success"] is True

    assert result["data_mode"] == "real_web_search"

    assert result["mock_fallback_used"] is False

    assert result["result_count"] == len(
        result["results"]
    )

    assert all(
        page["source_url"].startswith(
            ("http://", "https://")
        )
        for page in result["results"]
    )

    assert all(
        page["verification_status"]
        == "search_result_only"
        for page in result["results"]
    )

    print("\n" + "=" * 60)

    print("Phase 6.1 Real Search Test Passed")

    print("=" * 60)


if __name__ == "__main__":
    main()