
"""Phase 6.3.3 - Real Research Agent integration.

No fake companies.
No mock search results.
No DeepSeek-generated research facts.
No CRM operations.
"""

from app.multi_agent.real_research_agent import (
    run_real_research,
)


def main():

    print("=" * 65)
    print("Phase 6.3.3 - Real Research Agent")
    print("=" * 65)

    state = {
        "goal": {
            "target_industry": "汽车零部件",
            "target_region": "中国",
            "target_count": 1,
            "product_focus": "工业机器视觉质检解决方案",
            "user_requirement": (
                "寻找近期扩产、新建生产线或自动化升级的"
                "真实汽车零部件企业，并保留原始证据。"
            ),
        },
    }

    print("\n[1] Starting Real Research...")

    result = run_real_research(
        state,
        max_companies=1,
        max_news_per_company=3,
        max_jobs_per_company=2,
    )

    research = result["research_output"]

    print("\n[2] Research Statistics")

    print("Status:", research["status"])

    print("Data Mode:", research["data_mode"])

    print(
        "Discovered Companies:",
        research["discovered_company_count"],
    )

    print(
        "Researched Companies:",
        research["researched_company_count"],
    )

    print(
        "Verified Companies:",
        research["verified_company_count"],
    )

    print(
        "Verified Evidence:",
        research["verified_evidence_count"],
    )

    print(
        "Review-only Sources:",
        len(research["review_only_sources"]),
    )

    print(
        "Target Met:",
        research["target_met"],
    )

    print(
        "Mock Fallback:",
        research["mock_fallback_used"],
    )

    # ========================================================
    # 3. Actual research records
    # ========================================================

    print("\n[3] Company Records")

    for record in research["company_records"]:

        print("\n" + "-" * 60)

        print("Company:", record["company"])

        print(
            "Identity Status:",
            record["identity_status"],
        )

        print(
            "Evidence Count:",
            record["evidence_count"],
        )

        for item in record["verified_evidence"]:

            print("\nLiteral Evidence:")

            print(
                "Quote:",
                item["quote"],
            )

            print(
                "Types:",
                item["signal_types"],
            )

            print(
                "Source:",
                item["source_url"],
            )

            print(
                "Published:",
                item["published_at"],
            )

            print(
                "Verification:",
                item["verification_status"],
            )

    # ========================================================
    # 4. Evidence reliability
    # ========================================================

    print("\n[4] Reliability Assertions")

    assert research["data_mode"] == (
        "real_source_page"
    )

    assert research["mock_fallback_used"] is False

    assert research["crm_write_performed"] is False

    assert research["send_performed"] is False

    assert research["requires_human_review"] is True

    assert research["independent_source_count"] is None

    assert research["researched_company_count"] <= 1

    assert research["verified_evidence_count"] == len(
        research["verified_evidence"]
    )

    # For this live integration, require at least one
    # real source-backed literal evidence record.
    # Never generate placeholder evidence to pass.

    assert research["verified_evidence_count"] >= 1, (
        "No verified original-page evidence was retrieved"
    )

    assert research["status"] == "complete"

    for item in research["verified_evidence"]:

        assert item["company"] in item["quote"]

        assert item["source_url"].startswith(
            ("https://", "http://")
        )

        assert item["verification_status"] == (
            "literal_quote_from_article"
        )

        assert item["signal_types"]

        assert item["requires_human_review"] is True

    print("Real Company MCP: PASS")
    print("Original Page Verification: PASS")
    print("Literal Evidence Extraction: PASS")
    print("Source URL Preservation: PASS")
    print("Publication Date Handling: PASS")
    print("No Mock Data: PASS")
    print("No CRM Write: PASS")
    print("No Message Sending: PASS")

    print("\n" + "=" * 65)

    print(
        "Phase 6.3.3 Real Research Integration Passed"
    )

    print("=" * 65)


if __name__ == "__main__":
    main()
