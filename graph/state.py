"""
graph/state.py — Shared state for the 3-Agent Pipeline.

Agents: Research · Writer · GitHub
"""

from typing import TypedDict, List, Dict, Any


class AgentState(TypedDict):
    # Core
    task:             str   # Original user input
    next:             str   # Routing decision from Supervisor

    # Agent results
    research_notes:   str   # Raw research text (Research Agent)
    final_report:     str   # Polished markdown report (Writer Agent)
    github_result:    str   # GitHub operation result (GitHub Agent)
