import unittest


from app.multi_agent.real_sales_agent import (
    _validate_analysis_for_sales,
)



class RealSalesTests(
    unittest.TestCase
):


    # ========================================================
    # 1. 正常真实分析结果应该通过
    # ========================================================

    def test_verified_analysis_pass(
        self
    ):

        data = {

            "assessments":[

                {

                    "company":
                    "湖北敏能汽车零部件有限公司",


                    "observed_evidence":[

                        {

                            "quote":
                            "湖北敏能汽车零部件有限公司，工作人员正用新的智能生产线完成高精度作业。",


                            "source_url":
                            "http://example.com/article",


                            "verification_status":
                            "literal_quote_from_article"

                        }

                    ]

                }

            ]

        }


        result = _validate_analysis_for_sales(
            data
        )


        self.assertIsNone(
            result
        )



    # ========================================================
    # 2. 未验证搜索结果必须拒绝
    # ========================================================

    def test_unverified_evidence_rejected(
        self
    ):

        data = {

            "assessments":[

                {

                    "company":
                    "测试企业",


                    "observed_evidence":[

                        {

                            "quote":
                            "企业新增产线",


                            "source_url":
                            "http://example.com",


                            "verification_status":
                            "search_result_only"

                        }

                    ]

                }

            ]

        }


        with self.assertRaises(
            ValueError
        ):

            _validate_analysis_for_sales(
                data
            )



    # ========================================================
    # 3. 缺少 URL 必须拒绝
    # ========================================================

    def test_missing_source_url_rejected(
        self
    ):

        data = {

            "assessments":[

                {

                    "company":
                    "测试企业",


                    "observed_evidence":[

                        {

                            "quote":
                            "企业新增产线",


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

            _validate_analysis_for_sales(
                data
            )



    # ========================================================
    # 4. 空证据拒绝
    # ========================================================

    def test_empty_evidence_rejected(
        self
    ):

        data = {

            "assessments":[

                {

                    "company":
                    "测试企业",

                    "observed_evidence":[]

                }

            ]

        }


        with self.assertRaises(
            ValueError
        ):

            _validate_analysis_for_sales(
                data
            )



if __name__ == "__main__":

    unittest.main()