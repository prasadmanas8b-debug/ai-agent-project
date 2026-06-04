"""
tools/text_utils.py — Shared text processing utilities.

Consolidates duplicated helpers that were scattered across agents:
  - _strip_fences (duplicated in github_agent.py, coder_agent.py)
  - _make_slug    (duplicated in writer_agent.py, coder_agent.py)
  - _safe_path    (github_tools.py — improved with traversal prevention)
  - truncate_context (new — smart context truncation for token optimization)
  - summarize_for_context (new — compress long text for downstream agents)

Usage:
    from tools.text_utils import strip_fences, make_slug, safe_github_path
"""

from __future__ import annotations

import os
import re
import unicodedata


# ── Code / Markdown fences ────────────────────────────────────────────────────

def strip_fences(text: str) -> str:
    """
    Remove markdown code fences from LLM output.

    Handles:
        ```python
        code here
        ```
        or just
        ```
        code here
        ```

    Returns clean code/text without surrounding fences.
    """
    text = text.strip()
    # Remove opening fence (with optional language tag)
    text = re.sub(r"^```[a-zA-Z0-9_\-]*\s*\n?", "", text, count=1)
    # Remove closing fence
    text = re.sub(r"\n?```\s*$", "", text, count=1)
    return text.strip()


# ── Slug generation ───────────────────────────────────────────────────────────

def make_slug(text: str, max_length: int = 50) -> str:
    """
    Convert arbitrary text to a safe filename slug.

    Steps:
        1. Normalize unicode (NFKD)
        2. Remove non-ASCII characters
        3. Lowercase
        4. Remove non-word characters
        5. Collapse whitespace to underscores
        6. Strip leading/trailing underscores BEFORE truncating
        7. Truncate to max_length

    Examples:
        "Write a Binary Search Algorithm" → "write_a_binary_search_algorithm"
        "Résumé.pdf" → "resume_pdf"
        "What is AI???" → "what_is_ai"
    """
    # Normalize unicode
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    # Remove non-alphanumeric (keep spaces and underscores)
    text = re.sub(r"[^\w\s]", "", text)
    # Collapse whitespace to single underscore
    text = re.sub(r"\s+", "_", text.strip())
    # Remove leading/trailing underscores
    text = text.strip("_")
    # Truncate (after stripping, so we don't end with a trailing _)
    text = text[:max_length].rstrip("_")
    return text or "task"


# ── Path safety ───────────────────────────────────────────────────────────────

def safe_github_path(path: str, output_folder: str = "git_agent_output") -> str:
    """
    Enforce that a path lives inside the allowed output folder.

    Security improvements over the original _safe_path:
        - Explicitly rejects paths containing '..' (path traversal)
        - Rejects paths starting with '/' (absolute path injection)
        - Rejects filenames starting with '.' (hidden file injection)
        - Logs a warning when the path is silently redirected

    Args:
        path:          Input path (may be raw LLM output).
        output_folder: The allowed output folder (default: git_agent_output).

    Returns:
        A safe path guaranteed to be inside output_folder.

    Raises:
        ValueError: If the path contains a traversal attempt.
    """
    # Block path traversal attempts
    if ".." in path:
        raise ValueError(f"Path traversal attempt blocked: '{path}'")

    # Block absolute paths
    if path.startswith("/") or (len(path) > 1 and path[1] == ":"):
        raise ValueError(f"Absolute path blocked: '{path}'")

    path = path.strip("/").strip()
    filename = os.path.basename(path) if "/" in path else path

    # Block empty or hidden filenames
    if not filename or filename.startswith("."):
        filename = "output.md"

    # Block filenames with suspicious characters
    filename = re.sub(r"[^\w\-.]", "_", filename)

    result = f"{output_folder}/{filename}"
    if result != f"{output_folder}/{os.path.basename(path)}" and path:
        import logging
        logging.getLogger(__name__).warning(
            "[text_utils] Path redirected: '%s' → '%s'", path, result
        )

    return result


# ── Context management ────────────────────────────────────────────────────────

def truncate_context(text: str, max_chars: int = 4000, keep_start: float = 0.7) -> str:
    """
    Intelligently truncate a long text for use as context in LLM prompts.

    Keeps `keep_start` fraction from the beginning and fills the remainder
    from the end, separated by a truncation notice.

    Args:
        text:       The text to truncate.
        max_chars:  Maximum character count in the output.
        keep_start: Fraction of max_chars to allocate to the start of the text.

    Returns:
        Truncated text with a notice if truncation occurred.
    """
    if len(text) <= max_chars:
        return text

    start_chars = int(max_chars * keep_start)
    end_chars   = max_chars - start_chars - 60  # 60 chars for the notice

    if end_chars <= 0:
        return text[:max_chars]

    start_part = text[:start_chars]
    end_part   = text[-end_chars:] if end_chars > 0 else ""
    omitted    = len(text) - start_chars - end_chars

    return (
        f"{start_part}\n\n"
        f"[... {omitted:,} characters omitted for context ...]\n\n"
        f"{end_part}"
    )


def extract_json_block(text: str) -> str:
    """
    Extract the first JSON object or array from a string that may contain
    surrounding text or markdown fences.

    Useful when an LLM returns JSON embedded in an explanation.

    Returns the raw JSON string, or the original text if no JSON block found.
    """
    # Try to find a JSON object or array
    for pattern in [r"\{.*\}", r"\[.*\]"]:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            candidate = match.group(0)
            # Quick validation
            try:
                import json
                json.loads(candidate)
                return candidate
            except (ValueError, Exception):
                continue

    # Fallback: strip fences and return
    return strip_fences(text)


def sanitize_filename(filename: str, max_length: int = 100) -> str:
    """
    Sanitize a filename to be safe for all operating systems.

    Removes characters that are invalid on Windows/Mac/Linux.
    """
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", filename)
    # Collapse multiple underscores
    filename = re.sub(r"_+", "_", filename)
    # Strip leading/trailing dots and spaces (Windows issues)
    filename = filename.strip(". ")
    # Truncate
    name, _, ext = filename.rpartition(".")
    if ext and len(ext) <= 5:  # looks like a real extension
        max_name = max_length - len(ext) - 1
        return f"{name[:max_name]}.{ext}"
    return filename[:max_length]
