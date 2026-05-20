"""
graph/pipeline_graph.py  --  Builds and compiles the LangGraph state machine.
Flow: supervisor -> research | writer | coder | github -> supervisor -> ... -> FINISH
"""
from langgraph.graph import StateGraph, END
from graph.state import AgentState
from agents.manager_agent import run_supervisor
from agents.dynamic_research_agent import run_research_agent
from agents.writer_agent import run_writer_agent
from agents.coder_agent import run_coder_agent
from agents.github_agent import run_github_agent


def supervisor_node(state: AgentState) -> AgentState:
    return run_supervisor(state)

def research_node(state: AgentState) -> AgentState:
    return {**state, "research_notes": run_research_agent(state["task"])}

def writer_node(state: AgentState) -> AgentState:
    return {**state, "final_report": run_writer_agent(state["research_notes"], state["task"])}

def coder_node(state: AgentState) -> AgentState:
    return run_coder_agent(state)

def github_node(state: AgentState) -> AgentState:
    return run_github_agent(state)

def route(state: AgentState) -> str:
    return state["next"]

def build_graph():
    g = StateGraph(AgentState)
    g.add_node("supervisor", supervisor_node)
    g.add_node("research",   research_node)
    g.add_node("writer",     writer_node)
    g.add_node("coder",      coder_node)
    g.add_node("github",     github_node)

    g.set_entry_point("supervisor")
    g.add_conditional_edges("supervisor", route, {
        "research": "research",
        "writer":   "writer",
        "coder":    "coder",
        "github":   "github",
        "FINISH":   END,
    })
    g.add_edge("research", "supervisor")
    g.add_edge("writer",   "supervisor")
    g.add_edge("coder",    "supervisor")
    g.add_edge("github",   "supervisor")
    return g.compile()
