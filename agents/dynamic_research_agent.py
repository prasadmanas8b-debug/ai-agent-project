"""
agents/dynamic_research_agent.py — Research Agent.

Uses a LangChain ReAct agent backed by Groq (llama-3.3-70b) and Tavily web search
to research any topic and return a structured markdown report.
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate

load_dotenv()

# ── Lazy singletons ───────────────────────────────────────────────────────────
_agent: AgentExecutor | None = None


def _get_agent() -> AgentExecutor:
    """Build (and cache) the ReAct agent on first use."""
    global _agent
    if _agent is not None:
        return _agent

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.2,
        api_key=os.getenv("GROQ_API_KEY"),
    )
    tools = [TavilySearchResults(max_results=5, api_key=os.getenv("TAVILY_API_KEY"))]

    prompt = PromptTemplate.from_template("""
You are a thorough research assistant. Research the given topic and produce a
well-structured markdown report with these sections:

## Overview
2-3 sentence introduction.

## Key Findings
- Bullet points of the most important facts.

## Details
Deeper explanation with examples.

## Conclusion
1-2 sentence wrap-up.

Available tools: {tools}
Tool names: {tool_names}

Use this format:
Question: the input question
Thought: what to do
Action: tool name
Action Input: input to the tool
Observation: tool result
... (repeat as needed)
Thought: I now have enough to write the report
Final Answer: [the full markdown report]

Question: {input}
Thought: {agent_scratchpad}
""")

    _agent = AgentExecutor(
        agent=create_react_agent(llm, tools, prompt),
        tools=tools,
        verbose=False,
        handle_parsing_errors=True,
        max_iterations=6,
    )
    return _agent


def run_research_agent(task: str) -> str:
    """
    Research a topic and return a markdown report string.

    Args:
        task: The research question or topic.

    Returns:
        Markdown-formatted research report, or an error message.
    """
    print(f"\n🔍 Research Agent — task: {task[:100]}")
    try:
        result = _get_agent().invoke({"input": task})
        # AgentExecutor returns {"output": "..."} or {"messages": [...]}
        if isinstance(result, dict):
            output = result.get("output") or result.get("messages", [{}])[-1].get("content", "")
        else:
            output = str(result)
        print(f"🔍 Research Agent — done ({len(output)} chars)")
        return output
    except Exception as exc:
        msg = f"[Research Agent ERROR] {exc}"
        print(msg)
        return msg
