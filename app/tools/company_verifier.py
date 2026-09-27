# Phase 7.2 fixed company verifier
# Replace app/tools/company_verifier.py with this version.

from datetime import datetime
import re
import requests
from bs4 import BeautifulSoup

SIGNAL_RULES = {
    "new_production_line": ["新建产线","新增生产线","智能生产线","自动化生产线","生产线"],
    "capacity_expansion": ["扩产","扩建","产能提升","产能扩大","生产基地"],
    "automation_upgrade": ["自动化","智能制造","数字化","技改"],
    "quality_inspection": ["质量检测","质检","品检","检测能力","质量提升"],
}


def fetch_page(url: str) -> dict:
    """
    Fetch original webpage.

    Phase7:
    - tolerate news/government pages
    - keep original URL
    - fix Chinese encoding
    - no mock fallback
    """

    try:

        response = requests.get(
            url,
            timeout=15,
            allow_redirects=True,
            headers={
                "User-Agent":
                    (
                        "Mozilla/5.0 "
                        "(Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 "
                        "(KHTML, like Gecko) "
                        "Chrome/120 Safari/537.36"
                    )
            },
        )

        response.raise_for_status()


        # ==================================================
        # 中文网页编码修复
        #
        # requests 对部分新闻网站会错误识别编码，
        # 例如 UTF-8 页面被解析成 ISO-8859-1，
        # 导致中文乱码。
        #
        # 强制使用网页真实编码检测结果。
        # ==================================================

        detected_encoding = (
            response.apparent_encoding
        )

        if detected_encoding:

            response.encoding = (
                detected_encoding
            )

        else:

            response.encoding = (
                "utf-8"
            )


        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )


        # ==================================================
        # 删除无关区域
        # ==================================================

        for tag in soup(
            [
                "script",
                "style",
                "noscript",
            ]
        ):
            tag.decompose()


        text = soup.get_text(
            "\n",
            strip=True,
        )


        return {

            "success": True,

            # 最终跳转后的 URL
            "url":
                response.url,

            # 原始 URL 保留
            "original_url":
                url,

            "text":
                text,

        }


    except Exception as e:

        return {

            "success": False,

            "url":
                url,

            "text":
                "",

            "error":
                str(e),

        }


def extract_signals(text: str):
    result = []
    for t, words in SIGNAL_RULES.items():
        for w in words:
            if w in text:
                result.append({"type": t, "keyword": w})
                break
    return result


def extract_quotes(text: str, company: str):
    quotes = []
    for s in re.split(r"[。！？\n]", text):
        s = s.strip()
        if not s:
            continue
        if company in s or any(
            w in s
            for group in SIGNAL_RULES.values()
            for w in group
        ):
            quotes.append(s)
    return quotes[:5]


def _get_sources(company_record: dict):
    return (
        company_record.get("discovery_sources", [])
        or company_record.get("sources", [])
    )


def verify_company(company_record: dict):

    name = company_record.get("name")
    if not name:
        raise ValueError("company name missing")

    verified_sources = []
    signals = []
    quotes = []

    for source in _get_sources(company_record):

        url = (
            source.get("source_url")
            or source.get("url")
        )

        if not url:
            continue

        page = fetch_page(url)

        if not page.get("success"):
            continue

        text = page.get("text", "")

        if name not in text:
            continue

        page_signals = extract_signals(text)
        page_quotes = extract_quotes(text, name)

        verified_sources.append({
            "url": url,
            "company_name_found": True,
            "signal_count": len(page_signals)
        })

        signals.extend(page_signals)
        quotes.extend(page_quotes)

    return {
        "company": name,
        "verification_status": (
            "verified_company"
            if verified_sources
            else "unverified"
        ),
        "verified_sources": verified_sources,
        "signals": signals,
        "literal_quotes": list(dict.fromkeys(quotes)),
        "verified_at": datetime.now().isoformat()
    }
