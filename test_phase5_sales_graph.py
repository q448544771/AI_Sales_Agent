"""
Phase 5.6.3 - Four Real Agents + Supervisor Integration

Real:
    Research Agent  -> DeepSeek + Company MCP
    Knowledge Agent -> Knowledge MCP + Chroma
    Analysis Agent  -> DeepSeek Reasoning
    Sales Agent     -> DeepSeek

Stub:
    CRM Agent

No CRM database writes or message sending.
Company data is still Mock data.
"""

from app.graph.multi_workflow import create_multi_graph
from app.multi_agent.contracts import AGENT_SEQUENCE

from app.multi_agent.research_agent import run_research
from app.multi_agent.knowledge_agent import run_knowledge
from app.multi_agent.analysis_agent import run_analysis
from app.multi_agent.sales_agent import run_sales

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
    print("Selected Companies:", output["selected_count"])

    return result


# ============================================================
# 4. Real Sales Agent
# ============================================================

def sales_worker(state):

    execution_trace.append("sales")

    print("\n[4] Sales Agent Running...")

    assert state.get("analysis_output"), (
        "Sales Agent did not receive analysis_output"
    )

    assert state.get("candidate_leads"), (
        "Sales Agent did not receive candidate_leads"
    )

    result = run_sales(state)

    output = result["sales_output"]

    print("Status:", output["status"])
    print("Draft Count:", output["draft_count"])
    print("Send Performed:", output["send_performed"])
    print("CRM Write:", output["crm_write_performed"])

    return result


# ============================================================
# 5. CRM Test Stub
# ============================================================

def crm_stub(state):

    execution_trace.append("crm")

    print("\n[5] CRM Agent Test Stub...")

    sales = state.get("sales_output")

    assert sales is not None, (
        "CRM did not receive sales_output"
    )

    assert sales["status"] == "complete"

    assert sales["draft_count"] > 0

    assert sales["send_performed"] is False

    assert sales["crm_write_performed"] is False

    print("Received Drafts:", sales["draft_count"])
    print("CRM Write: SKIPPED")

    return {
        "crm_output": {
            "mode": "test_stub",
            "received_sales": True,
            "draft_count": sales["draft_count"],
            "write_performed": False,
        }
    }


# ============================================================
# 6. Initial State
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
# 7. Build Multi-Agent Graph
# ============================================================

def create_integration_graph():

    workers = {
        "research": research_worker,
        "knowledge": knowledge_worker,
        "analysis": analysis_worker,
        "sales": sales_worker,
        "crm": crm_stub,
    }

    return create_multi_graph(workers)


# ============================================================
# 8. Main Integration Test
# ============================================================

def main():

    execution_trace.clear()

    print("=" * 65)
    print("Phase 5.6.3 - Four Real Agents Integration")
    print("=" * 65)

    graph = create_integration_graph()

    state = create_initial_state()

    print("\nStarting Multi-Agent Graph...")

    result = graph.invoke(state)

    research = result["research_output"]
    knowledge = result["knowledge_output"]
    analysis = result["analysis_output"]
    sales = result["sales_output"]

    leads = result["candidate_leads"]

    # ========================================================
    # 9. Display Sales Results
    # ========================================================

    print("\n[6] Generated Sales Drafts")

    for draft in sales["drafts"]:

        print("\n" + "-" * 55)

        print("Company:", draft["company"])
        print("Contact Role:", draft["contact_role"])
        print("Entry Point:", draft["entry_point"])
        print("Draft Status:", draft["draft_status"])

        print("\nDiscovery Questions:")

        for question in draft["discovery_questions"]:
            print("-", question)

        print("\nOutreach Draft:")
        print(draft["outreach_draft"])

    # ========================================================
    # 10. Supervisor State
    # ========================================================

    print("\n[7] Supervisor State")

    print("Execution Trace:", execution_trace)
    print("Completed Agents:", result["completed_agents"])
    print("Supervisor Turns:", result["supervisor_turns"])
    print("Next Agent:", result["next_agent"])
    print("Final Status:", result["status"])

    # ========================================================
    # 11. Reliability Assertions
    # ========================================================

    print("\n[8] Reliability Assertions")

    # Supervisor routing
    assert execution_trace == list(AGENT_SEQUENCE)

    assert result["completed_agents"] == list(
        AGENT_SEQUENCE
    )

    assert result["supervisor_turns"] == 5

    assert result["next_agent"] == "finish"

    assert result["status"] == "multi_agent_completed"

    # Research
    assert research["data_mode"] == "mock_company_mcp"

    assert research["search_calls"] <= 2

    assert research["detail_calls"] <= 4

    assert research["enriched_company_count"] <= 2

    assert research["tool_trace"]

    # Knowledge
    assert 1 <= knowledge["mcp_calls"] <= 2

    assert knowledge["mcp_tool"] == "search_product_knowledge"

    assert knowledge["document_count"] >= 1

    # Analysis
    assert analysis["status"] == "complete"

    assert analysis["selected_count"] == len(leads)

    assert 1 <= len(leads) <= 2

    assert analysis["crm_stage_changed"] is False

    # Sales
    assert sales["status"] == "complete"

    assert sales["draft_count"] == len(leads)

    assert sales["data_mode"] == "mock_company_mcp"

    assert sales["send_performed"] is False

    assert sales["crm_write_performed"] is False

    assert sales["requires_human_review"] is True

    candidate_map = {}

    for lead in leads:

        LeadAssessment.model_validate(lead)

        candidate_map[lead["company"]] = lead

    assert len(candidate_map) == len(leads)

    knowledge_documents = knowledge["documents"]

    for draft in sales["drafts"]:

        company = draft["company"]

        assert company in candidate_map

        candidate = candidate_map[company]

        assert draft["entry_point"] in candidate["evidence"]

        assert all(
            fact in candidate["evidence"]
            for fact in draft["evidence_refs"]
        )

        for match in draft["knowledge_refs"]:

            assert match["company_signal"] in candidate["evidence"]

            assert any(
                document["source"] == match["knowledge_source"]
                and match["knowledge_quote"] in document["content"]
                for document in knowledge_documents
            )

        assert draft["draft_status"] == "mock_internal_only"

        assert "禁止发送" in draft["outreach_draft"]

        assert 2 <= len(draft["discovery_questions"]) <= 4

        assert draft["send_performed"] is False

        assert draft["crm_write_performed"] is False

    # CRM is only a stub, not an actual database operation.
    crm = result["crm_output"]

    assert crm["mode"] == "test_stub"

    assert crm["received_sales"] is True

    assert crm["draft_count"] == sales["draft_count"]

    assert crm["write_performed"] is False

    print("Supervisor Routing: PASS")
    print("Research State Transfer: PASS")
    print("Knowledge State Transfer: PASS")
    print("Analysis State Transfer: PASS")
    print("Sales State Transfer: PASS")
    print("Company MCP: PASS")
    print("Knowledge MCP: PASS")
    print("Analysis Evidence Validation: PASS")
    print("Sales Knowledge Citation: PASS")
    print("Mock Data Sending Restriction: PASS")
    print("No CRM Write: PASS")

    print("\n" + "=" * 65)
    print("Phase 5.6.3 Integration Test Passed")
    print("=" * 65)


if __name__ == "__main__":
    main()