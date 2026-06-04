"""
graph/state.py — Shared state passed between all agents in the LangGraph pipeline.

Every field is set once and never mutated by agents other than the one that owns it.
"""

from typing import TypedDict, List, Dict, Any


class AgentState(TypedDict):
    # ── Core ──────────────────────────────────────────────────────────────────
    task: str                          # Original user input — never changed.
    next: str                          # Routing decision written by Supervisor.

    # ── Agent results ─────────────────────────────────────────────────────────
    research_notes: str                # Raw web research text (Research Agent).
    final_report: str                  # Polished markdown report (Writer Agent).
    code_result: str                   # Code save confirmation (Coder Agent).
    github_result: str                 # GitHub operation result (GitHub Agent).
    pdf_result: str                    # JSON string with PDF data (PDF Agent).
    email_result: str                  # JSON string with email data (Email Agent).
    convo_result: str                  # Conversational reply (Convo Agent).
    db_result: str                     # JSON string with DB result (Database Agent).

    # ── Conversation history (Convo Agent only) ───────────────────────────────
    conversation_history: List[Dict[str, str]]  # [{role: "user"|"assistant", content: str}]

    # ── PDF Agent context ─────────────────────────────────────────────────────
    pdf_mode: str                      # Feature selector, default "auto".
    pdf_text: str                      # Pre-extracted text (skips file loading).
    pdf_bytes: bytes                   # Primary PDF file bytes.
    pdf2_bytes: bytes                  # Secondary PDF bytes (compare / merge).

    # ── Email Agent context ───────────────────────────────────────────────────
    email_mode: str                    # Feature selector, default "auto".
    email_context: Dict[str, Any]      # Extra context (e.g. original_email).

    # ── Database Agent context ────────────────────────────────────────────────
    db_mode: str                       # Feature selector, default "auto".
    db_context: Dict[str, Any]         # Extra context (table, query, data, …).
