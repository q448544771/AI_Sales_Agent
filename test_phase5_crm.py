
"""Phase 5.7 - Read-only CRM Agent tests."""

import json
import unittest

from app.graph.multi_workflow import create_multi_graph
from app.multi_agent.contracts import AGENT_SEQUENCE
from app.multi_agent.crm_agent import run_crm


COMPANY = "测试汽车零部件有限公司"

FACT = "新增两条自动化生产线"

ACTION = (
    "人工核实企业信息后联系质量负责人，"
    "确认检测对象、检测节拍及项目计划。"
)


# ============================================================
# 1. Fake query-only CRM MCP tool
# ============================================================

class FakeCRMQueryTool:

    name = "query_leads"

    def __init__(self, result=None, failure=None):

        self.result = (
            result
            if result is not None
            else []
        )

        self.failure = failure

        self.calls = []

    def invoke(self, arguments):

        self.calls.append(dict(arguments))

        if self.failure is not None:
            raise self.failure

        return self.result


# ============================================================
# 2. Test state
# ============================================================

def sample_state():

    return {
        "goal": {
            "target_count": 1,
            "target_industry": "汽车零部件",
        },

        "research_output": {
            "status": "complete",
            "data_mode": "mock_company_mcp",
        },

        "analysis_output": {
            "status": "complete",
            "selected_count": 1,
            "crm_stage_changed": False,
        },

        "candidate_leads": [
            {
                "company": COMPANY,
                "purchase_intent_score": 0.8,
                "opportunity_level": "高",
                "evidence": [
                    FACT,
                ],
                "solution_match": [],
                "recommended_action": ACTION,
            },
        ],

        "sales_output": {
            "status": "complete",
            "data_mode": "mock_company_mcp",
            "draft_count": 1,
            "requires_human_review": True,
            "send_performed": False,
            "crm_write_performed": False,
            "drafts": [
                {
                    "company": COMPANY,
                    "entry_point": FACT,
                    "evidence_refs": [
                        FACT,
                    ],
                    "next_action": ACTION,
                    "draft_status": "mock_internal_only",
                    "requires_human_review": True,
                    "send_performed": False,
                    "crm_write_performed": False,
                },
            ],
        },
    }


def existing_record():

    return {
        "company": COMPANY,
        "industry": "汽车零部件",
        "region": "江苏",
        "score": 0.5,
        "stage": "contacted",
        "next_action": "保留之前的客户跟进计划",
        "last_contact_time": None,
        "status": "new",
    }


# ============================================================
# 3. Tests
# ============================================================

class CRMAgentTests(unittest.TestCase):

    def test_new_candidate_only_generates_review_plan(self):

        tool = FakeCRMQueryTool([])

        output = run_crm(
            sample_state(),
            query_tool=tool,
        )["crm_output"]

        self.assertEqual(output["status"], "review_only")

        self.assertEqual(output["mode"], "read_only")

        self.assertEqual(output["missing_count"], 1)

        self.assertEqual(output["query_count"], 1)

        self.assertEqual(
            tool.calls,
            [{"industry": "", "min_score": 0.0}],
        )

        self.assertEqual(
            output["review_records"][0]["lookup_status"],
            "not_found",
        )

        self.assertFalse(output["create_performed"])

        self.assertFalse(output["update_performed"])

        self.assertFalse(output["stage_changed"])

    def test_existing_customer_preserves_stage_and_action(self):

        tool = FakeCRMQueryTool([
            existing_record(),
        ])

        output = run_crm(
            sample_state(),
            query_tool=tool,
        )["crm_output"]

        self.assertEqual(output["existing_count"], 1)

        record = output["review_records"][0]

        self.assertEqual(
            record["lookup_status"],
            "existing",
        )

        self.assertEqual(
            record["existing_stage"],
            "contacted",
        )

        self.assertEqual(
            record["existing_next_action"],
            "保留之前的客户跟进计划",
        )

        self.assertEqual(
            record["proposed_next_action"],
            ACTION,
        )

        self.assertEqual(
            record["action_taken"],
            "none",
        )

    def test_duplicate_crm_records_require_manual_dedup(self):

        record = existing_record()

        tool = FakeCRMQueryTool([
            record,
            dict(record),
        ])

        output = run_crm(
            sample_state(),
            query_tool=tool,
        )["crm_output"]

        self.assertEqual(
            output["status"],
            "manual_dedup_required",
        )

        self.assertEqual(
            output["duplicate_count"],
            1,
        )

        self.assertEqual(
            output["review_records"][0]["duplicate_record_count"],
            2,
        )

        self.assertFalse(output["update_performed"])

    def test_json_wrapped_result_is_supported(self):

        tool = FakeCRMQueryTool(
            json.dumps(
                {"result": [existing_record()]},
                ensure_ascii=False,
            )
        )

        output = run_crm(
            sample_state(),
            query_tool=tool,
        )["crm_output"]

        self.assertEqual(
            output["existing_count"],
            1,
        )

    def test_malformed_crm_result_is_rejected(self):

        tool = FakeCRMQueryTool([
            {"company": ""},
        ])

        with self.assertRaisesRegex(
            ValueError,
            "invalid company name",
        ):

            run_crm(
                sample_state(),
                query_tool=tool,
            )

    def test_wrong_tool_is_rejected(self):

        tool = FakeCRMQueryTool()

        tool.name = "update_lead_stage"

        with self.assertRaisesRegex(
            ValueError,
            "only invoke query_leads",
        ):

            run_crm(
                sample_state(),
                query_tool=tool,
            )

        self.assertEqual(tool.calls, [])

    def test_crm_transport_error_is_not_hidden(self):

        tool = FakeCRMQueryTool(
            failure=RuntimeError("MCP disconnected")
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "read-only query failed",
        ):

            run_crm(
                sample_state(),
                query_tool=tool,
            )

    def test_no_candidates_skips_crm_query(self):

        state = sample_state()

        state["candidate_leads"] = []

        state["analysis_output"] = {
            "status": "insufficient_research",
        }

        state["sales_output"] = {
            "status": "no_candidates",
            "draft_count": 0,
            "drafts": [],
            "requires_human_review": True,
            "send_performed": False,
            "crm_write_performed": False,
        }

        tool = FakeCRMQueryTool()

        output = run_crm(
            state,
            query_tool=tool,
        )["crm_output"]

        self.assertEqual(
            output["status"],
            "no_candidates",
        )

        self.assertEqual(tool.calls, [])

        self.assertFalse(
            output["read_performed"]
        )

    def test_missing_analysis_is_rejected(self):

        state = sample_state()

        state["analysis_output"] = {}

        with self.assertRaisesRegex(
            ValueError,
            "requires completed Analysis",
        ):

            run_crm(
                state,
                query_tool=FakeCRMQueryTool(),
            )

    def test_prior_crm_stage_change_is_rejected(self):

        state = sample_state()

        state["analysis_output"]["crm_stage_changed"] = True

        with self.assertRaisesRegex(
            ValueError,
            "must not change CRM stage",
        ):

            run_crm(
                state,
                query_tool=FakeCRMQueryTool(),
            )

    def test_sent_sales_message_is_rejected(self):

        state = sample_state()

        state["sales_output"]["send_performed"] = True

        with self.assertRaisesRegex(
            ValueError,
            "message was sent",
        ):

            run_crm(
                state,
                query_tool=FakeCRMQueryTool(),
            )

    def test_upstream_crm_write_is_rejected(self):

        state = sample_state()

        state["sales_output"]["crm_write_performed"] = True

        with self.assertRaisesRegex(
            ValueError,
            "indicates a CRM write",
        ):

            run_crm(
                state,
                query_tool=FakeCRMQueryTool(),
            )

    def test_sales_candidate_mismatch_is_rejected(self):

        state = sample_state()

        state["sales_output"]["drafts"][0]["company"] = (
            "另一家企业"
        )

        with self.assertRaisesRegex(
            ValueError,
            "Sales drafts and Analysis candidates differ",
        ):

            run_crm(
                state,
                query_tool=FakeCRMQueryTool(),
            )

    def test_mock_draft_must_be_internal_only(self):

        state = sample_state()

        state["sales_output"]["drafts"][0]["draft_status"] = (
            "approved"
        )

        with self.assertRaisesRegex(
            ValueError,
            "Mock Sales draft lacks internal-only",
        ):

            run_crm(
                state,
                query_tool=FakeCRMQueryTool(),
            )

    def test_nonmock_data_is_still_read_only(self):

        state = sample_state()

        state["research_output"]["data_mode"] = (
            "verified_external"
        )

        state["sales_output"]["data_mode"] = (
            "verified_external"
        )

        state["sales_output"]["drafts"][0]["draft_status"] = (
            "requires_human_review"
        )

        output = run_crm(
            state,
            query_tool=FakeCRMQueryTool(),
        )["crm_output"]

        self.assertEqual(
            output["write_block_reason"],
            "no_explicit_write_authorization",
        )

        self.assertFalse(output["create_performed"])

        self.assertFalse(output["update_performed"])

    def test_supervisor_sales_crm_handoff(self):

        fixture = sample_state()

        tool = FakeCRMQueryTool([
            existing_record(),
        ])

        def research_worker(state):

            return {
                "research_output": fixture["research_output"]
            }

        def knowledge_worker(state):

            return {
                "knowledge_output": {
                    "status": "complete",
                }
            }

        def analysis_worker(state):

            return {
                "analysis_output": fixture["analysis_output"],
                "candidate_leads": fixture["candidate_leads"],
            }

        def sales_worker(state):

            return {
                "sales_output": fixture["sales_output"]
            }

        def crm_worker(state):

            self.assertTrue(state.get("sales_output"))

            self.assertTrue(state.get("candidate_leads"))

            return run_crm(
                state,
                query_tool=tool,
            )

        graph = create_multi_graph({
            "research": research_worker,
            "knowledge": knowledge_worker,
            "analysis": analysis_worker,
            "sales": sales_worker,
            "crm": crm_worker,
        })

        result = graph.invoke({
            "goal": fixture["goal"],
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
            result["crm_output"]["existing_count"],
            1,
        )

        self.assertFalse(
            result["crm_output"]["update_performed"]
        )


if __name__ == "__main__":
    unittest.main()
