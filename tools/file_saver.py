"""
tools/file_saver.py — Local file save utilities.

Saves text content to the outputs/ directory and provides a
listing helper for previously saved reports.
"""

import os
import re
from datetime import datetime


OUTPUTS_DIR = "outputs"


def _ensure_outputs_dir() -> None:
    """Create outputs/ if it doesn't exist (handles git artifact edge case)."""
    if os.path.isfile(OUTPUTS_DIR):
        os.remove(OUTPUTS_DIR)
    os.makedirs(OUTPUTS_DIR, exist_ok=True)


def save_report(topic: str, content: str, extension: str = "md") -> str:
    """
    Save content to outputs/<safe_topic>.<extension>.

    Args:
        topic:     Used to build the filename.
        content:   Text content to write.
        extension: File extension (default 'md').

    Returns:
        The path of the saved file.
    """
    _ensure_outputs_dir()
    safe  = re.sub(r"[^\w\s]", "", topic.lower()).strip().replace(" ", "_")[:50]
    ts    = datetime.now().strftime("%Y%m%d_%H%M%S")
    path  = os.path.join(OUTPUTS_DIR, f"report_{safe}_{ts}.{extension}")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def list_reports() -> list[str]:
    """Return a sorted list of file paths inside outputs/."""
    _ensure_outputs_dir()
    return sorted(
        os.path.join(OUTPUTS_DIR, f)
        for f in os.listdir(OUTPUTS_DIR)
        if not f.startswith(".")
    )
