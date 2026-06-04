"""
tools/web_search.py — Web search utility.

Wraps the Tavily API to provide clean, formatted search results
for the Research Agent and any other agent that needs web data.
"""

import os
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

_client: TavilyClient | None = None  # lazy init


def _get_client() -> TavilyClient:
    global _client
    if _client is None:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise EnvironmentError("TAVILY_API_KEY not found in .env")
        _client = TavilyClient(api_key=api_key)
    return _client


def search_web(query: str, max_results: int = 5) -> str:
    """
    Search the web and return formatted results as a string.

    Args:
        query:       The search query.
        max_results: Number of results to return (default 5).

    Returns:
        Formatted string with a quick answer + individual results.
        Returns an error message string on failure.
    """
    print(f"🔎  Searching: {query}")
    try:
        response = _get_client().search(
            query=query,
            max_results=max_results,
            search_depth="advanced",
            include_answer=True,
        )
    except Exception as exc:
        return f"❌ Search failed for '{query}': {exc}"

    parts = []

    if response.get("answer"):
        parts.append(f"📌 Quick Answer:\n{response['answer']}\n")

    results = response.get("results", [])
    if not results:
        return "No results found."

    parts.append(f"🌐 Top {len(results)} Results:\n")
    for i, r in enumerate(results, 1):
        content = r.get("content", "").strip()
        if len(content) > 400:
            content = content[:400] + "…"
        parts.append(
            f"[{i}] {r.get('title', 'No title')}\n"
            f"    Source: {r.get('url', '')}\n"
            f"    {content}\n"
        )

    return "\n".join(parts)


def search_web_raw(query: str, max_results: int = 5) -> list[dict]:
    """
    Same as search_web() but returns a raw list of result dicts.

    Useful when the caller needs structured data rather than formatted text.
    """
    try:
        return _get_client().search(
            query=query,
            max_results=max_results,
            search_depth="advanced",
        ).get("results", [])
    except Exception as exc:
        print(f"❌ Raw search failed for '{query}': {exc}")
        return []
