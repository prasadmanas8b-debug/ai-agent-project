"""
graph/pipeline_graph.py
Builds and compiles the LangGraph state machine.
"""
from langgraph.graph import StateGraph, END
from graph.state import AgentState
from agents.manager_agent import run_supervisor
from agents.dynamic_research_agent import run_research_agent
from agents.writer_agent import run_writer_agent
from agents.github_agent import run_github_agent

def supervisor_node(state: AgentState) -> AgentState:
    return run_supervisor(state)

def research_node(state: AgentState) -> AgentState:
    result = run_research_agent(state["task"])
    return {**state, "research_notes": result}

def writer_node(state: AgentState) -> AgentState:
    report = run_writer_agent(state["research_notes"], state["task"])
    return {**state, "final_report": report}

def github_node(state: AgentState) -> AgentState:
    return run_github_agent(state)

def route(state: AgentState) -> str:
    return state["next"]

def build_graph():
    g = StateGraph(AgentState)
    g.add_node("supervisor", supervisor_node)
    g.add_node("research",   research_node)
    g.add_node("writer",     writer_node)
    g.add_node("github",     github_node)
    g.set_entry_point("supervisor")
    g.add_conditional_edges("supervisor", route, {
        "research": "research",
        "writer":   "writer",
        "github":   "github",
        "FINISH":   END,
    })
    g.add_edge("research", "supervisor")
    g.add_edge("writer",   "supervisor")
    g.add_edge("github",   "supervisor")
    return g.compile()
