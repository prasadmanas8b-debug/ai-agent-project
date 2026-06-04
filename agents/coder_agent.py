"""
agents/coder_agent.py — Coder Agent.

Reads the final_report / research_notes + task and generates clean, working
Python code. Saves the file to git_agent_output/ on GitHub automatically.
"""

import os
import re
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from tools.github_tools import create_or_update_file
from graph.state import AgentState

load_dotenv()

_llm: ChatGroq | None = None  # lazy init


def _get_llm() -> ChatGroq:
    global _llm
    if _llm is None:
        _llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            api_key=os.getenv("GROQ_API_KEY"),
        )
    return _llm


_SYSTEM_PROMPT = """
You are an expert Python software engineer.

Your job: read a task description (and optional research report) then generate
clean, working, well-commented Python code that implements or demonstrates it.

STRICT OUTPUT RULES:
1. Output ONLY raw Python code — no markdown fences, no prose outside comments.
2. Start with a module-level docstring explaining what the code does.
3. Add inline comments on non-obvious lines.
4. Use only stdlib OR: requests, numpy, pandas, langchain, langgraph, groq.
5. Always include a runnable `if __name__ == "__main__":` block with a demo.
6. If the topic is purely conceptual, write a simulation that illustrates it.
7. Keep it 50-200 lines. No bloat.
8. Read API keys via os.getenv() — never hardcode secrets.

START your response directly with the triple-quoted docstring. No preamble.
"""


def _strip_fences(code: str) -> str:
    """Remove accidental markdown code fences."""
    code = re.sub(r"^```[a-z]*\n?", "", code.strip(), flags=re.MULTILINE)
    return re.sub(r"```$", "", code.strip()).strip()


def run_coder_agent(state: AgentState) -> AgentState:
    """
    Generate Python code for the task and push it to GitHub.

    Returns:
        Updated state with code_result set.
    """
    task         = state.get("task", "")
    final_report = state.get("final_report", "")
    research     = state.get("research_notes", "")

    ctx = f"Task: {task}\n\n"
    if final_report:
        ctx += f"Research Report:\n{final_report[:3000]}\n\n"
    elif research:
        ctx += f"Research Notes:\n{research[:3000]}\n\n"
    ctx += "Generate the Python code now."

    print(f"\n💻 Coder Agent — task: {task[:100]}")

    try:
        response = _get_llm().invoke([
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=ctx),
        ])
        code = _strip_fences(response.content)
    except Exception as exc:
        msg = f"[Coder Agent ERROR] LLM call failed: {exc}"
        print(msg)
        return {**state, "code_result": msg}

    # Build a filesystem-safe filename from the task
    safe_name = re.sub(r"[^\w]", "_", task.lower())[:50].strip("_")
    filename  = f"git_agent_output/code_{safe_name}.py"

    save_result = create_or_update_file(
        path=filename,
        content=code,
        commit_message=f"feat(coder): generate code for '{task[:60]}'",
    )
    print(f"💻 Coder Agent — {save_result}")
    return {**state, "code_result": f"{save_result} | {len(code.splitlines())} lines"}
