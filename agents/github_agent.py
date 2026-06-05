"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              GITHUB AGENT — Phase 3                                         ║
║              agents/github_agent.py                                         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  WHAT THIS FILE IS:                                                          ║
║  The "waiter" in the restaurant analogy.                                     ║
║                                                                              ║
║  github_tools.py  =  the kitchen  (raw GitHub API functions)                ║
║  github_agent.py  =  the waiter   (reads natural language, decides what     ║
║                                    to order from the kitchen, brings back    ║
║                                    the result)                               ║
║                                                                              ║
║  The magic glue is the LLM: it translates "save the report to docs/"        ║
║  into a structured action like {"action": "create_or_update_file",          ║
║  "path": "docs/report.md", "content": "..."}.                               ║
║                                                                              ║
║  WHAT IT CAN DO:                                                             ║
║  - Create a new file in the repo                                             ║
║  - Update an existing file                                                   ║
║  - List files in any folder                                                  ║
║  - Create a new branch                                                       ║
║  - Smart-save (create or update automatically)                               ║
║                                                                              ║
║  WHAT IT CANNOT DO (by design):                                              ║
║  - Browse the web    ← never give it web search tools                       ║
║  - Write reports     ← that's the Writer Agent's job                        ║
║  - Make decisions about research ← that's the Supervisor's job              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
from langchain.schema import SystemMessage, HumanMessage

from tools.github_tools import (
    create_file,
    update_file,
    list_files,
    create_branch,
    get_file,
    create_or_update_file,
)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: SETUP
# ─────────────────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    print("❌  GROQ_API_KEY missing from .env")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2: SYSTEM PROMPT
# This prompt teaches the LLM to translate natural language into
# a structured JSON action object.
# ─────────────────────────────────────────────────────────────────────────────
GITHUB_AGENT_SYSTEM_PROMPT = """
You are a GitHub Agent. Your ONLY job is to interact with a GitHub repository.

You receive a task in natural language and must translate it into a JSON action object.

Available actions and when to use them:
  - "create_file"          → user wants to create a NEW file that doesn't exist yet
  - "update_file"          → user wants to change an EXISTING file
  - "create_or_update_file"→ user wants to save a file but you're not sure if it exists (PREFERRED for saving reports)
  - "list_files"           → user wants to see files in a folder
  - "create_branch"        → user wants to create a new branch
  - "get_file"             → user wants to read a file's content

You must respond with ONLY a valid JSON object — no explanation, no extra text.

JSON format for file actions:
{
  "action": "create_or_update_file",
  "path": "docs/report.md",
  "content": "# Report\n\nContent here...",
  "commit_message": "docs: add AI research report"
}

JSON format for list_files:
{
  "action": "list_files",
  "folder_path": "agents"
}

JSON format for create_branch:
{
  "action": "create_branch",
  "branch_name": "feature/new-feature"
}

JSON format for get_file:
{
  "action": "get_file",
  "path": "README.md"
}

Rules:
- Always use "create_or_update_file" when saving reports — it handles both create and update automatically
- For folder listing, use "" (empty string) to list root
- Commit messages should be descriptive: "docs: add quantum computing report"
- File paths should NOT start with "/" — use "docs/report.md" not "/docs/report.md"
- Respond with ONLY the JSON object. No markdown, no explanation.
"""

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3: ACTION DISPATCHER
# Maps the action string from JSON to the actual tool function.
# ─────────────────────────────────────────────────────────────────────────────
def _dispatch_action(action_json: dict) -> str:
    """
    Reads the parsed JSON action and calls the correct github_tools function.

    Args:
        action_json (dict): Parsed JSON from the LLM. Must have "action" key.

    Returns:
        str: Result string from the tool function.
    """
    action = action_json.get("action", "").lower()

    if action == "create_file":
        return create_file(
            path           = action_json.get("path", ""),
            content        = action_json.get("content", ""),
            commit_message = action_json.get("commit_message", "chore: create file via AI agent"),
        )
    elif action == "update_file":
        return update_file(
            path           = action_json.get("path", ""),
            content        = action_json.get("content", ""),
            commit_message = action_json.get("commit_message", "chore: update file via AI agent"),
        )
    elif action == "create_or_update_file":
        return create_or_update_file(
            path           = action_json.get("path", ""),
            content        = action_json.get("content", ""),
            commit_message = action_json.get("commit_message", "chore: save via AI agent"),
        )
    elif action == "list_files":
        return list_files(
            folder_path = action_json.get("folder_path", ""),
        )
    elif action == "create_branch":
        return create_branch(
            branch_name = action_json.get("branch_name", ""),
            from_branch = action_json.get("from_branch", "main"),
        )
    elif action == "get_file":
        return get_file(
            path = action_json.get("path", ""),
        )
    else:
        return f"⚠️ Unknown action '{action}'. Supported: create_file, update_file, create_or_update_file, list_files, create_branch, get_file."


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4: MAIN FUNCTION — run_github_agent()
# ─────────────────────────────────────────────────────────────────────────────
def run_github_agent(task: str, report_content: str = "") -> str:
    """
    Receives a natural language task and performs the appropriate GitHub action.

    Flow:
      1. LLM reads task → outputs JSON action
      2. _dispatch_action() calls the right github_tools function
      3. Returns the result string

    Args:
        task           (str): Natural language instruction.
                              Example: "Save the report to docs/ai_report.md"
        report_content (str): Optional. If saving a report, pass its content here.
                              The LLM will include it in the JSON action.
                              If empty, agent uses content from the task string.

    Returns:
        str: A description of what was done, or an error message.
    """
    print(f"\n[GitHub Agent] Task received: '{task}'")

    # ── GUARD: check GitHub config is present ────────────────────────────
    if not os.getenv("GITHUB_TOKEN"):
        return "❌ GitHub Agent cannot run: GITHUB_TOKEN not set in .env"
    if not os.getenv("GITHUB_REPO"):
        return "❌ GitHub Agent cannot run: GITHUB_REPO not set in .env (format: username/repo)"

    # ── Inject report content into the task if provided ──────────────────
    # This is how the Writer Agent's output gets saved to GitHub:
    # The pipeline passes final_report as report_content here.
    full_task = task
    if report_content and report_content.strip():
        full_task = f"{task}\n\nContent to save:\n{report_content[:8000]}"
        # [:8000] = safety cap — LLMs have context window limits

    # ── LLM Setup ─────────────────────────────────────────────────────────
    llm = ChatGroq(
        api_key    = GROQ_API_KEY,
        model      = "llama-3.3-70b-versatile",
        temperature= 0.0,    # 0 = fully deterministic — we need exact JSON output
        max_tokens = 2048,
    )

    # ── Build messages ────────────────────────────────────────────────────
    messages = [
        SystemMessage(content=GITHUB_AGENT_SYSTEM_PROMPT),
        HumanMessage(content=full_task),
    ]

    # ── Call LLM ──────────────────────────────────────────────────────────
    print("[GitHub Agent] Translating task to GitHub action...")
    try:
        response    = llm.invoke(messages)
        raw_output  = response.content.strip()
    except Exception as e:
        return f"❌ GitHub Agent LLM call failed: {str(e)}"

    # ── Parse JSON ────────────────────────────────────────────────────────
    # The LLM should return pure JSON. Strip markdown code fences if present.
    if raw_output.startswith("```"):
        lines      = raw_output.split("\n")
        raw_output = "\n".join(lines[1:-1])  # strip ```json ... ``` wrapper

    try:
        action_json = json.loads(raw_output)
    except json.JSONDecodeError as e:
        print(f"[GitHub Agent] ⚠️  LLM did not return valid JSON: {raw_output[:200]}")
        return f"❌ GitHub Agent failed to parse action: {str(e)}\nRaw output: {raw_output[:200]}"

    # ── Execute action ────────────────────────────────────────────────────
    print(f"[GitHub Agent] Action decided: {action_json.get('action')} → {action_json.get('path', action_json.get('folder_path', action_json.get('branch_name', '')))}")
    result = _dispatch_action(action_json)

    print(f"[GitHub Agent] ✅ Done: {result[:100]}")
    return result


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing github_agent.py...\n")

    print("Test 1 — List agents folder:")
    r1 = run_github_agent("List all files in the agents folder")
    print(r1)

    print("\nTest 2 — Save a test file:")
    r2 = run_github_agent(
        task           = "Save this content to docs/test_agent_output.md",
        report_content = "# Test\n\nThis was saved by the GitHub Agent.\n"
    )
    print(r2)

    print("\n✅ github_agent.py tests complete!")
