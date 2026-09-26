"""
Phase 5.5.2 - Analysis Agent Live Integration

Real execution:
    Research Agent -> DeepSeek + Company MCP
    Knowledge Agent -> Knowledge MCP + Chroma
    Analysis Agent -> DeepSeek Reasoning

No CRM writes.
Company research still uses Mock data.
"""

import json
import traceback

from app.multi_agent.research_agent import run_research
from app.multi_agent.knowledge_agent import run_knowledge
from app.multi_agent.analysis_agent import run_analysis


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
    print("Phase 5.5.2 - Analysis Agent Live Integration")
    print("=" * 65)

    state = create_initial_state()

    # ========================================================
    # 1. Real Research Agent
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

    print("Research Status:", research["status"])
    print("Search Calls:", research["search_calls"])
    print("Detail Calls:", research["detail_calls"])

    print(
        "Company Records:",
        len(research["company_records"]),
    )

    assert research["tool_trace"], (
        "Research Agent did not execute Company MCP tools"
    )

    assert research["search_calls"] <= 2
    assert research["detail_calls"] <= 4

    # ========================================================
    # 2. Real Knowledge Agent
    # ========================================================

    print("\n[2] Running Knowledge Agent...")

    knowledge_result = run_knowledge(state)

    state.update(knowledge_result)

    knowledge = state["knowledge_output"]

    print("Knowledge Status:", knowledge["status"])
    print("MCP Calls:", knowledge["mcp_calls"])
    print("Document Count:", knowledge["document_count"])

    assert knowledge["mcp_calls"] <= 2
    assert knowledge["document_count"] >= 1

    print("\nAvailable Knowledge Sources:")

    for document in knowledge["documents"]:
        print("-", document["source"])

    # ========================================================
    # 3. Real Analysis Agent
    # ========================================================

    print("\n[3] Running Analysis Agent with DeepSeek...")

    try:

        analysis_result = run_analysis(state)

    except Exception:

        print("\nAnalysis Agent validation failed.")
        print("Research and Knowledge outputs are still valid.")
        print("Inspect the traceback before changing validation rules.")

        traceback.print_exc()

        raise

    state.update(analysis_result)

    analysis = state["analysis_output"]

    leads = state["candidate_leads"]

    # ========================================================
    # 4. Structured Analysis
    # ========================================================

    print("\n[4] Analysis Statistics")

    print("Status:", analysis["status"])
    print("Data Mode:", analysis["data_mode"])
    print("Input Companies:", analysis["company_count"])
    print("Selected Companies:", analysis["selected_count"])

    print(
        "Knowledge Documents:",
        analysis["knowledge_document_count"],
    )

    print(
        "External Verification Required:",
        analysis["requires_external_verification"],
    )

    print(
        "CRM Stage Changed:",
        analysis["crm_stage_changed"],
    )

    print("\n[5] Candidate Leads")

    print(
        json.dumps(
            leads,
            ensure_ascii=False,
            indent=2,
        )
    )

    # ========================================================
    # 5. Evidence Provenance
    # ========================================================

    print("\n[6] Analysis Evidence Provenance")

    for assessment in analysis["assessments"]:

        print("\nCompany:", assessment["company"])

        print(
            "Enterprise Evidence:",
            json.dumps(
                assessment["evidence"],
                ensure_ascii=False,
            ),
        )

        print("Knowledge Matches:")

        for match in assessment["match_provenance"]:

            print(
                json.dumps(
                    match,
                    ensure_ascii=False,
                    indent=2,
                )
            )

    # ========================================================
    # 6. Reliability Assertions
    # ========================================================

    print("\n[7] Reliability Assertions")

    target_count = state["goal"]["target_count"]

    assert analysis["status"] == "complete"

    assert analysis["data_mode"] == "mock_company_mcp"

    assert 1 <= len(leads) <= target_count, (
        "Expected at least one evidence-backed candidate "
        "from the current mock dataset"
    )

    assert analysis["selected_count"] == len(leads)

    assert analysis["crm_stage_changed"] is False

    assert analysis["requires_external_verification"] is True

    assert analysis["knowledge_document_count"] >= 1

    assert len(analysis["assessments"]) == len(leads)

    known_companies = {
        item["company"]
        for item in research["company_records"]
    }

    assert all(
        lead["company"] in known_companies
        for lead in leads
    )

    assert all(
        0 <= lead["purchase_intent_score"] <= 1
        for lead in leads
    )

    print("Research MCP: PASS")
    print("Knowledge MCP: PASS")
    print("Analysis Structure: PASS")
    print("Company Source Validation: PASS")
    print("Knowledge Provenance: PASS")
    print("Candidate Count Limit: PASS")
    print("No CRM Write: PASS")

    print("\n" + "=" * 65)
    print("Phase 5.5.2 Integration Test Passed")
    print("=" * 65)


if __name__ == "__main__":
    main()