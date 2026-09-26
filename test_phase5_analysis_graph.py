"""
Phase 5.5.3 - Three Real Agents + Supervisor Integration

Real workers:
    Research  -> DeepSeek + Company MCP
    Knowledge -> Knowledge MCP + Chroma
    Analysis  -> DeepSeek Reasoning

Test stubs:
    Sales
    CRM

No CRM database writes.
Company data is still Mock data.
"""

import json

from app.graph.multi_workflow import create_multi_graph
from app.multi_agent.contracts import AGENT_SEQUENCE

from app.multi_agent.research_agent import run_research
from app.multi_agent.knowledge_agent import run_knowledge
from app.multi_agent.analysis_agent import run_analysis

from app.models.review_schema import LeadAssessment


execution_trace = []


# ============================================================
# 1. Real Research Agent
# ============================================================

def research_worker(state):

    execution_trace.append("research")

    print("\n[1] Research Agent Running...")

    result = run_research(
        state,
        max_rounds=6,
        search_budget=2,
        detail_budget=4,
    )

    output = result["research_output"]

    print("Status:", output["status"])
    print("Search Calls:", output["search_calls"])
    print("Detail Calls:", output["detail_calls"])
    print("Companies:", len(output["company_records"]))

    return result


# ============================================================
# 2. Real Knowledge Agent
# ============================================================

def knowledge_worker(state):

    execution_trace.append("knowledge")

    print("\n[2] Knowledge Agent Running...")

    assert state.get("research_output"), (
        "Knowledge Agent did not receive research_output"
    )

    result = run_knowledge(state)

    output = result["knowledge_output"]

    print("Status:", output["status"])
    print("MCP Calls:", output["mcp_calls"])
    print("Documents:", output["document_count"])

    return result


# ============================================================
# 3. Real Analysis Agent
# ============================================================

def analysis_worker(state):

    execution_trace.append("analysis")

    print("\n[3] Analysis Agent Running...")

    assert state.get("research_output"), (
        "Analysis Agent did not receive research_output"
    )

    assert state.get("knowledge_context"), (
        "Analysis Agent did not receive knowledge_context"
    )

    result = run_analysis(state)

    output = result["analysis_output"]

    print("Status:", output["status"])
    print("Input Companies:", output["company_count"])
    print("Selected Companies:", output["selected_count"])

    return result


# ============================================================
# 4. Sales and CRM Test Stubs
# ============================================================

def create_stub_worker(name):

    def worker(state):

        execution_trace.append(name)

        print(f"\n[{name.upper()} Agent] Test Stub")

        assert state.get("research_output")
        assert state.get("knowledge_output")
        assert state.get("analysis_output")

        leads = state.get("candidate_leads") or []

        assert leads, (
            f"{name} did not receive candidate_leads"
        )

        return {
            f"{name}_output": {
                "mode": "test_stub",
                "received_analysis": True,
                "candidate_count": len(leads),
                "executed_external_actions": False,
            }
        }

    return worker


# ============================================================
# 5. Initial State
# ============================================================

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

        "messages": [],
        "candidate_leads": [],
        "evidence": [],

        "status": "multi_agent_initializing",

        "iteration": 0,
        "max_iterations": 3,

        "memory_context": [],
        "knowledge_context": [],

        "completed_agents": [],
        "supervisor_turns": 0,
        "supervisor_max_turns": 10,
    }


# ============================================================
# 6. Create Multi-Agent Graph
# ============================================================

def create_integration_graph():

    workers = {
        "research": research_worker,
        "knowledge": knowledge_worker,
        "analysis": analysis_worker,
        "sales": create_stub_worker("sales"),
        "crm": create_stub_worker("crm"),
    }

    return create_multi_graph(workers)


# ============================================================
# 7. Main Integration Test
# ============================================================

def main():

    execution_trace.clear()

    print("=" * 65)
    print("Phase 5.5.3 - Three Real Agents Integration")
    print("=" * 65)

    graph = create_integration_graph()

    state = create_initial_state()

    print("\nStarting Multi-Agent Graph...")

    result = graph.invoke(state)

    research = result["research_output"]
    knowledge = result["knowledge_output"]
    analysis = result["analysis_output"]

    leads = result["candidate_leads"]

    # ========================================================
    # Show Analysis Results
    # ========================================================

    print("\n[4] Candidate Leads")

    for lead in leads:

        print("\nCompany:", lead["company"])

        print(
            "Purchase Intent Score:",
            lead["purchase_intent_score"],
        )

        print(
            "Opportunity Level:",
            lead["opportunity_level"],
        )

        print(
            "Evidence Count:",
            len(lead["evidence"]),
        )

        print(
            "Solution Matches:",
            len(lead["solution_match"]),
        )

    # ========================================================
    # Show Supervisor State
    # ========================================================

    print("\n[5] Supervisor State")

    print("Execution Trace:", execution_trace)

    print("Completed Agents:", result["completed_agents"])

    print("Supervisor Turns:", result["supervisor_turns"])

    print("Next Agent:", result["next_agent"])

    print("Final Status:", result["status"])

    # ========================================================
    # Reliability Assertions
    # ========================================================

    print("\n[6] Reliability Assertions")

    # Supervisor routing
    assert execution_trace == list(AGENT_SEQUENCE)

    assert result["completed_agents"] == list(
        AGENT_SEQUENCE
    )

    assert result["supervisor_turns"] == 5

    assert result["next_agent"] == "finish"

    assert result["status"] == "multi_agent_completed"

    # Research checks
    assert research["data_mode"] == "mock_company_mcp"

    assert research["search_calls"] <= 2

    assert research["detail_calls"] <= 4

    assert research["enriched_company_count"] <= 2

    assert research["tool_trace"]

    # Knowledge checks
    assert 1 <= knowledge["mcp_calls"] <= 2

    assert knowledge["mcp_tool"] == "search_product_knowledge"

    assert knowledge["document_count"] >= 1

    assert result["knowledge_context"]

    # Analysis checks
    assert analysis["status"] == "complete"

    assert analysis["selected_count"] == len(leads)

    assert 1 <= len(leads) <= 2

    assert analysis["crm_stage_changed"] is False

    assert analysis["requires_external_verification"] is True

    # Verify compatibility with existing LeadAssessment
    known_companies = {
        record["company"]
        for record in research["company_records"]
    }

    for lead in leads:

        LeadAssessment.model_validate(lead)

        assert lead["company"] in known_companies

        assert 0 <= lead["purchase_intent_score"] <= 1

    # Check actual knowledge citation provenance again
    knowledge_documents = knowledge["documents"]

    for assessment in analysis["assessments"]:

        evidence = assessment["evidence"]

        for match in assessment["match_provenance"]:

            assert match["company_signal"] in evidence

            assert any(
                document["source"] == match["knowledge_source"]
                and match["knowledge_quote"] in document["content"]
                for document in knowledge_documents
            )

    # Downstream state transfer
    for name in ("sales", "crm"):

        output = result[f"{name}_output"]

        assert output["mode"] == "test_stub"

        assert output["received_analysis"] is True

        assert output["candidate_count"] == len(leads)

        assert output["executed_external_actions"] is False

    print("Supervisor Routing: PASS")
    print("Research State Transfer: PASS")
    print("Knowledge State Transfer: PASS")
    print("Analysis State Transfer: PASS")
    print("Company MCP: PASS")
    print("Knowledge MCP: PASS")
    print("Analysis Evidence Validation: PASS")
    print("Legacy LeadAssessment Compatibility: PASS")
    print("Downstream State Transfer: PASS")
    print("No CRM Write: PASS (test stub only)")

    print("\n" + "=" * 65)

    print("Phase 5.5.3 Integration Test Passed")

    print("=" * 65)


if __name__ == "__main__":
    main()