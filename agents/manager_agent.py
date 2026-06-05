"""
manager_agent.py — Orchestrator Agent for the Multi-Agent System.

Routes tasks to the correct specialist agent:
  - research_agent  : web research, information gathering
  - writer_agent    : content generation, reports, articles
  - github_agent    : GitHub operations (read repos, push files)
  - coder_agent     : code generation, debugging, execution, testing
  - email_agent     : email drafting, sending, replying, summarizing
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()


def get_llm():
    return ChatGroq(
        model="llama3-70b-8192",
        temperature=0.0,
        api_key=os.getenv("GROQ_API_KEY"),
    )


# ── Routing Keywords (fast-path before LLM) ──────────────────────────────────
ROUTING_KEYWORDS = {
    "coder": [
        "write code", "generate code", "create a script", "python script",
        "javascript", "code for", "function to", "algorithm", "debug",
        "fix this code", "refactor", "unit test", "run this code", "execute",
        "convert code", "add docstring", "explain this code", "coding",
        "program that", "write a program",
    ],
    "email": [
        "send email", "draft email", "write an email", "email to",
        "compose email", "follow up email", "reply to email",
        "cold outreach", "apology email", "complaint email",
        "summarize email", "translate email", "email my", "mail to",
    ],
    "github": [
        "github", "push to", "commit", "repo", "repository", "pull request",
        "list files", "read repo", "save to github",
    ],
    "writer": [
        "write a blog", "write an article", "write a report", "content about",
        "essay on", "summary of", "draft a post", "write about",
    ],
    "research": [
        "research", "search for", "find information", "what is", "who is",
        "latest news", "look up", "gather data", "investigate",
    ],
}


def manager_agent(state: dict) -> dict:
    """
    LangGraph node: decides which agent to call next.
    Sets state["next"] to the agent name.
    """
    task = state.get("task", "").strip()
    if not task:
        state["next"] = "end"
        return state

    print(f"\n[Manager] 🧠 Routing task: {task[:80]}...")

    # 1) Try fast keyword routing first
    next_agent = _keyword_route(task)

    # 2) Fall back to LLM routing if unclear
    if not next_agent:
        next_agent = _llm_route(task)

    print(f"[Manager] ➡️  Routing to: {next_agent}")
    state["next"] = next_agent
    return state


def _keyword_route(task: str) -> str:
    task_lower = task.lower()
    for agent, keywords in ROUTING_KEYWORDS.items():
        if any(kw in task_lower for kw in keywords):
            return agent
    return ""


def _llm_route(task: str) -> str:
    llm = get_llm()
    system = SystemMessage(content=(
        "You are a task router for a multi-agent system. "
        "Given a user task, choose exactly ONE agent from this list:\n"
        "  - research  : for web search, information gathering, facts\n"
        "  - writer    : for writing articles, reports, blog posts, content\n"
        "  - github    : for GitHub operations (push, read repos, commits)\n"
        "  - coder     : for code generation, debugging, execution, testing\n"
        "  - email     : for drafting, sending, replying to emails\n\n"
        "Respond with ONLY the agent name, nothing else. "
        "No punctuation, no explanation."
    ))
    response = llm.invoke([system, HumanMessage(content=f"Task: {task}")])
    choice = response.content.strip().lower().split()[0]

    valid = {"research", "writer", "github", "coder", "email"}
    return choice if choice in valid else "research"


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    tests = [
        "Research quantum computing trends",
        "Write a Python function to sort a list",
        "Send an email to my boss about the meeting",
        "Push the research report to GitHub",
        "Write a blog post about LangGraph",
        "Debug this Python code that has a syntax error",
        "Draft a cold outreach email for our SaaS product",
    ]
    for t in tests:
        state = {"task": t, "next": ""}
        result = manager_agent(state)
        print(f"  '{t[:50]}' → {result['next']}")
