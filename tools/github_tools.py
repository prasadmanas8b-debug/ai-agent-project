"""
tools/github_tools.py
Low-level GitHub helpers used by the GitHub Agent.
ALL write operations (create/update/delete) are locked to git_agent_output/.
"""
import os
from github import Github, GithubException
from dotenv import load_dotenv

load_dotenv()

OUTPUT_FOLDER = "git_agent_output"

def _get_repo():
    token     = os.getenv("GITHUB_TOKEN")
    repo_name = os.getenv("GITHUB_REPO")
    if not token:
        raise ValueError("GITHUB_TOKEN not found in .env")
    if not repo_name:
        raise ValueError("GITHUB_REPO not found in .env")
    return Github(token).get_repo(repo_name)

def _safe_path(path: str) -> str:
    """
    Hard-enforce that any write/read path lives inside git_agent_output/.
    Strips any existing folder prefix and re-attaches the correct one.
    """
    filename = os.path.basename(path.strip("/")) if "/" in path else path.strip()
    if not filename:
        filename = "output.md"
    result = f"{OUTPUT_FOLDER}/{filename}"
    if result != path:
        print(f"[github_tools] 🔒 Path redirected: '{path}' → '{result}'")
    return result


def create_file(path: str, content: str, commit_message: str) -> str:
    path = _safe_path(path)
    try:
        repo = _get_repo()
        repo.create_file(path, commit_message, content)
        return f"✅ File '{path}' created — commit: '{commit_message}'"
    except GithubException as e:
        if e.status == 422:
            return f"❌ File '{path}' already exists. Use update_file() instead."
        return f"❌ GitHub error creating '{path}': {e.data.get('message', str(e))}"
    except Exception as e:
        return f"❌ Unexpected error creating file: {e}"


def update_file(path: str, content: str, commit_message: str) -> str:
    path = _safe_path(path)
    try:
        repo     = _get_repo()
        existing = repo.get_contents(path)
        repo.update_file(path, commit_message, content, existing.sha)
        return f"✅ File '{path}' updated — commit: '{commit_message}'"
    except GithubException as e:
        if e.status == 404:
            return f"❌ File '{path}' not found. Use create_file() instead."
        return f"❌ GitHub error updating '{path}': {e.data.get('message', str(e))}"
    except Exception as e:
        return f"❌ Unexpected error updating file: {e}"


def create_or_update_file(path: str, content: str, commit_message: str) -> str:
    """Smart upsert — creates if not exists, updates if it does."""
    path = _safe_path(path)
    try:
        repo = _get_repo()
        try:
            existing = repo.get_contents(path)
            repo.update_file(path, commit_message, content, existing.sha)
            return f"✅ File '{path}' updated — commit: '{commit_message}'"
        except GithubException as e:
            if e.status == 404:
                repo.create_file(path, commit_message, content)
                return f"✅ File '{path}' created — commit: '{commit_message}'"
            raise
    except GithubException as e:
        return f"❌ GitHub error upserting '{path}': {e.data.get('message', str(e))}"
    except Exception as e:
        return f"❌ Unexpected error upserting: {e}"


def list_files(folder_path: str = "") -> str:
    try:
        repo     = _get_repo()
        contents = repo.get_contents(folder_path)
        if not contents:
            return f"📂 Folder '{folder_path or 'root'}' is empty."
        lines = []
        for item in contents:
            icon = "📄" if item.type == "file" else "📁"
            lines.append(f"  {icon} {item.name}  ({item.type})")
        label = folder_path or "root"
        return f"📂 Files in '{label}':\n" + "\n".join(lines)
    except GithubException as e:
        if e.status == 404:
            return f"❌ Folder '{folder_path}' not found."
        return f"❌ GitHub error listing files: {e.data.get('message', str(e))}"
    except Exception as e:
        return f"❌ Unexpected error listing files: {e}"


def create_branch(branch_name: str, source_branch: str = "main") -> str:
    try:
        repo       = _get_repo()
        source_ref = repo.get_branch(source_branch)
        repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=source_ref.commit.sha)
        return f"✅ Branch '{branch_name}' created from '{source_branch}'."
    except GithubException as e:
        if e.status == 422:
            return f"❌ Branch '{branch_name}' already exists."
        if e.status == 404:
            return f"❌ Source branch '{source_branch}' not found."
        return f"❌ GitHub error creating branch: {e.data.get('message', str(e))}"
    except Exception as e:
        return f"❌ Unexpected error creating branch: {e}"


def read_file(path: str) -> str:
    path = _safe_path(path)
    try:
        repo    = _get_repo()
        content = repo.get_contents(path)
        decoded = content.decoded_content.decode("utf-8")
        return f"📄 Content of '{path}':\n\n{decoded}"
    except GithubException as e:
        if e.status == 404:
            return f"❌ File '{path}' not found."
        return f"❌ GitHub error reading '{path}': {e.data.get('message', str(e))}"
    except Exception as e:
        return f"❌ Unexpected error reading file: {e}"


def delete_file(path: str, commit_message: str) -> str:
    path = _safe_path(path)
    try:
        repo    = _get_repo()
        content = repo.get_contents(path)
        repo.delete_file(path, commit_message, content.sha)
        return f"✅ File '{path}' deleted — commit: '{commit_message}'"
    except GithubException as e:
        if e.status == 404:
            return f"❌ File '{path}' not found. Cannot delete."
        return f"❌ GitHub error deleting '{path}': {e.data.get('message', str(e))}"
    except Exception as e:
        return f"❌ Unexpected error deleting file: {e}"
