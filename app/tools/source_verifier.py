
"""Phase 6.3 - Real source-page verification.

This module verifies what is actually visible in retrieved HTML.

It does not:
- use mock data;
- treat search snippets as fetched page text;
- claim that a recruitment position is still open;
- prove legal business registration;
- count republished articles as independent confirmation.
"""

import ipaddress
import re
import socket

from datetime import date
from urllib.parse import urljoin, urlsplit

import requests

from bs4 import BeautifulSoup


# ============================================================
# Configuration
# ============================================================

MAX_HTML_BYTES = 2_000_000
MAX_REDIRECTS = 4
REQUEST_TIMEOUT = (8, 15)


ARTICLE_SELECTORS = [
    "#zoom",
    "#Zoom",
    ".TRS_Editor",
    ".article-content",
    ".article_content",
    ".news-content",
    ".news_content",
    ".detail-content",
    ".main-content",
    "article",
    "#content",
    ".content",
]


SIGNAL_PATTERNS = {
    "production_expansion": re.compile(
        r"扩产|扩建|产能提升|产线扩容"
    ),

    "new_production_line": re.compile(
        r"新建产线|新增产线|新建生产线|"
        r"新增生产线|智能生产线"
    ),

    "automation": re.compile(
        r"自动化|智能制造|机器人|智能化改造"
    ),

    "quality_inspection": re.compile(
        r"质量检测|视觉检测|机器视觉|"
        r"品检|质检|缺陷检测"
    ),

    "recruitment": re.compile(
        r"招聘|诚聘|职位|岗位"
    ),
}


# ============================================================
# Date parsing
# ============================================================

DATE_PATTERN = re.compile(
    r"(?P<year>20\d{2})[-/.年]\s*"
    r"(?P<month>1[0-2]|0?[1-9])[-/.月]\s*"
    r"(?P<day>3[01]|[12]\d|0?[1-9])日?"
    r"(?!\d)"
    r"(?:[T\s]+(?P<hour>2[0-3]|[01]?\d):"
    r"(?P<minute>[0-5]\d))?"
)


PUBLICATION_LABEL_PATTERN = re.compile(
    r"(?:发布时间|发布日期|发稿时间|刊发日期|刊登日期)"
    r"\s*[:：]?\s*"
    r"(?P<date>"
    r"20\d{2}[-/.年]\s*"
    r"(?:1[0-2]|0?[1-9])[-/.月]\s*"
    r"(?:3[01]|[12]\d|0?[1-9])日?"
    r"(?!\d)"
    r"(?:[T\s]+(?:2[0-3]|[01]?\d):[0-5]\d)?"
    r")"
)


URL_DATE_PATTERN = re.compile(
    r"(?<!\d)(20\d{2})[-/]?"
    r"(0[1-9]|1[0-2])[-/]?"
    r"(0[1-9]|[12]\d|3[01])(?!\d)"
)


class SourceFetchError(RuntimeError):
    pass


# ============================================================
# 1. Restrict the requested network target
# ============================================================

def _check_public_url(url):

    if not isinstance(url, str):
        raise SourceFetchError(
            "Invalid source URL"
        )

    parsed = urlsplit(
        url.strip()
    )

    if parsed.scheme not in {
        "http",
        "https",
    }:
        raise SourceFetchError(
            "Unsupported URL scheme"
        )

    hostname = parsed.hostname

    if not hostname:
        raise SourceFetchError(
            "Missing hostname"
        )

    if parsed.username or parsed.password:
        raise SourceFetchError(
            "Credential-bearing URLs are forbidden"
        )

    try:
        port = parsed.port

    except ValueError as exc:
        raise SourceFetchError(
            "Invalid port"
        ) from exc

    if port not in {
        None,
        80,
        443,
    }:
        raise SourceFetchError(
            "Unsupported URL port"
        )

    if (
        hostname.lower() == "localhost"
        or hostname.lower().endswith(
            (".local", ".internal")
        )
    ):
        raise SourceFetchError(
            "Local hostname is forbidden"
        )

    try:

        addresses = socket.getaddrinfo(
            hostname,
            port or (
                443
                if parsed.scheme == "https"
                else 80
            ),
            type=socket.SOCK_STREAM,
        )

    except OSError as exc:

        raise SourceFetchError(
            "Source hostname could not be resolved"
        ) from exc

    if not addresses:
        raise SourceFetchError(
            "No DNS result"
        )

    for address in addresses:

        ip = ipaddress.ip_address(
            address[4][0]
        )

        if not ip.is_global:
            raise SourceFetchError(
                "Non-public destination is forbidden"
            )

    return url.strip()


# ============================================================
# 2. Download actual HTML
# ============================================================

def _download_html(url):

    current_url = url

    session = requests.Session()

    # Keep the previous networking behavior.
    # Do not silently use environment HTTP proxies.
    session.trust_env = False

    try:

        for _ in range(
            MAX_REDIRECTS + 1
        ):

            current_url = _check_public_url(
                current_url
            )

            with session.get(
                current_url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 "
                        "(compatible; "
                        "ResearchSourceVerifier/1.0)"
                    ),
                    "Accept": (
                        "text/html,"
                        "application/xhtml+xml"
                    ),
                },
                timeout=REQUEST_TIMEOUT,
                allow_redirects=False,
                stream=True,
            ) as response:

                if response.status_code in {
                    301,
                    302,
                    303,
                    307,
                    308,
                }:

                    location = response.headers.get(
                        "Location"
                    )

                    if not location:
                        raise SourceFetchError(
                            "Redirect without Location"
                        )

                    current_url = urljoin(
                        current_url,
                        location,
                    )

                    continue

                response.raise_for_status()

                content_type = response.headers.get(
                    "Content-Type",
                    "",
                ).lower()

                if content_type and not any(
                    item in content_type
                    for item in (
                        "text/html",
                        "application/xhtml+xml",
                    )
                ):
                    raise SourceFetchError(
                        "Source is not an HTML page"
                    )

                chunks = []
                total_bytes = 0

                for chunk in response.iter_content(
                    chunk_size=16384
                ):

                    if not chunk:
                        continue

                    total_bytes += len(chunk)

                    if total_bytes > MAX_HTML_BYTES:
                        raise SourceFetchError(
                            "Source HTML exceeds size limit"
                        )

                    chunks.append(chunk)

                return (
                    b"".join(chunks),
                    current_url,
                )

        raise SourceFetchError(
            "Too many redirects"
        )

    except requests.RequestException as exc:

        raise SourceFetchError(
            "Source request failed: "
            f"{type(exc).__name__}"
        ) from exc

    finally:
        session.close()


# ============================================================
# 3. Extract original article text
# ============================================================

def _clean_text(element):

    if element is None:
        return ""

    return re.sub(
        r"[ \t\u3000]+",
        " ",
        element.get_text(
            separator="\n",
            strip=True,
        ),
    ).strip()


def _extract_article(soup):

    for element in soup.select(
        "script, style, noscript, svg, form"
    ):
        element.decompose()

    for selector in ARTICLE_SELECTORS:

        candidates = soup.select(
            selector
        )

        for candidate in candidates:

            text = _clean_text(
                candidate
            )

            if len(text) >= 80:

                return (
                    text,
                    selector,
                )

    # A whole-page match may come from navigation,
    # recommendations or the page footer.
    # Never promote it to a verified article match.

    body = soup.body or soup

    return (
        _clean_text(body),
        "body_fallback",
    )


# ============================================================
# 4. Publication date verification
# ============================================================

def _normalize_publication_date(value):

    if not isinstance(value, str):
        return None

    match = DATE_PATTERN.search(
        value.strip()
    )

    if not match:
        return None

    year = int(
        match.group("year")
    )

    month = int(
        match.group("month")
    )

    day = int(
        match.group("day")
    )

    try:

        validated = date(
            year,
            month,
            day,
        )

    except ValueError:
        return None

    normalized = validated.isoformat()

    if match.group("hour") is not None:

        normalized += (
            f" {int(match.group('hour')):02d}:"
            f"{match.group('minute')}"
        )

    return normalized


def _page_publication_date(soup, text):

    """
    Publication date priority:

    1. Publication-specific HTML metadata.
    2. Semantic HTML time element.
    3. Explicit publication label.

    Do not use an arbitrary date found in the body.
    """

    publication_meta_names = {
        "article:published_time",
        "datepublished",
        "pubdate",
        "publishdate",
        "publication_date",
    }

    # --------------------------------------------------------
    # 1. Publication metadata
    # --------------------------------------------------------

    for tag in soup.find_all("meta"):

        name = (
            tag.get("property")
            or tag.get("name")
            or tag.get("itemprop")
            or ""
        ).strip().lower()

        if name not in publication_meta_names:
            continue

        normalized = _normalize_publication_date(
            tag.get("content", "")
        )

        if normalized:

            return (
                normalized,
                "page_metadata",
            )

    # --------------------------------------------------------
    # 2. Semantic HTML time element
    # --------------------------------------------------------

    for tag in soup.select(
        'time[itemprop="datePublished"],'
        "time[datetime]"
    ):

        normalized = _normalize_publication_date(
            tag.get("datetime", "")
            or tag.get_text(
                " ",
                strip=True,
            )
        )

        if normalized:

            return (
                normalized,
                "html_time_element",
            )

    # --------------------------------------------------------
    # 3. Clearly labeled publication date
    # --------------------------------------------------------

    match = PUBLICATION_LABEL_PATTERN.search(
        text[:3500]
    )

    if match:

        normalized = _normalize_publication_date(
            match.group("date")
        )

        if normalized:

            return (
                normalized,
                "explicit_publication_label",
            )

    # No trustworthy publication date detected.
    return None, None


def _url_date_hint(url):

    """
    Extract a possible date embedded in the URL.

    This is only a cross-checking hint.
    It is not an authoritative publication date.
    """

    if not isinstance(url, str):
        return None

    match = URL_DATE_PATTERN.search(
        url
    )

    if not match:
        return None

    year, month, day = map(
        int,
        match.groups(),
    )

    try:

        return date(
            year,
            month,
            day,
        ).isoformat()

    except ValueError:
        return None


# ============================================================
# 5. Extract company-specific literal evidence
# ============================================================

def _candidate_quotes(
    article_text,
    company,
):

    """
    Extract only sentences that explicitly name
    the target company and contain a signal.

    No pronoun/coreference inference in Phase 6.3.
    """

    quotes = []
    seen = set()

    for line in article_text.splitlines():

        for sentence in re.split(
            r"(?<=[。！？；])",
            line.strip(),
        ):

            sentence = sentence.strip()

            if not sentence:
                continue

            # Avoid assigning another company's event
            # to the target company.
            if company not in sentence:
                continue

            signal_types = [
                signal_type
                for signal_type, pattern
                in SIGNAL_PATTERNS.items()
                if pattern.search(sentence)
            ]

            if not signal_types:
                continue

            # Preserve the literal company mention,
            # including when a long sentence needs
            # to be shortened for review.

            if len(sentence) <= 240:

                excerpt = sentence

            else:

                company_position = sentence.find(
                    company
                )

                start = max(
                    0,
                    company_position - 30,
                )

                excerpt = sentence[
                    start:start + 240
                ]

            if company not in excerpt:
                continue

            if excerpt in seen:
                continue

            seen.add(excerpt)

            quotes.append({
                "quote": excerpt,
                "signal_types": signal_types,
                "quote_status": (
                    "literal_page_excerpt_requires_review"
                ),
            })

            if len(quotes) >= 12:
                return quotes

    return quotes


# ============================================================
# 6. Detect content category from page title
# ============================================================

def _detect_page_type(title):

    if not isinstance(title, str):
        return "article_or_other"

    if re.search(
        r"招聘|诚聘|招聘职位|招聘岗位",
        title,
    ):
        return "recruitment"

    return "article_or_other"


# ============================================================
# 7. Fetch and check one original source page
# ============================================================

def fetch_source_page(
    company: str,
    source: dict,
    *,
    requested_type: str,
) -> dict:

    if requested_type not in {
        "news",
        "jobs",
    }:
        raise ValueError(
            "requested_type must be news or jobs"
        )

    company = (
        company or ""
    ).strip()

    if not company:
        raise ValueError(
            "Company name is required"
        )

    if not isinstance(source, dict):
        raise ValueError(
            "Source must be a dictionary"
        )

    source_url = source.get(
        "source_url"
    )

    result = {
        "company": company,
        "source_url": source_url,
        "requested_type": requested_type,

        "source_fetch_status": "fetch_failed",
        "identity_check": "not_checked",

        "article_selector": None,

        "final_url": None,
        "page_title": None,

        "page_published_at": None,
        "page_date_origin": None,

        "search_published_at": source.get(
            "published_at"
        ),

        "url_date_hint": None,
        "date_conflict_with_url_hint": False,

        "candidate_quotes": [],
        "detected_type": None,

        "error": None,
    }

    try:

        html, final_url = _download_html(
            source_url
        )

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        # Read the date before removing HTML elements.
        publication_date, date_origin = (
            _page_publication_date(
                soup,
                _clean_text(soup),
            )
        )

        title = _clean_text(
            soup.title
        )

        detected_type = _detect_page_type(
            title
        )

        article_text, selector = _extract_article(
            soup
        )

        # ----------------------------------------------------
        # Date cross-check
        # ----------------------------------------------------

        url_hint = _url_date_hint(
            final_url
        )

        result["final_url"] = final_url
        result["page_title"] = title

        result["page_published_at"] = publication_date
        result["page_date_origin"] = date_origin

        result["url_date_hint"] = url_hint

        result["date_conflict_with_url_hint"] = bool(
            publication_date
            and url_hint
            and publication_date[:10] != url_hint
        )

        result["article_selector"] = selector
        result["detected_type"] = detected_type

        # ----------------------------------------------------
        # Literal enterprise-name check
        # ----------------------------------------------------

        if company not in article_text:

            result["source_fetch_status"] = (
                "name_not_found_in_extracted_text"
            )

            result["identity_check"] = (
                "name_not_confirmed"
            )

            return result

        # ----------------------------------------------------
        # Whole-page fallback is not sufficient proof
        # that the company appears in an article.
        # ----------------------------------------------------

        if selector == "body_fallback":

            result["source_fetch_status"] = (
                "body_name_match_only"
            )

            result["identity_check"] = (
                "requires_manual_article_extraction"
            )

            return result

        # ----------------------------------------------------
        # Real article extraction succeeded
        # ----------------------------------------------------

        result["source_fetch_status"] = (
            "article_name_match"
        )

        result["identity_check"] = (
            "company_name_present_in_article"
        )

        result["candidate_quotes"] = (
            _candidate_quotes(
                article_text,
                company,
            )
        )

        return result

    except (
        SourceFetchError,
        ValueError,
    ) as exc:

        result["error"] = str(exc)

        return result


# ============================================================
# 8. Verify Company MCP detail results
# ============================================================

def verify_company_sources(
    company: str,
    news_output: dict,
    jobs_output: dict,
    *,
    max_news: int = 3,
    max_jobs: int = 2,
) -> dict:

    if not company or not company.strip():

        raise ValueError(
            "Company cannot be empty"
        )

    if (
        max_news < 0
        or max_jobs < 0
    ):

        raise ValueError(
            "Verification limits must be nonnegative"
        )

    # --------------------------------------------------------
    # Input origin validation
    # --------------------------------------------------------

    for output in (
        news_output,
        jobs_output,
    ):

        if not isinstance(output, dict):

            raise ValueError(
                "Malformed Company MCP output"
            )

        if output.get("data_mode") != "real_web_search":

            raise ValueError(
                "Only real web search results are accepted"
            )

        if output.get("company") != company:

            raise ValueError(
                "Company MCP identity mismatch"
            )

        if output.get("verification_status") != (
            "search_result_only"
        ):

            raise ValueError(
                "Unexpected upstream verification status"
            )

        if not isinstance(
            output.get("results"),
            list,
        ):

            raise ValueError(
                "Company MCP results must be a list"
            )

    # --------------------------------------------------------
    # Fetch source pages
    # --------------------------------------------------------

    results = []
    seen_urls = set()

    for requested_type, output, limit in [
        ("news", news_output, max_news),
        ("jobs", jobs_output, max_jobs),
    ]:

        checked = 0

        for source in output["results"]:

            if checked >= limit:
                break

            if not isinstance(source, dict):
                continue

            url = source.get(
                "source_url"
            )

            if not url or url in seen_urls:
                continue

            seen_urls.add(url)

            checked += 1

            result = fetch_source_page(
                company,
                source,
                requested_type=requested_type,
            )

            # ------------------------------------------------
            # Check category consistency
            # ------------------------------------------------

            if (
                requested_type == "news"
                and result["detected_type"] == "recruitment"
            ):

                result["category_check"] = (
                    "recruitment_page_misclassified_as_news"
                )

            elif (
                requested_type == "jobs"
                and result["detected_type"] != "recruitment"
            ):

                result["category_check"] = (
                    "recruitment_type_not_confirmed"
                )

            else:

                result["category_check"] = (
                    "category_consistent"
                )

            results.append(result)

    # --------------------------------------------------------
    # Count actual article matches
    # --------------------------------------------------------

    verified_pages = [
        item
        for item in results
        if (
            item["source_fetch_status"]
            == "article_name_match"
            and item["category_check"]
            == "category_consistent"
        )
    ]

    date_conflict_count = sum(
        bool(item["date_conflict_with_url_hint"])
        for item in results
    )

    return {
        "company": company,

        "data_mode": "real_source_page",

        "pages_checked": len(results),

        "article_match_count": len(verified_pages),

        "date_conflict_count": date_conflict_count,

        "results": results,

        # Different URLs may republish the same report.
        # Do not call them independent corroboration.
        "independent_source_count": None,

        "mock_fallback_used": False,
    }
