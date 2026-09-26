
"""
Phase 5.3.3 - Research Agent + Multi-Agent Graph Integration

Research Agent:
    Real DeepSeek + Real Company MCP communication

Other Agents:
    Test stubs only

Company data:
    Mock provider data

This test does not write CRM data or modify the Phase 4 workflow.
"""

import json

from app.graph.multi_workflow import create_multi_graph

from app.multi_agent.contracts import AGENT_SEQUENCE

from app.multi_agent.research_agent import run_research


# ============================================================
# 1. 实际 Research Agent
# ============================================================

def real_research_worker(state):

    print("\n[Research Agent] Starting...")

    result = run_research(
        state,
        max_rounds=6,
        search_budget=2,
        detail_budget=4,
    )

    research = result["research_output"]

    print(
        "[Research Agent] Status:",
        research["status"],
    )

    print(
        "[Research Agent] Search Calls:",
        research["search_calls"],
    )

    print(
        "[Research Agent] Detail Calls:",
        research["detail_calls"],
    )

    print(
        "[Research Agent] Company Records:",
        len(research["company_records"]),
    )

    return result


# ============================================================
# 2. 其他 Agent 使用测试替身
# ============================================================

def create_stub_worker(name):

    def worker(state):

        print(
            f"[{name.upper()} Agent] Test stub executed"
        )

        research = state.get(
            "research_output",
            {},
        )

        # 验证 Supervisor 已经传递 Research 结果
        assert research, (
            f"{name} cannot read research_output"
        )

        return {
            f"{name}_output": {
                "mode": "test_stub",
                "executed": False,
                "received_research": True,
            }
        }

    return worker


# ============================================================
# 3. 构建测试工作流
# ============================================================

def create_test_graph():

    workers = {
        "research": real_research_worker,

        "knowledge": create_stub_worker(
            "knowledge"
        ),

        "analysis": create_stub_worker(
            "analysis"
        ),

        "sales": create_stub_worker(
            "sales"
        ),

        "crm": create_stub_worker(
            "crm"
        ),
    }

    return create_multi_graph(workers)


# ============================================================
# 4. 初始化 State
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
# 5. 执行与验收
# ============================================================

def main():

    print("=" * 65)
    print("Phase 5.3.3 - Research + Supervisor Integration")
    print("=" * 65)

    graph = create_test_graph()

    state = create_initial_state()

    print("\n[1] Running Multi-Agent Graph...")

    result = graph.invoke(state)

    # ========================================================
    # Research Results
    # ========================================================

    research = result["research_output"]

    print("\n[2] Research Output")

    print(
        json.dumps(
            {
                "status": research["status"],
                "data_mode": research["data_mode"],
                "search_calls": research["search_calls"],
                "detail_calls": research["detail_calls"],
                "enriched_company_count": (
                    research["enriched_company_count"]
                ),
                "companies": [
                    item["company"]
                    for item in research["company_records"]
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )

    # ========================================================
    # Supervisor State
    # ========================================================

    print("\n[3] Supervisor State")

    print(
        "Completed Agents:",
        result["completed_agents"],
    )

    print(
        "Supervisor Turns:",
        result["supervisor_turns"],
    )

    print(
        "Next Agent:",
        result["next_agent"],
    )

    print(
        "Final Status:",
        result["status"],
    )

    # ========================================================
    # Reliability Assertions
    # ========================================================

    print("\n[4] Reliability Assertions")

    assert result["completed_agents"] == list(
        AGENT_SEQUENCE
    )

    assert result["next_agent"] == "finish"

    assert result["status"] == "multi_agent_completed"

    assert result["supervisor_turns"] == 5

    assert research["search_calls"] <= 2

    assert research["detail_calls"] <= 4

    assert research["enriched_company_count"] <= 2

    assert research["data_mode"] == "mock_company_mcp"

    assert research["tool_trace"], (
        "Research Agent did not execute any MCP tool"
    )

    allowed_tools = {
        "search_company",
        "get_company_news",
        "get_company_jobs",
    }

    assert all(
        item["tool"] in allowed_tools
        for item in research["tool_trace"]
    )

    for name in (
        "knowledge",
        "analysis",
        "sales",
        "crm",
    ):

        output = result[f"{name}_output"]

        assert output["mode"] == "test_stub"

        assert output["received_research"] is True

    print("Supervisor Routing: PASS")
    print("Research State Transfer: PASS")
    print("Research MCP Execution: PASS")
    print("Search Budget: PASS")
    print("Detail Budget: PASS")
    print("Tool Permission: PASS")
    print("Worker State Isolation: PASS")

    print("\n" + "=" * 65)
    print("Phase 5.3.3 Integration Test Passed")
    print("=" * 65)


if __name__ == "__main__":
    main()
