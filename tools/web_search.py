"""
tools/web_search.py — Member 2 owns this file
AI Agent Project | Phase 1

Provides search_web() — called by research_agent.py to search the web.
Uses Tavily API under the hood.
"""
import os
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

# ── Tavily client setup ───────────────────────────────────────────────────────
_client = None

def _get_client() -> TavilyClient:
    """Lazy-load the Tavily client (only created once)."""
    global _client
    if _client is None:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise EnvironmentError("❌ TAVILY_API_KEY not found in .env")
        _client = TavilyClient(api_key=api_key)
    return _client

# ── Main function used by research_agent.py ──────────────────────────────────
def search_web(query: str, max_results: int = 5) -> str:
    """
    Search the web for a given query and return results as a formatted string.

    Args:
        query       (str): The search query.
        max_results (int): How many results to return (default 5).

    Returns:
        str: Formatted search results ready for the agent to read.

    Example:
        results = search_web("LangChain agents tutorial")
        print(results)
    """
    print(f"🔎  Searching: {query}")
    try:
        client   = _get_client()
        response = client.search(
            query=query,
            max_results=max_results,
            search_depth="advanced",       # deeper = better results
            include_answer=True,           # get a quick summary answer too
        )

        # ── Format results into clean readable text ───────────────────────────
        parts = []

        # Tavily quick answer (if available)
        if response.get("answer"):
            parts.append(f"📌 Quick Answer:\n{response['answer']}\n")

        # Individual search results
        results = response.get("results", [])
        if not results:
            return "No results found for this query."

        parts.append(f"🌐 Top {len(results)} Results:\n")
        for i, result in enumerate(results, 1):
            title   = result.get("title",   "No title")
            url     = result.get("url",     "")
            content = result.get("content", "").strip()

            # Trim content to avoid overloading the agent
            if len(content) > 400:
                content = content[:400] + "..."

            parts.append(
                f"[{i}] {title}\n"
                f"    Source: {url}\n"
                f"    {content}\n"
            )

        return "\n".join(parts)

    except Exception as e:
        error_msg = f"❌ Search failed for '{query}': {str(e)}"
        print(error_msg)
        return error_msg


# ── Bonus: search and return raw list (useful for Member 1's agent) ──────────
def search_web_raw(query: str, max_results: int = 5) -> list[dict]:
    """
    Same as search_web() but returns raw list of result dicts.
    Useful if you want to process results yourself.

    Returns:
        list of dicts with keys: title, url, content, score
    """
    try:
        client   = _get_client()
        response = client.search(query=query, max_results=max_results, search_depth="advanced")
        return response.get("results", [])
    except Exception as e:
        print(f"❌ Raw search failed: {e}")
        return []


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_query = "What are LangChain agents?"
    print(f"\nTesting web_search.py with: '{test_query}'\n")
    print("─" * 50)
    result = search_web(test_query, max_results=3)
    print(result)
    print("\n✅ web_search.py is working!")
