"""
graph/pipeline_graph.py — Phase 3
AI Agent Project | LangGraph Graph Definition

What this file is:
──────────────────
This is where everything connects. It defines the graph — the nodes,
the edges, and the routing logic — and compiles it into a runnable app.

Graph structure:
  START → Supervisor → [decides] → Research Node → Supervisor
                                 → Writer Node   → Supervisor
                                 → GitHub Node   → Supervisor
                                 → END

Key difference from Phase 2:
  Phase 2: hardcoded → research() then write(), always in that order
  Phase 3: dynamic   → Supervisor decides at each step based on the task

After every agent runs, control ALWAYS returns to the Supervisor.
The Supervisor then decides the next step. This loop continues until
the Supervisor returns "FINISH" → the graph ends.

Usage:
  from graph.pipeline_graph import build_graph
  graph = build_graph()
  result = graph.invoke({"task": "Research quantum computing"})
"""

import os
import sys
import re

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv()

# LangGraph imports
from langgraph.graph import StateGraph, END

# State
from graph.state import AgentState

# Agent functions
from agents.manager_agent  import run_supervisor
from agents.research_agent import run_research_agent
from agents.writer_agent   import run_writer_agent
from agents.github_agent   import run_github_agent


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: NODE WRAPPER FUNCTIONS
# Each wrapper adapts an agent function to the LangGraph node signature.
# Every node function must:
#   - Accept the full state dict
#   - Return a (partial or full) updated state dict
# ─────────────────────────────────────────────────────────────────────────────

def research_node(state: AgentState) -> AgentState:
    """
    Wraps run_research_agent() for use as a LangGraph node.

    Calls the Research Agent with the task from state,
    extracts the report string from the returned dict,
    and writes it into state["research_notes"].
    """
    print("\n" + "─"*55)
    print("[ NODE ] Research Agent running...")
    print("─"*55)

    topic = state["task"]

    # research_agent returns a dict {topic, report, saved_to}
    result = run_research_agent(topic)

    if isinstance(result, dict):
        raw_notes = result.get("report", "")
    else:
        raw_notes = str(result)

    # Clean the notes before storing in state
    research_notes = _clean_notes(raw_notes)

    print(f"[ NODE ] Research complete — {len(research_notes)} chars stored in state.")
    return {**state, "research_notes": research_notes}


def writer_node(state: AgentState) -> AgentState:
    """
    Wraps run_writer_agent() for use as a LangGraph node.

    Reads research_notes from state, calls Writer Agent,
    writes the final report back to state["final_report"].
    """
    print("\n" + "─"*55)
    print("[ NODE ] Writer Agent running...")
    print("─"*55)

    research_notes = state.get("research_notes", "")
    topic          = state["task"]

    final_report = run_writer_agent(
        research_notes = research_notes,
        topic          = topic,
    )

    print(f"[ NODE ] Writer complete — {len(final_report)} chars stored in state.")
    return {**state, "final_report": final_report}


def github_node(state: AgentState) -> AgentState:
    """
    Wraps run_github_agent() for use as a LangGraph node.

    Passes the task and (if available) the final_report to the GitHub Agent.
    The GitHub Agent decides what GitHub action to take based on the task.
    Writes the result to state["github_result"].
    """
    print("\n" + "─"*55)
    print("[ NODE ] GitHub Agent running...")
    print("─"*55)

    task         = state["task"]
    final_report = state.get("final_report", "")

    github_result = run_github_agent(
        task           = task,
        report_content = final_report,  # Pass report if available (for save-to-GitHub tasks)
    )

    print(f"[ NODE ] GitHub complete — result: {github_result[:80]}")
    return {**state, "github_result": github_result}


def supervisor_node(state: AgentState) -> AgentState:
    """
    Wraps run_supervisor() for use as a LangGraph node.
    Simply passes state through — run_supervisor handles everything.
    """
    return run_supervisor(state)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2: ROUTING FUNCTION
# The conditional edge reads state["next"] and returns the next node name.
# LangGraph uses the returned string to decide which node to go to.
# ─────────────────────────────────────────────────────────────────────────────

def route_from_supervisor(state: AgentState) -> str:
    """
    Conditional edge function — reads the Supervisor's decision from state
    and returns the name of the next node to run.

    This is what LangGraph calls to decide routing after the Supervisor runs.

    Returns:
        str: One of "research_node", "writer_node", "github_node", or END
    """
    next_agent = state.get("next", "FINISH")

    routing_map = {
        "research": "research_node",
        "writer":   "writer_node",
        "github":   "github_node",
        "FINISH":   END,
    }

    destination = routing_map.get(next_agent, END)
    print(f"[Router] Routing to: {destination}")
    return destination


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3: BUILD THE GRAPH
# ─────────────────────────────────────────────────────────────────────────────

def build_graph():
    """
    Assembles all nodes and edges into a compiled LangGraph application.

    Graph structure:
      Entry point → supervisor_node (always starts here)
      supervisor_node → [conditional edge] → research_node | writer_node | github_node | END
      research_node   → supervisor_node  (always returns to supervisor)
      writer_node     → supervisor_node  (always returns to supervisor)
      github_node     → supervisor_node  (always returns to supervisor)

    Returns:
        CompiledGraph: A runnable graph object. Call .invoke({"task": ...}) to run it.
    """
    # ── Create the graph with our state schema ────────────────────────────
    workflow = StateGraph(AgentState)

    # ── Add nodes ──────────────────────────────────────────────────────────
    # Each node is a name → function mapping
    workflow.add_node("supervisor_node", supervisor_node)
    workflow.add_node("research_node",   research_node)
    workflow.add_node("writer_node",     writer_node)
    workflow.add_node("github_node",     github_node)

    # ── Set entry point ────────────────────────────────────────────────────
    # Every run starts at the Supervisor — it decides who goes first
    workflow.set_entry_point("supervisor_node")

    # ── Add conditional edge from Supervisor ───────────────────────────────
    # After Supervisor runs, call route_from_supervisor() to pick the next node.
    # The dict maps possible return values → node names.
    workflow.add_conditional_edges(
        "supervisor_node",            # from this node
        route_from_supervisor,        # call this function to decide
        {                             # map return values to destinations
            "research_node": "research_node",
            "writer_node":   "writer_node",
            "github_node":   "github_node",
            END:             END,
        }
    )

    # ── Add return edges — every agent goes back to Supervisor ─────────────
    # After each agent finishes, always return to Supervisor for next decision
    workflow.add_edge("research_node", "supervisor_node")
    workflow.add_edge("writer_node",   "supervisor_node")
    workflow.add_edge("github_node",   "supervisor_node")

    # ── Compile ────────────────────────────────────────────────────────────
    # .compile() validates the graph structure and returns a runnable app
    graph = workflow.compile()

    print("[Graph] ✅ LangGraph pipeline compiled successfully.")
    return graph


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4: HELPER — NOTE CLEANER
# Same cleaning logic as Phase 2's main.py, now lives here in the graph layer
# ─────────────────────────────────────────────────────────────────────────────

def _clean_notes(raw: str) -> str:
    """Cleans raw research agent output before it's stored in state."""
    cleaned = re.sub(r'Invalid Format:.*?(?=##|\Z)', '', raw, flags=re.DOTALL)
    cleaned = re.sub(r'Agent stopped.*?(?=##|\Z)', '', cleaned, flags=re.DOTALL)

    lines = cleaned.split('\n')
    seen, deduped = set(), []
    for line in lines:
        key = line.strip()
        if key not in seen or key == '':
            deduped.append(line)
            seen.add(key)

    cleaned = '\n'.join(deduped).strip()

    failed_keywords = ['iteration limit', 'time limit', 'agent stopped', 'could not complete']
    if any(kw in cleaned.lower() for kw in failed_keywords):
        print("[Graph] ⚠️  Research notes contain failure message. Returning empty.")
        return ''

    return cleaned


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Building graph...\n")
    graph = build_graph()
    print("\nGraph built. Test with:")
    print('  result = graph.invoke({"task": "Research LangChain agents", '
          '"research_notes": "", "final_report": "", "github_result": "", "next": ""})')
