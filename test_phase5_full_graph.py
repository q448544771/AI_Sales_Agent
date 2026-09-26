
"""
Phase 5.7.3 - Five Real Agents Full Integration

Research  -> DeepSeek + Company MCP
Knowledge -> Knowledge MCP + Chroma
Analysis  -> DeepSeek Reasoning
Sales     -> DeepSeek
CRM       -> Real CRM MCP (read-only)

Additional verification:
Compare complete CRM database snapshots before and after execution.

No message sending.
No CRM create/update.
Mock company data must never be automatically written to CRM.
"""

from app.graph.multi_workflow import create_multi_graph

from app.multi_agent.contracts import AGENT_SEQUENCE
from app.multi_agent.research_agent import run_research
from app.multi_agent.knowledge_agent import run_knowledge
from app.multi_agent.analysis_agent import run_analysis
from app.multi_agent.sales_agent import run_sales
from app.multi_agent.crm_agent import run_crm

from app.database.db import SessionLocal
from app.database.models import Lead

from app.models.review_schema import LeadAssessment


execution_trace = []


# ============================================================
# 1. Read-only database snapshot
# ============================================================

def crm_snapshot():

    db = SessionLocal()

    try:

        leads = (
            db.query(Lead)
            .order_by(Lead.id.asc())
            .all()
        )

        return [
            (
                lead.id,
                lead.company,
                lead.industry,
                lead.region,
                lead.score,
                lead.level,
                lead.evidence,
                lead.action,
                lead.stage,
                lead.next_action,
                lead.owner,
                (
                    lead.last_contact_time.isoformat()
                    if lead.last_contact_time
                    else None
                ),
                lead.status,
            )
            for lead in leads
        ]

    finally:

        db.close()


# ============================================================
# 2. Real Research Agent
# ============================================================

def research_worker(state):

    execution_trace.append("research")

    print("\n[1] Research Agent...")

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
    print("Company Records:", len(output["company_records"]))

    return result


# ============================================================
# 3. Real Knowledge Agent
# ============================================================

def knowledge_worker(state):

    execution_trace.append("knowledge")

    print("\n[2] Knowledge Agent...")

    assert state.get("research_output")

    result = run_knowledge(state)

    output = result["knowledge_output"]

    print("Status:", output["status"])
    print("MCP Calls:", output["mcp_calls"])
    print("Documents:", output["document_count"])

    return result


# ============================================================
# 4. Real Analysis Agent
# ============================================================

def analysis_worker(state):

    execution_trace.append("analysis")

    print("\n[3] Analysis Agent...")

    assert state.get("research_output")
    assert state.get("knowledge_output")

    result = run_analysis(state)

    output = result["analysis_output"]

    print("Status:", output["status"])
    print("Selected:", output["selected_count"])

    return result


# ============================================================
# 5. Real Sales Agent
# ============================================================

def sales_worker(state):

    execution_trace.append("sales")

    print("\n[4] Sales Agent...")

    assert state.get("analysis_output")
    assert state.get("candidate_leads")

    result = run_sales(state)

    output = result["sales_output"]

    print("Status:", output["status"])
    print("Draft Count:", output["draft_count"])
    print("Send Performed:", output["send_performed"])

    return result


# ============================================================
# 6. Real CRM Agent - read-only
# ============================================================

def crm_worker(state):

    execution_trace.append("crm")

    print("\n[5] CRM Agent (Real MCP, Read-only)...")

    assert state.get("sales_output")
    assert state.get("candidate_leads")

    # No query_tool injection.
    # This invokes the actual CRM MCP query_leads tool.
    result = run_crm(state)

    output = result["crm_output"]

    print("Status:", output["status"])
    print("Mode:", output["mode"])
    print("Query Count:", output["query_count"])
    print("Existing:", output["existing_count"])
    print("Missing:", output["missing_count"])
    print("Duplicates:", output["duplicate_count"])

    return result


# ============================================================
# 7. Initial state
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
                "质量检测能力升级",
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
# 8. Construct full graph
# ============================================================

def create_integration_graph():

    return create_multi_graph({
        "research": research_worker,
        "knowledge": knowledge_worker,
        "analysis": analysis_worker,
        "sales": sales_worker,
        "crm": crm_worker,
    })


# ============================================================
# 9. Run full integration
# ============================================================

def main():

    execution_trace.clear()

    print("=" * 65)
    print("Phase 5.7.3 - Five Real Agents Integration")
    print("=" * 65)

    # Read the database before executing the graph.
    before_snapshot = crm_snapshot()

    print(
        "\nCRM records before execution:",
        len(before_snapshot),
    )

    graph = create_integration_graph()

    initial_state = create_initial_state()

    print("\nStarting Five-Agent Graph...")

    try:

        result = graph.invoke(initial_state)

    finally:

        # Compare even if an upstream Agent fails.
        after_snapshot = crm_snapshot()

        assert before_snapshot == after_snapshot, (
            "CRM database contents changed during integration!"
        )

        print(
            "\nCRM Database Snapshot: UNCHANGED"
        )

    research = result["research_output"]
    knowledge = result["knowledge_output"]
    analysis = result["analysis_output"]
    sales = result["sales_output"]
    crm = result["crm_output"]

    leads = result["candidate_leads"]

    # ========================================================
    # 10. Supervisor state
    # ========================================================

    print("\n[6] Supervisor State")

    print("Execution Trace:", execution_trace)

    print(
        "Completed Agents:",
        result["completed_agents"],
    )

    print(
        "Supervisor Turns:",
        result["supervisor_turns"],
    )

    print("Next Agent:", result["next_agent"])
    print("Final Status:", result["status"])

    # ========================================================
    # 11. CRM review result
    # ========================================================

    print("\n[7] CRM Review Results")

    for record in crm["review_records"]:

        print("\nCompany:", record["company"])

        print(
            "Lookup Status:",
            record["lookup_status"],
        )

        print(
            "Existing Stage:",
            record["existing_stage"],
        )

        print(
            "Action Taken:",
            record["action_taken"],
        )

        print(
            "CRM Write:",
            record["crm_write_performed"],
        )

    # ========================================================
    # 12. Supervisor assertions
    # ========================================================

    print("\n[8] Reliability Assertions")

    assert execution_trace == list(AGENT_SEQUENCE)

    assert result["completed_agents"] == list(
        AGENT_SEQUENCE
    )

    assert result["supervisor_turns"] == 5

    assert result["next_agent"] == "finish"

    assert result["status"] == "multi_agent_completed"

    # ========================================================
    # 13. Research / Knowledge assertions
    # ========================================================

    assert research["data_mode"] == "mock_company_mcp"

    assert research["search_calls"] <= 2
    assert research["detail_calls"] <= 4
    assert research["tool_trace"]

    assert 1 <= knowledge["mcp_calls"] <= 2

    assert knowledge["document_count"] >= 1

    # ========================================================
    # 14. Analysis assertions
    # ========================================================

    assert analysis["status"] == "complete"

    assert analysis["selected_count"] == len(leads)

    assert 1 <= len(leads) <= 2

    assert analysis["crm_stage_changed"] is False

    candidate_map = {}

    for lead in leads:

        LeadAssessment.model_validate(lead)

        candidate_map[lead["company"]] = lead

    assert len(candidate_map) == len(leads)

    # ========================================================
    # 15. Sales assertions
    # ========================================================

    assert sales["status"] == "complete"

    assert sales["draft_count"] == len(leads)

    assert sales["data_mode"] == "mock_company_mcp"

    assert sales["send_performed"] is False

    assert sales["crm_write_performed"] is False

    assert sales["requires_human_review"] is True

    documents = knowledge["documents"]

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
                for document in documents
            )

        assert draft["draft_status"] == "mock_internal_only"

        assert "禁止发送" in draft["outreach_draft"]

        assert draft["send_performed"] is False
        assert draft["crm_write_performed"] is False

    # ========================================================
    # 16. Real CRM assertions
    # ========================================================

    assert crm["status"] in {
        "review_only",
        "manual_dedup_required",
    }

    assert crm["mode"] == "read_only"

    assert crm["data_mode"] == "mock_company_mcp"

    assert crm["query_count"] == 1

    assert crm["candidate_count"] == len(leads)

    assert len(crm["review_records"]) == len(leads)

    assert (
        crm["existing_count"]
        + crm["missing_count"]
        + crm["duplicate_count"]
        == len(leads)
    )

    assert crm["read_performed"] is True

    assert crm["create_performed"] is False
    assert crm["update_performed"] is False
    assert crm["stage_changed"] is False

    assert crm["requires_human_review"] is True

    assert crm["write_block_reason"] == "mock_company_data"

    returned_companies = {
        record["company"]
        for record in crm["review_records"]
    }

    assert returned_companies == set(candidate_map)

    for record in crm["review_records"]:

        assert record["action_taken"] == "none"

        assert record["crm_write_performed"] is False

    # ========================================================
    # 17. Final report
    # ========================================================

    print("\nSupervisor Routing: PASS")
    print("Research MCP: PASS")
    print("Knowledge MCP: PASS")
    print("Analysis Evidence: PASS")
    print("Sales Evidence and Citations: PASS")
    print("Real CRM MCP Query: PASS")
    print("CRM Candidate Matching: PASS")
    print("Mock Data Sending Restriction: PASS")
    print("CRM Database Unchanged: PASS")

    print("\n" + "=" * 65)
    print("Phase 5.7.3 Full Integration Test Passed")
    print("=" * 65)


if __name__ == "__main__":
    main()
