
"""Phase 5.5 - Analysis Agent tests."""

import copy
import json
import unittest

from langchain_core.messages import AIMessage

from app.graph.multi_workflow import create_multi_graph

from app.multi_agent.contracts import AGENT_SEQUENCE

from app.multi_agent.analysis_agent import run_analysis


COMPANY = "测试精密汽车零部件有限公司"

FACT = "新增两条自动化生产线"

KNOWLEDGE_SOURCE = "vision_solution.md"

KNOWLEDGE_CONTENT = (
    "工业机器视觉方案支持汽车零部件外观缺陷检测、"
    "尺寸测量和装配检测。"
)


# ============================================================
# Fake LLM
# ============================================================

class FakeAnalysisLLM:

    def __init__(self, data):

        self.data = data

        self.calls = 0

        self.last_prompt = None

    def invoke(self, prompt):

        self.calls += 1

        self.last_prompt = prompt

        return AIMessage(
            content=json.dumps(
                self.data,
                ensure_ascii=False,
            )
        )


# ============================================================
# Test fixtures
# ============================================================

def sample_state():

    return {
        "goal": {
            "target_industry": "汽车零部件",
            "target_region": "中国",
            "target_count": 2,
            "product_focus": "工业机器视觉质检解决方案",
        },

        "research_output": {
            "status": "complete",
            "data_mode": "mock_company_mcp",
            "company_records": [
                {
                    "company": COMPANY,
                    "profile": {
                        "name": COMPANY,
                        "region": "江苏",
                        "signals": [
                            "新能源汽车零部件扩产",
                        ],
                    },
                    "news": (
                        "新建生产基地\n"
                        "新增两条自动化生产线"
                    ),
                    "jobs": (
                        "机器视觉工程师\n"
                        "质量工程师"
                    ),
                },
            ],
        },

        "knowledge_output": {
            "status": "complete",
            "source_type": "internal_product_knowledge",
            "documents": [
                {
                    "content": KNOWLEDGE_CONTENT,
                    "source": KNOWLEDGE_SOURCE,
                    "metadata": {
                        "source": KNOWLEDGE_SOURCE,
                    },
                },
            ],
        },

        "knowledge_context": [
            {
                "content": KNOWLEDGE_CONTENT,
                "source": KNOWLEDGE_SOURCE,
            },
        ],
    }


def valid_assessment():

    return {
        "company": COMPANY,

        "purchase_intent_score": 0.78,

        "opportunity_level": "高",

        "evidence": [
            FACT,
            "机器视觉工程师",
        ],

        "solution_match": [
            {
                "company_signal": FACT,
                "knowledge_quote": "外观缺陷检测",
                "knowledge_source": KNOWLEDGE_SOURCE,
                "reason": (
                    "自动化产线可能存在在线质检需求，"
                    "具体检测对象需要进一步确认。"
                ),
            },
        ],

        "recommended_action": (
            "联系质量与自动化负责人，确认检测对象、"
            "产线节拍、预算及采购计划；准备知识库已支持的"
            "外观缺陷检测资料，后续安排样件验证。"
        ),
    }


# ============================================================
# Tests
# ============================================================

class AnalysisAgentTests(unittest.TestCase):

    def test_valid_grounded_assessment(self):

        model = FakeAnalysisLLM([
            valid_assessment(),
        ])

        result = run_analysis(
            sample_state(),
            llm=model,
        )

        self.assertEqual(model.calls, 1)

        self.assertEqual(
            result["analysis_output"]["status"],
            "complete",
        )

        self.assertEqual(
            result["analysis_output"]["data_mode"],
            "mock_company_mcp",
        )

        self.assertEqual(
            len(result["candidate_leads"]),
            1,
        )

        self.assertIn(
            KNOWLEDGE_SOURCE,
            result["candidate_leads"][0]["solution_match"][0],
        )

        provenance = (
            result["analysis_output"]
            ["assessments"][0]
            ["match_provenance"][0]
        )

        self.assertEqual(
            provenance["knowledge_quote"],
            "外观缺陷检测",
        )

        self.assertFalse(
            result["analysis_output"]["crm_stage_changed"]
        )

    def test_invented_enterprise_evidence_is_rejected(self):

        assessment = valid_assessment()

        assessment["evidence"].append(
            "企业已经确认采购预算"
        )

        with self.assertRaisesRegex(
            ValueError,
            "unsupported facts",
        ):

            run_analysis(
                sample_state(),
                llm=FakeAnalysisLLM([assessment]),
            )

    def test_unknown_company_is_rejected(self):

        assessment = valid_assessment()

        assessment["company"] = "不存在于研究记录的企业"

        with self.assertRaisesRegex(
            ValueError,
            "Unknown company",
        ):

            run_analysis(
                sample_state(),
                llm=FakeAnalysisLLM([assessment]),
            )

    def test_fabricated_product_quote_is_rejected(self):

        assessment = valid_assessment()

        assessment["solution_match"][0][
            "knowledge_quote"
        ] = "已实现百分之百缺陷检出率"

        with self.assertRaisesRegex(
            ValueError,
            "knowledge quotation or source",
        ):

            run_analysis(
                sample_state(),
                llm=FakeAnalysisLLM([assessment]),
            )

    def test_unknown_knowledge_source_is_rejected(self):

        assessment = valid_assessment()

        assessment["solution_match"][0][
            "knowledge_source"
        ] = "invented_case.md"

        with self.assertRaisesRegex(
            ValueError,
            "knowledge quotation or source",
        ):

            run_analysis(
                sample_state(),
                llm=FakeAnalysisLLM([assessment]),
            )

    def test_invalid_score_is_rejected(self):

        assessment = valid_assessment()

        assessment["purchase_intent_score"] = 1.5

        with self.assertRaisesRegex(
            ValueError,
            "invalid purchase_intent_score",
        ):

            run_analysis(
                sample_state(),
                llm=FakeAnalysisLLM([assessment]),
            )

    def test_output_must_respect_target_count(self):

        assessment = valid_assessment()

        with self.assertRaisesRegex(
            ValueError,
            "more than",
        ):

            run_analysis(
                {
                    **sample_state(),
                    "goal": {
                        "target_count": 1,
                    },
                },
                llm=FakeAnalysisLLM([
                    assessment,
                    copy.deepcopy(assessment),
                ]),
            )

    def test_duplicate_company_is_rejected(self):

        assessment = valid_assessment()

        with self.assertRaisesRegex(
            ValueError,
            "Duplicate company",
        ):

            run_analysis(
                sample_state(),
                llm=FakeAnalysisLLM([
                    assessment,
                    copy.deepcopy(assessment),
                ]),
            )

    def test_unsupported_crm_action_is_rejected(self):

        assessment = valid_assessment()

        assessment["recommended_action"] = (
            "直接推进CRM阶段至qualified。"
        )

        with self.assertRaisesRegex(
            ValueError,
            "unsupported factual or CRM claim",
        ):

            run_analysis(
                sample_state(),
                llm=FakeAnalysisLLM([assessment]),
            )

    def test_empty_research_does_not_call_llm(self):

        state = sample_state()

        state["research_output"]["company_records"] = []

        model = FakeAnalysisLLM([
            valid_assessment(),
        ])

        result = run_analysis(
            state,
            llm=model,
        )

        self.assertEqual(model.calls, 0)

        self.assertEqual(
            result["candidate_leads"],
            [],
        )

        self.assertEqual(
            result["analysis_output"]["status"],
            "insufficient_research",
        )

    def test_no_knowledge_requires_empty_solution_match(self):

        state = sample_state()

        state["knowledge_output"]["documents"] = []

        state["knowledge_context"] = []

        assessment = valid_assessment()

        assessment["solution_match"] = []

        result = run_analysis(
            state,
            llm=FakeAnalysisLLM([assessment]),
        )

        self.assertEqual(
            result["candidate_leads"][0]["solution_match"],
            [],
        )

        self.assertEqual(
            result["analysis_output"]["knowledge_document_count"],
            0,
        )

    def test_supervisor_state_handoff(self):

        state = sample_state()

        model = FakeAnalysisLLM([
            valid_assessment(),
        ])

        def research_worker(current):

            return {
                "research_output": state["research_output"]
            }

        def knowledge_worker(current):

            self.assertTrue(
                current.get("research_output")
            )

            return {
                "knowledge_output": state["knowledge_output"],
                "knowledge_context": state["knowledge_context"],
            }

        def analysis_worker(current):

            self.assertTrue(
                current.get("research_output")
            )

            self.assertTrue(
                current.get("knowledge_context")
            )

            return run_analysis(
                current,
                llm=model,
            )

        def stub_worker(name):

            def worker(current):

                self.assertTrue(
                    current.get("candidate_leads")
                )

                return {
                    f"{name}_output": {
                        "mode": "test_stub",
                    }
                }

            return worker

        graph = create_multi_graph({
            "research": research_worker,
            "knowledge": knowledge_worker,
            "analysis": analysis_worker,
            "sales": stub_worker("sales"),
            "crm": stub_worker("crm"),
        })

        result = graph.invoke({
            "goal": state["goal"],
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
            result["analysis_output"]["selected_count"],
            1,
        )

        self.assertEqual(model.calls, 1)

    def test_short_valid_knowledge_quote_is_allowed(self):

        assessment = valid_assessment()

        # 尺寸测量虽然不足6个字符，
        # 但确实存在于测试知识文档中。
        assessment["solution_match"][0][
            "knowledge_quote"
        ] = "尺寸测量"

        result = run_analysis(
            sample_state(),
            llm=FakeAnalysisLLM([assessment]),
        )

        provenance = (
            result["analysis_output"]
            ["assessments"][0]
            ["match_provenance"][0]
        )

        self.assertEqual(
            provenance["knowledge_quote"],
            "尺寸测量",
        )

        
if __name__ == "__main__":
    unittest.main()
