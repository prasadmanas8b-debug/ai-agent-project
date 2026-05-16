# Before you run this, check two things with Kunal:
# What does run_github_agent() return — a string or a dict?
# What are its exact parameter names?
# Those two lines in github_node are your most likely integration point to adjust. Everything else should connect cleanly since run_research_agent and run_writer_agent are your own Phase 2 code.
# Ready to move to main.py update next?
from langgraph.graph import StateGraph, END
from graph.state import AgentState
from agents.manager_agent import run_supervisor
from agents.research_agent import run_research_agent
from agents.writer_agent import run_writer_agent
from agents.github_agent import run_github_agent

# ── Node wrappers ──────────────────────────────────────────────────
def supervisor_node(state: AgentState) -> AgentState:
    return run_supervisor(state)

def research_node(state: AgentState) -> AgentState:
    result = run_research_agent(state['task'])
    return { **state, 'research_notes': result['report'] }

def writer_node(state: AgentState) -> AgentState:
    report = run_writer_agent(state['research_notes'], state['task'])
    return { **state, 'final_report': report }

def github_node(state: AgentState) -> AgentState:
    return run_github_agent(state)

# ── Routing function ───────────────────────────────────────────────
def route(state: AgentState) -> str:
    return state['next']

# ── Build the graph ────────────────────────────────────────────────
def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node('supervisor', supervisor_node)
    graph.add_node('research',   research_node)
    graph.add_node('writer',     writer_node)
    graph.add_node('github',     github_node)

    graph.set_entry_point('supervisor')

    graph.add_conditional_edges(
        'supervisor',
        route,
        {
            'research': 'research',
            'writer':   'writer',
            'github':   'github',
            'FINISH':   END,
        }
    )

    graph.add_edge('research', 'supervisor')
    graph.add_edge('writer',   'supervisor')
    graph.add_edge('github',   'supervisor')

    return graph.compile()