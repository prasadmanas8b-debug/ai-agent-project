# graph/state.py
# ─────────────────────────────────────────────────────────
# STATE — The shared whiteboard for all agents
# Every agent reads from this and writes back to it
# Nothing is passed manually between agents anymore
# ─────────────────────────────────────────────────────────

from typing import TypedDict
# TypedDict → lets us define a dictionary where each key
# has a specific type (str, int, etc.)
# Python uses this to catch mistakes early
# Example: if you accidentally write state["tsk"] instead of
# state["task"] — Python will warn you


class AgentState(TypedDict):
    # This is the blueprint of our shared whiteboard
    # Every field starts empty — agents fill them in as they run

    task: str
    # The original thing the user typed
    # Example: "Research AI in healthcare"
    # Set ONCE at the start — never changed after that

    research_notes: str
    # Written BY the Research Agent ONLY
    # Contains raw research text from web search
    # Empty until Research Agent runs
    # Example: "## Overview\nAI in healthcare means..."

    final_report: str
    # Written BY the Writer Agent ONLY
    # Contains the polished markdown report
    # Empty until Writer Agent runs
    # Example: "# Final Report\n## Overview..."

    github_result: str
    # Written BY the GitHub Agent ONLY
    # Contains the result of the GitHub action
    # Empty until GitHub Agent runs
    # Example: "File saved to docs/report.md ✅"

    next: str
    # Written BY the Supervisor ONLY
    # Contains the routing decision for next step
    # Possible values: "research" / "writer" / "github" / "FINISH"
    # This is what drives the entire flow of the system