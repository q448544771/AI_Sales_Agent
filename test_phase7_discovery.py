
"""Phase 7.1 - Discovery strategy unit tests.

Controlled data are used only inside tests.
Production tools always invoke the real provider.
"""

import unittest

from unittest.mock import patch

from app.tools.real_company_discovery import (
    discover_companies,
    extract_company_names,
    build_discovery_queries,
)


def make_page(
    company,
    url,
    *,
    signal="新增自动化生产线",
):

    return {
        "title": f"{company} {signal}",

        "source_url": url,

        "publisher": "测试来源",

        "snippet": (
            f"{company}从事汽车零部件相关业务，"
            f"报道提及{signal}。"
        ),

        "published_at": (
            "2026-07-10T08:58:00+08:00"
        ),

        "retrieved_at": (
            "2026-09-27T00:00:00+08:00"
        ),

        "provider": "bocha",
    }


class DiscoveryTests(unittest.TestCase):

    def test_nationwide_query_coverage(self):

        queries = build_discovery_queries(
            "汽车零部件",
            "中国",
        )

        regions = {
            region
            for region, _ in queries
        }

        self.assertEqual(
            len(queries),
            8,
        )

        self.assertIn(
            "浙江",
            regions,
        )

        self.assertIn(
            "广东",
            regions,
        )

        self.assertIn(
            "湖北",
            regions,
        )

        self.assertIn(
            "广西",
            regions,
        )

    def test_literal_company_extraction(self):

        text = (
            "连日来，在浙江博奥铝业有限公司"
            "自动化生产车间，工作人员正抓紧生产汽车配件。"
        )

        names = extract_company_names(
            text
        )

        self.assertIn(
            "浙江博奥铝业有限公司",
            names,
        )

        self.assertNotIn(
            "在浙江博奥铝业有限公司",
            names,
        )

    @patch(
        "app.tools.real_company_discovery.search_real_web"
    )
    def test_multi_region_deduplication(
        self,
        mocked_search,
    ):

        def provider(
            *,
            query,
            count,
            freshness,
        ):

            if "浙江" in query:

                pages = [
                    make_page(
                        "浙江甲汽车部件有限公司",
                        "https://example.com/a",
                    ),
                ]

            elif "广东" in query:

                pages = [
                    make_page(
                        "广东乙汽车零部件有限公司",
                        "https://example.com/b",
                    ),
                ]

            elif "湖北" in query:

                pages = [
                    make_page(
                        "湖北丙汽车零部件有限公司",
                        "https://example.com/c",
                    ),
                    make_page(
                        "湖北丙汽车零部件有限公司",
                        "https://example.com/c",
                    ),
                ]

            else:

                pages = []

            return {
                "success": True,
                "data_mode": "real_web_search",
                "mock_fallback_used": False,
                "results": pages,
            }

        mocked_search.side_effect = provider

        result = discover_companies(
            industry="汽车零部件",
            region="中国",
        )

        self.assertEqual(
            result["search_call_count"],
            8,
        )

        self.assertEqual(
            result["company_count"],
            3,
        )

        self.assertFalse(
            result["mock_fallback_used"]
        )

        companies = {
            item["name"]: item
            for item in result["companies"]
        }

        self.assertEqual(
            companies[
                "湖北丙汽车零部件有限公司"
            ]["source_count"],
            1,
        )

        for item in result["companies"]:

            self.assertEqual(
                item["identity_status"],
                "name_mentioned_in_search_result",
            )

            self.assertEqual(
                item["signals"],
                [],
            )

            self.assertIsNone(
                item["independent_source_count"]
            )

    @patch(
        "app.tools.real_company_discovery.search_real_web"
    )
    def test_mock_fallback_is_rejected(
        self,
        mocked_search,
    ):

        mocked_search.return_value = {
            "success": True,
            "data_mode": "real_web_search",
            "mock_fallback_used": True,
            "results": [],
        }

        with self.assertRaises(
            RuntimeError
        ):

            discover_companies(
                industry="汽车零部件",
                region="中国",
            )


if __name__ == "__main__":

    unittest.main()
