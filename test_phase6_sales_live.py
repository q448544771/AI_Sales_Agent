
"""Phase 6.5 - Four real agents integration.

Real Web Search -> Company MCP -> Original HTML Verification
-> Knowledge MCP -> DeepSeek Analysis -> DeepSeek Sales Selection
-> Deterministic Internal Draft

No mock companies. No messages sent. No CRM writes.
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

from app.multi_agent.real_sales_agent import (
    run_real_sales,
    DRAFT_BANNER,
)


def main():

    print("=" * 65)
    print("Phase 6.5 - Four Real Agents Integration")
    print("=" * 65)

    state = {
        "goal": {
            "target_industry": "汽车零部件",
            "target_region": "中国",
            "target_count": 1,
            "product_focus": "工业机器视觉质检解决方案",
            "user_requirement": (
                "根据真实企业新闻和原网页证据，"
                "识别值得人工核实的质检应用场景，"
                "生成禁止自动发送的销售准备草稿。"
            ),
        },
    }

    # ========================================================
    # 1. Research
    # ========================================================

    print("\n[1] Real Research Agent...")

    state.update(
        run_real_research(
            state,
            max_companies=1,
            max_news_per_company=3,
            max_jobs_per_company=2,
        )
    )

    research = state["research_output"]

    print(
        "Verified Evidence:",
        research["verified_evidence_count"],
    )

    assert research["data_mode"] == "real_source_page"
    assert research["mock_fallback_used"] is False
    assert research["verified_evidence_count"] >= 1

    # ========================================================
    # 2. Knowledge
    # ========================================================

    print("\n[2] Knowledge Agent...")

    state.update(
        run_knowledge(state)
    )

    knowledge = state["knowledge_output"]

    print(
        "Documents:",
        knowledge["document_count"],
    )

    # ========================================================
    # 3. Analysis
    # ========================================================

    print("\n[3] Real Analysis Agent...")

    state.update(
        run_real_analysis(state)
    )

    analysis = state["analysis_output"]

    print(
        "Selected:",
        analysis["selected_count"],
    )

    assert analysis["selected_count"] >= 1

    # ========================================================
    # 4. Sales
    # ========================================================

    print("\n[4] Real Sales Agent...")

    state.update(
        run_real_sales(state)
    )

    sales = state["sales_output"]

    print("Status:", sales["status"])
    print("Draft Count:", sales["draft_count"])
    print("Data Mode:", sales["data_mode"])

    # ========================================================
    # 5. Review generated drafts
    # ========================================================

    print("\n[5] Internal Sales Drafts")

    for draft in sales["drafts"]:

        print("\n" + "-" * 60)

        print("Company:", draft["company"])

        print(
            "Draft Status:",
            draft["draft_status"],
        )

        print(
            "Contact Role:",
            draft["contact_role"],
        )

        print(
            "Knowledge References:",
            len(draft["knowledge_refs"]),
        )

        print("\nOutreach Draft:\n")

        print(
            draft["outreach_draft"]
        )

        print(
            "\nSend Performed:",
            draft["send_performed"],
        )

        print(
            "CRM Write Performed:",
            draft["crm_write_performed"],
        )

    # ========================================================
    # 6. Reliability assertions
    # ========================================================

    print("\n[6] Reliability Assertions")

    assert sales["status"] == "complete"

    assert sales["data_mode"] == "real_source_page"

    assert sales["draft_count"] >= 1

    assert sales["draft_count"] == len(
        sales["drafts"]
    )

    assert sales["requires_human_review"] is True

    assert sales["send_performed"] is False

    assert sales["crm_write_performed"] is False

    assert sales["crm_stage_changed"] is False

    assert state["candidate_leads"] == []

    original_evidence = research[
        "verified_evidence"
    ]

    knowledge_documents = knowledge[
        "documents"
    ]

    for draft in sales["drafts"]:

        assert draft["entry_point"] in original_evidence

        assert draft["entry_point"]["quote"] in (
            draft["outreach_draft"]
        )

        assert draft["entry_point"]["source_url"] in (
            draft["outreach_draft"]
        )

        assert DRAFT_BANNER in draft["outreach_draft"]

        assert draft["draft_status"] == (
            "real_internal_review_only"
        )

        assert draft["purchase_intent_status"] == (
            "unverified"
        )

        assert draft["budget_status"] == "unknown"

        assert draft["requires_human_review"] is True

        assert draft["send_performed"] is False

        assert draft["crm_write_performed"] is False

        for match in draft["knowledge_refs"]:

            assert any(
                document["source"]
                == match["knowledge_source"]
                and match["knowledge_quote"]
                in document["content"]
                for document in knowledge_documents
            )

    print("Real Research: PASS")
    print("Original-page Evidence: PASS")
    print("Knowledge Provenance: PASS")
    print("Analysis to Sales Handoff: PASS")
    print("Real Source URL Retention: PASS")
    print("No Fabricated Purchase Score: PASS")
    print("Internal Draft Restriction: PASS")
    print("No Mock Data: PASS")
    print("No Message Sending: PASS")
    print("No CRM Write: PASS")

    print("\n" + "=" * 65)

    print(
        "Phase 6.5 Four Real Agents Integration Passed"
    )

    print("=" * 65)


if __name__ == "__main__":
    main()
