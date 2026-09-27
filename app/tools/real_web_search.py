"""
Phase 6.1 - Real Web Search Provider.

Production data comes only from the external Bocha API.
There is no mock fallback or hard-coded company list.

Important:
Search results are discovery material, not independently
verified source-page facts.
"""

import os

from datetime import datetime, timezone
from urllib.parse import urlsplit

import requests

from dotenv import load_dotenv


load_dotenv()


BOCHA_ENDPOINT = "https://api.bocha.cn/v1/web-search"

VALID_FRESHNESS = {
    "noLimit",
    "oneDay",
    "oneWeek",
    "oneMonth",
    "oneYear",
}


class RealSearchError(RuntimeError):
    pass


def _normalize_date(value):

    if not isinstance(value, str) or not value.strip():
        return None

    value = value.strip()

    try:
        datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )
    except ValueError:
        return None

    return value


def _valid_url(value):

    if not isinstance(value, str):
        return False

    try:
        parsed = urlsplit(value.strip())
    except ValueError:
        return False

    return (
        parsed.scheme in {"http", "https"}
        and bool(parsed.hostname)
        and not parsed.username
        and not parsed.password
    )


def search_real_web(
    query: str,
    *,
    count: int = 5,
    freshness: str = "noLimit",
    timeout: int = 25,
) -> dict:

    """
    Search actual web results.

    No API key -> explicit failure.
    API failure -> explicit failure.
    Empty results -> empty results, never mock substitution.
    """

    if not isinstance(query, str) or not query.strip():

        raise ValueError(
            "Real search query cannot be empty"
        )

    if (
        isinstance(count, bool)
        or not isinstance(count, int)
        or not 1 <= count <= 20
    ):

        raise ValueError(
            "count must be between 1 and 20"
        )

    if freshness not in VALID_FRESHNESS:

        raise ValueError(
            "Unsupported freshness option"
        )

    api_key = os.getenv("BOCHA_API_KEY", "").strip()

    if not api_key:

        raise RealSearchError(
            "BOCHA_API_KEY is missing. "
            "Real search cannot fall back to mock data."
        )

    query = query.strip()

    try:

        response = requests.post(
            BOCHA_ENDPOINT,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "query": query,
                "count": count,
                "freshness": freshness,
                "summary": False,
            },
            timeout=timeout,
        )

        response.raise_for_status()

        payload = response.json()

    except (
        requests.RequestException,
        ValueError,
    ) as exc:

        raise RealSearchError(
            "Real web search request failed"
        ) from exc

    if not isinstance(payload, dict):

        raise RealSearchError(
            "Search provider returned malformed JSON"
        )

    if payload.get("code") != 200:

        raise RealSearchError(
            "Search provider rejected the request; "
            f"log_id={payload.get('log_id', 'unknown')}"
        )

    data = payload.get("data")

    if not isinstance(data, dict):

        raise RealSearchError(
            "Search provider returned invalid data"
        )

    web_pages = data.get("webPages")

    if not isinstance(web_pages, dict):

        raise RealSearchError(
            "Search provider returned invalid webPages"
        )

    pages = web_pages.get("value")

    if not isinstance(pages, list):

        raise RealSearchError(
            "Search provider returned invalid results"
        )

    retrieved_at = datetime.now(
        timezone.utc
    ).isoformat()

    results = []

    seen_urls = set()

    for item in pages:

        if not isinstance(item, dict):
            continue

        title = item.get("name")
        url = item.get("url")
        snippet = item.get("snippet")
        publisher = item.get("siteName")

        if (
            not isinstance(title, str)
            or not title.strip()
            or not _valid_url(url)
        ):
            continue

        url = url.strip()

        if url in seen_urls:
            continue

        seen_urls.add(url)

        results.append({
            "title": title.strip(),
            "source_url": url,
            "publisher": (
                publisher.strip()
                if isinstance(publisher, str)
                else ""
            ),
            "snippet": (
                snippet.strip()
                if isinstance(snippet, str)
                else ""
            ),
            "published_at": _normalize_date(
                item.get("datePublished")
            ),
            "retrieved_at": retrieved_at,
            "search_query": query,
            "provider": "bocha",
            "verification_status": "search_result_only",
        })

    return {
        "success": True,
        "data_mode": "real_web_search",
        "provider": "bocha",
        "query": query,
        "result_count": len(results),
        "results": results,
        "mock_fallback_used": False,
    }