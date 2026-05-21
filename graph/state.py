"""
graph/state.py  --  Shared whiteboard passed between all agents.
"""
from typing import TypedDict

class AgentState(TypedDict):
    task: str
    # Original user input. Set once, never changed.

    research_notes: str
    # Written by Research Agent -- raw web research text.

    final_report: str
    # Written by Writer Agent -- polished markdown report.

    code_result: str
    # Written by Coder Agent -- save confirmation + line count.

    github_result: str
    # Written by GitHub Agent -- result of file/branch operations.

    pdf_result: str
    # Written by PDF Agent -- extracted text or summary from a PDF file.

    next: str
    # Written by Supervisor each loop.
    # Values: "research" | "writer" | "coder" | "github" | "pdf" | "FINISH"
