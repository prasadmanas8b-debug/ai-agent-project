"""
agents/manager_agent.py — Supervisor: reads the current state and decides
which agent to invoke next, or terminates the graph with FINISH.
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import AgentState

load_dotenv()

_llm = None  # lazy init — prevents crash at import when GROQ_API_KEY is absent


def _get_llm() -> ChatGroq:
    global _llm
    if _llm is None:
        _llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0,
            api_key=os.getenv("GROQ_API_KEY"),
        )
    return _llm


_SYSTEM_PROMPT = """
You are a supervisor managing EIGHT specialized agents:
  - research  : searches the web, fills research_notes
  - writer    : turns research_notes into a polished report in final_report
  - coder     : generates working Python code, saves to git_agent_output/
  - github    : performs GitHub operations (list files, create/update files, branches)
  - pdf       : reads, extracts, analyzes, converts, or generates PDF files
  - email     : composes, sends, reads, analyzes, and manages emails
  - convo     : handles greetings, small-talk, clarifications, and general chat
  - database  : queries, analyzes, and manages databases (SQLite/PostgreSQL/MySQL)

Your ONLY job: read the task + state, return ONE word for the next agent.

Decision rules — apply TOP TO BOTTOM, stop at first match:
  1.  github_result is not empty                                                      -> FINISH
  2.  pdf_result is not empty                                                         -> FINISH
  3.  email_result is not empty                                                       -> FINISH
  4.  db_result is not empty                                                          -> FINISH
  5.  code_result is not empty AND task does NOT mention github/save/commit/push      -> FINISH
  6.  code_result is not empty AND task mentions github/save/commit/push              -> github
  7.  final_report is not empty AND task mentions code/implement/build/script         -> coder
  8.  final_report is not empty AND task mentions github/save/commit/push             -> github
  9.  task mentions list files OR create branch OR delete file (pure GitHub ops)      -> github
 10.  task mentions pdf/PDF/extract pdf/summarize pdf/read pdf/convert pdf/ocr        -> pdf
 11.  task mentions email/inbox/compose/send email/reply/forward/mail/gmail/outlook   -> email
 12.  task mentions draft/subject line/phishing/unsubscribe/mail merge/drip campaign  -> email
 13.  task mentions database/sql/sqlite/postgresql/mysql/query/table/db/insert/select -> database
 14.  task mentions export csv/export excel/export json/data export/audit log         -> database
 15.  task needs info AND research_notes is empty                                     -> research
 16.  research_notes is not empty AND final_report is empty                           -> writer
 17.  task mentions code/implement/build/script AND research_notes is empty           -> research
 18.  task mentions github/save/commit/push AND github_result is empty                -> github
 19.  task is a greeting, small-talk, clarification, or simple question               -> convo
 20.  convo_result is not empty                                                       -> FINISH
 21.  everything done                                                                 -> FINISH

CRITICAL:
  - Reply with EXACTLY ONE word. No punctuation. No explanation.
  - Valid replies: research | writer | coder | github | pdf | email | convo | database | FINISH
"""

_VALID_DECISIONS = frozenset(
    {"research", "writer", "coder", "github", "pdf", "email", "convo", "database", "FINISH"}
)


def run_supervisor(state: AgentState) -> AgentState:
    """Invoke the LLM supervisor and update state["next"]."""
    human = (
        f"Task: {state['task']}\n\n"
        f"State:\n"
        f"  research_notes : {bool(state.get('research_notes'))}\n"
        f"  final_report   : {bool(state.get('final_report'))}\n"
        f"  code_result    : {bool(state.get('code_result'))}\n"
        f"  github_result  : {bool(state.get('github_result'))}\n"
        f"  pdf_result     : {bool(state.get('pdf_result'))}\n"
        f"  email_result   : {bool(state.get('email_result'))}\n"
        f"  db_result      : {bool(state.get('db_result'))}\n"
        f"  convo_result   : {bool(state.get('convo_result'))}\n\n"
        f"What runs next? (one word only)"
    )

    response = _get_llm().invoke([
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=human),
    ])
    decision = response.content.strip().lower()

    # Normalize "finish" -> "FINISH"
    if decision == "finish":
        decision = "FINISH"

    if decision not in _VALID_DECISIONS:
        print(f"[Supervisor] WARNING: unexpected '{decision}'. Defaulting to FINISH.")
        decision = "FINISH"

    print(f"[Supervisor] '{state['task'][:60]}' -> {decision}")
    return {**state, "next": decision}
