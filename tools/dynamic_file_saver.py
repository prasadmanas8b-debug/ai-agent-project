"""
tools/dynamic_file_saver.py — Dynamic file save utility.

Saves arbitrary content with auto-detected file type based on content
or an explicit extension hint. Used by agents that produce mixed output
(markdown, JSON, CSV, Python, etc.).
"""

import os
import re
from datetime import datetime

OUTPUTS_DIR = "outputs"


def save_dynamic(content: str, name_hint: str = "output", ext: str = "txt") -> str:
    """
    Save content to outputs/<name_hint>_<timestamp>.<ext>.

    Args:
        content:   Content to write.
        name_hint: Human-friendly filename prefix.
        ext:       File extension (e.g. 'md', 'json', 'csv', 'py').

    Returns:
        Absolute path of the saved file.
    """
    if os.path.isfile(OUTPUTS_DIR):
        os.remove(OUTPUTS_DIR)
    os.makedirs(OUTPUTS_DIR, exist_ok=True)

    safe  = re.sub(r"[^\w]", "_", name_hint.lower())[:40].strip("_")
    ts    = datetime.now().strftime("%Y%m%d_%H%M%S")
    path  = os.path.join(OUTPUTS_DIR, f"{safe}_{ts}.{ext}")

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path
