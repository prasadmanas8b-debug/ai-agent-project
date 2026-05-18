import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import AgentState

load_dotenv()

_llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY"),
)

_SYSTEM_PROMPT = """
You are a supervisor managing three specialized agents:
  - research : searches the web and writes research notes into research_notes
  - writer   : takes research_notes and writes a polished report into final_report
  - github   : performs GitHub actions (create/update files, list files, commit, push)

Your ONLY job: read the task + current state, then decide which agent runs next.

Decision rules (apply top to bottom):
  1. github_result is not empty                                              → FINISH
  2. final_report exists AND task mentions github/save/commit/push          → github
  3. task needs research AND research_notes is empty                        → research
  4. research_notes exists AND final_report is empty                        → writer
  5. task mentions github/list/files AND github_result is empty             → github
  6. all required work is done                                              → FINISH

CRITICAL:
  - Reply with EXACTLY ONE word. No punctuation, no explanation.
  - Valid replies: research | writer | github | FINISH
"""

def run_supervisor(state: AgentState) -> AgentState:
    human = (
        f"Task: {state['task']}\n\n"
        f"State:\n"
        f"  research_notes exists: {bool(state['research_notes'])}\n"
        f"  final_report   exists: {bool(state['final_report'])}\n"
        f"  github_result  exists: {bool(state['github_result'])}\n\n"
        f"What runs next? (one word only)"
    )
    response = _llm.invoke([
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=human),
    ])
    decision = response.content.strip().lower()
    if decision == "finish":
        decision = "FINISH"
    if decision not in {"research", "writer", "github", "FINISH"}:
        print(f"[Supervisor] ⚠️  Unexpected decision '{decision}'. Defaulting to FINISH.")
        decision = "FINISH"
    print(f"[Supervisor] '{state['task'][:60]}' → {decision}")
    return {**state, "next": decision}
