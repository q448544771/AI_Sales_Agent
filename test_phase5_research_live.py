
"""
Phase 5.3.2 - Research Agent Live Integration Test

真实调用链：

DeepSeek
    ↓
Research Agent
    ↓
LangChain Tool
    ↓
Company MCP Client
    ↓
Company MCP Server
    ↓
Mock Company Data

注意：
这里的真实联调是指 LLM + MCP 通信链路。
当前企业数据仍然是 Mock 数据，不代表真实互联网调研。

不执行 CRM 写入，不修改 Phase 4 Workflow。
"""

import json

from app.multi_agent.research_agent import run_research


def main():

    print("=" * 65)
    print("Phase 5.3.2 - Research Agent Live Integration")
    print("=" * 65)

    # ========================================================
    # 1. 本轮销售目标
    # ========================================================

    state = {
        "goal": {
            "target_industry": "汽车零部件",
            "target_region": "中国",
            "target_count": 2,
            "product_focus": "工业机器视觉质检解决方案",
            "user_requirement": (
                "寻找近期可能需要机器视觉质检方案的汽车零部件企业，"
                "重点关注扩产、新建产线和自动化升级。"
            ),
        },

        "research_plan": {
            "buying_signals": [
                "新建或扩建生产线",
                "自动化及智能制造升级",
                "招聘机器视觉工程师",
                "招聘质量检测工程师",
            ],

            "search_queries": [
                "中国汽车零部件扩产",
                "汽车零部件机器视觉招聘",
            ],
        },

        "memory_context": [],
    }

    # ========================================================
    # 2. 运行真实 Research Agent
    # ========================================================

    print("\n[1] Connecting DeepSeek and Company MCP...")

    output = run_research(
        state,
        max_rounds=6,
        search_budget=2,
        detail_budget=4,
    )

    result = output["research_output"]

    # ========================================================
    # 3. 显示执行统计
    # ========================================================

    print("\n[2] Research Statistics")

    print("Status:", result["status"])

    print("Data Mode:", result["data_mode"])

    print("Search Calls:", result["search_calls"])

    print("Detail Calls:", result["detail_calls"])

    print(
        "Enriched Companies:",
        result["enriched_company_count"],
    )

    print(
        "Empty Search Streak:",
        result["empty_search_streak"],
    )

    print(
        "Rejected Calls:",
        len(result["rejected_calls"]),
    )

    # ========================================================
    # 4. 展示真正执行的 MCP 工具
    # ========================================================

    print("\n[3] Actual MCP Tool Calls")

    for index, item in enumerate(
        result["tool_trace"],
        start=1,
    ):

        print(f"\nTool #{index}")

        print("Name:", item["tool"])

        print(
            "Arguments:",
            json.dumps(
                item["args"],
                ensure_ascii=False,
            ),
        )

        print("Source:", item["source"])

    # ========================================================
    # 5. 展示结构化企业结果
    # ========================================================

    print("\n[4] Structured Company Records")

    for record in result["company_records"]:

        print("\nCompany:", record["company"])

        print(
            "Profile:",
            json.dumps(
                record["profile"],
                ensure_ascii=False,
            ),
        )

        print(
            "News:",
            json.dumps(
                record["news"],
                ensure_ascii=False,
            ),
        )

        print(
            "Jobs:",
            json.dumps(
                record["jobs"],
                ensure_ascii=False,
            ),
        )

    # ========================================================
    # 6. 展示被拒绝的调用
    # ========================================================

    print("\n[5] Rejected Tool Calls")

    for item in result["rejected_calls"]:

        print(
            json.dumps(
                item,
                ensure_ascii=False,
            )
        )

    # ========================================================
    # 7. 模型总结，仅用于查看，不作为企业证据
    # ========================================================

    print("\n[6] LLM Summary (Unverified)")

    print(
        result["model_summary_unverified"]
    )

    # ========================================================
    # 8. 可靠性断言
    # ========================================================

    print("\n[7] Reliability Assertions")

    allowed_tools = {
        "search_company",
        "get_company_news",
        "get_company_jobs",
    }

    assert result["search_calls"] <= 2

    assert result["detail_calls"] <= 4

    assert result["enriched_company_count"] <= 2

    assert result["data_mode"] == "mock_company_mcp"

    assert all(
        item["tool"] in allowed_tools
        for item in result["tool_trace"]
    )

    print("Search Budget: PASS")
    print("Detail Budget: PASS")
    print("Company Count Limit: PASS")
    print("Tool Permission: PASS")
    print("Data Source Label: PASS")

    print("\n" + "=" * 65)
    print("Phase 5.3.2 Integration Test Finished")
    print("=" * 65)


if __name__ == "__main__":
    main()
