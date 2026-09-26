
"""
Phase 5.4.4 - Research + Knowledge Multi-Agent Integration

Real:
    Supervisor routing
    Research Agent + DeepSeek + Company MCP
    Knowledge Agent + Knowledge MCP + Chroma

Test stubs:
    Analysis Agent
    Sales Agent
    CRM Agent

The company data is still Mock data.
No CRM writes are performed.
The Phase 4 workflow is not modified.
"""

import json

from app.graph.multi_workflow import create_multi_graph

from app.multi_agent.contracts import AGENT_SEQUENCE

from app.multi_agent.research_agent import run_research

from app.multi_agent.knowledge_agent import (
    run_knowledge,
    build_knowledge_queries,
)


# ============================================================
# 1. Execution trace
# ============================================================

execution_trace = []


# ============================================================
# 2. Real Research Agent
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

    print(
        "Company Records:",
        len(output["company_records"]),
    )

    print(
        "Enriched Companies:",
        output["enriched_company_count"],
    )

    return result


# ============================================================
# 3. Real Knowledge Agent
# ============================================================

def knowledge_worker(state):

    execution_trace.append("knowledge")

    print("\n[2] Knowledge Agent Running...")

    research = state.get("research_output")

    assert research is not None, (
        "Knowledge Agent did not receive research_output"
    )

    assert research["company_records"], (
        "Research Agent returned no company records"
    )

    result = run_knowledge(state)

    output = result["knowledge_output"]

    print("Status:", output["status"])

    print("MCP Calls:", output["mcp_calls"])

    print("Documents:", output["document_count"])

    print("\nContextual Queries:")

    for query in output["queries"]:

        print("-", query)

    return result


# ============================================================
# 4. Remaining Agents - Test Stubs
# ============================================================

def make_stub_agent(name):

    def worker(state):

        execution_trace.append(name)

        print(f"\n[{name.upper()} Agent] Test Stub")

        research = state.get("research_output")
        knowledge = state.get("knowledge_output")
        context = state.get("knowledge_context")

        assert research is not None
        assert knowledge is not None
        assert context

        return {
            f"{name}_output": {
                "mode": "test_stub",
                "received_research": True,
                "received_knowledge": True,
                "research_company_count": len(
                    research["company_records"]
                ),
                "knowledge_document_count": len(context),
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
                "汽车零部件 扩产",
                "汽车零部件 机器视觉 招聘",
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
# 6. Graph Construction
# ============================================================

def create_integration_graph():

    workers = {
        "research": research_worker,

        "knowledge": knowledge_worker,

        "analysis": make_stub_agent("analysis"),

        "sales": make_stub_agent("sales"),

        "crm": make_stub_agent("crm"),
    }

    return create_multi_graph(workers)


# ============================================================
# 7. Integration Test
# ============================================================

def main():

    execution_trace.clear()

    print("=" * 65)
    print("Phase 5.4.4 - Research + Knowledge Integration")
    print("=" * 65)

    graph = create_integration_graph()

    state = create_initial_state()

    result = graph.invoke(state)

    research = result["research_output"]

    knowledge = result["knowledge_output"]

    context = result["knowledge_context"]

    # ========================================================
    # Research Statistics
    # ========================================================

    print("\n[3] Research Output")

    print(
        json.dumps(
            {
                "status": research["status"],
                "data_mode": research["data_mode"],
                "search_calls": research["search_calls"],
                "detail_calls": research["detail_calls"],
                "enriched_companies": (
                    research["enriched_company_count"]
                ),
                "companies": [
                    record["company"]
                    for record in research["company_records"]
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )

    # ========================================================
    # Knowledge Statistics
    # ========================================================

    print("\n[4] Knowledge Output")

    print(
        json.dumps(
            {
                "status": knowledge["status"],
                "source_type": knowledge["source_type"],
                "mcp_calls": knowledge["mcp_calls"],
                "document_count": knowledge["document_count"],
                "query_log": knowledge["query_log"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )

    print("\nKnowledge Sources:")

    for item in context:

        print("-", item["source"])

    # ========================================================
    # Supervisor State
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

    assert execution_trace == list(AGENT_SEQUENCE)

    assert result["completed_agents"] == list(
        AGENT_SEQUENCE
    )

    assert result["supervisor_turns"] == 5

    assert result["next_agent"] == "finish"

    assert result["status"] == "multi_agent_completed"

    # Research budget and source protection
    assert research["search_calls"] <= 2

    assert research["detail_calls"] <= 4

    assert research["enriched_company_count"] <= 2

    assert research["data_mode"] == "mock_company_mcp"

    assert research["tool_trace"]

    company_tools = {
        "search_company",
        "get_company_news",
        "get_company_jobs",
    }

    assert all(
        item["tool"] in company_tools
        for item in research["tool_trace"]
    )

    # Knowledge MCP and evidence protection
    assert 1 <= knowledge["mcp_calls"] <= 2

    assert knowledge["mcp_tool"] == "search_product_knowledge"

    assert knowledge["source_type"] == "internal_product_knowledge"

    assert knowledge["document_count"] >= 1

    assert len(context) == knowledge["document_count"]

    assert all(
        item["content"] and item["source"]
        for item in context
    )

    # Confirm query planning used the actual upstream state.
    expected_queries = build_knowledge_queries(result)

    assert knowledge["queries"] == expected_queries

    # Verify downstream state handoff.
    for name in ("analysis", "sales", "crm"):

        output = result[f"{name}_output"]

        assert output["mode"] == "test_stub"

        assert output["received_research"] is True

        assert output["received_knowledge"] is True

    print("Supervisor Routing: PASS")
    print("Research -> Knowledge State Transfer: PASS")
    print("Company MCP: PASS")
    print("Knowledge MCP: PASS")
    print("Research Budget: PASS")
    print("Knowledge Budget: PASS")
    print("Knowledge Source Preservation: PASS")
    print("Downstream State Transfer: PASS")
    print("No CRM Write: PASS (CRM worker is a test stub)")

    print("\n" + "=" * 65)
    print("Phase 5.4.4 Integration Test Passed")
    print("=" * 65)


if __name__ == "__main__":
    main()
