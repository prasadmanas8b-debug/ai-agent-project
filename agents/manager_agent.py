"""
agents/manager_agent.py  --  Supervisor: decides which agent runs next.
"""
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
You are a supervisor managing FOUR specialized agents:
  - research : searches the web, fills research_notes
  - writer   : turns research_notes into a polished report in final_report
  - coder    : reads final_report/task and generates working Python code
  - github   : performs GitHub operations (files, branches, listings)

Your ONLY job: read the task + state, return ONE word for the next agent.

Decision rules -- apply TOP TO BOTTOM, stop at first match:
  1. github_result is not empty                                                      -> FINISH
  2. code_result is not empty AND task does NOT mention github/save/commit/push      -> FINISH
  3. code_result is not empty AND task mentions github/save/commit/push              -> github
  4. final_report is not empty AND task mentions code/implement/build/script/program -> coder
  5. final_report is not empty AND task mentions github/save/commit/push             -> github
  6. research_notes is empty AND task needs info (what/who/how/explain/research/why/latest/trends/history/compare) -> research
  7. research_notes is not empty AND final_report is empty                           -> writer
  8. task mentions code/implement/build/script/program AND research_notes is empty   -> research
  9. task mentions github/list/branch/create file AND github_result is empty         -> github
 10. everything done                                                                 -> FINISH

CRITICAL:
  - Reply with EXACTLY ONE word. No punctuation. No explanation.
  - Valid replies: research | writer | coder | github | FINISH
"""

def run_supervisor(state: AgentState) -> AgentState:
    human = (
        f"Task: {state['task']}

"
        f"State:
"
        f"  research_notes : {bool(state['research_notes'])}
"
        f"  final_report   : {bool(state['final_report'])}
"
        f"  code_result    : {bool(state.get('code_result', ''))}
"
        f"  github_result  : {bool(state['github_result'])}

"
        f"What runs next? (one word only)"
    )
    response = _llm.invoke([
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=human),
    ])
    decision = response.content.strip().lower()
    if decision == "finish":
        decision = "FINISH"
    if decision not in {"research", "writer", "coder", "github", "FINISH"}:
        print(f"[Supervisor] WARNING: unexpected decision '{decision}'. Defaulting to FINISH.")
        decision = "FINISH"
    print(f"[Supervisor] '{state['task'][:60]}' -> {decision}")
    return {**state, "next": decision}
