
"""Phase 6.4 - Real Research + Knowledge + Analysis.

Live execution:
    Real Company MCP
    Original HTML verifier
    Internal Knowledge MCP
    DeepSeek reasoning

No mocked enterprise data.
No CRM writes.
No outbound messages.
"""

from app.multi_agent.real_research_agent import (
    run_real_research,
)

from app.multi_agent.knowledge_agent import (
    run_knowledge,
)

from app.multi_agent.real_analysis_agent import (
    run_real_analysis,
)


def main():

    print("=" * 65)
    print("Phase 6.4 - Real Analysis Integration")
    print("=" * 65)

    state = {
        "goal": {
            "target_industry": "汽车零部件",
            "target_region": "中国",
            "target_count": 1,
            "product_focus": "工业机器视觉质检解决方案",
            "user_requirement": (
                "根据真实网页证据识别企业运营信号，"
                "结合内部产品知识提出待核实的销售机会，"
                "不得编造采购、预算和联系人。"
            ),
        },
    }

    # ========================================================
    # 1. Real Research
    # ========================================================

    print("\n[1] Real Research Agent...")

    research_result = run_real_research(
        state,
        max_companies=1,
        max_news_per_company=3,
        max_jobs_per_company=2,
    )

    state.update(
        research_result
    )

    research = state[
        "research_output"
    ]

    print(
        "Data Mode:",
        research["data_mode"],
    )

    print(
        "Verified Evidence:",
        research["verified_evidence_count"],
    )

    assert research["data_mode"] == (
        "real_source_page"
    )

    assert research["mock_fallback_used"] is False

    assert research["verified_evidence_count"] >= 1, (
        "No verified source evidence; "
        "do not create a fake company assessment"
    )

    # ========================================================
    # 2. Real Knowledge MCP
    # ========================================================

    print("\n[2] Knowledge Agent...")

    knowledge_result = run_knowledge(
        state
    )

    state.update(
        knowledge_result
    )

    knowledge = state[
        "knowledge_output"
    ]

    print(
        "Status:",
        knowledge["status"],
    )

    print(
        "Documents:",
        knowledge["document_count"],
    )

    assert knowledge["source_type"] == (
        "internal_product_knowledge"
    )

    # ========================================================
    # 3. Real Analysis + DeepSeek
    # ========================================================

    print("\n[3] Real Analysis Agent...")

    analysis_result = run_real_analysis(
        state
    )

    state.update(
        analysis_result
    )

    analysis = state[
        "analysis_output"
    ]

    print(
        "Status:",
        analysis["status"],
    )

    print(
        "Selected:",
        analysis["selected_count"],
    )

    print(
        "Data Mode:",
        analysis["data_mode"],
    )

    # ========================================================
    # 4. Print traceable assessments
    # ========================================================

    print("\n[4] Source-backed Assessments")

    for assessment in analysis["assessments"]:

        print("\n" + "-" * 60)

        print(
            "Company:",
            assessment["company"],
        )

        print(
            "Purchase Intent:",
            assessment["purchase_intent_status"],
        )

        print(
            "Budget:",
            assessment["budget_status"],
        )

        print(
            "Contact:",
            assessment["contact_status"],
        )

        for evidence in assessment[
            "observed_evidence"
        ]:

            print("\nObserved Fact:")

            print(
                "Quote:",
                evidence["quote"],
            )

            print(
                "URL:",
                evidence["source_url"],
            )

            print(
                "Published:",
                evidence["published_at"],
            )

            print(
                "Verification:",
                evidence["verification_status"],
            )

        for match in assessment[
            "product_matches"
        ]:

            print("\nPotential Product Match:")

            print(
                "Knowledge Quote:",
                match["knowledge_quote"],
            )

            print(
                "Knowledge Source:",
                match["knowledge_source"],
            )

            print(
                "Match Status:",
                match["match_status"],
            )

        print(
            "\nRecommended Action:",
            assessment["recommended_action"],
        )

    # ========================================================
    # 5. Reliability assertions
    # ========================================================

    print("\n[5] Reliability Assertions")

    assert analysis["data_mode"] == (
        "real_source_page"
    )

    assert analysis["selected_count"] == len(
        analysis["assessments"]
    )

    assert analysis["selected_count"] >= 1

    assert analysis["requires_human_review"] is True

    assert analysis["crm_stage_changed"] is False

    assert analysis["crm_write_performed"] is False

    assert analysis["send_performed"] is False

    assert state["candidate_leads"] == []

    knowledge_documents = knowledge[
        "documents"
    ]

    research_evidence = research[
        "verified_evidence"
    ]

    for assessment in analysis["assessments"]:

        assert assessment[
            "purchase_intent_status"
        ] == "unverified"

        assert assessment["budget_status"] == "unknown"

        for evidence in assessment[
            "observed_evidence"
        ]:

            assert evidence in research_evidence

            assert evidence["source_url"]

            assert evidence["verification_status"] == (
                "literal_quote_from_article"
            )

        for match in assessment[
            "product_matches"
        ]:

            assert any(
                document["source"]
                == match["knowledge_source"]
                and match["knowledge_quote"]
                in document["content"]
                for document in knowledge_documents
            )

            assert match["match_status"] == (
                "potential_fit_requires_human_review"
            )

    print("Real Research Evidence: PASS")
    print("Knowledge MCP Provenance: PASS")
    print("DeepSeek Reference Validation: PASS")
    print("Original URL Preservation: PASS")
    print("No Fabricated Purchase Score: PASS")
    print("No Mock Data: PASS")
    print("No CRM Write: PASS")
    print("No Message Sending: PASS")

    print("\n" + "=" * 65)

    print(
        "Phase 6.4 Real Analysis Integration Passed"
    )

    print("=" * 65)


if __name__ == "__main__":
    main()
