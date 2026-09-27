
"""Phase 6.5 - Real Sales Agent reliability tests."""

import copy
import json
import unittest

from types import SimpleNamespace

from app.multi_agent.real_sales_agent import (
    run_real_sales,
    RealSalesError,
    DRAFT_BANNER,
)


COMPANY = "湖北敏能汽车零部件有限公司"

QUOTE = (
    "7月4日，湖北敏能汽车零部件有限公司，"
    "工作人员正用新的智能生产线完成高精度作业。"
)

SOURCE_URL = (
    "http://szb.xnnews.com.cn/xnrb/html/"
    "2026-07/10/content_841678.htm"
)

KNOWLEDGE_SOURCE = (
    "test_fixture/product_knowledge.md"
)


class FakeModel:

    def __init__(self, payload):

        self.payload = payload
        self.calls = 0

    def invoke(self, prompt):

        self.calls += 1

        return SimpleNamespace(
            content=json.dumps(
                self.payload,
                ensure_ascii=False,
            )
        )


def make_state():

    evidence = {
        "company": COMPANY,
        "quote": QUOTE,
        "source_url": SOURCE_URL,
        "published_at": None,
        "signal_types": ["new_production_line"],
        "verification_status": (
            "literal_quote_from_article"
        ),
        "requires_human_review": True,
    }

    match = {
        "company_signal": QUOTE,
        "company_source_url": SOURCE_URL,
        "knowledge_quote": "外观缺陷检测",
        "knowledge_source": KNOWLEDGE_SOURCE,
        "match_status": (
            "potential_fit_requires_human_review"
        ),
    }

    return {
        "goal": {
            "target_count": 1,
            "product_focus": "工业机器视觉质检解决方案",
        },

        "research_output": {
            "status": "complete",
            "data_mode": "real_source_page",
            "mock_fallback_used": False,
            "verified_evidence": [
                copy.deepcopy(evidence),
            ],
            "verified_evidence_count": 1,
            "crm_write_performed": False,
            "send_performed": False,
        },

        "knowledge_output": {
            "status": "complete",
            "source_type": "internal_product_knowledge",
            "documents": [{
                "content": (
                    "支持尺寸测量和外观缺陷检测。"
                ),
                "source": KNOWLEDGE_SOURCE,
            }],
        },

        "analysis_output": {
            "status": "complete",
            "data_mode": "real_source_page",
            "selected_count": 1,
            "assessments": [{
                "company": COMPANY,
                "observed_evidence": [
                    copy.deepcopy(evidence),
                ],
                "product_matches": [
                    copy.deepcopy(match),
                ],
                "purchase_intent_status": "unverified",
                "budget_status": "unknown",
                "contact_status": "unknown",
                "requires_human_review": True,
                "crm_stage_changed": False,
                "send_performed": False,
            }],
            "crm_write_performed": False,
            "send_performed": False,
        },

        "candidate_leads": [],
    }


def valid_selection():

    return [{
        "company": COMPANY,
        "evidence_index": 1,
        "match_indices": [1],
        "question_ids": [
            "Q1",
            "Q3",
            "Q4",
        ],
    }]


class RealSalesTests(unittest.TestCase):

    def test_valid_internal_draft(self):

        state = make_state()

        model = FakeModel(
            valid_selection()
        )

        result = run_real_sales(
            state,
            llm=model,
        )

        output = result["sales_output"]

        self.assertEqual(model.calls, 1)

        self.assertEqual(
            output["status"],
            "complete",
        )

        self.assertEqual(
            output["draft_count"],
            1,
        )

        draft = output["drafts"][0]

        self.assertEqual(
            draft["company"],
            COMPANY,
        )

        self.assertIn(
            QUOTE,
            draft["outreach_draft"],
        )

        self.assertIn(
            SOURCE_URL,
            draft["outreach_draft"],
        )

        self.assertIn(
            DRAFT_BANNER,
            draft["outreach_draft"],
        )

        self.assertEqual(
            draft["purchase_intent_status"],
            "unverified",
        )

        self.assertFalse(
            draft["send_performed"]
        )

        self.assertFalse(
            draft["crm_write_performed"]
        )

    def test_unknown_evidence_index_is_rejected(self):

        decision = valid_selection()

        decision[0]["evidence_index"] = 99

        with self.assertRaises(
            RealSalesError
        ):

            run_real_sales(
                make_state(),
                llm=FakeModel(decision),
            )

    def test_unknown_product_match_is_rejected(self):

        decision = valid_selection()

        decision[0]["match_indices"] = [99]

        with self.assertRaises(
            RealSalesError
        ):

            run_real_sales(
                make_state(),
                llm=FakeModel(decision),
            )

    def test_unknown_question_is_rejected(self):

        decision = valid_selection()

        decision[0]["question_ids"] = [
            "Q1",
            "Q999",
        ]

        with self.assertRaises(
            RealSalesError
        ):

            run_real_sales(
                make_state(),
                llm=FakeModel(decision),
            )

    def test_extra_model_claim_is_rejected(self):

        decision = valid_selection()

        decision[0]["purchase_confirmed"] = True

        with self.assertRaises(
            RealSalesError
        ):

            run_real_sales(
                make_state(),
                llm=FakeModel(decision),
            )

    def test_fabricated_evidence_is_rejected(self):

        state = make_state()

        state["analysis_output"]["assessments"][0][
            "observed_evidence"
        ][0]["quote"] = (
            "企业已确认采购机器视觉设备"
        )

        with self.assertRaises(
            RealSalesError
        ):

            run_real_sales(
                state,
                llm=FakeModel(
                    valid_selection()
                ),
            )

    def test_fabricated_knowledge_is_rejected(self):

        state = make_state()

        state["analysis_output"]["assessments"][0][
            "product_matches"
        ][0]["knowledge_quote"] = (
            "已实现百分之百投资回报率"
        )

        with self.assertRaises(
            RealSalesError
        ):

            run_real_sales(
                state,
                llm=FakeModel(
                    valid_selection()
                ),
            )

    def test_mock_data_is_rejected(self):

        state = make_state()

        state["research_output"]["data_mode"] = (
            "mock_company_mcp"
        )

        with self.assertRaises(
            RealSalesError
        ):

            run_real_sales(
                state,
                llm=FakeModel(
                    valid_selection()
                ),
            )

    def test_legacy_scored_leads_are_rejected(self):

        state = make_state()

        state["candidate_leads"] = [{
            "company": COMPANY,
            "purchase_intent_score": 0.9,
        }]

        with self.assertRaises(
            RealSalesError
        ):

            run_real_sales(
                state,
                llm=FakeModel(
                    valid_selection()
                ),
            )

    def test_empty_assessments_skip_llm(self):

        state = make_state()

        state["analysis_output"]["assessments"] = []
        state["analysis_output"]["selected_count"] = 0

        model = FakeModel(
            valid_selection()
        )

        result = run_real_sales(
            state,
            llm=model,
        )

        self.assertEqual(
            model.calls,
            0,
        )

        self.assertEqual(
            result["sales_output"]["draft_count"],
            0,
        )

        self.assertFalse(
            result["sales_output"]["send_performed"]
        )


if __name__ == "__main__":
    unittest.main()
