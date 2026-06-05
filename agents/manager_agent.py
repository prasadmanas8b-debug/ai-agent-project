"""
agents/manager_agent.py — Supervisor / Router

Routes tasks to: research, writer, or github.
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
You are a supervisor routing user tasks to one of 3 specialist agents.
Understand intent even with typos or vague phrasing.

AGENTS:
  research → web search, find info, explain topics, latest news, comparisons
  writer   → turn research notes into a polished report, blog, summary, document
  github   → list/read/create/update/delete files or branches on GitHub

ROUTING RULES (apply in order):

[ALREADY DONE]
1. github_result filled            → FINISH
2. final_report filled             → FINISH
3. research_notes filled AND final_report empty → writer

[DIRECT ROUTING]
4. Task about GitHub (list files, push, branch, read file, commit) → github
5. Task about writing/report/blog/summary (with research already done) → writer
6. Everything else → research

OUTPUT: Reply with exactly one word — the agent name or FINISH.
No explanation. No punctuation. Just: research / writer / github / FINISH
"""


def run_supervisor(state: AgentState) -> AgentState:
    fields = {
        "github_result":  state.get("github_result", ""),
        "final_report":   state.get("final_report", ""),
        "research_notes": state.get("research_notes", ""),
    }

    user_msg = f"""
TASK: {state['task']}

CURRENT STATE:
- research_notes: {"filled" if fields["research_notes"] else "empty"}
- final_report:   {"filled" if fields["final_report"] else "empty"}
- github_result:  {"filled" if fields["github_result"] else "empty"}

What is the next step?
""".strip()

    response = _get_llm().invoke([
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=user_msg),
    ])

    decision = response.content.strip().split()[0].lower()
    valid = {"research", "writer", "github", "finish"}
    if decision not in valid:
        decision = "research"

    next_node = "FINISH" if decision == "finish" else decision
    print(f"\n[Supervisor] → {next_node}")
    return {**state, "next": next_node}
