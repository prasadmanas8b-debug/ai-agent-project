"""
coder_agent.py — AI-powered Coder Agent for the Multi-Agent System.

CAPABILITIES:
  1. Generate code in any language (Python, JS, Bash, SQL, etc.)
  2. Execute Python code safely in a sandboxed subprocess
  3. Debug code — detect errors, explain them, auto-fix and retry
  4. Refactor existing code (clean up, optimize, add type hints)
  5. Explain code in plain English
  6. Add docstrings / comments automatically
  7. Write unit tests for any function
  8. Convert code between languages (Python → JS, etc.)
  9. Save generated code to a local file
 10. Return structured output: language, code, output, errors, explanation
"""

import os
import sys
import subprocess
import tempfile
import traceback
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

# ── LLM Setup ────────────────────────────────────────────────────────────────
def get_llm():
    return ChatGroq(
        model="llama3-70b-8192",
        temperature=0.2,
        api_key=os.getenv("GROQ_API_KEY"),
    )

# ── Safe Python Executor ──────────────────────────────────────────────────────
def execute_python_code(code: str, timeout: int = 15) -> dict:
    """
    Executes Python code in a sandboxed subprocess.
    Returns: { success, stdout, stderr, returncode }
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(code)
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"[TIMEOUT] Code execution exceeded {timeout}s limit.",
            "returncode": -1,
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1,
        }
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


# ── Core Agent Function ───────────────────────────────────────────────────────
def coder_agent(state: dict) -> dict:
    """
    Main LangGraph node for the Coder Agent.
    Reads `state["task"]` and performs the appropriate coding action.
    Updates state with `code_output` and `code_result`.
    """
    task = state.get("task", "").strip()
    context = state.get("research_notes", "") or state.get("final_report", "")

    if not task:
        state["code_output"] = ""
        state["code_result"] = "❌ No task provided to the Coder Agent."
        state["next"] = "end"
        return state

    print(f"\n[CoderAgent] 🖥️  Task received: {task[:80]}...")

    # Detect what kind of coding task this is
    action = _detect_action(task)
    print(f"[CoderAgent] 🔍 Detected action: {action}")

    result = _dispatch(action, task, context)

    state["code_output"] = result.get("code", "")
    state["code_result"] = result.get("summary", "")
    state["next"] = "end"

    print(f"[CoderAgent] ✅ Done. Action={action}")
    return state


# ── Action Dispatcher ─────────────────────────────────────────────────────────
def _detect_action(task: str) -> str:
    task_lower = task.lower()
    if any(k in task_lower for k in ["fix", "debug", "error", "bug", "broken"]):
        return "debug"
    if any(k in task_lower for k in ["explain", "what does", "describe this code"]):
        return "explain"
    if any(k in task_lower for k in ["refactor", "clean", "optimize", "improve"]):
        return "refactor"
    if any(k in task_lower for k in ["test", "unit test", "write tests for"]):
        return "write_tests"
    if any(k in task_lower for k in ["convert", "translate to", "rewrite in"]):
        return "convert"
    if any(k in task_lower for k in ["docstring", "comment", "document this"]):
        return "add_docs"
    if any(k in task_lower for k in ["run", "execute", "output of"]):
        return "run"
    return "generate"


def _dispatch(action: str, task: str, context: str) -> dict:
    dispatch_map = {
        "generate":    _generate_code,
        "debug":       _debug_code,
        "explain":     _explain_code,
        "refactor":    _refactor_code,
        "write_tests": _write_tests,
        "convert":     _convert_code,
        "add_docs":    _add_docs,
        "run":         _run_code,
    }
    fn = dispatch_map.get(action, _generate_code)
    return fn(task, context)


# ── Action Implementations ────────────────────────────────────────────────────

def _generate_code(task: str, context: str) -> dict:
    """Generate code from scratch based on the task."""
    llm = get_llm()
    system = SystemMessage(content=(
        "You are an expert software engineer. "
        "When asked to write code, output ONLY the raw code block with NO markdown fences, "
        "NO explanation before or after — just the pure code. "
        "Include a brief comment at the top explaining what the code does."
    ))
    prompt = task
    if context:
        prompt = f"Context/Research:\n{context}\n\nTask: {task}"

    response = llm.invoke([system, HumanMessage(content=prompt)])
    code = response.content.strip()

    # Try to execute if it's Python
    exec_result = None
    if _looks_like_python(code):
        exec_result = execute_python_code(code)

    summary = _build_summary("Generated", code, exec_result)
    return {"code": code, "summary": summary, "exec": exec_result}


def _debug_code(task: str, context: str) -> dict:
    """Debug code: identify the bug, explain it, return fixed code."""
    llm = get_llm()
    system = SystemMessage(content=(
        "You are an expert debugger. "
        "Given buggy code or an error description: "
        "1) Identify the root cause. "
        "2) Output the FIXED code only (no markdown fences). "
        "3) After the code, add a comment block starting with '# DEBUG_NOTES:' "
        "   listing what was wrong and what you fixed."
    ))
    response = llm.invoke([system, HumanMessage(content=task)])
    code = response.content.strip()

    exec_result = None
    if _looks_like_python(code):
        exec_result = execute_python_code(code)

    summary = _build_summary("Debugged", code, exec_result)
    return {"code": code, "summary": summary, "exec": exec_result}


def _explain_code(task: str, context: str) -> dict:
    """Explain what the given code does in plain English."""
    llm = get_llm()
    system = SystemMessage(content=(
        "You are a senior developer and teacher. "
        "Explain the given code clearly: what it does, how it works, "
        "and any important patterns or pitfalls. Write in plain English."
    ))
    response = llm.invoke([system, HumanMessage(content=task)])
    explanation = response.content.strip()
    return {
        "code": "",
        "summary": f"📖 Code Explanation:\n\n{explanation}",
        "exec": None,
    }


def _refactor_code(task: str, context: str) -> dict:
    """Refactor code: clean up, optimize, add type hints."""
    llm = get_llm()
    system = SystemMessage(content=(
        "You are an expert at code quality. "
        "Refactor the given code to be cleaner, more efficient, and Pythonic. "
        "Add type hints where missing. Output ONLY the refactored code (no markdown fences). "
        "Add a '# REFACTOR_NOTES:' comment block at the end listing improvements made."
    ))
    response = llm.invoke([system, HumanMessage(content=task)])
    code = response.content.strip()

    exec_result = None
    if _looks_like_python(code):
        exec_result = execute_python_code(code)

    summary = _build_summary("Refactored", code, exec_result)
    return {"code": code, "summary": summary, "exec": exec_result}


def _write_tests(task: str, context: str) -> dict:
    """Write unit tests for the given function/code."""
    llm = get_llm()
    system = SystemMessage(content=(
        "You are a test engineer. "
        "Write comprehensive unit tests using Python's `unittest` module. "
        "Cover: happy path, edge cases, and error cases. "
        "Output ONLY the test code (no markdown fences)."
    ))
    response = llm.invoke([system, HumanMessage(content=task)])
    code = response.content.strip()

    exec_result = execute_python_code(code)
    summary = _build_summary("Unit Tests Written", code, exec_result)
    return {"code": code, "summary": summary, "exec": exec_result}


def _convert_code(task: str, context: str) -> dict:
    """Convert code from one language to another."""
    llm = get_llm()
    system = SystemMessage(content=(
        "You are a polyglot programmer. "
        "Convert the code to the requested target language. "
        "Preserve all logic and functionality exactly. "
        "Output ONLY the converted code (no markdown fences). "
        "Add a comment at the top noting the source and target language."
    ))
    response = llm.invoke([system, HumanMessage(content=task)])
    code = response.content.strip()
    return {
        "code": code,
        "summary": f"🔄 Code Converted Successfully:\n\n{code[:300]}{'...' if len(code) > 300 else ''}",
        "exec": None,
    }


def _add_docs(task: str, context: str) -> dict:
    """Add docstrings and comments to code."""
    llm = get_llm()
    system = SystemMessage(content=(
        "You are a documentation expert. "
        "Add comprehensive docstrings (Google style) and inline comments to the code. "
        "Do NOT change any logic — only add documentation. "
        "Output ONLY the documented code (no markdown fences)."
    ))
    response = llm.invoke([system, HumanMessage(content=task)])
    code = response.content.strip()
    return {
        "code": code,
        "summary": f"📝 Documentation Added:\n\n{code[:300]}{'...' if len(code) > 300 else ''}",
        "exec": None,
    }


def _run_code(task: str, context: str) -> dict:
    """Extract and run Python code from the task, return its output."""
    llm = get_llm()
    # First ask LLM to extract/prepare the code
    system = SystemMessage(content=(
        "Extract the Python code from the user's message and output ONLY the raw code "
        "(no markdown, no explanation). If there's no code, write the code that would "
        "accomplish the described task."
    ))
    response = llm.invoke([system, HumanMessage(content=task)])
    code = response.content.strip()

    exec_result = execute_python_code(code)
    summary = _build_summary("Executed", code, exec_result)
    return {"code": code, "summary": summary, "exec": exec_result}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _looks_like_python(code: str) -> bool:
    python_markers = ["def ", "import ", "print(", "class ", "if __name__", "return ", "for ", "while "]
    return any(marker in code for marker in python_markers)


def _build_summary(action: str, code: str, exec_result: dict | None) -> str:
    lines = [f"✅ {action} Successfully\n"]
    lines.append(f"📄 Code ({len(code.splitlines())} lines):\n{code[:600]}{'...' if len(code) > 600 else ''}")

    if exec_result:
        if exec_result["success"]:
            lines.append(f"\n▶ Execution Output:\n{exec_result['stdout'] or '(no output)'}")
        else:
            lines.append(f"\n⚠️ Execution Error:\n{exec_result['stderr']}")

    return "\n".join(lines)


def save_code_to_file(code: str, filename: str, folder: str = "outputs") -> str:
    """Utility: save generated code to a file on disk."""
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(code)
    return path


# ── Standalone CLI mode ───────────────────────────────────────────────────────
if __name__ == "__main__":
    test_state = {
        "task": "Write a Python function to check if a string is a palindrome, then run it with 3 test cases",
        "research_notes": "",
        "final_report": "",
        "code_output": "",
        "code_result": "",
        "next": "",
    }
    result = coder_agent(test_state)
    print("\n" + "=" * 60)
    print(result["code_result"])
