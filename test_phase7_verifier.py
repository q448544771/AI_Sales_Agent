import unittest


from app.tools.company_verifier import (
    extract_signals,
)



class CompanyVerifierTests(unittest.TestCase):


    def test_extract_new_line_signal(self):

        text = """
        湖北某公司新增智能生产线，
        推进自动化升级。
        """


        result = extract_signals(
            text
        )


        types = [
            x["type"]
            for x in result
        ]


        self.assertIn(
            "new_production_line",
            types,
        )


        self.assertIn(
            "automation_upgrade",
            types,
        )



if __name__ == "__main__":

    unittest.main()