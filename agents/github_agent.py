"""
agents/github_agent.py
Performs GitHub actions — all output files are saved inside git_agent_output/.
Uses lazy LLM initialization so it's testable without API keys.
"""
import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from tools.github_tools import (
    create_file, update_file, create_or_update_file,
    list_files, create_branch, read_file, delete_file,
)

load_dotenv()

OUTPUT_FOLDER = "git_agent_output"

_llm = None

def _get_llm():
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
You do NOT research topics. You do NOT write reports. You ONLY interact with GitHub.

IMPORTANT: When saving any file, ALWAYS prefix the path with "{OUTPUT_FOLDER}/".
Example: save a report as "{OUTPUT_FOLDER}/report_ai_trends.md", NOT "outputs/report.md".

Given a natural language task, respond with a single JSON object (no markdown, no explanation).

Available actions:

1. create_file
   {{"action": "create_file", "path": "...", "content": "...", "commit_message": "..."}}

2. update_file
   {{"action": "update_file", "path": "...", "content": "...", "commit_message": "..."}}

3. create_or_update_file  ← use when unsure if file exists
   {{"action": "create_or_update_file", "path": "...", "content": "...", "commit_message": "..."}}

4. list_files
   {{"action": "list_files", "folder_path": "..."}}
   Use "" for root directory.

5. create_branch
   {{"action": "create_branch", "branch_name": "...", "source_branch": "main"}}

6. read_file
   {{"action": "read_file", "path": "..."}}

7. delete_file
   {{"action": "delete_file", "path": "...", "commit_message": "..."}}

8. unknown
   {{"action": "unknown", "reason": "..."}}

Rules:
- Respond with ONLY valid JSON. No markdown fences. No explanation.
- If report/content is provided in the task, use it as the "content" field.
- Always save output files under "{OUTPUT_FOLDER}/" prefix.
- Infer a sensible commit_message if not explicitly given.
- Never invent content — if none provided, use empty string.
"""

def _clean_json(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1] if len(parts) > 1 else raw
        if raw.startswith("json"):
            raw = raw[4:]
    return raw.strip()

def _enforce_output_folder(path: str) -> str:
    """Ensure file path is inside git_agent_output/."""
    if not path.startswith(OUTPUT_FOLDER + "/"):
        filename = os.path.basename(path) if "/" in path else path
        return f"{OUTPUT_FOLDER}/{filename}"
    return path

def run_github_agent(state: dict) -> dict:
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
        action_obj = json.loads(_clean_json(response.content))
    except json.JSONDecodeError as e:
        msg = f"❌ GitHub Agent: failed to parse LLM response as JSON: {e}"
        print(msg)
        return {**state, "github_result": msg}
    except Exception as e:
        msg = f"❌ GitHub Agent: LLM call failed: {e}"
        print(msg)
        return {**state, "github_result": msg}

    action = action_obj.get("action", "unknown")

    if action in ("create_file", "update_file", "create_or_update_file", "read_file", "delete_file"):
        action_obj["path"] = _enforce_output_folder(action_obj.get("path", "output.md"))

    print(f"🔧 GitHub Agent — action: {action} | path: {action_obj.get('path', 'N/A')}")

    result = _execute_action(action, action_obj)
    print(f"📬 GitHub Agent — result: {result[:200]}")
    return {**state, "github_result": result}

def _execute_action(action: str, p: dict) -> str:
    try:
        if action == "create_file":
            return create_file(p["path"], p.get("content", ""), p.get("commit_message", "Add file via GitHub Agent"))
        elif action == "update_file":
            return update_file(p["path"], p.get("content", ""), p.get("commit_message", "Update file via GitHub Agent"))
        elif action == "create_or_update_file":
            return create_or_update_file(p["path"], p.get("content", ""), p.get("commit_message", "Save file via GitHub Agent"))
        elif action == "list_files":
            return list_files(p.get("folder_path", ""))
        elif action == "create_branch":
            return create_branch(p["branch_name"], p.get("source_branch", "main"))
        elif action == "read_file":
            return read_file(p["path"])
        elif action == "delete_file":
            return delete_file(p["path"], p.get("commit_message", "Delete file via GitHub Agent"))
        elif action == "unknown":
            return f"⚠️ GitHub Agent: unknown action requested. Reason: {p.get('reason', 'N/A')}"
        else:
            return f"⚠️ GitHub Agent: unrecognized action '{action}'"
    except KeyError as e:
        return f"❌ GitHub Agent: missing required field {e} for action '{action}'"
    except Exception as e:
        return f"❌ GitHub Agent: unexpected error during '{action}': {e}"
