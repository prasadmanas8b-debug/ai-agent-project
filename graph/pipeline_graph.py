"""
graph/pipeline_graph.py — LangGraph state machine for the Multi-Agent System.

Agents:
  manager_agent  → routes to the right specialist
  research_agent → web research
  writer_agent   → content writing
  github_agent   → GitHub operations
  coder_agent    → code generation + execution
  email_agent    → email drafting + sending

Flow:
  START → manager → (research | writer | github | coder | email) → END
"""

from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

# ── State Schema ──────────────────────────────────────────────────────────────
class AgentState(TypedDict):
    # Input
    task: str

    # Research Agent output
    research_notes: str

    # Writer Agent output
    final_report: str

    # GitHub Agent output
    github_result: str

    # Coder Agent output
    code_output: str        # raw generated code
    code_result: str        # formatted summary (with exec output)

    # Email Agent output
    email_draft: str        # raw drafted email
    email_result: str       # formatted summary (with send status)

    # Routing
    next: str


# ── Import Agents (lazy to allow partial installs) ────────────────────────────
def _load_agents():
    from agents.manager_agent  import manager_agent
    # ✅ Correct
    from agents.research_agent import run_research_agent as research_agent
    from agents.writer_agent   import writer_agent
    from agents.github_agent   import github_agent
    from agents.coder_agent    import coder_agent
    from agents.email_agent    import email_agent
    return manager_agent, research_agent, writer_agent, github_agent, coder_agent, email_agent


# ── Routing Function ──────────────────────────────────────────────────────────
def route_decision(state: AgentState) -> str:
    """Called after manager_agent to decide which node to visit next."""
    return state.get("next", "end")


# ── Graph Builder ─────────────────────────────────────────────────────────────
def build_graph():
    (
        manager_agent,
        research_agent,
        writer_agent,
        github_agent,
        coder_agent,
        email_agent,
    ) = _load_agents()

    graph = StateGraph(AgentState)

    # Register all nodes
    graph.add_node("manager",  manager_agent)
    graph.add_node("research", research_agent)
    graph.add_node("writer",   writer_agent)
    graph.add_node("github",   github_agent)
    graph.add_node("coder",    coder_agent)
    graph.add_node("email",    email_agent)

    # Entry point
    graph.set_entry_point("manager")

    # Conditional routing from manager
    graph.add_conditional_edges(
        "manager",
        route_decision,
        {
            "research": "research",
            "writer":   "writer",
            "github":   "github",
            "coder":    "coder",
            "email":    "email",
            "end":      END,
        },
    )

    # All specialist agents go to END after completing
    for node in ["research", "writer", "github", "coder", "email"]:
        graph.add_edge(node, END)

    return graph.compile()


# ── Convenience: get empty initial state ─────────────────────────────────────
def initial_state(task: str) -> AgentState:
    return {
        "task":           task,
        "research_notes": "",
        "final_report":   "",
        "github_result":  "",
        "code_output":    "",
        "code_result":    "",
        "email_draft":    "",
        "email_result":   "",
        "next":           "",
    }
