
"""Phase 6.4 - Real Analysis reliability tests.

All network and LLM execution is isolated.
Production data are never replaced by test fixtures.
"""

import copy
import json
import unittest

from types import SimpleNamespace

from app.multi_agent.real_analysis_agent import (
    run_real_analysis,
    RealAnalysisError,
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
        "signal_types": [
            "new_production_line",
        ],
        "source_url": SOURCE_URL,
        "source_title": "新建产线 扩产提能 -咸宁日报",
        "source_type": "news",
        "published_at": None,
        "date_origin": None,
        "url_date_hint": "2026-07-10",
        "date_conflict": False,
        "article_selector": ".content",
        "verification_status": (
            "literal_quote_from_article"
        ),
        "requires_human_review": True,
    }

    page = {
        "company": COMPANY,
        "source_url": SOURCE_URL,
        "final_url": SOURCE_URL,
        "page_title": evidence["source_title"],
        "requested_type": "news",
        "source_fetch_status": "article_name_match",
        "category_check": "category_consistent",
        "page_published_at": None,
        "page_date_origin": None,
        "url_date_hint": "2026-07-10",
        "date_conflict_with_url_hint": False,
        "candidate_quotes": [{
            "quote": QUOTE,
            "signal_types": [
                "new_production_line",
            ],
            "quote_status": (
                "literal_page_excerpt_requires_review"
            ),
        }],
    }

    report = {
        "company": COMPANY,
        "data_mode": "real_source_page",
        "mock_fallback_used": False,
        "results": [page],
        "article_match_count": 1,
    }

    return {
        "goal": {
            "target_industry": "汽车零部件",
            "target_region": "中国",
            "target_count": 1,
            "product_focus": "工业机器视觉质检解决方案",
        },

        "research_output": {
            "status": "complete",
            "data_mode": "real_source_page",
            "mock_fallback_used": False,
            "company_records": [{
                "company": COMPANY,
                "verified_evidence": [
                    copy.deepcopy(evidence),
                ],
                "evidence_count": 1,
                "verification_report": report,
            }],
            "verified_evidence": [
                copy.deepcopy(evidence),
            ],
            "verified_evidence_count": 1,
        },

        "knowledge_output": {
            "status": "complete",
            "source_type": "internal_product_knowledge",
            "documents": [{
                "content": (
                    "工业机器视觉质检方案支持尺寸测量"
                    "与外观缺陷检测。"
                ),
                "source": "test_fixture/product_knowledge.md",
                "metadata": {
                    "source": "test_fixture/product_knowledge.md",
                },
            }],
        },
    }


def valid_decision(with_product_match=True):

    matches = []

    if with_product_match:

        matches = [{
            "evidence_id": "E1",
            "knowledge_id": "K1",
            "knowledge_quote": "尺寸测量",
        }]

    return [{
        "company": COMPANY,
        "evidence_ids": ["E1"],
        "product_matches": matches,
        "next_step": "requirements_discovery",
    }]


class RealAnalysisTests(unittest.TestCase):

    def test_valid_source_grounded_analysis(self):

        state = make_state()

        model = FakeModel(
            valid_decision()
        )

        result = run_real_analysis(
            state,
            llm=model,
        )

        output = result["analysis_output"]

        self.assertEqual(
            model.calls,
            1,
        )

        self.assertEqual(
            output["status"],
            "complete",
        )

        self.assertEqual(
            output["selected_count"],
            1,
        )

        self.assertEqual(
            result["candidate_leads"],
            [],
        )

        assessment = output["assessments"][0]

        original = assessment[
            "observed_evidence"
        ][0]

        self.assertEqual(
            original["quote"],
            QUOTE,
        )

        self.assertEqual(
            original["source_url"],
            SOURCE_URL,
        )

        self.assertIsNone(
            original["published_at"]
        )

        self.assertEqual(
            assessment["purchase_intent_status"],
            "unverified",
        )

        self.assertFalse(
            output["crm_write_performed"]
        )

        match = assessment[
            "product_matches"
        ][0]

        self.assertEqual(
            match["knowledge_quote"],
            "尺寸测量",
        )

        self.assertEqual(
            match["company_source_url"],
            SOURCE_URL,
        )

    def test_unknown_evidence_id_is_rejected(self):

        state = make_state()

        decision = valid_decision()

        decision[0]["evidence_ids"] = [
            "E999",
        ]

        with self.assertRaises(
            RealAnalysisError
        ):

            run_real_analysis(
                state,
                llm=FakeModel(decision),
            )

    def test_fabricated_knowledge_quote_is_rejected(self):

        state = make_state()

        decision = valid_decision()

        decision[0]["product_matches"][0][
            "knowledge_quote"
        ] = "已验证投资回报率达到百分之百"

        with self.assertRaises(
            RealAnalysisError
        ):

            run_real_analysis(
                state,
                llm=FakeModel(decision),
            )

    def test_no_knowledge_disallows_product_match(self):

        state = make_state()

        state["knowledge_output"] = {
            "status": "empty",
            "source_type": "internal_product_knowledge",
            "documents": [],
        }

        with self.assertRaises(
            RealAnalysisError
        ):

            run_real_analysis(
                state,
                llm=FakeModel(
                    valid_decision()
                ),
            )

    def test_no_knowledge_accepts_empty_matches(self):

        state = make_state()

        state["knowledge_output"] = {
            "status": "empty",
            "source_type": "internal_product_knowledge",
            "documents": [],
        }

        result = run_real_analysis(
            state,
            llm=FakeModel(
                valid_decision(
                    with_product_match=False,
                )
            ),
        )

        assessment = result[
            "analysis_output"
        ]["assessments"][0]

        self.assertEqual(
            assessment["product_matches"],
            [],
        )

    def test_body_only_page_cannot_become_evidence(self):

        state = make_state()

        report = state[
            "research_output"
        ]["company_records"][0][
            "verification_report"
        ]

        report["results"][0][
            "source_fetch_status"
        ] = "body_name_match_only"

        with self.assertRaises(
            RealAnalysisError
        ):

            run_real_analysis(
                state,
                llm=FakeModel(
                    valid_decision()
                ),
            )

    def test_invented_publication_date_is_rejected(self):

        state = make_state()

        state[
            "research_output"
        ]["verified_evidence"][0][
            "published_at"
        ] = "2026-07-10"

        state[
            "research_output"
        ]["company_records"][0][
            "verified_evidence"
        ][0]["published_at"] = "2026-07-10"

        with self.assertRaises(
            RealAnalysisError
        ):

            run_real_analysis(
                state,
                llm=FakeModel(
                    valid_decision()
                ),
            )

    def test_mock_research_is_rejected(self):

        state = make_state()

        state[
            "research_output"
        ]["data_mode"] = "mock_company_mcp"

        with self.assertRaises(
            RealAnalysisError
        ):

            run_real_analysis(
                state,
                llm=FakeModel(
                    valid_decision()
                ),
            )

    def test_no_verified_evidence_skips_llm(self):

        state = make_state()

        research = state[
            "research_output"
        ]

        research["status"] = "insufficient_evidence"

        research["verified_evidence"] = []
        research["verified_evidence_count"] = 0

        record = research[
            "company_records"
        ][0]

        record["verified_evidence"] = []
        record["evidence_count"] = 0

        model = FakeModel(
            valid_decision()
        )

        result = run_real_analysis(
            state,
            llm=model,
        )

        self.assertEqual(
            model.calls,
            0,
        )

        self.assertEqual(
            result["analysis_output"]["status"],
            "insufficient_evidence",
        )

        self.assertEqual(
            result["candidate_leads"],
            [],
        )


if __name__ == "__main__":
    unittest.main()
