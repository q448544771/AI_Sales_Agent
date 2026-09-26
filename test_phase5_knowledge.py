"""Phase 5.4 Knowledge Agent unit and graph tests."""

import json
import unittest

from app.graph.multi_workflow import create_multi_graph
from app.multi_agent.contracts import AGENT_SEQUENCE

from app.multi_agent.knowledge_agent import (
    build_knowledge_queries,
    run_knowledge,
)


DOCUMENT = {
    "content": (
        "支持汽车零部件外观缺陷检测、尺寸测量及装配检测。"
    ),
    "source": "vision_solution.md",
    "metadata": {
        "source": "vision_solution.md",
    },
}


def success_result(documents=None):

    if documents is None:
        documents = [DOCUMENT]

    return {
        "success": True,
        "query": "test",
        "count": len(documents),
        "results": documents,
    }


class FakeKnowledgeTool:

    name = "search_product_knowledge"

    def __init__(self, result=None, failure=None):

        self.result = (
            result
            if result is not None
            else success_result()
        )

        self.failure = failure
        self.calls = []

    def invoke(self, arguments):

        self.calls.append(dict(arguments))

        if self.failure is not None:
            raise self.failure

        return self.result


def research_state():

    return {
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
                    "company": "测试结构件企业",
                    "profile": {
                        "signals": ["新增机器人焊接工位"],
                    },
                    "news": [
                        "计划升级焊缝检测及质量追溯",
                    ],
                    "jobs": [
                        "质量检测工程师",
                    ],
                },
            ],
        },
    }


class KnowledgeAgentTests(unittest.TestCase):

    def test_research_signals_drive_contextual_query(self):

        queries = build_knowledge_queries(research_state())

        self.assertEqual(len(queries), 2)

        self.assertIn("焊缝检测", queries[1])

        self.assertIn("质量追溯", queries[1])

    def test_no_research_uses_baseline_query(self):

        queries = build_knowledge_queries({
            "goal": {
                "product_focus": "工业机器视觉质检",
                "target_industry": "汽车零部件",
            },
        })

        self.assertEqual(len(queries), 1)

        self.assertIn("工业机器视觉质检", queries[0])

    def test_document_deduplication_and_source(self):

        tool = FakeKnowledgeTool()

        result = run_knowledge(
            research_state(),
            tool=tool,
        )

        output = result["knowledge_output"]
        context = result["knowledge_context"]

        self.assertEqual(output["mcp_calls"], 2)

        self.assertEqual(len(tool.calls), 2)

        self.assertEqual(output["document_count"], 1)

        self.assertEqual(len(context), 1)

        self.assertEqual(
            context[0]["source"],
            "vision_solution.md",
        )

        self.assertEqual(
            output["query_log"][1]["new_unique_documents"],
            0,
        )

    def test_empty_retrieval_does_not_invent_knowledge(self):

        tool = FakeKnowledgeTool(
            result=success_result([])
        )

        result = run_knowledge(
            research_state(),
            tool=tool,
        )

        self.assertEqual(
            result["knowledge_output"]["status"],
            "empty",
        )

        self.assertEqual(
            result["knowledge_context"],
            [],
        )

    def test_mcp_reported_failure(self):

        tool = FakeKnowledgeTool(
            result={
                "success": False,
                "message": "retriever unavailable",
                "results": [],
            }
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "retriever unavailable",
        ):
            run_knowledge(
                research_state(),
                tool=tool,
            )

    def test_malformed_result_is_rejected(self):

        tool = FakeKnowledgeTool(
            result={"success": True}
        )

        with self.assertRaises(ValueError):
            run_knowledge(
                research_state(),
                tool=tool,
            )

    def test_mcp_transport_error_is_not_hidden(self):

        tool = FakeKnowledgeTool(
            failure=RuntimeError("MCP disconnected")
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "Knowledge MCP tool invocation failed",
        ):
            run_knowledge(
                research_state(),
                tool=tool,
            )

    def test_wrong_tool_is_rejected(self):

        tool = FakeKnowledgeTool()
        tool.name = "update_lead_stage"

        with self.assertRaises(ValueError):
            run_knowledge(
                research_state(),
                tool=tool,
            )

        self.assertEqual(tool.calls, [])

    def test_hard_call_limit(self):

        tool = FakeKnowledgeTool()

        result = run_knowledge(
            research_state(),
            tool=tool,
            max_calls=99,
        )

        self.assertLessEqual(
            result["knowledge_output"]["mcp_calls"],
            2,
        )

        self.assertLessEqual(len(tool.calls), 2)

    def test_supervisor_research_knowledge_handoff(self):

        tool = FakeKnowledgeTool()

        def research_worker(state):
            return {
                "research_output": research_state()["research_output"]
            }

        def knowledge_worker(state):

            self.assertIn("research_output", state)

            return run_knowledge(
                state,
                tool=tool,
            )

        def other_worker(name):

            def worker(state):

                self.assertTrue(state["knowledge_context"])

                return {
                    f"{name}_output": {
                        "mode": "test_stub",
                    }
                }

            return worker

        workers = {
            "research": research_worker,
            "knowledge": knowledge_worker,
            "analysis": other_worker("analysis"),
            "sales": other_worker("sales"),
            "crm": other_worker("crm"),
        }

        graph = create_multi_graph(workers)

        result = graph.invoke({
            "goal": research_state()["goal"],
            "completed_agents": [],
            "supervisor_turns": 0,
            "supervisor_max_turns": 10,
        })

        self.assertEqual(
            result["completed_agents"],
            list(AGENT_SEQUENCE),
        )

        self.assertEqual(
            result["status"],
            "multi_agent_completed",
        )

        self.assertEqual(
            result["knowledge_output"]["document_count"],
            1,
        )


if __name__ == "__main__":
    unittest.main()