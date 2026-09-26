
"""Phase 5.3 Research Agent tests.

No external API or MCP subprocess needed.
"""

import unittest

from langchain_core.messages import (
    AIMessage,
    ToolMessage,
)

from app.multi_agent.research_agent import run_research


# ============================================================
# Fake MCP Tool
# ============================================================

class FakeTool:

    def __init__(
        self,
        name,
        result=None,
        failure=None,
    ):

        self.name = name

        self.result = result

        self.failure = failure

        self.calls = []

    def invoke(self, args):

        self.calls.append(args)

        if self.failure:
            raise self.failure

        return self.result


# ============================================================
# Scripted Fake LLM
# ============================================================

class ScriptedModel:

    def __init__(self, replies):

        self.replies = list(replies)

        self.bound_names = []

        self.inputs = []

    def bind_tools(self, tools):

        self.bound_names = [
            t.name
            for t in tools
        ]

        return self

    def invoke(self, messages):

        self.inputs.append(
            list(messages)
        )

        if not self.replies:

            raise AssertionError(
                "Test exhausted scripted AI replies"
            )

        return self.replies.pop(0)


# ============================================================
# Test Helpers
# ============================================================

def call(name, args, id_):

    return {
        "name": name,
        "args": args,
        "id": id_,
    }


def reply(*calls):

    return AIMessage(
        content="",
        tool_calls=list(calls),
    )


def mock_tools():

    return [
        FakeTool(
            "search_company",
            [
                {
                    "name": "示例零部件企业",
                    "region": "江苏",
                }
            ],
        ),
        FakeTool(
            "get_company_news",
            [
                "新增自动化生产线",
            ],
        ),
        FakeTool(
            "get_company_jobs",
            [
                "视觉检测工程师",
            ],
        ),
    ]


# ============================================================
# Research Agent Tests
# ============================================================

class ResearchAgentTests(unittest.TestCase):

    # --------------------------------------------------------
    # 1. 企业搜索 + 新闻 + 招聘 + 原始数据保存
    # --------------------------------------------------------

    def test_company_mcp_research_and_provenance(self):

        tools = mock_tools()

        model = ScriptedModel([
            reply(
                call(
                    "search_company",
                    {
                        "industry": "汽车零部件",
                        "region": "中国",
                    },
                    "s1",
                )
            ),
            reply(
                call(
                    "get_company_news",
                    {
                        "company": "示例零部件企业",
                    },
                    "n1",
                ),
                call(
                    "get_company_jobs",
                    {
                        "company": "示例零部件企业",
                    },
                    "j1",
                ),
            ),
            AIMessage(
                content="调研完成"
            ),
        ])

        state = {
            "goal": {
                "target_count": 1,
            },
            "research_plan": None,
        }

        result = run_research(
            state,
            llm=model,
            tools=tools,
        )["research_output"]

        self.assertEqual(
            result["status"],
            "complete",
        )

        self.assertEqual(
            result["data_mode"],
            "mock_company_mcp",
        )

        self.assertEqual(
            (
                result["search_calls"],
                result["detail_calls"],
            ),
            (1, 2),
        )

        self.assertEqual(
            result["company_records"][0]["news"],
            ["新增自动化生产线"],
        )

        self.assertEqual(
            result["company_records"][0]["jobs"],
            ["视觉检测工程师"],
        )

        self.assertEqual(
            len(result["tool_trace"]),
            3,
        )

        self.assertEqual(
            set(model.bound_names),
            {
                "search_company",
                "get_company_news",
                "get_company_jobs",
            },
        )

        # 确认 ToolMessage 与 Tool Call ID 对应
        tool_ids = {
            msg.tool_call_id
            for turn in model.inputs
            for msg in turn
            if isinstance(msg, ToolMessage)
        }

        self.assertEqual(
            tool_ids,
            {"s1", "n1", "j1"},
        )

    # --------------------------------------------------------
    # 2. 搜索预算与重复调用缓存
    # --------------------------------------------------------

    def test_search_budget_and_no_double_count_on_cached_call(self):

        tools = mock_tools()

        model = ScriptedModel([
            reply(
                call(
                    "search_company",
                    {
                        "industry": "汽车零部件",
                        "region": "中国",
                    },
                    "s1",
                ),
                call(
                    "search_company",
                    {
                        "industry": "汽车零部件",
                        "region": "中国",
                    },
                    "s2",
                ),
                call(
                    "search_company",
                    {
                        "industry": "汽车零部件",
                        "region": "广东",
                    },
                    "s3",
                ),
            ),
            AIMessage(content="结束"),
        ])

        result = run_research(
            {
                "goal": {
                    "target_count": 1,
                },
            },
            llm=model,
            tools=tools,
            search_budget=1,
        )["research_output"]

        self.assertEqual(
            result["search_calls"],
            1,
        )

        self.assertEqual(
            len(tools[0].calls),
            1,
        )

        self.assertEqual(
            len(result["rejected_calls"]),
            1,
        )

    # --------------------------------------------------------
    # 3. Research Agent 禁止调用 CRM
    # --------------------------------------------------------

    def test_crm_call_is_rejected(self):

        tools = mock_tools()

        model = ScriptedModel([
            reply(
                call(
                    "update_lead_stage",
                    {
                        "company": "测试",
                        "stage": "won",
                    },
                    "c1",
                )
            ),
            AIMessage(content="结束"),
        ])

        result = run_research(
            {},
            llm=model,
            tools=tools,
        )["research_output"]

        self.assertEqual(
            result["search_calls"],
            0,
        )

        self.assertEqual(
            len(result["rejected_calls"]),
            1,
        )

        self.assertFalse(
            any(tool.calls for tool in tools)
        )

    # --------------------------------------------------------
    # 4. 禁止查询未知企业
    # --------------------------------------------------------

    def test_unconfirmed_company_is_rejected(self):

        tools = mock_tools()

        model = ScriptedModel([
            reply(
                call(
                    "get_company_news",
                    {
                        "company": "凭空编造的企业",
                    },
                    "n1",
                )
            ),
            AIMessage(content="结束"),
        ])

        result = run_research(
            {},
            llm=model,
            tools=tools,
        )["research_output"]

        self.assertEqual(
            result["detail_calls"],
            0,
        )

        self.assertEqual(
            len(result["rejected_calls"]),
            1,
        )

    # --------------------------------------------------------
    # 5. 连续三次搜索为空则停止
    # --------------------------------------------------------

    def test_stops_after_three_empty_searches(self):

        tools = mock_tools()

        tools[0].result = []

        model = ScriptedModel([
            reply(
                *(
                    call(
                        "search_company",
                        {
                            "industry": "汽车零部件",
                            "region": region,
                        },
                        f"s{i}",
                    )
                    for i, region in enumerate(
                        (
                            "四川",
                            "天津",
                            "福建",
                            "云南",
                        ),
                        1,
                    )
                )
            ),
            AIMessage(content="无结果"),
        ])

        result = run_research(
            {},
            llm=model,
            tools=tools,
        )["research_output"]

        self.assertEqual(
            result["search_calls"],
            3,
        )

        self.assertEqual(
            result["empty_search_streak"],
            3,
        )

        self.assertEqual(
            len(result["rejected_calls"]),
            1,
        )

    # --------------------------------------------------------
    # 6. 不超过目标企业数量
    # --------------------------------------------------------

    def test_enrichment_does_not_exceed_target_company_count(self):

        tools = mock_tools()

        model = ScriptedModel([
            reply(
                call(
                    "search_company",
                    {
                        "industry": "汽车零部件",
                        "region": "中国",
                    },
                    "s1",
                )
            ),
            reply(
                call(
                    "get_company_news",
                    {
                        "company": "示例零部件企业",
                    },
                    "n1",
                )
            ),
            reply(
                call(
                    "get_company_news",
                    {
                        "company": "历史企业",
                    },
                    "n2",
                )
            ),
            AIMessage(content="完成"),
        ])

        result = run_research(
            {
                "goal": {
                    "target_count": 1,
                },
                "memory_context": [
                    {
                        "company": "历史企业",
                    }
                ],
            },
            llm=model,
            tools=tools,
        )["research_output"]

        self.assertEqual(
            result["enriched_company_count"],
            1,
        )

        self.assertEqual(
            result["detail_calls"],
            1,
        )

        self.assertEqual(
            len(result["rejected_calls"]),
            1,
        )

    # --------------------------------------------------------
    # 7. MCP 异常不能伪装成成功
    # --------------------------------------------------------

    def test_company_mcp_failure_does_not_fake_completion(self):

        tools = mock_tools()

        tools[0].failure = RuntimeError(
            "MCP disconnected"
        )

        model = ScriptedModel([
            reply(
                call(
                    "search_company",
                    {
                        "industry": "汽车零部件",
                        "region": "中国",
                    },
                    "s1",
                )
            ),
        ])

        with self.assertRaisesRegex(
            RuntimeError,
            "Company MCP tool search_company failed",
        ):

            run_research(
                {},
                llm=model,
                tools=tools,
            )

    # --------------------------------------------------------
    # 8. 最大轮数保护
    # --------------------------------------------------------

    def test_round_limit_returns_partial_result(self):

        tools = mock_tools()

        model = ScriptedModel([
            reply(
                call(
                    "search_company",
                    {
                        "industry": "汽车零部件",
                        "region": "中国",
                    },
                    "s1",
                )
            ),
        ])

        result = run_research(
            {},
            llm=model,
            tools=tools,
            max_rounds=1,
        )["research_output"]

        self.assertEqual(
            result["status"],
            "partial",
        )

        self.assertEqual(
            result["search_calls"],
            1,
        )


if __name__ == "__main__":
    unittest.main()