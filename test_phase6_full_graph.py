
"""Phase 6.6 - Full real five-agent LangGraph integration.

Supervisor:
    Real Research
        -> Knowledge MCP
        -> Real Analysis
        -> Real Sales
        -> Read-only Real CRM

Uses:
    Bocha Web Search
    Company MCP
    Original HTML verification
    Internal Knowledge MCP
    DeepSeek
    CRM MCP query_leads

No mock fallback.
No CRM create/update.
No outbound messaging.
"""

from app.graph.multi_workflow import (
    create_multi_graph,
)

from app.multi_agent.contracts import (
    AGENT_SEQUENCE,
)

from app.multi_agent.real_research_agent import (
    real_research_agent_node,
)

from app.multi_agent.knowledge_agent import (
    knowledge_agent_node,
)

from app.multi_agent.real_analysis_agent import (
    real_analysis_agent_node,
)

from app.multi_agent.real_sales_agent import (
    real_sales_agent_node,
    DRAFT_BANNER,
)

from app.multi_agent.real_crm_agent import (
    real_crm_agent_node,
    capture_crm_snapshot,
)


def create_phase6_graph():

    return create_multi_graph({
        "research": real_research_agent_node,
        "knowledge": knowledge_agent_node,
        "analysis": real_analysis_agent_node,
        "sales": real_sales_agent_node,
        "crm": real_crm_agent_node,
    })


def initial_state():

    return {
        "goal": {
            "product_focus": "工业机器视觉质检解决方案",
            "target_industry": "汽车零部件",
            "target_region": "中国",
            "target_count": 1,
            "user_requirement": (
                "寻找有真实公开网页依据的近期扩产、"
                "新建生产线或自动化升级企业；"
                "保留原始来源，核实产品匹配，"
                "生成仅供人工审核的销售草稿；"
                "CRM仅执行只读重复匹配。"
            ),
        },

        "status": "planning",

        "completed_agents": [],

        "supervisor_turns": 0,
        "max_supervisor_turns": 12,
    }


def verify_final_state(result):

    print("\n[3] Verify Supervisor Completion")

    completed = list(
        result.get("completed_agents") or []
    )

    print(
        "Completed Agents:",
        completed,
    )

    assert completed == list(AGENT_SEQUENCE), (
        "Supervisor did not complete the expected sequence"
    )

    # ========================================================
    # Research
    # ========================================================

    research = result["research_output"]

    assert research["data_mode"] == (
        "real_source_page"
    )

    assert research["mock_fallback_used"] is False

    assert research["verified_evidence_count"] >= 1

    assert research["crm_write_performed"] is False

    assert research["send_performed"] is False

    print(
        "Verified Research Evidence:",
        research["verified_evidence_count"],
    )

    # ========================================================
    # Knowledge
    # ========================================================

    knowledge = result["knowledge_output"]

    assert knowledge["source_type"] == (
        "internal_product_knowledge"
    )

    assert knowledge["document_count"] >= 1

    print(
        "Knowledge Documents:",
        knowledge["document_count"],
    )

    # ========================================================
    # Analysis
    # ========================================================

    analysis = result["analysis_output"]

    assert analysis["data_mode"] == (
        "real_source_page"
    )

    assert analysis["selected_count"] >= 1

    assert analysis["selected_count"] == len(
        analysis["assessments"]
    )

    assert analysis["crm_stage_changed"] is False

    assert analysis["crm_write_performed"] is False

    assert analysis["send_performed"] is False

    assert result["candidate_leads"] == []

    print(
        "Analysis Assessments:",
        analysis["selected_count"],
    )

    # ========================================================
    # Sales
    # ========================================================

    sales = result["sales_output"]

    assert sales["data_mode"] == (
        "real_source_page"
    )

    assert sales["status"] == "complete"

    assert sales["draft_count"] >= 1

    assert sales["draft_count"] == len(
        sales["drafts"]
    )

    assert sales["send_performed"] is False

    assert sales["crm_write_performed"] is False

    print(
        "Internal Sales Drafts:",
        sales["draft_count"],
    )

    original_evidence = research[
        "verified_evidence"
    ]

    for draft in sales["drafts"]:

        assert draft["draft_status"] == (
            "real_internal_review_only"
        )

        assert draft["entry_point"] in original_evidence

        assert draft["requires_human_review"] is True

        assert draft["send_performed"] is False

        assert draft["crm_write_performed"] is False

        assert DRAFT_BANNER in draft["outreach_draft"]

        assert draft["entry_point"]["quote"] in (
            draft["outreach_draft"]
        )

        assert draft["entry_point"]["source_url"] in (
            draft["outreach_draft"]
        )

    # ========================================================
    # CRM
    # ========================================================

    crm = result["crm_output"]

    assert crm["data_mode"] == (
        "real_source_page"
    )

    assert crm["mode"] == "read_only"

    assert crm["candidate_count"] == (
        analysis["selected_count"]
    )

    assert crm["query_count"] == 1

    assert crm["read_performed"] is True

    assert crm["create_performed"] is False

    assert crm["update_performed"] is False

    assert crm["stage_changed"] is False

    assert crm["send_performed"] is False

    assert crm["requires_human_review"] is True

    assert crm["write_block_reason"] == (
        "no_explicit_write_authorization"
    )

    print(
        "CRM Candidates:",
        crm["candidate_count"],
    )

    print(
        "CRM Existing:",
        crm["existing_count"],
    )

    print(
        "CRM Missing:",
        crm["missing_count"],
    )

    print(
        "CRM Duplicates:",
        crm["duplicate_count"],
    )

    assert (
        crm["existing_count"]
        + crm["missing_count"]
        + crm["duplicate_count"]
    ) == crm["candidate_count"]

    # ========================================================
    # Final user-facing source-backed results
    # ========================================================

    print("\n[4] Real Company Review Records")

    for review in crm["review_records"]:

        print("\n" + "-" * 60)

        print(
            "Company:",
            review["company"],
        )

        print(
            "CRM Lookup:",
            review["lookup_status"],
        )

        print(
            "CRM Provenance:",
            review["crm_record_provenance"],
        )

        print(
            "Draft Present:",
            review["draft_present"],
        )

        print(
            "Source Evidence Count:",
            review["source_evidence_count"],
        )

        print(
            "Original URLs:",
        )

        for url in review["source_urls"]:

            print("-", url)

        print(
            "Existing Stage:",
            review["existing_stage"],
        )

        print(
            "Existing Next Action:",
            review["existing_next_action"],
        )

        print(
            "Proposed Next Action:",
            review["proposed_next_action"],
        )

        print(
            "Manual Review:",
            review["suggested_review"],
        )

        assert review["action_taken"] == "none"

        assert review["crm_write_performed"] is False

        assert review["requires_human_review"] is True

    print("\nFive Agent Reliability: PASS")

    return crm


def main():

    print("=" * 68)

    print(
        "Phase 6.6 - Five Real Agents Integration"
    )

    print("=" * 68)

    # --------------------------------------------------------
    # 1. CRM snapshot before execution
    # --------------------------------------------------------

    print("\n[1] CRM Snapshot Before Execution")

    before = capture_crm_snapshot()

    print(
        "CRM Rows:",
        before["row_count"],
    )

    print(
        "CRM SHA256:",
        before["sha256"],
    )

    # --------------------------------------------------------
    # 2. Compile existing Supervisor graph
    # --------------------------------------------------------

    print("\n[2] Running Five-Agent LangGraph...")

    graph = create_phase6_graph()

    final_result = None

    crm = None

    try:

        final_result = graph.invoke(
            initial_state(),
            config={
                "recursion_limit": 35,
            },
        )

        crm = verify_final_state(
            final_result
        )

    finally:

        # Always check CRM even if an Agent fails.
        print("\n[5] CRM Snapshot After Execution")

        after = capture_crm_snapshot()

        print(
            "CRM Rows:",
            after["row_count"],
        )

        print(
            "CRM SHA256:",
            after["sha256"],
        )

        assert before == after, (
            "CRM query-result snapshot changed "
            "during Phase 6 execution. "
            "Stop and investigate before continuing."
        )

        print(
            "CRM Query Result Unchanged: PASS"
        )

    # --------------------------------------------------------
    # 6. Check the snapshot observed inside CRM Worker
    # --------------------------------------------------------

    assert crm is not None

    assert crm["crm_query_snapshot_sha256"] == (
        before["sha256"]
    ), (
        "CRM Worker observed data different from "
        "the pre-execution snapshot"
    )

    print("\n" + "=" * 68)

    print(
        "Phase 6.6 Five Real Agents Integration Passed"
    )

    print("=" * 68)

    print("\nVerification Summary:")

    print("Real Research: PASS")
    print("Knowledge MCP: PASS")
    print("Real Analysis: PASS")
    print("Real Sales: PASS")
    print("Read-only CRM: PASS")
    print("Supervisor Routing: PASS")
    print("Source URL Provenance: PASS")
    print("No Mock Fallback: PASS")
    print("No External Sending: PASS")
    print("No CRM Create / Update: PASS")
    print("CRM Query Snapshot Unchanged: PASS")


if __name__ == "__main__":

    main()
