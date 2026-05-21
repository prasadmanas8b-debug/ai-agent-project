"""
graph/state.py  --  Shared whiteboard passed between all agents.
"""
from typing import TypedDict, List, Dict

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

    convo_result: str
    # Written by Convo Agent -- latest conversational reply.

    conversation_history: List[Dict[str, str]]
    # Maintained by Convo Agent -- list of {role: str, content: str} dicts.
    # role is "user" or "assistant".

    next: str
    # Written by Supervisor each loop.
    # Values: "research" | "writer" | "coder" | "github" | "pdf" | "convo" | "FINISH"
