"""
tools/github_tools.py — Low-level GitHub helpers.

All write operations (create / update / delete) are path-locked to
git_agent_output/ to prevent accidental repo pollution.
"""

import os
from github import Github, GithubException
from dotenv import load_dotenv

load_dotenv()

OUTPUT_FOLDER = "git_agent_output"

_repo = None  # lazy init — one connection per process


def _get_repo():
    """Return (and cache) the authenticated PyGithub repo object."""
    global _repo
    if _repo is None:
        token     = os.getenv("GITHUB_TOKEN")
        repo_name = os.getenv("GITHUB_REPO")
        if not token:
            raise EnvironmentError("GITHUB_TOKEN not set in .env")
        if not repo_name:
            raise EnvironmentError("GITHUB_REPO not set in .env")
        _repo = Github(token).get_repo(repo_name)
    return _repo


def _safe_path(path: str) -> str:
    """
    Enforce that any write/read path lives inside git_agent_output/.

    Strips any existing folder prefix and re-attaches the correct one.
    Logs a warning when the path is silently redirected.
    """
    path     = path.strip("/").strip()
    filename = os.path.basename(path) if "/" in path else path
    if not filename:
        filename = "output.md"
    result = f"{OUTPUT_FOLDER}/{filename}"
    if result != path:
        print(f"[github_tools] ⚠️  Path redirected: '{path}' → '{result}'")
    return result


# ── Public API ────────────────────────────────────────────────────────────────

def create_file(path: str, content: str, commit_message: str) -> str:
    """Create a new file. Returns an error string if it already exists."""
    path = _safe_path(path)
    try:
        _get_repo().create_file(path, commit_message, content)
        return f"✅ '{path}' created — {commit_message}"
    except GithubException as exc:
        if exc.status == 422:
            return f"❌ '{path}' already exists — use update_file() instead."
        return f"❌ GitHub error (create): {exc.data.get('message', exc)}"
    except Exception as exc:
        return f"❌ Unexpected error (create): {exc}"


def update_file(path: str, content: str, commit_message: str) -> str:
    """Update an existing file. Returns an error string if not found."""
    path = _safe_path(path)
    try:
        existing = _get_repo().get_contents(path)
        _get_repo().update_file(path, commit_message, content, existing.sha)
        return f"✅ '{path}' updated — {commit_message}"
    except GithubException as exc:
        if exc.status == 404:
            return f"❌ '{path}' not found — use create_file() instead."
        return f"❌ GitHub error (update): {exc.data.get('message', exc)}"
    except Exception as exc:
        return f"❌ Unexpected error (update): {exc}"


def create_or_update_file(path: str, content: str, commit_message: str) -> str:
    """Upsert: creates if absent, updates if present."""
    path = _safe_path(path)
    try:
        repo = _get_repo()
        try:
            existing = repo.get_contents(path)
            repo.update_file(path, commit_message, content, existing.sha)
            return f"✅ '{path}' updated — {commit_message}"
        except GithubException as exc:
            if exc.status == 404:
                repo.create_file(path, commit_message, content)
                return f"✅ '{path}' created — {commit_message}"
            raise
    except GithubException as exc:
        return f"❌ GitHub error (upsert): {exc.data.get('message', exc)}"
    except Exception as exc:
        return f"❌ Unexpected error (upsert): {exc}"


def list_files(folder_path: str = "") -> str:
    """List files/folders at the given path (default: repo root)."""
    try:
        contents = _get_repo().get_contents(folder_path)
        if not contents:
            return f"📂 '{folder_path or 'root'}' is empty."
        lines = [
            f"  {'📄' if item.type == 'file' else '📁'} {item.name}"
            for item in contents
        ]
        return f"📂 '{folder_path or 'root'}':\n" + "\n".join(lines)
    except GithubException as exc:
        if exc.status == 404:
            return f"❌ Path '{folder_path}' not found."
        return f"❌ GitHub error (list): {exc.data.get('message', exc)}"
    except Exception as exc:
        return f"❌ Unexpected error (list): {exc}"


def create_branch(branch_name: str, source_branch: str = "main") -> str:
    """Create a new branch from source_branch."""
    try:
        repo = _get_repo()
        sha  = repo.get_branch(source_branch).commit.sha
        repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=sha)
        return f"✅ Branch '{branch_name}' created from '{source_branch}'."
    except GithubException as exc:
        if exc.status == 422:
            return f"❌ Branch '{branch_name}' already exists."
        if exc.status == 404:
            return f"❌ Source branch '{source_branch}' not found."
        return f"❌ GitHub error (branch): {exc.data.get('message', exc)}"
    except Exception as exc:
        return f"❌ Unexpected error (branch): {exc}"


def read_file(path: str) -> str:
    """Read and return the decoded content of a file."""
    path = _safe_path(path)
    try:
        content = _get_repo().get_contents(path)
        return f"📄 '{path}':\n\n{content.decoded_content.decode('utf-8')}"
    except GithubException as exc:
        if exc.status == 404:
            return f"❌ '{path}' not found."
        return f"❌ GitHub error (read): {exc.data.get('message', exc)}"
    except Exception as exc:
        return f"❌ Unexpected error (read): {exc}"


def delete_file(path: str, commit_message: str) -> str:
    """Delete a file from the repo."""
    path = _safe_path(path)
    try:
        content = _get_repo().get_contents(path)
        _get_repo().delete_file(path, commit_message, content.sha)
        return f"✅ '{path}' deleted — {commit_message}"
    except GithubException as exc:
        if exc.status == 404:
            return f"❌ '{path}' not found — cannot delete."
        return f"❌ GitHub error (delete): {exc.data.get('message', exc)}"
    except Exception as exc:
        return f"❌ Unexpected error (delete): {exc}"
