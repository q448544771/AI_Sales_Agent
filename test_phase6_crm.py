
"""Phase 6.6 - Real CRM Agent unit tests.

Uses controlled in-memory test fixtures.
Never invokes a real CRM write tool.
"""

import copy
import unittest

from app.multi_agent.real_crm_agent import (
    run_real_crm,
    capture_crm_snapshot,
    RealCRMError,
)


COMPANY = "湖北敏能汽车零部件有限公司"

QUOTE = (
    "7月4日，湖北敏能汽车零部件有限公司，"
    "工作人员正用新的智能生产线完成高精度作业。"
)

URL = (
    "http://szb.xnnews.com.cn/xnrb/html/"
    "2026-07/10/content_841678.htm"
)

BANNER = "【真实公开资料｜内部待审核｜禁止自动发送】"


class FakeQueryTool:

    name = "query_leads"

    def __init__(self, rows):

        self.rows = copy.deepcopy(rows)
        self.calls = []

    def invoke(self, arguments):

        self.calls.append(
            copy.deepcopy(arguments)
        )

        return copy.deepcopy(
            self.rows
        )


def make_state():

    evidence = {
        "company": COMPANY,
        "quote": QUOTE,
        "source_url": URL,
        "published_at": None,
        "verification_status": (
            "literal_quote_from_article"
        ),
        "requires_human_review": True,
    }

    return {
        "candidate_leads": [],

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

        "analysis_output": {
            "status": "complete",
            "data_mode": "real_source_page",
            "selected_count": 1,
            "assessments": [{
                "company": COMPANY,
                "observed_evidence": [
                    copy.deepcopy(evidence),
                ],
                "product_matches": [],
                "purchase_intent_status": "unverified",
                "budget_status": "unknown",
                "contact_status": "unknown",
                "requires_human_review": True,
                "crm_stage_changed": False,
                "send_performed": False,
                "recommended_action": (
                    "人工核实质量检测流程与实际需求。"
                ),
            }],
            "crm_write_performed": False,
            "crm_stage_changed": False,
            "send_performed": False,
            "requires_human_review": True,
        },

        "sales_output": {
            "status": "complete",
            "data_mode": "real_source_page",
            "draft_count": 1,
            "drafts": [{
                "company": COMPANY,
                "entry_point": copy.deepcopy(evidence),
                "evidence_refs": [
                    copy.deepcopy(evidence),
                ],
                "knowledge_refs": [],
                "outreach_draft": (
                    f"{BANNER}\n"
                    f"{QUOTE}\n"
                    f"原文：{URL}\n"
                ),
                "next_action": (
                    "人工核实联系人与实际检测需求。"
                ),
                "draft_status": (
                    "real_internal_review_only"
                ),
                "purchase_intent_status": "unverified",
                "budget_status": "unknown",
                "requires_human_review": True,
                "send_performed": False,
                "crm_write_performed": False,
            }],
            "crm_write_performed": False,
            "crm_stage_changed": False,
            "send_performed": False,
            "requires_human_review": True,
        },
    }


class RealCRMTests(unittest.TestCase):

    def test_existing_record_preserved(self):

        rows = [{
            "company": COMPANY,
            "stage": "new",
            "next_action": "原有跟进事项",
            "last_contact_time": None,
        }]

        tool = FakeQueryTool(rows)

        original_rows = copy.deepcopy(
            tool.rows
        )

        result = run_real_crm(
            make_state(),
            query_tool=tool,
        )

        output = result["crm_output"]
        review = output["review_records"][0]

        self.assertEqual(
            review["lookup_status"],
            "existing",
        )

        self.assertEqual(
            review["existing_stage"],
            "new",
        )

        self.assertEqual(
            review["existing_next_action"],
            "原有跟进事项",
        )

        self.assertEqual(
            review["crm_record_provenance"],
            "unverified_legacy_crm_record",
        )

        self.assertEqual(
            tool.rows,
            original_rows,
        )

        self.assertFalse(
            output["create_performed"]
        )

        self.assertFalse(
            output["update_performed"]
        )

        self.assertEqual(
            tool.calls,
            [{
                "industry": "",
                "min_score": 0.0,
            }],
        )

    def test_missing_company_is_not_created(self):

        tool = FakeQueryTool([])

        result = run_real_crm(
            make_state(),
            query_tool=tool,
        )

        output = result["crm_output"]

        self.assertEqual(
            output["missing_count"],
            1,
        )

        self.assertEqual(
            output["review_records"][0][
                "lookup_status"
            ],
            "not_found",
        )

        self.assertFalse(
            output["create_performed"]
        )

    def test_duplicate_company_requires_review(self):

        rows = [
            {
                "company": COMPANY,
                "stage": "new",
            },
            {
                "company": COMPANY,
                "stage": "contacted",
            },
        ]

        result = run_real_crm(
            make_state(),
            query_tool=FakeQueryTool(rows),
        )

        output = result["crm_output"]

        self.assertEqual(
            output["duplicate_count"],
            1,
        )

        self.assertEqual(
            output["status"],
            "manual_dedup_required",
        )

        self.assertEqual(
            output["review_records"][0][
                "duplicate_record_count"
            ],
            2,
        )

        self.assertFalse(
            output["stage_changed"]
        )

    def test_mock_research_rejected(self):

        state = make_state()

        state["research_output"]["data_mode"] = (
            "mock_company_mcp"
        )

        with self.assertRaises(RealCRMError):

            run_real_crm(
                state,
                query_tool=FakeQueryTool([]),
            )

    def test_legacy_scored_lead_rejected(self):

        state = make_state()

        state["candidate_leads"] = [{
            "company": COMPANY,
            "purchase_intent_score": 0.9,
        }]

        with self.assertRaises(RealCRMError):

            run_real_crm(
                state,
                query_tool=FakeQueryTool([]),
            )

    def test_fabricated_sales_evidence_rejected(self):

        state = make_state()

        state["sales_output"]["drafts"][0][
            "entry_point"
        ]["quote"] = "已确认采购机器视觉系统"

        with self.assertRaises(RealCRMError):

            run_real_crm(
                state,
                query_tool=FakeQueryTool([]),
            )

    def test_sent_draft_rejected(self):

        state = make_state()

        state["sales_output"]["drafts"][0][
            "send_performed"
        ] = True

        with self.assertRaises(RealCRMError):

            run_real_crm(
                state,
                query_tool=FakeQueryTool([]),
            )

    def test_wrong_tool_rejected(self):

        tool = FakeQueryTool([])

        tool.name = "create_lead"

        with self.assertRaises(RealCRMError):

            run_real_crm(
                make_state(),
                query_tool=tool,
            )

        self.assertEqual(
            tool.calls,
            [],
        )

    def test_empty_assessments_skip_crm_query(self):

        state = make_state()

        state["analysis_output"]["status"] = (
            "insufficient_evidence"
        )

        state["analysis_output"]["assessments"] = []
        state["analysis_output"]["selected_count"] = 0

        state["sales_output"]["status"] = (
            "no_verified_assessments"
        )

        state["sales_output"]["drafts"] = []
        state["sales_output"]["draft_count"] = 0

        tool = FakeQueryTool([])

        result = run_real_crm(
            state,
            query_tool=tool,
        )

        self.assertEqual(
            tool.calls,
            [],
        )

        self.assertEqual(
            result["crm_output"]["status"],
            "no_candidates",
        )

        self.assertFalse(
            result["crm_output"]["read_performed"]
        )

    def test_snapshot_ignores_record_order(self):

        rows = [
            {
                "company": COMPANY,
                "stage": "new",
            },
            {
                "company": "其他测试企业有限公司",
                "stage": "contacted",
            },
        ]

        first = capture_crm_snapshot(
            query_tool=FakeQueryTool(rows),
        )

        second = capture_crm_snapshot(
            query_tool=FakeQueryTool(
                list(reversed(rows))
            ),
        )

        self.assertEqual(
            first,
            second,
        )

    def test_review_does_not_generate_score(self):

        result = run_real_crm(
            make_state(),
            query_tool=FakeQueryTool([]),
        )

        review = result["crm_output"][
            "review_records"
        ][0]

        self.assertNotIn(
            "purchase_intent_score",
            review,
        )

        self.assertEqual(
            review["purchase_intent_status"],
            "unverified",
        )


if __name__ == "__main__":

    unittest.main()
