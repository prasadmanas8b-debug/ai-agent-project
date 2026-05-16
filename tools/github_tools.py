import os
from github import Github, GithubException
from dotenv import load_dotenv

load_dotenv()

def _get_repo():
    """Initialize and return the GitHub repo object."""
    token = os.getenv("GITHUB_TOKEN")
    repo_name = os.getenv("GITHUB_REPO")

    if not token:
        raise ValueError("GITHUB_TOKEN not found in .env file.")
    if not repo_name:
        raise ValueError("GITHUB_REPO not found in .env file.")

    g = Github(token)
    return g.get_repo(repo_name)


def create_file(path: str, content: str, commit_message: str) -> str:
    """
    Creates a new file in the GitHub repository.

    Args:
        path: File path in the repo (e.g., 'docs/report.md')
        content: File content as a string
        commit_message: Commit message for this action

    Returns:
        Success or error message string
    """
    try:
        repo = _get_repo()
        repo.create_file(path, commit_message, content)
        return f"✅ File '{path}' created successfully with commit: '{commit_message}'"
    except GithubException as e:
        if e.status == 422:
            return f"❌ File '{path}' already exists. Use update_file() instead."
        return f"❌ GitHub error while creating '{path}': {e.data.get('message', str(e))}"
    except Exception as e:
        return f"❌ Unexpected error while creating file: {str(e)}"


def update_file(path: str, content: str, commit_message: str) -> str:
    """
    Updates an existing file in the GitHub repository.

    Args:
        path: File path in the repo (e.g., 'docs/report.md')
        content: New file content as a string
        commit_message: Commit message for this action

    Returns:
        Success or error message string
    """
    try:
        repo = _get_repo()
        existing_file = repo.get_contents(path)
        repo.update_file(
            path,
            commit_message,
            content,
            existing_file.sha
        )
        return f"✅ File '{path}' updated successfully with commit: '{commit_message}'"
    except GithubException as e:
        if e.status == 404:
            return f"❌ File '{path}' not found. Use create_file() instead."
        return f"❌ GitHub error while updating '{path}': {e.data.get('message', str(e))}"
    except Exception as e:
        return f"❌ Unexpected error while updating file: {str(e)}"


def create_or_update_file(path: str, content: str, commit_message: str) -> str:
    """
    Smart upsert — creates the file if it doesn't exist, updates it if it does.

    Args:
        path: File path in the repo
        content: File content as a string
        commit_message: Commit message

    Returns:
        Success or error message string
    """
    try:
        repo = _get_repo()
        try:
            existing_file = repo.get_contents(path)
            repo.update_file(path, commit_message, content, existing_file.sha)
            return f"✅ File '{path}' updated successfully with commit: '{commit_message}'"
        except GithubException as e:
            if e.status == 404:
                repo.create_file(path, commit_message, content)
                return f"✅ File '{path}' created successfully with commit: '{commit_message}'"
            raise
    except GithubException as e:
        return f"❌ GitHub error during upsert for '{path}': {e.data.get('message', str(e))}"
    except Exception as e:
        return f"❌ Unexpected error during upsert: {str(e)}"


def list_files(folder_path: str = "") -> str:
    """
    Lists all files in a given folder of the repository.

    Args:
        folder_path: Folder path in the repo (e.g., 'agents'). Leave empty for root.

    Returns:
        A formatted string listing all files, or an error message
    """
    try:
        repo = _get_repo()
        contents = repo.get_contents(folder_path)

        if not contents:
            return f"📂 Folder '{folder_path}' is empty."

        file_list = []
        for item in contents:
            icon = "📄" if item.type == "file" else "📁"
            file_list.append(f"  {icon} {item.name}  ({item.type})")

        folder_label = folder_path if folder_path else "root"
        result = f"📂 Files in '{folder_label}':\n" + "\n".join(file_list)
        return result

    except GithubException as e:
        if e.status == 404:
            return f"❌ Folder '{folder_path}' not found in the repository."
        return f"❌ GitHub error while listing files: {e.data.get('message', str(e))}"
    except Exception as e:
        return f"❌ Unexpected error while listing files: {str(e)}"


def create_branch(branch_name: str, source_branch: str = "main") -> str:
    """
    Creates a new branch from the source branch (default: main).

    Args:
        branch_name: Name for the new branch
        source_branch: Branch to create from (default 'main')

    Returns:
        Success or error message string
    """
    try:
        repo = _get_repo()
        source_ref = repo.get_branch(source_branch)
        repo.create_git_ref(
            ref=f"refs/heads/{branch_name}",
            sha=source_ref.commit.sha
        )
        return f"✅ Branch '{branch_name}' created from '{source_branch}' successfully."
    except GithubException as e:
        if e.status == 422:
            return f"❌ Branch '{branch_name}' already exists."
        if e.status == 404:
            return f"❌ Source branch '{source_branch}' not found."
        return f"❌ GitHub error while creating branch: {e.data.get('message', str(e))}"
    except Exception as e:
        return f"❌ Unexpected error while creating branch: {str(e)}"


def read_file(path: str) -> str:
    """
    Reads and returns the content of a file from the repository.

    Args:
        path: File path in the repo (e.g., 'README.md')

    Returns:
        File content string, or an error message
    """
    try:
        repo = _get_repo()
        file_content = repo.get_contents(path)
        decoded = file_content.decoded_content.decode("utf-8")
        return f"📄 Content of '{path}':\n\n{decoded}"
    except GithubException as e:
        if e.status == 404:
            return f"❌ File '{path}' not found in the repository."
        return f"❌ GitHub error while reading '{path}': {e.data.get('message', str(e))}"
    except Exception as e:
        return f"❌ Unexpected error while reading file: {str(e)}"


def delete_file(path: str, commit_message: str) -> str:
    """
    Deletes a file from the repository.

    Args:
        path: File path in the repo
        commit_message: Commit message for this deletion

    Returns:
        Success or error message string
    """
    try:
        repo = _get_repo()
        file_content = repo.get_contents(path)
        repo.delete_file(path, commit_message, file_content.sha)
        return f"✅ File '{path}' deleted successfully with commit: '{commit_message}'"
    except GithubException as e:
        if e.status == 404:
            return f"❌ File '{path}' not found. Cannot delete."
        return f"❌ GitHub error while deleting '{path}': {e.data.get('message', str(e))}"
    except Exception as e:
        return f"❌ Unexpected error while deleting file: {str(e)}"