"""
agents/github_agent.py — GitHub Agent

Performs any GitHub operation from natural language. Understands informal
phrasing and typos — "lst files in repo" → list_files, "mak a branch" → create_branch.

Key upgrades:
  - Typo-tolerant intent understanding via LLM
  - Validates required fields before executing actions
  - Path enforcement: all writes go to git_agent_output/
  - Clear, informative result messages
"""

import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from tools.github_tools import (
    create_file,
    update_file,
    create_or_update_file,
    list_files,
    create_branch,
    read_file,
    delete_file,
)
from graph.state import AgentState

load_dotenv()

OUTPUT_FOLDER = "git_agent_output"

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


_SYSTEM_PROMPT = f"""
You are a GitHub Agent. You translate natural language tasks into GitHub API calls.
Understand the intent even if the request has typos or informal phrasing.

IMPORTANT: Any file path for writes MUST start with "{OUTPUT_FOLDER}/".

Respond with a single valid JSON object (no markdown, no explanation).

AVAILABLE ACTIONS:

create_or_update_file  ← DEFAULT for saving any file (creates or updates automatically)
  {{"action": "create_or_update_file", "path": "{OUTPUT_FOLDER}/filename.ext", "content": "...", "commit_message": "..."}}

list_files
  {{"action": "list_files", "folder_path": "agents"}}
  Use "" or "." for the root directory.

read_file
  {{"action": "read_file", "path": "{OUTPUT_FOLDER}/filename.ext"}}

create_branch
  {{"action": "create_branch", "branch_name": "feature/my-branch", "source_branch": "main"}}

delete_file
  {{"action": "delete_file", "path": "{OUTPUT_FOLDER}/filename.ext", "commit_message": "Remove file"}}

unknown  ← use only if you truly cannot understand the request
  {{"action": "unknown", "reason": "explanation"}}

TYPO EXAMPLES:
  "lst files in agents"          → list_files, folder_path="agents"
  "reed the report file"         → read_file
  "mak a new branch called dev"  → create_branch, branch_name="dev"
  "sav this report to github"    → create_or_update_file
  "delet the old test file"      → delete_file

RULES:
  - Always output ONLY valid JSON. No markdown.
  - Infer a sensible commit_message from context if not given.
  - Never invent file content — use what's provided in the task.
  - If report content is given, use it as the "content" field verbatim.
"""


def _strip_fences(raw: str) -> str:
    """Remove optional markdown fences from LLM JSON output."""
    raw = raw.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw   = parts[1] if len(parts) > 1 else raw
        if raw.lower().startswith("json"):
            raw = raw[4:]
    return raw.strip()


def _execute(action: str, p: dict) -> str:
    """Dispatch a parsed action to the correct github_tools function."""
    try:
        if action == "create_or_update_file":
            return create_or_update_file(p["path"], p.get("content", ""), p.get("commit_message", "Save via GitHub Agent"))
        elif action == "create_file":
            return create_file(p["path"], p.get("content", ""), p.get("commit_message", "Add file"))
        elif action == "update_file":
            return update_file(p["path"], p.get("content", ""), p.get("commit_message", "Update file"))
        elif action == "list_files":
            return list_files(p.get("folder_path", ""))
        elif action == "read_file":
            return read_file(p["path"])
        elif action == "create_branch":
            return create_branch(p["branch_name"], p.get("source_branch", "main"))
        elif action == "delete_file":
            return delete_file(p["path"], p.get("commit_message", "Delete file"))
        elif action == "unknown":
            return f"⚠️ GitHub Agent: could not understand request — {p.get('reason', 'N/A')}"
        else:
            return f"⚠️ GitHub Agent: unrecognized action '{action}'"
    except KeyError as exc:
        return f"❌ GitHub Agent: missing required field {exc} for action '{action}'"
    except Exception as exc:
        return f"❌ GitHub Agent: error during '{action}': {exc}"


def run_github_agent(state: AgentState) -> AgentState:
    """
    Parse the task and execute the appropriate GitHub operation.

    Returns:
        Updated state with github_result set.
    """
    task         = state.get("task", "")
    final_report = state.get("final_report", "")

    # Include any report content so the LLM can use it as file content
    user_message = task
    if final_report:
        user_message += f"\n\n[CONTENT TO SAVE]:\n{final_report}"

    print(f"\n🐙 GitHub Agent — task: {task[:120]}")

    try:
        response   = _get_llm().invoke([
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=user_message),
        ])
        raw        = _strip_fences(response.content)
        action_obj = json.loads(raw)
    except json.JSONDecodeError as exc:
        msg = f"❌ GitHub Agent: could not parse LLM response as JSON: {exc}"
        print(msg)
        return {**state, "github_result": msg}
    except Exception as exc:
        msg = f"❌ GitHub Agent: LLM error: {exc}"
        print(msg)
        return {**state, "github_result": msg}

    action = action_obj.get("action", "unknown")
    print(f"🔧 GitHub Agent — action: {action} | path: {action_obj.get('path', 'N/A')}")

    result = _execute(action, action_obj)
    print(f"📬 GitHub Agent — {result[:200]}")
    return {**state, "github_result": result}
