
"""
Phase 5.6.2 - Sales Agent Live Integration

Real:
    Research Agent + DeepSeek + Company MCP
    Knowledge Agent + Knowledge MCP + Chroma
    Analysis Agent + DeepSeek Reasoning
    Sales Agent + DeepSeek

No emails or messages are sent.
No CRM tools or database writes are executed.

Company data currently comes from the Mock provider.
"""

import json
import traceback

from app.multi_agent.research_agent import run_research
from app.multi_agent.knowledge_agent import run_knowledge
from app.multi_agent.analysis_agent import run_analysis
from app.multi_agent.sales_agent import run_sales


def create_initial_state():

    return {
        "goal": {
            "target_industry": "汽车零部件",
            "target_region": "中国",
            "target_count": 2,
            "product_focus": "工业机器视觉质检解决方案",
            "user_requirement": (
                "寻找近期扩产、新建产线或自动化升级，"
                "可能需要机器视觉质检方案的汽车零部件企业。"
            ),
        },

        "research_plan": {
            "buying_signals": [
                "扩产或新建生产线",
                "自动化升级",
                "招聘机器视觉工程师",
                "招聘质量检测工程师",
            ],
            "search_queries": [
                "汽车零部件扩产",
                "汽车零部件机器视觉招聘",
            ],
        },

        "memory_context": [],
        "knowledge_context": [],
    }


def main():

    print("=" * 65)
    print("Phase 5.6.2 - Sales Agent Live Integration")
    print("=" * 65)

    state = create_initial_state()

    # ========================================================
    # 1. Research Agent
    # ========================================================

    print("\n[1] Running Research Agent...")

    research_result = run_research(
        state,
        max_rounds=6,
        search_budget=2,
        detail_budget=4,
    )

    state.update(research_result)

    research = state["research_output"]

    print("Status:", research["status"])
    print("Search Calls:", research["search_calls"])
    print("Detail Calls:", research["detail_calls"])

    print(
        "Company Records:",
        len(research["company_records"]),
    )

    # ========================================================
    # 2. Knowledge Agent
    # ========================================================

    print("\n[2] Running Knowledge Agent...")

    knowledge_result = run_knowledge(state)

    state.update(knowledge_result)

    knowledge = state["knowledge_output"]

    print("Status:", knowledge["status"])
    print("MCP Calls:", knowledge["mcp_calls"])

    print(
        "Document Count:",
        knowledge["document_count"],
    )

    # ========================================================
    # 3. Analysis Agent
    # ========================================================

    print("\n[3] Running Analysis Agent...")

    analysis_result = run_analysis(state)

    state.update(analysis_result)

    analysis = state["analysis_output"]

    print("Status:", analysis["status"])

    print(
        "Selected Companies:",
        analysis["selected_count"],
    )

    # ========================================================
    # 4. Sales Agent
    # ========================================================

    print("\n[4] Running Sales Agent with DeepSeek...")

    try:

        sales_result = run_sales(state)

    except Exception:

        print("\nSales Agent execution or validation failed.")
        print(
            "Previous Research, Knowledge and Analysis "
            "outputs remain valid."
        )

        traceback.print_exc()

        raise

    state.update(sales_result)

    sales = state["sales_output"]

    # ========================================================
    # 5. Sales Statistics
    # ========================================================

    print("\n[5] Sales Statistics")

    print("Status:", sales["status"])

    print("Data Mode:", sales["data_mode"])

    print("Draft Count:", sales["draft_count"])

    print(
        "Requires Human Review:",
        sales["requires_human_review"],
    )

    print(
        "Send Performed:",
        sales["send_performed"],
    )

    print(
        "CRM Write Performed:",
        sales["crm_write_performed"],
    )

    # ========================================================
    # 6. Sales Drafts
    # ========================================================

    print("\n[6] Generated Sales Drafts")

    for index, draft in enumerate(
        sales["drafts"],
        start=1,
    ):

        print("\n" + "-" * 65)

        print(f"Draft #{index}")

        print("Company:", draft["company"])

        print("Contact Role:", draft["contact_role"])

        print("Entry Point:", draft["entry_point"])

        print("Draft Status:", draft["draft_status"])

        print("\nSelected Enterprise Evidence:")

        for evidence in draft["evidence_refs"]:

            print("-", evidence)

        print("\nVerified Product Knowledge:")

        for match in draft["knowledge_refs"]:

            print(
                json.dumps(
                    match,
                    ensure_ascii=False,
                    indent=2,
                )
            )

        print("\nDiscovery Questions:")

        for question in draft["discovery_questions"]:

            print("-", question)

        print("\nOutreach Draft:")

        print(draft["outreach_draft"])

        print("\nNext Action:")

        print(draft["next_action"])

    # ========================================================
    # 7. Reliability Assertions
    # ========================================================

    print("\n[7] Reliability Assertions")

    assert sales["status"] == "complete"

    assert sales["data_mode"] == "mock_company_mcp"

    assert sales["draft_count"] == len(
        state["candidate_leads"]
    )

    assert sales["draft_count"] <= 2

    assert sales["requires_human_review"] is True

    assert sales["send_performed"] is False

    assert sales["crm_write_performed"] is False

    assert analysis["crm_stage_changed"] is False

    candidate_map = {
        lead["company"]: lead
        for lead in state["candidate_leads"]
    }

    knowledge_documents = knowledge["documents"]

    for draft in sales["drafts"]:

        company = draft["company"]

        assert company in candidate_map

        candidate = candidate_map[company]

        # Sales evidence must be selected from Analysis output.
        assert all(
            fact in candidate["evidence"]
            for fact in draft["evidence_refs"]
        )

        assert draft["entry_point"] in candidate["evidence"]

        # Each cited product capability must match actual KB text.
        for match in draft["knowledge_refs"]:

            assert any(
                document["source"] == match["knowledge_source"]
                and match["knowledge_quote"] in document["content"]
                for document in knowledge_documents
            )

        assert 2 <= len(draft["discovery_questions"]) <= 4

        assert draft["draft_status"] == "mock_internal_only"

        assert "禁止发送" in draft["outreach_draft"]

        assert draft["requires_human_review"] is True

        assert draft["send_performed"] is False

        assert draft["crm_write_performed"] is False

    print("\nResearch MCP: PASS")
    print("Knowledge MCP: PASS")
    print("Analysis Result Transfer: PASS")
    print("Sales Draft Generation: PASS")
    print("Enterprise Evidence Validation: PASS")
    print("Knowledge Citation Validation: PASS")
    print("Candidate Count Limit: PASS")
    print("Mock Data Sending Restriction: PASS")
    print("No CRM Write: PASS")

    print("\n" + "=" * 65)
    print("Phase 5.6.2 Integration Test Passed")
    print("=" * 65)


if __name__ == "__main__":
    main()
