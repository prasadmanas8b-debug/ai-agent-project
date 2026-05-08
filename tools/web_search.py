"""
tools/web_search.py
--------------------
Web Search Tool for the Research Agent.
Uses Tavily Search API to fetch high-quality, relevant web results
and returns them in a clean format the agent can directly consume.

Owner   : Member 2
Branch  : feature/web-search-tool
API Key : TAVILY_API_KEY  (set this in your .env file)
"""

import os
from typing import Optional
from dotenv import load_dotenv
from tavily import TavilyClient

# ── Load .env so TAVILY_API_KEY is available ──────────────────────────────────
load_dotenv()


# ─────────────────────────────────────────────────────────────────────────────
# Internal helper
# ─────────────────────────────────────────────────────────────────────────────

def _get_client() -> TavilyClient:
    """
    Build and return a TavilyClient from the environment.

    Raises:
        EnvironmentError: If TAVILY_API_KEY is missing from .env
    """
    api_key = os.getenv("TAVILY_API_KEY", "").strip()
    if not api_key:
        raise EnvironmentError(
            "TAVILY_API_KEY is missing or empty.\n"
            "→ Open your .env file and add:  TAVILY_API_KEY=tvly-xxxxxxxx\n"
            "→ Get a free key at: https://tavily.com"
        )
    return TavilyClient(api_key=api_key)


# ─────────────────────────────────────────────────────────────────────────────
# Main public function — this is what the agent calls
# ─────────────────────────────────────────────────────────────────────────────

def web_search(
    query: str,
    max_results: int = 5,
    search_depth: str = "advanced",
    include_answer: bool = True,
) -> dict:
    """
    Search the web using Tavily and return structured, agent-ready results.

    Args:
        query         : What to search for (e.g. "LangChain agents tutorial").
        max_results   : How many results to return (default: 5, max: 10).
        search_depth  : "basic" (faster) or "advanced" (more thorough).
        include_answer: If True, Tavily returns its own AI-generated summary.

    Returns:
        dict with keys:
            "query"   → original query string
            "answer"  → Tavily's quick AI answer (str, may be empty)
            "results" → list of dicts, each containing:
                            "title"   : page title
                            "url"     : source URL
                            "content" : relevant excerpt (up to ~500 chars)
                            "score"   : relevance score (0.0 – 1.0)
            "error"   → only present if something went wrong (str)

    Usage (from research_agent.py):
        from tools.web_search import web_search, format_results_for_llm

        raw   = web_search("LangChain agents overview")
        text  = format_results_for_llm(raw)   # pass this into your LLM prompt
    """

    # ── Validate input ────────────────────────────────────────────────────────
    if not query or not query.strip():
        return {
            "query"  : query,
            "answer" : "",
            "results": [],
            "error"  : "Query is empty. Please provide a search term.",
        }

    max_results = max(1, min(max_results, 10))   # clamp between 1 and 10

    # ── Call Tavily ───────────────────────────────────────────────────────────
    try:
        client   = _get_client()
        response = client.search(
            query          = query.strip(),
            search_depth   = search_depth,
            max_results    = max_results,
            include_answer = include_answer,
        )

        # ── Normalise into a clean structure ──────────────────────────────────
        clean_results = []
        for item in response.get("results", []):
            clean_results.append({
                "title"  : item.get("title",   "No title"),
                "url"    : item.get("url",     ""),
                "content": item.get("content", "").strip(),
                "score"  : round(item.get("score", 0.0), 4),
            })

        # Sort best matches first
        clean_results.sort(key=lambda x: x["score"], reverse=True)

        return {
            "query"  : query,
            "answer" : response.get("answer", ""),
            "results": clean_results,
        }

    except EnvironmentError as env_err:
        return {"query": query, "answer": "", "results": [], "error": str(env_err)}

    except Exception as exc:
        return {
            "query"  : query,
            "answer" : "",
            "results": [],
            "error"  : f"Search failed — {type(exc).__name__}: {exc}",
        }


# ─────────────────────────────────────────────────────────────────────────────
# Formatter — converts raw dict → clean text the LLM can read
# ─────────────────────────────────────────────────────────────────────────────

def format_results_for_llm(search_output: dict, excerpt_length: int = 400) -> str:
    """
    Convert the dict from web_search() into a readable string
    ready to be injected into an LLM prompt.

    Args:
        search_output  : The dict returned by web_search().
        excerpt_length : Max characters to show per result excerpt.

    Returns:
        A formatted multi-line string.
    """
    if "error" in search_output:
        return f"[Search Error] {search_output['error']}"

    lines = []
    lines.append(f"Search Query: {search_output['query']}\n")

    answer = search_output.get("answer", "").strip()
    if answer:
        lines.append(f"Quick Answer:\n{answer}\n")

    results = search_output.get("results", [])
    if not results:
        lines.append("No results were found for this query.")
        return "\n".join(lines)

    lines.append(f"Top {len(results)} Web Results:\n")
    for i, r in enumerate(results, start=1):
        excerpt = r["content"][:excerpt_length].strip()
        if len(r["content"]) > excerpt_length:
            excerpt += "..."
        lines.append(f"[{i}] {r['title']}")
        lines.append(f"    Source  : {r['url']}")
        lines.append(f"    Excerpt : {excerpt}")
        lines.append("")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Quick self-test  →  run:  python tools/web_search.py
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("web_search.py — Self Test")
    print("=" * 60)

    query = "LangChain agents tutorial 2024"
    print(f"\nSearching for: '{query}'\n")

    result = web_search(query, max_results=3)

    if "error" in result:
        print(f"FAIL — {result['error']}")
    else:
        print(format_results_for_llm(result))
        print("=" * 60)
        print(f"PASS — Returned {len(result['results'])} results.")
        print("web_search.py is working correctly.")
