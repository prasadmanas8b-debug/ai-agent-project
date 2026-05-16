import os
import json
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from tools.github_tools import (
    save_report, create_file, update_file, list_files, create_branch
)
from graph.state import AgentState

llm = ChatOpenAI(
    model       = "gpt-4o-mini",
    temperature = 0,
    api_key     = os.getenv("OPENAI_API_KEY"),
)

SYSTEM_PROMPT = """
You are a GitHub Agent. You perform real actions on a GitHub repository.
You have 5 available actions:

  save_report   — save the writer's report to the outputs/ folder (use this when a report exists)
  create_file   — create a new file at a specific path
  update_file   — update or upsert an existing file
  list_files    — list files in a folder
  create_branch — create a new git branch

Respond ONLY with a valid JSON object. No markdown fences. No explanation. Example:
{
  "action":  "save_report",
  "path":    "",
  "content": "",
  "message": "",
  "branch":  "",
  "filename": "outputs/quantum_computing.md"
}

Rules:
- If a final report is available and the task involves saving/committing to GitHub → use save_report
- For save_report, set filename only if the user named a specific file, else leave it empty
- For list_files, put the folder path in "path" (empty string for root)
- For create_branch, put the branch name in "branch"
- For create_file / update_file, fill "path", "content", and "message"
"""

def run_github_agent(state: AgentState) -> AgentState:
    task   = state.get("task", "")
    report = state.get("final_report", "")

    # Build context for LLM
    user_prompt = f"Task: {task}"
    if report:
        user_prompt += f"\n\nFinal report content (from Writer Agent):\n{report}"

    try:
        response = llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ])

        raw = response.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        params = json.loads(raw)

    except json.JSONDecodeError:
        state["github_result"] = "❌ GitHub Agent failed to parse LLM response. No action taken."
        return state
    except Exception as e:
        state["github_result"] = f"❌ GitHub Agent LLM call failed: {str(e)}"
        return state

    action   = params.get("action",   "").strip()
    path     = params.get("path",     "").strip()
    content  = params.get("content",  "").strip()
    message  = params.get("message",  "Auto-commit by AI Agent").strip()
    branch   = params.get("branch",   "").strip()
    filename = params.get("filename", "").strip()

    # Execute the chosen action
    if action == "save_report":
        result = save_report(content=report, filename=filename or None)

    elif action == "create_file":
        result = create_file(path, content, message)

    elif action == "update_file":
        result = update_file(path, content, message)

    elif action == "list_files":
        result = list_files(path)

    elif action == "create_branch":
        result = create_branch(branch)

    else:
        result = f"❌ Unknown action '{action}'. No GitHub operation performed."

    state["github_result"] = result
    return state