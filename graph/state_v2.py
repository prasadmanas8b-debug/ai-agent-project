"""
graph/state_v2.py — Enhanced AgentState for production-grade orchestration.

Extends the original AgentState with:
  - run_id:          Unique trace identifier per pipeline run
  - iteration_count: Guards against infinite supervisor loops
  - agent_history:   Ordered list of agents that have run
  - error_log:       Accumulated non-fatal errors during the run
  - start_time:      Float timestamp for total run duration tracking
  - context_summary: Compressed research context for token optimization
  - task_plan:       Optional multi-step plan for complex tasks

BACKWARD COMPATIBLE: All original fields preserved with identical types.
New fields have safe defaults so existing code continues to work.

Usage:
    from graph.state_v2 import AgentState, make_initial_state
"""

from typing import TypedDict, List, Dict, Any, Optional


class AgentState(TypedDict, total=False):
    # ══════════════════════════════════════════════════════════════════════════
    # ORIGINAL FIELDS — unchanged for backward compatibility
    # ══════════════════════════════════════════════════════════════════════════

    # Core
    task: str                          # Original user input — never changed.
    next: str                          # Routing decision written by Supervisor.

    # Agent results
    research_notes: str                # Raw web research text (Research Agent).
    final_report: str                  # Polished markdown report (Writer Agent).
    code_result: str                   # Code save confirmation (Coder Agent).
    github_result: str                 # GitHub operation result (GitHub Agent).
    pdf_result: str                    # JSON string with PDF data (PDF Agent).
    email_result: str                  # JSON string with email data (Email Agent).
    convo_result: str                  # Conversational reply (Convo Agent).
    db_result: str                     # JSON string with DB result (Database Agent).

    # Conversation history
    conversation_history: List[Dict[str, str]]

    # PDF Agent context
    pdf_mode: str
    pdf_text: str
    pdf_bytes: bytes
    pdf2_bytes: bytes

    # Email Agent context
    email_mode: str
    email_context: Dict[str, Any]

    # Database Agent context
    db_mode: str
    db_context: Dict[str, Any]

    # ══════════════════════════════════════════════════════════════════════════
    # NEW FIELDS — all optional with safe defaults
    # ══════════════════════════════════════════════════════════════════════════

    # Observability
    run_id: str                        # Unique ID for this pipeline run (for tracing).
    start_time: float                  # time.monotonic() at run start.

    # Orchestration guards
    iteration_count: int               # Number of supervisor→agent loops. Guards against infinite loops.
    agent_history: List[str]           # Ordered list of agent names that have executed.
    last_agent: str                    # Name of the agent that ran most recently.

    # Error tracking
    error_log: List[str]               # Non-fatal errors accumulated during the run.
    has_error: bool                    # True if any agent produced an error result.

    # Context optimization
    context_summary: str               # Compressed summary of research_notes for token efficiency.
    task_plan: List[str]               # Optional multi-step plan (["research", "writer", "github"]).

    # User context
    user_preferences: Dict[str, Any]   # Persisted preferences (code style, output format, etc.).


def make_initial_state(
    task: str,
    email_body: str = "",
    pdf_bytes: bytes = b"",
    pdf2_bytes: bytes = b"",
    run_id: str | None = None,
    user_preferences: dict | None = None,
) -> AgentState:
    """
    Create a fully initialized AgentState with all fields set to safe defaults.

    This is the canonical way to create an initial state — avoids KeyError
    when new fields are added and the calling code isn't updated.

    Args:
        task:             The user's task string.
        email_body:       Optional email body for email analysis tasks.
        pdf_bytes:        Optional primary PDF bytes.
        pdf2_bytes:       Optional secondary PDF bytes (for compare/merge).
        run_id:           Optional run ID (auto-generated if not provided).
        user_preferences: Optional user preferences dict.

    Returns:
        Fully initialized AgentState.
    """
    import time
    import uuid

    if run_id is None:
        run_id = uuid.uuid4().hex[:12]

    return AgentState(
        # Core
        task=task,
        next="",

        # Agent results — all empty
        research_notes="",
        final_report="",
        code_result="",
        github_result="",
        pdf_result="",
        email_result="",
        convo_result="",
        db_result="",

        # Conversation
        conversation_history=[],

        # PDF context
        pdf_mode="auto",
        pdf_text="",
        pdf_bytes=pdf_bytes,
        pdf2_bytes=pdf2_bytes,

        # Email context
        email_mode="auto",
        email_context={"original_email": email_body} if email_body else {},

        # Database context
        db_mode="auto",
        db_context={},

        # Observability (new)
        run_id=run_id,
        start_time=time.monotonic(),

        # Orchestration (new)
        iteration_count=0,
        agent_history=[],
        last_agent="",

        # Error tracking (new)
        error_log=[],
        has_error=False,

        # Context optimization (new)
        context_summary="",
        task_plan=[],

        # User context (new)
        user_preferences=user_preferences or {},
    )


def record_agent_run(state: AgentState, agent_name: str, had_error: bool = False) -> AgentState:
    """
    Update state to record that an agent has run.

    Call this at the start of each agent node wrapper in pipeline_graph.py.

    Returns updated state (does not mutate in place).
    """
    new_history = list(state.get("agent_history", [])) + [agent_name]
    new_error_log = list(state.get("error_log", []))

    return {
        **state,
        "iteration_count": state.get("iteration_count", 0) + 1,
        "agent_history":   new_history,
        "last_agent":      agent_name,
        "has_error":       state.get("has_error", False) or had_error,
        "error_log":       new_error_log,
    }


def add_error(state: AgentState, error: str) -> AgentState:
    """
    Add an error message to the error log.

    Does NOT stop the pipeline — just records the error for observability.
    """
    error_log = list(state.get("error_log", []))
    error_log.append(error)
    return {
        **state,
        "error_log": error_log,
        "has_error": True,
    }


def get_state_summary(state: AgentState) -> dict:
    """
    Return a compact summary of the current state for logging/debugging.
    Does NOT include large binary fields (pdf_bytes, etc.).
    """
    return {
        "run_id":          state.get("run_id", "unknown"),
        "task":            state.get("task", "")[:100],
        "next":            state.get("next", ""),
        "iteration":       state.get("iteration_count", 0),
        "agents_run":      state.get("agent_history", []),
        "has_error":       state.get("has_error", False),
        "error_count":     len(state.get("error_log", [])),
        "research_done":   bool(state.get("research_notes")),
        "report_done":     bool(state.get("final_report")),
        "code_done":       bool(state.get("code_result")),
        "github_done":     bool(state.get("github_result")),
        "pdf_done":        bool(state.get("pdf_result")),
        "email_done":      bool(state.get("email_result")),
        "convo_done":      bool(state.get("convo_result")),
        "db_done":         bool(state.get("db_result")),
    }
