"""
agents/dynamic_research_agent.py — Research Agent

A thorough AI researcher. Given any topic (even with typos or vague phrasing),
it searches the web via Tavily and produces a structured markdown report.

Key upgrades:
  - Intent correction: silently fixes typos before searching
  - Smarter prompt: forces structured output every time
  - Graceful fallback if Tavily is unavailable
  - Returns clean markdown always
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

_agent: AgentExecutor | None = None
_llm_fallback: ChatGroq | None = None


def _get_llm() -> ChatGroq:
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.2,
        max_tokens=4096,
        api_key=os.getenv("GROQ_API_KEY"),
    )


def _get_agent() -> AgentExecutor:
    """Build and cache the ReAct research agent."""
    global _agent
    if _agent is not None:
        return _agent

    tools = [TavilySearchResults(
        max_results=6,
        api_key=os.getenv("TAVILY_API_KEY"),
        include_answer=True,
    )]

    prompt = PromptTemplate.from_template(
        """You are a brilliant research assistant. Your job:
1. Silently correct any typos in the question before researching
2. Search for accurate, up-to-date information
3. Write a structured markdown report

Report format (ALWAYS follow this):
## Overview
2-3 sentence introduction.

## Key Findings
- 5-8 bullet points of the most important facts with sources where possible.

## Details
Deeper explanation organized into sub-topics with examples.

## Latest Developments
What is happening recently in this area.

## Conclusion
2-3 actionable takeaways.

Available tools: {tools}
Tool names: {tool_names}

ReAct format:
Question: {input}
Thought: First I'll understand and correct the question, then search.
Action: [tool name]
Action Input: [search query]
Observation: [result]
... (search 2-3 times with different queries for depth)
Thought: I have enough information to write the report.
Final Answer: [full markdown report — start with ##  Overview]

Question: {input}
Thought:{agent_scratchpad}"""
    )

    _agent = AgentExecutor(
        agent=create_react_agent(_get_llm(), tools, prompt),
        tools=tools,
        verbose=False,
        handle_parsing_errors=True,
        max_iterations=8,
        return_intermediate_steps=False,
    )
    return _agent


def _fallback_research(task: str) -> str:
    """
    If Tavily is unavailable, use the LLM's own knowledge to generate a report.
    Clearly labels the output as knowledge-based (no live search).
    """
    global _llm_fallback
    if _llm_fallback is None:
        _llm_fallback = _get_llm()

    system = """You are a knowledgeable research assistant.
Write a structured markdown research report on the given topic using your training knowledge.
Start your response with: > ⚠️ Note: This report is based on training knowledge (no live web search).

Then follow this structure:
## Overview
## Key Findings (bullet points)
## Details
## Conclusion
"""
    try:
        resp = _llm_fallback.invoke([
            SystemMessage(content=system),
            HumanMessage(content=f"Research topic: {task}"),
        ])
        return resp.content.strip()
    except Exception as exc:
        return f"[Research Agent] Could not complete research: {exc}"


def run_research_agent(task: str) -> str:
    """
    Research any topic and return a structured markdown report.

    Handles typos and vague inputs gracefully. Falls back to LLM knowledge
    if web search is unavailable.

    Args:
        task: The research question or topic (typos are OK).

    Returns:
        Markdown-formatted research report string.
    """
    print(f"\n🔍 Research Agent — task: {task[:100]}")

    # Check if Tavily is configured
    if not os.getenv("TAVILY_API_KEY"):
        print("🔍 Research Agent — Tavily not configured, using LLM fallback")
        return _fallback_research(task)

    try:
        result = _get_agent().invoke({"input": task})
        if isinstance(result, dict):
            output = (
                result.get("output")
                or (result.get("messages") or [{}])[-1].get("content", "")
            )
        else:
            output = str(result)

        output = output.strip()
        if not output:
            raise ValueError("Empty output from research agent")

        print(f"🔍 Research Agent — done ({len(output)} chars)")
        return output

    except Exception as exc:
        print(f"🔍 Research Agent — web search failed ({exc}), using LLM fallback")
        return _fallback_research(task)
