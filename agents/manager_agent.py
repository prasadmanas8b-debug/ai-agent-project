"""
agents/manager_agent.py  --  Supervisor: decides which agent runs next.
FIX: LLM is now lazily initialized to prevent crash on import if API key is missing.
"""
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import AgentState

load_dotenv()

_llm = None  # FIX: lazy init -- was crashing on import when GROQ_API_KEY was absent

def _get_llm():
    global _llm
    if _llm is None:
        _llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0,
            api_key=os.getenv("GROQ_API_KEY"),
        )
    return _llm

_SYSTEM_PROMPT = """
You are a supervisor managing SIX specialized agents:
  - research : searches the web, fills research_notes
  - writer   : turns research_notes into a polished report in final_report
  - coder    : reads final_report/task and generates working Python code, saves to git_agent_output/
  - github   : performs GitHub operations (list files, create/update files, branches)
  - pdf      : reads, extracts text from, or summarizes a PDF file (local or URL)
  - convo    : handles greetings, small-talk, clarifications, and general chat

Your ONLY job: read the task + state, return ONE word for the next agent.

Decision rules -- apply TOP TO BOTTOM, stop at first match:
  1.  github_result is not empty                                                           -> FINISH
  2.  pdf_result is not empty                                                              -> FINISH
  3.  code_result is not empty AND task does NOT mention github/save/commit/push           -> FINISH
  4.  code_result is not empty AND task mentions github/save/commit/push                   -> github
  5.  final_report is not empty AND task mentions code/implement/build/script/program      -> coder
  6.  final_report is not empty AND task mentions github/save/commit/push                  -> github
  7.  task mentions list/listing files OR create branch OR delete file (pure GitHub ops)   -> github
  8.  task mentions pdf/PDF/extract pdf/summarize pdf/read pdf                             -> pdf
  9.  task needs info (what/who/how/explain/research/why/latest/trends/history/compare)
      AND research_notes is empty                                                           -> research
 10.  research_notes is not empty AND final_report is empty                                -> writer
 11.  task mentions code/implement/build/script/program AND research_notes is empty        -> research
 12.  task mentions github/save/commit/push AND github_result is empty                     -> github
 13.  task is a greeting, small-talk, clarification, or simple question (hi/hello/thanks/
      what is X/tell me/explain briefly/help/can you) AND no specialist work is needed     -> convo
 14.  convo_result is not empty                                                            -> FINISH
 15.  everything done                                                                      -> FINISH

CRITICAL:
  - Reply with EXACTLY ONE word. No punctuation. No explanation.
  - Valid replies: research | writer | coder | github | pdf | convo | FINISH
"""

def run_supervisor(state: AgentState) -> AgentState:
    human = (
        f"Task: {state['task']}\n\n"
        f"State:\n"
        f"  research_notes       : {bool(state['research_notes'])}\n"
        f"  final_report         : {bool(state['final_report'])}\n"
        f"  code_result          : {bool(state.get('code_result', ''))}\n"
        f"  github_result        : {bool(state['github_result'])}\n"
        f"  pdf_result           : {bool(state.get('pdf_result', ''))}\n"
        f"  convo_result         : {bool(state.get('convo_result', ''))}\n\n"
        f"What runs next? (one word only)"
    )
    response = _get_llm().invoke([
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=human),
    ])
    decision = response.content.strip().lower()
    if decision == "finish":
        decision = "FINISH"
    if decision not in {"research", "writer", "coder", "github", "pdf", "convo", "FINISH"}:
        print(f"[Supervisor] WARNING: unexpected '{decision}'. Defaulting to FINISH.")
        decision = "FINISH"
    print(f"[Supervisor] '{state['task'][:60]}' -> {decision}")
    return {**state, "next": decision}
