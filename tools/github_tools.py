"""
tools/github_tools.py — Phase 3
AI Agent Project | GitHub API Wrapper

What this file is:
──────────────────
This is the "kitchen" of the GitHub system.
It contains the raw cooking functions — each one does exactly one GitHub action.
It knows nothing about user intent or natural language.

github_agent.py is the "waiter" — it reads the customer's request,
translates it into a kitchen order, and calls these functions.

All functions use PyGithub (pip install PyGithub) under the hood.
Authentication is done via GITHUB_TOKEN from .env — never hardcoded.

Functions:
  create_file()   — create a new file in the repo
  update_file()   — update an existing file's content
  list_files()    — list all files in a folder
  create_branch() — create a new branch from main
  get_file()      — read a file's content (useful for checking before update)
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv()

from github import Github, GithubException

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: SETUP
# ─────────────────────────────────────────────────────────────────────────────
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO  = os.getenv("GITHUB_REPO")   # format: "username/repo-name"

def _get_repo():
    """
    Returns an authenticated PyGithub repo object.
    Called at the start of every tool function.

    Returns:
        github.Repository.Repository: The connected repo object.

    Raises:
        EnvironmentError: If GITHUB_TOKEN or GITHUB_REPO is missing from .env
        GithubException: If authentication fails (bad token) or repo not found
    """
    if not GITHUB_TOKEN:
        raise EnvironmentError("❌ GITHUB_TOKEN missing from .env")
    if not GITHUB_REPO:
        raise EnvironmentError("❌ GITHUB_REPO missing from .env — format: username/repo-name")

    g    = Github(GITHUB_TOKEN)
    repo = g.get_repo(GITHUB_REPO)
    return repo


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2: TOOL FUNCTIONS
# Each function does exactly ONE GitHub action and returns a result string.
# ─────────────────────────────────────────────────────────────────────────────

def create_file(path: str, content: str, commit_message: str = "chore: create file via AI agent") -> str:
    """
    Creates a NEW file in the GitHub repository.
    If the file already exists, returns an error message instead of crashing.

    Args:
        path           (str): File path in the repo. Example: "docs/report.md"
        content        (str): The text content to write into the file.
        commit_message (str): The Git commit message. Defaults to a sensible value.

    Returns:
        str: Success or error message.

    Example:
        result = create_file("docs/ai_report.md", "# AI Report\n\nContent here.")
        print(result)  # "✅ Created docs/ai_report.md in main branch."
    """
    try:
        repo = _get_repo()
        repo.create_file(
            path    = path,
            message = commit_message,
            content = content,
        )
        return f"✅ Created '{path}' in the repository with commit: '{commit_message}'"
    except GithubException as e:
        if e.status == 422:
            return f"⚠️ File '{path}' already exists. Use update_file() to modify it."
        return f"❌ GitHub error creating '{path}': {e.data.get('message', str(e))}"
    except Exception as e:
        return f"❌ Unexpected error creating '{path}': {str(e)}"


def update_file(path: str, content: str, commit_message: str = "chore: update file via AI agent") -> str:
    """
    Updates an EXISTING file in the GitHub repository.
    If the file does not exist, returns an error message instead of crashing.

    Args:
        path           (str): File path in the repo. Example: "docs/report.md"
        content        (str): The new text content to overwrite the file with.
        commit_message (str): The Git commit message.

    Returns:
        str: Success or error message.
    """
    try:
        repo     = _get_repo()
        contents = repo.get_contents(path)   # Get current file (need its SHA to update)
        repo.update_file(
            path    = contents.path,
            message = commit_message,
            content = content,
            sha     = contents.sha,          # GitHub requires the current SHA to prevent conflicts
        )
        return f"✅ Updated '{path}' in the repository with commit: '{commit_message}'"
    except GithubException as e:
        if e.status == 404:
            return f"⚠️ File '{path}' does not exist. Use create_file() to create it first."
        return f"❌ GitHub error updating '{path}': {e.data.get('message', str(e))}"
    except Exception as e:
        return f"❌ Unexpected error updating '{path}': {str(e)}"


def list_files(folder_path: str = "") -> str:
    """
    Lists all files in a folder of the repository.
    Pass empty string or "/" to list root directory files.

    Args:
        folder_path (str): The folder path. Example: "agents" or "tools" or "" for root.

    Returns:
        str: A formatted list of file paths, or an error message.

    Example:
        print(list_files("agents"))
        # Files in 'agents/':
        #   📄 agents/research_agent.py
        #   📄 agents/writer_agent.py
    """
    try:
        repo     = _get_repo()
        contents = repo.get_contents(folder_path)

        files = [item.path for item in contents if item.type == "file"]
        dirs  = [item.path + "/" for item in contents if item.type == "dir"]

        result_lines = [f"📂 Contents of '{folder_path or 'root'}':"]
        for d in sorted(dirs):
            result_lines.append(f"  📁 {d}")
        for f in sorted(files):
            result_lines.append(f"  📄 {f}")

        if not files and not dirs:
            result_lines.append("  (empty folder)")

        return "\n".join(result_lines)
    except GithubException as e:
        if e.status == 404:
            return f"⚠️ Folder '{folder_path}' not found in the repository."
        return f"❌ GitHub error listing '{folder_path}': {e.data.get('message', str(e))}"
    except Exception as e:
        return f"❌ Unexpected error listing '{folder_path}': {str(e)}"


def create_branch(branch_name: str, from_branch: str = "main") -> str:
    """
    Creates a new branch in the repository from an existing branch.

    Args:
        branch_name (str): The name of the new branch. Example: "feature/github-agent"
        from_branch (str): The source branch to create from. Default: "main"

    Returns:
        str: Success or error message.
    """
    try:
        repo   = _get_repo()
        source = repo.get_branch(from_branch)
        repo.create_git_ref(
            ref = f"refs/heads/{branch_name}",
            sha = source.commit.sha
        )
        return f"✅ Created branch '{branch_name}' from '{from_branch}'."
    except GithubException as e:
        if e.status == 422:
            return f"⚠️ Branch '{branch_name}' already exists."
        return f"❌ GitHub error creating branch '{branch_name}': {e.data.get('message', str(e))}"
    except Exception as e:
        return f"❌ Unexpected error creating branch '{branch_name}': {str(e)}"


def get_file(path: str) -> str:
    """
    Reads the content of a file from the repository.
    Useful for checking if a file exists before creating/updating it.

    Args:
        path (str): File path in the repo. Example: "docs/report.md"

    Returns:
        str: The file's decoded text content, or an error message.
    """
    try:
        repo     = _get_repo()
        contents = repo.get_contents(path)
        text     = contents.decoded_content.decode("utf-8")
        return f"📄 Content of '{path}':\n\n{text}"
    except GithubException as e:
        if e.status == 404:
            return f"⚠️ File '{path}' not found in the repository."
        return f"❌ GitHub error reading '{path}': {e.data.get('message', str(e))}"
    except Exception as e:
        return f"❌ Unexpected error reading '{path}': {str(e)}"


def create_or_update_file(path: str, content: str, commit_message: str = "chore: save via AI agent") -> str:
    """
    Smart save — creates the file if it doesn't exist, updates it if it does.
    This is the preferred function for saving reports to GitHub.

    Args:
        path           (str): File path in repo. Example: "docs/quantum_report.md"
        content        (str): Text content to write.
        commit_message (str): Git commit message.

    Returns:
        str: Success message saying whether the file was created or updated.
    """
    try:
        repo = _get_repo()
        try:
            # Try to get existing file
            existing = repo.get_contents(path)
            # File exists → update it
            repo.update_file(
                path    = existing.path,
                message = commit_message,
                content = content,
                sha     = existing.sha,
            )
            return f"✅ Updated existing file '{path}' with commit: '{commit_message}'"
        except GithubException as e:
            if e.status == 404:
                # File doesn't exist → create it
                repo.create_file(
                    path    = path,
                    message = commit_message,
                    content = content,
                )
                return f"✅ Created new file '{path}' with commit: '{commit_message}'"
            raise
    except Exception as e:
        return f"❌ Error saving '{path}': {str(e)}"


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing github_tools.py...\n")

    print("1. Listing root files:")
    print(list_files(""))
    print()

    print("2. Listing agents/ folder:")
    print(list_files("agents"))
    print()

    print("✅ github_tools.py connected to GitHub!")
