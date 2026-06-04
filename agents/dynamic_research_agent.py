"""
agents/dynamic_research_agent.py — Research Agent

Searches the web via Tavily and produces a structured markdown report.
Falls back to LLM knowledge if Tavily is unavailable.

Implementation: Manual tool-calling loop using langchain_core only.
NO dependency on langchain.agents (AgentExecutor / create_react_agent) —
those imports are unstable across langchain versions and not needed here.
"""

import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool

load_dotenv()

# ── Lazy singletons ───────────────────────────────────────────────────────────
_llm: ChatGroq | None = None
_llm_with_tools: ChatGroq | None = None


def _get_llm() -> ChatGroq:
    global _llm
    if _llm is None:
        _llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.2,
            max_tokens=4096,
            api_key=os.getenv("GROQ_API_KEY"),
        )
    return _llm


# ── Tavily search tool ────────────────────────────────────────────────────────

def _tavily_search(query: str, max_results: int = 6) -> str:
    """Run a Tavily search and return formatted results."""
    try:
        from tavily import TavilyClient
        client   = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        response = client.search(
            query=query,
            max_results=max_results,
            search_depth="advanced",
            include_answer=True,
        )
        parts = []
        if response.get("answer"):
            parts.append(f"Quick Answer: {response['answer']}\n")
        for i, r in enumerate(response.get("results", []), 1):
            content = r.get("content", "").strip()[:500]
            parts.append(f"[{i}] {r.get('title','')}\n    {r.get('url','')}\n    {content}")
        return "\n\n".join(parts) if parts else "No results found."
    except Exception as exc:
        return f"Search error: {exc}"


# ── Manual tool-call loop (replaces AgentExecutor) ───────────────────────────

_SEARCH_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": (
            "Search the web for up-to-date information on a topic. "
            "Call this 2-4 times with different queries to get broad coverage."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query string.",
                }
            },
            "required": ["query"],
        },
    },
}

_SYSTEM_PROMPT = """You are a thorough research assistant.

Your job:
1. Silently correct any typos or grammar mistakes in the user's question.
2. Call web_search() 2-4 times with different, specific queries to gather broad information.
3. After gathering enough information, write a polished structured markdown report.

Report structure (ALWAYS use this format):
## Overview
2-3 sentence introduction.

## Key Findings
- 5-8 specific bullet points with the most important facts.

## Details
Deeper explanation in sub-sections with examples and data.

## Latest Developments
What's happening recently in this area.

## Conclusion
2-3 actionable takeaways.

Start writing the Final Answer only after you've done at least 2 searches.
"""


def _run_tool_loop(task: str) -> str:
    """
    Manual agentic loop:
      1. Send task to LLM (with web_search tool bound)
      2. If LLM calls the tool → execute it → feed result back
      3. Repeat until LLM gives a plain text Final Answer
    """
    llm_with_tools = _get_llm().bind_tools([_SEARCH_TOOL_SCHEMA])

    messages = [
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=f"Research this topic (correct any typos first): {task}"),
    ]

    for iteration in range(8):  # max 8 iterations
        response = llm_with_tools.invoke(messages)
        messages.append(response)

        # Check if the LLM wants to call a tool
        tool_calls = getattr(response, "tool_calls", None) or []
        if not tool_calls:
            # No tool calls → this is the final answer
            return response.content.strip()

        # Execute each tool call and append results
        for tc in tool_calls:
            tool_name = tc.get("name", "")
            tool_args = tc.get("args", {})
            tool_id   = tc.get("id", f"call_{iteration}")

            if tool_name == "web_search":
                query  = tool_args.get("query", task)
                print(f"🔍 Research Agent — searching: {query[:80]}")
                result = _tavily_search(query)
            else:
                result = f"Unknown tool: {tool_name}"

            messages.append(
                ToolMessage(content=result, tool_call_id=tool_id)
            )

    # Exhausted iterations — extract last content
    for msg in reversed(messages):
        content = getattr(msg, "content", "")
        if content and not getattr(msg, "tool_calls", None):
            return content.strip()

    return "[Research Agent] Could not complete research within iteration limit."


# ── LLM-only fallback (no Tavily) ─────────────────────────────────────────────

def _fallback_research(task: str) -> str:
    """Use LLM training knowledge when Tavily is unavailable."""
    system = """You are a knowledgeable research assistant.
Write a structured markdown research report using your training knowledge.
Begin with this note on line 1:
> ⚠️ Note: This report is based on training knowledge — no live web search was performed.

Then use this structure:
## Overview
## Key Findings
## Details
## Conclusion
"""
    try:
        resp = _get_llm().invoke([
            SystemMessage(content=system),
            HumanMessage(content=f"Research topic: {task}"),
        ])
        return resp.content.strip()
    except Exception as exc:
        return f"[Research Agent ERROR] {exc}"


# ── Public entry point ────────────────────────────────────────────────────────

def run_research_agent(task: str) -> str:
    """
    Research any topic and return a structured markdown report.

    Silently handles typos. Falls back to LLM knowledge if Tavily unavailable.

    Args:
        task: Research question or topic (typos are fine).

    Returns:
        Markdown-formatted research report string.
    """
    print(f"\n🔍 Research Agent — task: {task[:100]}")

    if not os.getenv("TAVILY_API_KEY"):
        print("🔍 Research Agent — TAVILY_API_KEY not set, using LLM fallback")
        return _fallback_research(task)

    try:
        output = _run_tool_loop(task)
        if not output:
            raise ValueError("Empty output")
        print(f"🔍 Research Agent — done ({len(output)} chars)")
        return output
    except Exception as exc:
        print(f"🔍 Research Agent — tool loop failed ({exc}), using LLM fallback")
        return _fallback_research(task)
