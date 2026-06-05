"""
graph/pipeline_graph.py — 3-Agent LangGraph Pipeline.

Flow:
  supervisor → research | writer | github → supervisor → ... → FINISH
"""

from langgraph.graph import StateGraph, END

from graph.state import AgentState
from agents.manager_agent import run_supervisor
from agents.dynamic_research_agent import run_research_agent
from agents.writer_agent import run_writer_agent
from agents.github_agent import run_github_agent


# ── Node wrappers ─────────────────────────────────────────────────────────────

def supervisor_node(state: AgentState) -> AgentState:
    return run_supervisor(state)

def research_node(state: AgentState) -> AgentState:
    return {**state, "research_notes": run_research_agent(state["task"])}

def writer_node(state: AgentState) -> AgentState:
    return {**state, "final_report": run_writer_agent(state["research_notes"], state["task"])}

def github_node(state: AgentState) -> AgentState:
    return run_github_agent(state)


# ── Router ────────────────────────────────────────────────────────────────────

def _route(state: AgentState) -> str:
    return state["next"]


# ── Graph factory ─────────────────────────────────────────────────────────────

def build_graph():
    g = StateGraph(AgentState)

    g.add_node("supervisor", supervisor_node)
    g.add_node("research",   research_node)
    g.add_node("writer",     writer_node)
    g.add_node("github",     github_node)

    g.set_entry_point("supervisor")
    g.add_conditional_edges("supervisor", _route, {
        "research": "research",
        "writer":   "writer",
        "github":   "github",
        "FINISH":   END,
    })

    for agent in ("research", "writer", "github"):
        g.add_edge(agent, "supervisor")

    return g.compile()
