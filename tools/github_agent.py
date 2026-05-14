import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

# Import all tools from github_tools
from tools.github_tools import (
    create_file,
    update_file,
    create_or_update_file,
    list_files,
    create_branch,
    read_file,
    delete_file,
)

load_dotenv()

# ── LLM setup ────────────────────────────────────────────────────────────────
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    openai_api_key=os.getenv("OPENAI_API_KEY"),
)

# ── System prompt ─────────────────────────────────────────────────────────────
GITHUB_AGENT_SYSTEM_PROMPT = """
You are a GitHub Agent. Your ONLY job is to perform actions on a GitHub repository.
You do NOT research topics. You do NOT write reports. You ONLY interact with GitHub.

Given a natural language task, you must respond with a JSON object (no markdown, no explanation)
that describes the exact GitHub action to take.

Available actions and their required fields:

1. create_file
   { "action": "create_file", "path": "...", "content": "...", "commit_message": "..." }

2. update_file
   { "action": "update_file", "path": "...", "content": "...", "commit_message": "..." }

3. create_or_update_file  ← use this when unsure if file exists
   { "action": "create_or_update_file", "path": "...", "content": "...", "commit_message": "..." }

4. list_files
   { "action": "list_files", "folder_path": "..." }
   Use folder_path "" for the root directory.

5. create_branch
   { "action": "create_branch", "branch_name": "...", "source_branch": "main" }

6. read_file
   { "action": "read_file", "path": "..." }

7. delete_file
   { "action": "delete_file", "path": "...", "commit_message": "..." }

8. unknown  ← if the task is not a GitHub action
   { "action": "unknown", "reason": "..." }

Rules:
- Respond with ONLY valid JSON. No markdown. No explanation. No code fences.
- If a report/content is provided in the task, use it as the "content" field directly.
- Infer a sensible commit_message if not explicitly provided.
- For list actions, extract the folder name from the task.
- Never invent content. If content is needed but not provided, use an empty string.
"""


# ── Core agent function ────────────────────────────────────────────────────────

def run_github_agent(state: dict) -> dict:
    """
    GitHub Agent node for LangGraph.

    Reads the task (and optionally the final_report) from state,
    determines the correct GitHub action via LLM, executes it,
    and writes the result back to state["github_result"].

    Args:
        state: LangGraph shared state dict with keys:
               - task (str): the original user instruction
               - final_report (str): report produced by Writer Agent (may be empty)

    Returns:
        Updated state dict with "github_result" populated.
    """
    task = state.get("task", "")
    final_report = state.get("final_report", "")

    # If a report was written, include it so the LLM can use it as file content
    user_message = task
    if final_report:
        user_message += f"\n\n[REPORT CONTENT TO SAVE]:\n{final_report}"

    print(f"\n🐙 GitHub Agent received task: {task[:120]}...")

    # ── Step 1: Ask LLM to parse the task into a structured action ────────────
    try:
        response = llm.invoke([
            SystemMessage(content=GITHUB_AGENT_SYSTEM_PROMPT),
            HumanMessage(content=user_message),
        ])
        raw = response.content.strip()

        # Strip accidental markdown fences if LLM adds them
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        action_obj = json.loads(raw)

    except json.JSONDecodeError as e:
        error_msg = f"❌ GitHub Agent failed to parse LLM response as JSON: {str(e)}\nRaw response: {raw}"
        print(error_msg)
        state["github_result"] = error_msg
        return state
    except Exception as e:
        error_msg = f"❌ GitHub Agent LLM call failed: {str(e)}"
        print(error_msg)
        state["github_result"] = error_msg
        return state

    action = action_obj.get("action", "unknown")
    print(f"🔧 GitHub Agent decided action: {action}")

    # ── Step 2: Execute the chosen action ────────────────────────────────────
    result = _execute_action(action, action_obj)

    print(f"📬 GitHub Agent result: {result}")
    state["github_result"] = result
    return state


def _execute_action(action: str, params: dict) -> str:
    """
    Dispatches the action to the correct github_tools function.

    Args:
        action: Action name string from LLM response
        params: Full JSON dict from LLM (contains path, content, etc.)

    Returns:
        Result string from the tool function
    """
    try:
        if action == "create_file":
            return create_file(
                path=params["path"],
                content=params.get("content", ""),
                commit_message=params.get("commit_message", "Add file via GitHub Agent"),
            )

        elif action == "update_file":
            return update_file(
                path=params["path"],
                content=params.get("content", ""),
                commit_message=params.get("commit_message", "Update file via GitHub Agent"),
            )

        elif action == "create_or_update_file":
            return create_or_update_file(
                path=params["path"],
                content=params.get("content", ""),
                commit_message=params.get("commit_message", "Save file via GitHub Agent"),
            )

        elif action == "list_files":
            return list_files(
                folder_path=params.get("folder_path", ""),
            )

        elif action == "create_branch":
            return create_branch(
                branch_name=params["branch_name"],
                source_branch=params.get("source_branch", "main"),
            )

        elif action == "read_file":
            return read_file(
                path=params["path"],
            )

        elif action == "delete_file":
            return delete_file(
                path=params["path"],
                commit_message=params.get("commit_message", "Delete file via GitHub Agent"),
            )

        elif action == "unknown":
            reason = params.get("reason", "No reason provided.")
            return f"⚠️ GitHub Agent could not determine a valid GitHub action. Reason: {reason}"

        else:
            return f"❌ GitHub Agent received an unrecognised action: '{action}'"

    except KeyError as e:
        return f"❌ GitHub Agent missing required field for action '{action}': {str(e)}"
    except Exception as e:
        return f"❌ GitHub Agent encountered an error executing '{action}': {str(e)}"


# ── Standalone test (run this file directly to test without the graph) ─────────
if __name__ == "__main__":
    print("=" * 60)
    print("GitHub Agent — Standalone Test")
    print("=" * 60)

    test_cases = [
        {
            "name": "List files in agents folder",
            "state": {
                "task": "List all files in the agents folder",
                "final_report": "",
                "github_result": "",
            },
        },
        {
            "name": "Create a new file",
            "state": {
                "task": "Create a file called test_notes.md in the outputs folder",
                "final_report": "# Test Notes\nThis is a test file created by the GitHub Agent.",
                "github_result": "",
            },
        },
        {
            "name": "Create a new branch",
            "state": {
                "task": "Create a branch called feature/github-agent",
                "final_report": "",
                "github_result": "",
            },
        },
        {
            "name": "Unknown / non-GitHub task",
            "state": {
                "task": "What is the capital of France?",
                "final_report": "",
                "github_result": "",
            },
        },
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n── Test {i}: {test['name']} ──")
        updated_state = run_github_agent(test["state"])
        print(f"Result: {updated_state['github_result']}")

    print("\n" + "=" * 60)
    print("All standalone tests complete.")