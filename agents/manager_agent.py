"""
agents/manager_agent.py — Supervisor / Router

The brain of the pipeline. Uses an LLM to understand the user's intent
(even with typos or vague phrasing) and route to the correct agent.

Key upgrades:
  - Intent understanding over keyword matching — handles typos & paraphrasing
  - Passes full task semantics to LLM, not just boolean flags
  - Catches all edge-case routing (e.g. "code this" → coder, "make a py file" → coder)
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import AgentState

load_dotenv()

_llm: ChatGroq | None = None


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
You are a smart supervisor routing user tasks to the correct specialist agent.
You must understand intent even when the task has typos, grammar mistakes, or
vague phrasing. Think like a senior engineer who can read between the lines.

AGENTS AVAILABLE:
  research  → web search, find info, explain topics, latest news, comparisons
  writer    → turn research into a polished report or document
  coder     → write Python code, scripts, algorithms, tools, automation, debugging
  github    → list/read/create/update/delete files or branches on GitHub
  pdf       → read, summarize, extract, convert, create, OCR, merge, split PDFs
  email     → compose, send, read, analyze, reply, templates, campaigns
  convo     → greetings, general chat, system questions, clarifications, "what can you do"
  database  → SQL queries, table management, data analysis, exports, NL-to-SQL

ROUTING RULES (apply in order, stop at first match):

[ALREADY DONE — wrap up]
  1. github_result filled   → FINISH
  2. pdf_result filled      → FINISH
  3. email_result filled    → FINISH
  4. db_result filled       → FINISH
  5. code_result filled AND task has NO github/save/push intent  → FINISH
  6. code_result filled AND task HAS github/save/push intent     → github
  7. convo_result filled    → FINISH

[CHAIN — continue to next step]
  8. final_report filled AND task implies code/script/program    → coder
  9. final_report filled AND task implies github save/push       → github
 10. research_notes filled AND final_report empty               → writer

[DIRECT ROUTING — from task intent]
 11. Task is about writing/running/debugging/generating CODE or a SCRIPT or PROGRAM
     Examples: "write a binary search", "make a python file", "code a web scraper",
               "implement merge sort", "create a tool that does X", "write me a script"
     → coder  (do NOT go to research first unless task explicitly says "research then code")

 12. Task is about PDF files                                     → pdf
 13. Task is about email / inbox / compose / mail               → email
 14. Task is about database / SQL / tables / data queries       → database
 15. Task is about GitHub file ops (list/read/create/branch)    → github

 16. Task needs factual info AND research_notes empty           → research
 17. Task is a greeting / chat / clarification / system question → convo
 18. Fallback                                                    → convo

TYPO TOLERANCE EXAMPLES:
  "wrtie a sort algortihm"    → coder
  "reserch quantum computng"  → research
  "summerize this pdf"        → pdf
  "send an emal to john"      → email
  "lst files in repo"         → github
  "qurey the users tabel"     → database

CRITICAL:
  - Reply with EXACTLY ONE WORD. No punctuation. No explanation.
  - Valid words: research | writer | coder | github | pdf | email | convo | database | FINISH
"""

_VALID = frozenset(
    {"research", "writer", "coder", "github", "pdf", "email", "convo", "database", "FINISH"}
)

# Fallback fuzzy map for partial/mangled LLM responses
_FUZZY_MAP = {
    "cod":   "coder",   "code":  "coder",   "coding": "coder",   "script": "coder",
    "res":   "research","resea": "research","search": "research",
    "writ":  "writer",  "write": "writer",  "report": "writer",
    "git":   "github",  "hub":   "github",
    "pdf":   "pdf",     "doc":   "pdf",
    "mail":  "email",   "emai":  "email",   "inbox":  "email",
    "db":    "database","sql":   "database","data":   "database",
    "conv":  "convo",   "chat":  "convo",   "hello":  "convo",
    "fini":  "FINISH",  "done":  "FINISH",  "end":    "FINISH",
    "finish":"FINISH",  "stop":  "FINISH",
}


def _resolve(raw: str) -> str:
    """Resolve an LLM response to a valid agent name, with fuzzy fallback."""
    cleaned = raw.strip().lower().split()[0] if raw.strip() else ""
    if cleaned == "finish":
        return "FINISH"
    if cleaned in _VALID:
        return cleaned
    # Try prefix match
    for prefix, agent in _FUZZY_MAP.items():
        if cleaned.startswith(prefix):
            return agent
    return "FINISH"


def run_supervisor(state: AgentState) -> AgentState:
    """
    Read current state and decide which agent runs next.

    Sends the actual task text (not just booleans) to the LLM so it can
    understand intent even for typo-heavy or vague requests.
    """
    task = state.get("task", "")

    human = (
        f"TASK: {task}\n\n"
        f"COMPLETED SO FAR:\n"
        f"  research_notes : {'filled' if state.get('research_notes') else 'empty'}\n"
        f"  final_report   : {'filled' if state.get('final_report')   else 'empty'}\n"
        f"  code_result    : {'filled' if state.get('code_result')    else 'empty'}\n"
        f"  github_result  : {'filled' if state.get('github_result')  else 'empty'}\n"
        f"  pdf_result     : {'filled' if state.get('pdf_result')     else 'empty'}\n"
        f"  email_result   : {'filled' if state.get('email_result')   else 'empty'}\n"
        f"  db_result      : {'filled' if state.get('db_result')      else 'empty'}\n"
        f"  convo_result   : {'filled' if state.get('convo_result')   else 'empty'}\n\n"
        f"Which agent runs next? (one word)"
    )

    try:
        response = _get_llm().invoke([
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=human),
        ])
        decision = _resolve(response.content)
    except Exception as exc:
        print(f"[Supervisor] LLM error: {exc} — defaulting to convo")
        decision = "convo"

    print(f"[Supervisor] '{task[:70]}' → {decision}")
    return {**state, "next": decision}
