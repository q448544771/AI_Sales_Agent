"""Phase 5.6 - Sales Agent unit and graph integration tests."""

import copy
import json
import unittest

from langchain_core.messages import AIMessage

from app.graph.multi_workflow import create_multi_graph
from app.multi_agent.contracts import AGENT_SEQUENCE
from app.multi_agent.sales_agent import run_sales


COMPANY = "测试新能源汽车零部件有限公司"

EVIDENCE = "新增两条自动化生产线"

SOURCE = "vision_solution.md"

QUOTE = "支持汽车零部件外观缺陷检测"

KNOWLEDGE_CONTENT = (
    "工业机器视觉质检解决方案："
    "支持汽车零部件外观缺陷检测、尺寸测量与装配检测。"
)


# ============================================================
# 1. Fake LLM
# ============================================================

class FakeSalesLLM:

    def __init__(self, payload):

        self.payload = payload

        self.calls = 0
        self.last_prompt = None

    def invoke(self, prompt):

        self.calls += 1
        self.last_prompt = prompt

        return AIMessage(
            content=json.dumps(
                self.payload,
                ensure_ascii=False,
            )
        )


# ============================================================
# 2. Test fixtures
# ============================================================

def sample_lead():

    return {
        "company": COMPANY,
        "purchase_intent_score": 0.78,
        "opportunity_level": "高",
        "evidence": [
            "新能源车零部件扩产",
            EVIDENCE,
            "机器视觉工程师",
        ],
        "solution_match": [
            "自动化产线与内部机器视觉检测能力存在潜在匹配"
        ],
        "recommended_action": (
            "联系质量和自动化负责人，确认检测需求。"
        ),
    }


def sample_provenance():

    return {
        "company_signal": EVIDENCE,
        "knowledge_quote": QUOTE,
        "knowledge_source": SOURCE,
        "reason": (
            "新增自动化产线与已有视觉检测能力存在潜在匹配，"
            "具体需求仍需确认。"
        ),
    }


def sample_state():

    lead = sample_lead()

    assessment = {
        **lead,
        "match_provenance": [
            sample_provenance()
        ],
        "requires_external_verification": True,
    }

    return {
        "goal": {
            "target_count": 1,
            "product_focus": "工业机器视觉质检解决方案",
            "target_industry": "汽车零部件",
        },

        "research_output": {
            "status": "complete",
            "data_mode": "mock_company_mcp",
            "company_records": [
                {
                    "company": COMPANY,
                    "profile": {
                        "name": COMPANY,
                        "signals": [
                            "新能源车零部件扩产",
                            EVIDENCE,
                        ],
                    },
                    "news": [
                        "新建生产基地",
                    ],
                    "jobs": [
                        "机器视觉工程师",
                    ],
                },
            ],
        },

        "knowledge_output": {
            "status": "complete",
            "documents": [
                {
                    "content": KNOWLEDGE_CONTENT,
                    "source": SOURCE,
                    "metadata": {
                        "source": SOURCE,
                    },
                },
            ],
        },

        "analysis_output": {
            "status": "complete",
            "selected_count": 1,
            "assessments": [
                assessment,
            ],
        },

        "candidate_leads": [
            lead,
        ],
    }


def valid_selection():

    return {
        "company": COMPANY,
        "contact_role": "质量负责人",
        "evidence_refs": [
            EVIDENCE,
            "机器视觉工程师",
        ],
        "knowledge_match_indices": [0],
        "question_ids": [
            "current_method",
            "defect_types",
            "project_timing",
        ],
    }


def run_with_selection(
    selection,
    state=None,
):

    if state is None:
        state = sample_state()

    return run_sales(
        state,
        llm=FakeSalesLLM([
            selection
        ]),
    )


# ============================================================
# 3. Sales Agent Tests
# ============================================================

class SalesAgentTests(unittest.TestCase):

    def test_valid_sales_draft(self):

        model = FakeSalesLLM([
            valid_selection(),
        ])

        result = run_sales(
            sample_state(),
            llm=model,
        )

        output = result["sales_output"]

        self.assertEqual(
            output["status"],
            "complete",
        )

        self.assertEqual(
            output["draft_count"],
            1,
        )

        self.assertEqual(
            model.calls,
            1,
        )

        draft = output["drafts"][0]

        self.assertEqual(
            draft["entry_point"],
            EVIDENCE,
        )

        self.assertEqual(
            draft["contact_role"],
            "质量负责人",
        )

        self.assertEqual(
            draft["knowledge_refs"][0]["knowledge_source"],
            SOURCE,
        )

        self.assertEqual(
            len(draft["discovery_questions"]),
            3,
        )

        self.assertIn(
            EVIDENCE,
            draft["outreach_draft"],
        )

        self.assertIn(
            QUOTE,
            draft["outreach_draft"],
        )

    def test_mock_draft_cannot_be_sent(self):

        result = run_with_selection(
            valid_selection()
        )

        output = result["sales_output"]

        draft = output["drafts"][0]

        self.assertEqual(
            draft["draft_status"],
            "mock_internal_only",
        )

        self.assertIn(
            "禁止发送",
            draft["outreach_draft"],
        )

        self.assertFalse(
            draft["send_performed"],
        )

        self.assertFalse(
            draft["crm_write_performed"],
        )

        self.assertTrue(
            draft["requires_human_review"],
        )

        self.assertFalse(
            output["crm_write_performed"],
        )

    def test_no_candidates_does_not_call_llm(self):

        state = sample_state()

        state["candidate_leads"] = []

        state["analysis_output"] = {
            "status": "insufficient_research",
            "assessments": [],
        }

        model = FakeSalesLLM([
            valid_selection(),
        ])

        result = run_sales(
            state,
            llm=model,
        )

        self.assertEqual(
            model.calls,
            0,
        )

        self.assertEqual(
            result["sales_output"]["status"],
            "no_candidates",
        )

        self.assertEqual(
            result["sales_output"]["drafts"],
            [],
        )

    def test_missing_analysis_is_rejected(self):

        state = sample_state()

        state["analysis_output"] = {}

        with self.assertRaisesRegex(
            ValueError,
            "requires completed Analysis",
        ):

            run_sales(
                state,
                llm=FakeSalesLLM([
                    valid_selection()
                ]),
            )

    def test_invented_research_evidence_is_rejected(self):

        state = sample_state()

        fake_fact = "企业已经确定采购预算"

        state["candidate_leads"][0]["evidence"].append(
            fake_fact
        )

        state["analysis_output"]["assessments"][0][
            "evidence"
        ].append(fake_fact)

        with self.assertRaisesRegex(
            ValueError,
            "Unsupported research evidence",
        ):

            run_sales(
                state,
                llm=FakeSalesLLM([
                    valid_selection()
                ]),
            )

    def test_fabricated_knowledge_quote_is_rejected(self):

        state = sample_state()

        state["analysis_output"]["assessments"][0][
            "match_provenance"
        ][0]["knowledge_quote"] = (
            "已达到百分之百检测准确率"
        )

        with self.assertRaisesRegex(
            ValueError,
            "Unsupported knowledge quotation",
        ):

            run_sales(
                state,
                llm=FakeSalesLLM([
                    valid_selection()
                ]),
            )

    def test_candidate_analysis_drift_is_rejected(self):

        state = sample_state()

        state["analysis_output"]["assessments"][0][
            "evidence"
        ] = [EVIDENCE]

        with self.assertRaisesRegex(
            ValueError,
            "Analysis and candidate evidence differ",
        ):

            run_sales(
                state,
                llm=FakeSalesLLM([
                    valid_selection()
                ]),
            )

    def test_llm_cannot_select_invented_evidence(self):

        selection = valid_selection()

        selection["evidence_refs"] = [
            "已经签订采购合同",
        ]

        with self.assertRaisesRegex(
            ValueError,
            "Unsupported selected evidence",
        ):

            run_with_selection(
                selection
            )

    def test_invalid_knowledge_index_is_rejected(self):

        selection = valid_selection()

        selection["knowledge_match_indices"] = [99]

        with self.assertRaisesRegex(
            ValueError,
            "Unsupported knowledge index",
        ):

            run_with_selection(
                selection
            )

    def test_invalid_contact_role_is_rejected(self):

        selection = valid_selection()

        selection["contact_role"] = "已确认的采购经理张某"

        with self.assertRaisesRegex(
            ValueError,
            "Invalid contact role",
        ):

            run_with_selection(
                selection
            )

    def test_unknown_question_id_is_rejected(self):

        selection = valid_selection()

        selection["question_ids"] = [
            "current_method",
            "invented_question",
        ]

        with self.assertRaisesRegex(
            ValueError,
            "Unknown question ID",
        ):

            run_with_selection(
                selection
            )

    def test_duplicate_question_id_is_rejected(self):

        selection = valid_selection()

        selection["question_ids"] = [
            "current_method",
            "current_method",
        ]

        with self.assertRaisesRegex(
            ValueError,
            "Invalid discovery questions",
        ):

            run_with_selection(
                selection
            )

    def test_wrong_response_count_is_rejected(self):

        model = FakeSalesLLM([])

        with self.assertRaisesRegex(
            ValueError,
            "incorrect candidate count",
        ):

            run_sales(
                sample_state(),
                llm=model,
            )

    def test_supervisor_analysis_sales_handoff(self):

        fixtures = sample_state()

        model = FakeSalesLLM([
            valid_selection(),
        ])

        def research_worker(state):

            return {
                "research_output": (
                    fixtures["research_output"]
                )
            }

        def knowledge_worker(state):

            self.assertTrue(
                state.get("research_output")
            )

            return {
                "knowledge_output": (
                    fixtures["knowledge_output"]
                )
            }

        def analysis_worker(state):

            self.assertTrue(
                state.get("knowledge_output")
            )

            return {
                "analysis_output": (
                    fixtures["analysis_output"]
                ),
                "candidate_leads": (
                    fixtures["candidate_leads"]
                ),
            }

        def sales_worker(state):

            self.assertTrue(
                state.get("analysis_output")
            )

            self.assertTrue(
                state.get("candidate_leads")
            )

            return run_sales(
                state,
                llm=model,
            )

        def crm_stub(state):

            output = state.get("sales_output")

            self.assertTrue(output)

            self.assertEqual(
                output["draft_count"],
                1,
            )

            self.assertFalse(
                output["crm_write_performed"],
            )

            return {
                "crm_output": {
                    "mode": "test_stub",
                    "received_sales": True,
                    "write_performed": False,
                }
            }

        graph = create_multi_graph({
            "research": research_worker,
            "knowledge": knowledge_worker,
            "analysis": analysis_worker,
            "sales": sales_worker,
            "crm": crm_stub,
        })

        result = graph.invoke({
            "goal": fixtures["goal"],
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
            result["sales_output"]["draft_count"],
            1,
        )

        self.assertTrue(
            result["crm_output"]["received_sales"]
        )

        self.assertFalse(
            result["crm_output"]["write_performed"]
        )


if __name__ == "__main__":
    unittest.main()