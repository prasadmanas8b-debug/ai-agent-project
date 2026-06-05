"""
tools/file_saver.py — Member 3 owns this file
AI Agent Project | Phase 1 + Phase 2 update

Provides:
  save_report()    — Phase 1: saves report from research_agent (topic-based naming)
  save_to_file()   — Phase 2 new: saves any content with a custom filename
  save_report_txt()— saves as plain .txt backup
  list_reports()   — lists all saved reports in outputs/

Phase 2 change: Added save_to_file() with filename + folder parameters
so each agent can name its output file independently.
"""
import os
import re
from datetime import datetime


# ══════════════════════════════════════════════════════════════════════════════
# Phase 2 — NEW FUNCTION: save_to_file()
# Added in Phase 2 so Writer Agent can save with a custom filename.
# Used by: writer_agent.py
# ══════════════════════════════════════════════════════════════════════════════
def save_to_file(content: str, filename: str = "output.txt", folder: str = "outputs") -> str:
    """
    Saves content to a file inside the outputs/ folder.
    Creates the folder if it doesn't exist.
    Returns the full filepath.

    This is the Phase 2 upgrade — a general-purpose saver that accepts
    any filename. Agents use this to name their outputs meaningfully.

    Args:
        content  (str): The text content to write to the file.
        filename (str): The filename to use. Default: "output.txt"
                        Example: "final_report_quantum_computing.md"
        folder   (str): Subfolder inside the project to save in. Default: "outputs"

    Returns:
        str: The full path to the saved file.

    Examples:
        save_to_file("# My Report\n...", "final_report_ai.md")
        save_to_file("raw notes here", "research_notes_ai.txt")
    """
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[File Saver] Saved to: {filepath}")
    return filepath


# ══════════════════════════════════════════════════════════════════════════════
# Phase 1 — EXISTING FUNCTION: save_report()
# Used by: research_agent.py (unchanged from Phase 1)
# ══════════════════════════════════════════════════════════════════════════════
def save_report(topic: str, content: str, output_dir: str = "outputs") -> str:
    """
    Save a research report to the outputs/ folder as a markdown file.
    (Phase 1 function — unchanged)

    Args:
        topic      (str): The research topic (used to name the file).
        content    (str): The full report content (markdown text).
        output_dir (str): Folder to save in. Default is 'outputs/'.

    Returns:
        str: The full path to the saved file.
    """
    os.makedirs(output_dir, exist_ok=True)

    safe_name = _make_safe_filename(topic)
    filename  = f"report_{safe_name}.md"
    filepath  = os.path.join(output_dir, filename)

    timestamp    = datetime.now().strftime("%Y-%m-%d %H:%M")
    full_content = _build_markdown(topic, content, timestamp)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(full_content)

    print(f"💾  Report saved → {filepath}")
    return filepath


# ── Bonus: save as plain text ─────────────────────────────────────────────────
def save_report_txt(topic: str, content: str, output_dir: str = "outputs") -> str:
    """
    Save the report as a plain .txt file instead of markdown.
    Useful as a backup format.
    """
    os.makedirs(output_dir, exist_ok=True)
    safe_name = _make_safe_filename(topic)
    filepath  = os.path.join(output_dir, f"report_{safe_name}.txt")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"Research Report: {topic}\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write("=" * 60 + "\n\n")
        f.write(content)

    print(f"💾  TXT report saved → {filepath}")
    return filepath


# ── List all saved reports ────────────────────────────────────────────────────
def list_reports(output_dir: str = "outputs") -> list[str]:
    """
    Returns a list of all saved report filenames in the outputs/ folder.

    Returns:
        list of str: filenames like ['report_langchain_agents.md',
                                      'final_report_langchain_agents.md']
    """
    if not os.path.exists(output_dir):
        return []
    files = [
        f for f in os.listdir(output_dir)
        if (f.startswith("report_") or f.startswith("final_report_")) and
           (f.endswith(".md") or f.endswith(".txt"))
    ]
    return sorted(files)


# ── Helper: make a safe filename ──────────────────────────────────────────────
def _make_safe_filename(topic: str) -> str:
    """
    Converts a topic string into a safe filename.
    Example: "LangChain agents & tools" → "langchain_agents__tools"
    """
    safe = topic.lower()
    safe = re.sub(r"[^\w\s-]", "", safe)
    safe = re.sub(r"[\s-]+",   "_", safe)
    safe = safe.strip("_")
    return safe[:60]


# ── Helper: build the full markdown report ────────────────────────────────────
def _build_markdown(topic: str, content: str, timestamp: str) -> str:
    """
    Wraps the content in a clean markdown document with a header and footer.
    """
    return f"""# Research Report: {topic}

> **Generated:** {timestamp}  
> **Powered by:** AI Research Agent (Groq + Tavily)

---

{content}

---
*Report generated automatically by AI Research Agent — Phase 1*
"""


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing file_saver.py (Phase 2 version)...\n")

    # Test Phase 2 new function
    path1 = save_to_file(
        content="## Final Report\n\nThis is a test final report.",
        filename="final_report_test_topic.md"
    )
    print(f"✅ save_to_file → {path1}")

    # Test Phase 1 original function
    path2 = save_report(
        topic   = "LangChain agents",
        content = "## Overview\n\nLangChain is a framework for LLM apps.\n"
    )
    print(f"✅ save_report → {path2}")

    print(f"\n📂 All saved reports: {list_reports()}")
