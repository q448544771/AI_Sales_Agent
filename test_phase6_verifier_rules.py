
"""Phase 6.3 - Source verifier rule tests.

These tests do not make network requests.
They validate publication dates, URL hints,
and company-specific literal evidence extraction.
"""

import unittest

from bs4 import BeautifulSoup

from app.tools.source_verifier import (
    _page_publication_date,
    _url_date_hint,
    _candidate_quotes,
)


COMPANY = "湖北敏能汽车零部件有限公司"


class VerifierRuleTests(unittest.TestCase):

    # ========================================================
    # 1. Explicit publication date
    # ========================================================

    def test_explicit_publication_date(self):

        html = """
        <html>
          <body>
            <div>站内其他日期：2026-07-01</div>
            <div>发布时间：2026-07-10 08:58</div>
          </body>
        </html>
        """

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        value, origin = _page_publication_date(
            soup,
            soup.get_text(
                " ",
                strip=True,
            ),
        )

        self.assertEqual(
            value,
            "2026-07-10 08:58",
        )

        self.assertEqual(
            origin,
            "explicit_publication_label",
        )

    # ========================================================
    # 2. Metadata has higher priority
    # ========================================================

    def test_metadata_has_priority(self):

        html = """
        <html>
          <head>
            <meta property="article:published_time"
                  content="2026-07-10T08:58:00+08:00">
          </head>
          <body>
            发布时间：2026-07-01
          </body>
        </html>
        """

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        value, origin = _page_publication_date(
            soup,
            soup.get_text(
                " ",
                strip=True,
            ),
        )

        self.assertEqual(
            value,
            "2026-07-10 08:58",
        )

        self.assertEqual(
            origin,
            "page_metadata",
        )

    # ========================================================
    # 3. An arbitrary page date cannot become publish date
    # ========================================================

    def test_unlabeled_date_is_not_publication_date(self):

        html = """
        <html>
          <body>
            <div>2026-07-01 相关文章导航</div>
          </body>
        </html>
        """

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        value, origin = _page_publication_date(
            soup,
            soup.get_text(
                " ",
                strip=True,
            ),
        )

        self.assertIsNone(value)

        self.assertIsNone(origin)

    # ========================================================
    # 4. URL date is only a hint
    # ========================================================

    def test_url_date_is_only_hint(self):

        url = (
            "http://news.xnnews.com.cn/"
            "202607/t20260710_5021435.shtml"
        )

        self.assertEqual(
            _url_date_hint(url),
            "2026-07-10",
        )

        self.assertIsNone(
            _url_date_hint(
                "https://example.com/article/abc"
            )
        )

    # ========================================================
    # 5. Quote must explicitly mention target company
    # ========================================================

    def test_quote_must_mention_target_company(self):

        text = (
            "7月4日，湖北敏能汽车零部件有限公司，"
            "工作人员正用新的智能生产线完成高精度作业。\n"
            "另一条行业信息提到新增自动化生产线。"
        )

        quotes = _candidate_quotes(
            text,
            COMPANY,
        )

        self.assertEqual(
            len(quotes),
            1,
        )

        self.assertIn(
            COMPANY,
            quotes[0]["quote"],
        )

        self.assertIn(
            "new_production_line",
            quotes[0]["signal_types"],
        )

        self.assertEqual(
            quotes[0]["quote_status"],
            "literal_page_excerpt_requires_review",
        )


if __name__ == "__main__":

    unittest.main()
