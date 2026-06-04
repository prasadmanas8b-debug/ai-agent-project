"""
agents/github_agent.py — GitHub Agent.

Translates natural language tasks into GitHub API actions via an LLM.
All output files are saved inside git_agent_output/ (enforced in github_tools).
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

_llm: ChatGroq | None = None  # lazy init


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
You are a GitHub Agent. Your ONLY job is to perform actions on a GitHub repository.
You do NOT research topics. You do NOT write reports.

IMPORTANT: When saving any file, ALWAYS prefix the path with "{OUTPUT_FOLDER}/".

Given a task, respond with a single JSON object (no markdown, no explanation).

Available actions:

1. create_file
   {{"action": "create_file", "path": "...", "content": "...", "commit_message": "..."}}

2. update_file
   {{"action": "update_file", "path": "...", "content": "...", "commit_message": "..."}}

3. create_or_update_file  ← use when unsure if file exists
   {{"action": "create_or_update_file", "path": "...", "content": "...", "commit_message": "..."}}

4. list_files
   {{"action": "list_files", "folder_path": ""}}

5. create_branch
   {{"action": "create_branch", "branch_name": "...", "source_branch": "main"}}

6. read_file
   {{"action": "read_file", "path": "..."}}

7. delete_file
   {{"action": "delete_file", "path": "...", "commit_message": "..."}}

8. unknown
   {{"action": "unknown", "reason": "..."}}

Rules:
- Respond with ONLY valid JSON. No markdown. No explanation.
- Always save output files under "{OUTPUT_FOLDER}/" prefix.
- Infer a sensible commit_message if not given.
"""


def _strip_fences(raw: str) -> str:
    """Remove optional markdown code fences from LLM JSON output."""
    raw = raw.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw   = parts[1] if len(parts) > 1 else raw
        if raw.startswith("json"):
            raw = raw[4:]
    return raw.strip()


def _execute_action(action: str, params: dict) -> str:
    """Dispatch the parsed action to the appropriate github_tools function."""
    try:
        if action == "create_file":
            return create_file(params["path"], params.get("content", ""), params.get("commit_message", "Add file"))
        elif action == "update_file":
            return update_file(params["path"], params.get("content", ""), params.get("commit_message", "Update file"))
        elif action == "create_or_update_file":
            return create_or_update_file(params["path"], params.get("content", ""), params.get("commit_message", "Save file"))
        elif action == "list_files":
            return list_files(params.get("folder_path", ""))
        elif action == "create_branch":
            return create_branch(params["branch_name"], params.get("source_branch", "main"))
        elif action == "read_file":
            return read_file(params["path"])
        elif action == "delete_file":
            return delete_file(params["path"], params.get("commit_message", "Delete file"))
        elif action == "unknown":
            return f"⚠️ GitHub Agent: unknown action. Reason: {params.get('reason', 'N/A')}"
        else:
            return f"⚠️ GitHub Agent: unrecognized action '{action}'"
    except KeyError as exc:
        return f"❌ GitHub Agent: missing required field {exc} for action '{action}'"
    except Exception as exc:
        return f"❌ GitHub Agent: unexpected error during '{action}': {exc}"


def run_github_agent(state: AgentState) -> AgentState:
    """
    Parse the task, call the appropriate GitHub operation, and return updated state.

    Returns:
        Updated state with github_result set.
    """
    task         = state.get("task", "")
    final_report = state.get("final_report", "")

    user_message = task
    if final_report:
        user_message += f"\n\n[REPORT CONTENT TO SAVE]:\n{final_report}"

    print(f"\n🐙 GitHub Agent — task: {task[:120]}")

    try:
        response   = _get_llm().invoke([
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=user_message),
        ])
        action_obj = json.loads(_strip_fences(response.content))
    except json.JSONDecodeError as exc:
        msg = f"❌ GitHub Agent: failed to parse LLM JSON: {exc}"
        print(msg)
        return {**state, "github_result": msg}
    except Exception as exc:
        msg = f"❌ GitHub Agent: LLM call failed: {exc}"
        print(msg)
        return {**state, "github_result": msg}

    action = action_obj.get("action", "unknown")
    print(f"🔧 GitHub Agent — action: {action} | path: {action_obj.get('path', 'N/A')}")

    result = _execute_action(action, action_obj)
    print(f"📬 GitHub Agent — {result[:200]}")
    return {**state, "github_result": result}
