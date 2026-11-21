import asyncio
import logging
from typing import Any

from app.config import SEARCH_MAX_RESULTS, get_settings

logger = logging.getLogger(__name__)


def _tavily(query: str, api_key: str) -> list[dict[str, str]]:
    from tavily import TavilyClient

    response = TavilyClient(api_key=api_key).search(query, max_results=SEARCH_MAX_RESULTS)
    return [
        {
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "snippet": item.get("content", ""),
        }
        for item in response.get("results", [])
    ]


def _duckduckgo(query: str) -> list[dict[str, str]]:
    from ddgs import DDGS

    results = DDGS().text(query, max_results=SEARCH_MAX_RESULTS)
    return [
        {
            "title": item.get("title", ""),
            "url": item.get("href", ""),
            "snippet": item.get("body", ""),
        }
        for item in results or []
    ]


def _search_sync(query: str) -> list[dict[str, str]]:
    api_key = get_settings().tavily_api_key
    return _tavily(query, api_key) if api_key else _duckduckgo(query)


async def web_search(query: str) -> dict[str, Any]:
    try:
        results = await asyncio.to_thread(_search_sync, query)
    except Exception as error:
        logger.warning("web search failed: %s", error)
        return {"error": "Web search is unavailable right now. Say so; do not invent sources."}
    if not results:
        return {"results": [], "note": "No results found. Say so; do not invent sources."}
    return {"results": results}
