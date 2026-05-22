"""
agents/coder_agent.py
Coder Agent — reads the final_report + task and generates working Python code.
Saves the .py file into git_agent_output/ on GitHub automatically.
"""
import os
import re
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from tools.github_tools import create_or_update_file

load_dotenv()

_llm = None  # Lazy init — avoids crash at import if GROQ_API_KEY not set yet

def _get_llm():
    global _llm
    if _llm is None:
        _llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            api_key=os.getenv("GROQ_API_KEY"),
        )
    return _llm

_SYSTEM_PROMPT = """
You are an expert Python software engineer acting as a Coder Agent.

Your job: read a task description (and optional research report) then generate
clean, working, well-commented Python code that implements or demonstrates it.

STRICT OUTPUT RULES:
1. Output ONLY raw Python code — no markdown fences, no prose outside comments.
2. Start with a module docstring explaining what the code does.
3. Add inline comments on non-obvious lines.
4. Use only stdlib OR: requests, numpy, pandas, langchain, langgraph, groq.
5. Always include a runnable  if __name__ == "__main__":  block with a demo.
6. If the topic is purely conceptual, write a simulation that illustrates it.
7. Keep it 50-200 lines. No bloat.
8. Read API keys via os.getenv() -- never hardcode secrets.

START your response directly with the triple-quoted docstring. No preamble.
"""

def run_coder_agent(state: dict) -> dict:
    task         = state.get("task", "")
    final_report = state.get("final_report", "")
    research     = state.get("research_notes", "")

    ctx = f"Task: {task}\n\n"
    if final_report:
        ctx += f"Research Report (use as context):\n{final_report[:3000]}\n\n"
    elif research:
        ctx += f"Research Notes (use as context):\n{research[:3000]}\n\n"
    ctx += "Generate the Python code now."

    print(f"\n💻 Coder Agent -- task: {task[:100]}")

    try:
        response = _get_llm().invoke([
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=ctx),
        ])
        code = response.content.strip()
        # Strip accidental markdown fences
        if code.startswith("```"):
            code = re.sub(r"^```[a-z]*\n?", "", code, flags=re.MULTILINE)
            code = re.sub(r"```$", "", code.strip()).strip()

    except Exception as e:
        msg = f"ERROR Coder Agent: LLM call failed: {e}"
        print(msg)
        return {**state, "code_result": msg}

    safe = re.sub(r"[^\w]", "_", task.lower())[:50].strip("_")
    filename = f"outputs/code_{safe}.py"
    print(f"💻 Coder Agent -- saving to: {filename}")

    save_result = create_or_update_file(
        path=filename,
        content=code,
        commit_message=f"feat(coder): generate code for '{task[:60]}'",
    )
    print(f"💻 Coder Agent -- {save_result}")
    return {**state, "code_result": f"{save_result} | {len(code.splitlines())} lines generated."}


if __name__ == "__main__":
    test_state = {
        "task":           "implement a binary search algorithm",
        "final_report":   "",
        "research_notes": "",
        "code_result":    "",
        "github_result":  "",
        "next":           "",
    }
    out = run_coder_agent(test_state)
    print(out["code_result"])
