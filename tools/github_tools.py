import os
from datetime import datetime
from github import Github, GithubException
from dotenv import load_dotenv

load_dotenv()

# ── Connection ────────────────────────────────────────────────────────────────
_token = os.getenv("GITHUB_TOKEN")
_repo_name = os.getenv("GITHUB_REPO")

if not _token or not _repo_name:
    raise EnvironmentError(
        "GITHUB_TOKEN and GITHUB_REPO must be set in your .env file."
    )

_gh   = Github(_token)
_repo = _gh.get_repo(_repo_name)


# ── Core Functions ────────────────────────────────────────────────────────────

def save_report(content: str, filename: str = None) -> str:
    """
    Primary function — saves Writer Agent output to the repo.
    Auto-generates a timestamped filename under outputs/ if none given.
    Safely updates the file if it already exists.
    """
    if not content or not content.strip():
        return "⚠️ No report content provided. Nothing was saved."

    if not filename:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename  = f"outputs/report_{timestamp}.md"

    commit_msg = f"Auto-save report — {filename}"

    try:
        existing = _repo.get_contents(filename)
        _repo.update_file(filename, commit_msg, content, existing.sha)
        return f"✅ Report updated → '{filename}'"
    except GithubException as e:
        if e.status == 404:
            try:
                _repo.create_file(filename, commit_msg, content)
                return f"✅ Report saved → '{filename}'"
            except GithubException as ce:
                return f"❌ Failed to create file: {ce.data.get('message', str(ce))}"
        return f"❌ GitHub error ({e.status}): {e.data.get('message', str(e))}"


def create_file(path: str, content: str, commit_message: str) -> str:
    """Create a new file. Returns error if it already exists."""
    try:
        _repo.create_file(path, commit_message, content)
        return f"✅ Created '{path}'"
    except GithubException as e:
        if e.status == 422:
            return f"❌ '{path}' already exists. Use update_file() instead."
        return f"❌ GitHub error ({e.status}): {e.data.get('message', str(e))}"


def update_file(path: str, content: str, commit_message: str) -> str:
    """Update an existing file. Creates it if it does not exist (safe upsert)."""
    try:
        existing = _repo.get_contents(path)
        _repo.update_file(path, commit_message, content, existing.sha)
        return f"✅ Updated '{path}'"
    except GithubException as e:
        if e.status == 404:
            return create_file(path, content, commit_message)
        return f"❌ GitHub error ({e.status}): {e.data.get('message', str(e))}"


def list_files(folder_path: str = "") -> str:
    """List all files and folders at the given path. Empty string = repo root."""
    try:
        contents = _repo.get_contents(folder_path)
        if not contents:
            return f"📂 '{folder_path or 'root'}' is empty."
        lines = [f"  {'📁' if item.type == 'dir' else '📄'} {item.path}" for item in contents]
        return f"📂 '{folder_path or 'root'}':\n" + "\n".join(lines)
    except GithubException as e:
        return f"❌ Cannot list '{folder_path}': {e.data.get('message', str(e))}"


def create_branch(branch_name: str) -> str:
    """Create a new branch off main, falling back to master."""
    source = None
    for base in ("main", "master"):
        try:
            source = _repo.get_branch(base)
            break
        except GithubException:
            continue

    if not source:
        return "❌ Could not find 'main' or 'master' to branch from."

    try:
        _repo.create_git_ref(f"refs/heads/{branch_name}", source.commit.sha)
        return f"✅ Branch '{branch_name}' created from '{source.name}'"
    except GithubException as e:
        if e.status == 422:
            return f"❌ Branch '{branch_name}' already exists."
        return f"❌ GitHub error ({e.status}): {e.data.get('message', str(e))}"