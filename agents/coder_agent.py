"""
agents/coder_agent.py — Coder Agent

A pro-level AI software engineer. Given any coding task (even with typos or
vague descriptions), it:
  1. Understands and corrects the intent
  2. Generates clean, production-quality Python code
  3. Saves the file locally to outputs/ AND pushes to GitHub

Key capabilities:
  - Algorithms & data structures
  - Automation scripts
  - API clients
  - Data processing (pandas/numpy)
  - Web scrapers
  - AI/ML tools
  - File processors
  - CLI utilities

Always saves output to:
  - Local:  outputs/code_<task_slug>.py
  - GitHub: git_agent_output/code_<task_slug>.py
"""

import os
import re
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from tools.github_tools import create_or_update_file
from graph.state import AgentState

load_dotenv()

_llm: ChatGroq | None = None


def _get_llm() -> ChatGroq:
    global _llm
    if _llm is None:
        _llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.2,
            max_tokens=4096,
            api_key=os.getenv("GROQ_API_KEY"),
        )
    return _llm


_SYSTEM_PROMPT = """
You are a brilliant AI software engineer. Your job is to write production-quality
Python code for any task — even if the task description has typos, is vague, or
uses informal language.

STEP 1 — Understand the intent:
  - Silently correct spelling mistakes (e.g. "bianry serach" → binary search)
  - Infer what the user actually wants from partial descriptions
  - If the task is vague, pick the most useful and complete interpretation

STEP 2 — Write the code:
  - Start with a module docstring explaining what the code does
  - Write clean, modular, well-commented Python
  - Handle edge cases and include error handling (try/except where appropriate)
  - Use type hints on all function signatures
  - Use only: stdlib, requests, numpy, pandas, langchain, langgraph, groq, openai
  - Never hardcode secrets — always use os.getenv()
  - Aim for 80-250 lines. Enough to be genuinely useful, not padded.

STEP 3 — Include a demo:
  - Always end with `if __name__ == "__main__":` that demonstrates the code working
  - The demo should be realistic, not just `print("hello")`

OUTPUT RULES:
  - Output ONLY raw Python code
  - No markdown fences (no ```)
  - No explanations before or after the code
  - Start directly with the triple-quoted module docstring

EXAMPLES of tasks you handle:
  "wrtie a binary search"           → clean binary_search.py
  "make a web scrapper for news"    → requests-based news scraper
  "sort algorithim in python"       → multiple sort algorithms with benchmarks
  "creat a file that reads csvs"    → pandas CSV reader with analysis
  "write a tool that calls openai"  → OpenAI API client wrapper
  "automation for renaming files"   → os/pathlib-based file renamer
"""


def _strip_fences(code: str) -> str:
    """Strip any accidental markdown code fences from LLM output."""
    code = re.sub(r"^```[a-zA-Z]*\n?", "", code.strip(), flags=re.MULTILINE)
    code = re.sub(r"\n?```$", "", code.strip())
    return code.strip()


def _make_slug(task: str) -> str:
    """Turn a task string into a safe filename slug (max 50 chars)."""
    slug = re.sub(r"[^\w\s]", "", task.lower())
    slug = re.sub(r"\s+", "_", slug.strip())[:50].strip("_")
    return slug or "task"


def _save_locally(filename: str, code: str) -> str:
    """Save code to local outputs/ folder. Returns the saved path."""
    os.makedirs("outputs", exist_ok=True)
    path = os.path.join("outputs", filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(code)
    return path


def run_coder_agent(state: AgentState) -> AgentState:
    """
    Generate Python code for the task, save locally and push to GitHub.

    Handles typos and vague task descriptions gracefully.
    Returns updated state with code_result set.
    """
    task         = state.get("task", "")
    final_report = state.get("final_report", "")
    research     = state.get("research_notes", "")

    # Build rich context for the LLM
    ctx_parts = [f"TASK: {task}"]
    if final_report:
        ctx_parts.append(f"\nRESEARCH REPORT (use as context):\n{final_report[:3000]}")
    elif research:
        ctx_parts.append(f"\nRESEARCH NOTES (use as context):\n{research[:3000]}")
    ctx_parts.append("\nWrite the Python code now. Output ONLY raw Python, no markdown.")
    context = "\n".join(ctx_parts)

    print(f"\n💻 Coder Agent — task: {task[:100]}")

    try:
        response = _get_llm().invoke([
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=context),
        ])
        code = _strip_fences(response.content)
    except Exception as exc:
        msg = f"[Coder Agent ERROR] LLM failed: {exc}"
        print(msg)
        return {**state, "code_result": msg}

    if not code.strip():
        msg = "[Coder Agent ERROR] LLM returned empty code."
        print(msg)
        return {**state, "code_result": msg}

    # Build filename from task slug
    slug     = _make_slug(task)
    filename = f"code_{slug}.py"

    # 1. Save locally to outputs/
    local_path = _save_locally(filename, code)
    print(f"💻 Coder Agent — saved locally: {local_path}")

    # 2. Push to GitHub (git_agent_output/)
    github_path = f"git_agent_output/{filename}"
    github_result = create_or_update_file(
        path=github_path,
        content=code,
        commit_message=f"feat(coder): {task[:72]}",
    )
    print(f"💻 Coder Agent — GitHub: {github_result}")

    lines      = len(code.splitlines())
    summary    = (
        f"✅ Code generated ({lines} lines)\n"
        f"📁 Local:  {local_path}\n"
        f"🐙 GitHub: {github_result}"
    )
    return {**state, "code_result": summary}
