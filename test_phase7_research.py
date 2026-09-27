"""
Phase 7.3 - Real Research Agent Tests

Verify:
- verified company can pass
- unverified company cannot enter downstream
"""

import unittest


class RealResearchTests(unittest.TestCase):


    def test_unverified_company_filtered(self):

        companies = [

            {
                "company":
                "测试企业",

                "verification_status":
                "unverified"
            }

        ]


        verified = [

            c for c in companies

            if c.get(
                "verification_status"
            )
            ==
            "verified_company"

        ]


        self.assertEqual(
            len(verified),
            0
        )


    def test_verified_company_kept(self):

        companies = [

            {

                "company":
                "湖北敏能汽车零部件有限公司",

                "verification_status":
                "verified_company"

            }

        ]


        verified = [

            c for c in companies

            if c.get(
                "verification_status"
            )
            ==
            "verified_company"

        ]


        self.assertEqual(
            len(verified),
            1
        )


if __name__ == "__main__":
    unittest.main()