import unittest


from app.tools.real_company_discovery import (
    _clean_name,
)



class NameCleanTests(unittest.TestCase):


    def test_remove_number_prefix(self):

        result = _clean_name(
            "02审批公示苏州巨田精密塑胶模具有限公司"
        )

        self.assertEqual(
            result,
            "苏州巨田精密塑胶模具有限公司"
        )



    def test_remove_notice_prefix(self):

        result = _clean_name(
            "审批公示瑞安市神际汽车零部件有限公司"
        )

        self.assertEqual(
            result,
            "瑞安市神际汽车零部件有限公司"
        )



    def test_keep_normal_company(self):

        result = _clean_name(
            "湖北敏能汽车零部件有限公司"
        )

        self.assertEqual(
            result,
            "湖北敏能汽车零部件有限公司"
        )



if __name__ == "__main__":

    unittest.main()