"""Phase 5.4 - Real Knowledge MCP integration test."""

from app.multi_agent.knowledge_agent import run_knowledge


def main():

    print("=" * 60)
    print("Phase 5.4 - Knowledge MCP Integration")
    print("=" * 60)

    state = {
        "goal": {
            "product_focus": "工业机器视觉质检解决方案",
            "target_industry": "汽车零部件",
            "target_count": 2,
        },
        "research_output": {
            "status": "complete",
            "data_mode": "mock_company_mcp",
            "company_records": [
                {
                    "company": "模拟新能源汽车零部件企业",
                    "profile": {
                        "signals": [
                            "新增自动化装配与检测工位",
                        ],
                    },
                    "news": [
                        "计划提升质量追溯能力",
                    ],
                    "jobs": [
                        "机器视觉工程师",
                    ],
                },
            ],
        },
    }

    print("\n[1] Calling Knowledge MCP...")

    result = run_knowledge(state)

    output = result["knowledge_output"]
    context = result["knowledge_context"]

    print("\n[2] Retrieval Statistics")

    print("Status:", output["status"])
    print("Source Type:", output["source_type"])
    print("MCP Calls:", output["mcp_calls"])
    print("Document Count:", output["document_count"])

    print("\n[3] Queries")

    for query in output["queries"]:
        print("-", query)

    print("\n[4] Retrieved Documents")

    for document in context:
        print("Source:", document["source"])
        print("Content:", document["content"][:250])
        print()

    assert output["mcp_calls"] <= 2
    assert output["document_count"] >= 1
    assert len(context) == output["document_count"]

    assert all(
        document["content"] and document["source"]
        for document in context
    )

    print("\nKnowledge MCP: PASS")
    print("Call Budget: PASS")
    print("Document Source: PASS")
    print("State Output: PASS")


if __name__ == "__main__":
    main()