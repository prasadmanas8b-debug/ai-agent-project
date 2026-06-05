"""
graph/state.py — Phase 3
AI Agent Project | Shared State Definition

What is State?
──────────────
State is the shared whiteboard that all agents read from and write to.
Think of it like a shared Google Doc that every agent can open:
  - Research Agent opens it, writes research_notes, closes it
  - Writer Agent opens it, reads research_notes, writes final_report, closes it
  - GitHub Agent opens it, reads final_report, writes github_result, closes it
  - Supervisor opens it, reads everything, writes "next" to say who runs next

Agents do NOT talk to each other directly.
They only communicate through this shared state object.

Why TypedDict?
──────────────
TypedDict lets Python know the exact shape (keys + types) of the dict.
This means:
  - Autocomplete works in your editor
  - Type errors are caught early
  - LangGraph can validate the state between nodes
"""

from typing import TypedDict


class AgentState(TypedDict):
    """
    The shared state object passed between every node in the LangGraph pipeline.

    Fields:
        task           (str): The original user input. Set once at the start.
                              Example: "Research quantum computing and save to GitHub"
                              Never modified after being set.

        research_notes (str): Raw research output from the Research Agent.
                              Starts empty. Research Agent fills this in.
                              Writer Agent reads this to generate the report.

        final_report   (str): The polished markdown report from the Writer Agent.
                              Starts empty. Writer Agent fills this in.
                              GitHub Agent reads this if it needs to save to repo.

        github_result  (str): A summary of what the GitHub Agent did.
                              Starts empty. GitHub Agent fills this in.
                              Example: "Created file docs/quantum.md in main branch."

        next           (str): The Supervisor writes the name of the NEXT agent here.
                              The graph's conditional edge reads this to decide routing.
                              Values: "research" | "writer" | "github" | "FINISH"
    """
    task:           str
    research_notes: str
    final_report:   str
    github_result:  str
    next:           str
