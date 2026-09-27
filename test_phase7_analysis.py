import unittest

from app.multi_agent.real_analysis_agent import (
    _validate_research_evidence,
)


class RealAnalysisEvidenceTests(
    unittest.TestCase
):


    def test_verified_literal_evidence_pass(
        self
    ):

        data = {

            "company_records":[

                {

                    "company":
                    "湖北敏能汽车零部件有限公司",

                    "identity_status":
                    "source_article_name_match",

                    "verified_evidence":[

                        {

                            "quote":
                            "湖北敏能汽车零部件有限公司，工作人员正用新的智能生产线完成高精度作业。",

                            "source_url":
                            "http://example.com",

                            "verification_status":
                            "literal_quote_from_article"

                        }

                    ]

                }

            ]

        }


        _validate_research_evidence(
            data
        )


    def test_unverified_company_rejected(
        self
    ):

        data = {

            "company_records":[

                {

                    "company":
                    "测试企业",

                    "identity_status":
                    "search_result_only",

                    "verified_evidence":[

                        {

                            "quote":
                            "xxx",

                            "source_url":
                            "http://example.com",

                            "verification_status":
                            "literal_quote_from_article"

                        }

                    ]

                }

            ]

        }


        with self.assertRaises(
            ValueError
        ):

            _validate_research_evidence(
                data
            )


    def test_body_only_evidence_rejected(
        self
    ):

        data = {

            "company_records":[

                {

                    "company":
                    "测试企业",

                    "identity_status":
                    "source_article_name_match",

                    "verified_evidence":[

                        {

                            "quote":
                            "xxx",

                            "source_url":
                            "http://example.com",

                            "verification_status":
                            "body_only_match"

                        }

                    ]

                }

            ]

        }


        with self.assertRaises(
            ValueError
        ):

            _validate_research_evidence(
                data
            )



if __name__ == "__main__":

    unittest.main()