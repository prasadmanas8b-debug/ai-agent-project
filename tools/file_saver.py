"""
tools/file_saver.py — Member 3 owns this file
AI Agent Project | Phase 1

Provides save_report() — called by research_agent.py to save the final report.
Saves reports to the outputs/ folder as markdown files.
"""

import os
import re
from datetime import datetime


# ── Main function used by research_agent.py ──────────────────────────────────
def save_report(topic: str, content: str, output_dir: str = "outputs") -> str:
    """
    Save a research report to the outputs/ folder as a markdown file.

    Args:
        topic      (str): The research topic (used to name the file).
        content    (str): The full report content (markdown text).
        output_dir (str): Folder to save in. Default is 'outputs/'.

    Returns:
        str: The full path to the saved file.

    Example:
        path = save_report("LangChain agents", "## Summary\n...")
        print(f"Saved to: {path}")
    """
    # ── Create outputs/ folder if it doesn't exist ───────────────────────────
    os.makedirs(output_dir, exist_ok=True)

    # ── Build a clean filename from the topic ────────────────────────────────
    safe_name = _make_safe_filename(topic)
    filename  = f"report_{safe_name}.md"
    filepath  = os.path.join(output_dir, filename)

    # ── Build the full markdown file content ─────────────────────────────────
    timestamp   = datetime.now().strftime("%Y-%m-%d %H:%M")
    full_content = _build_markdown(topic, content, timestamp)

    # ── Write to file ────────────────────────────────────────────────────────
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
        list of str: filenames like ['report_langchain_agents.md', ...]
    """
    if not os.path.exists(output_dir):
        return []

    files = [
        f for f in os.listdir(output_dir)
        if f.startswith("report_") and (f.endswith(".md") or f.endswith(".txt"))
    ]
    return sorted(files)


# ── Helper: make a safe filename ──────────────────────────────────────────────
def _make_safe_filename(topic: str) -> str:
    """
    Converts a topic string into a safe filename.
    Example: "LangChain agents & tools" → "langchain_agents__tools"
    """
    safe = topic.lower()
    safe = re.sub(r"[^\w\s-]", "", safe)     # remove special chars
    safe = re.sub(r"[\s-]+",   "_", safe)    # spaces → underscores
    safe = safe.strip("_")
    return safe[:60]                          # max 60 chars


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
    print("Testing file_saver.py...\n")

    # Save a dummy report
    test_path = save_report(
        topic   = "LangChain agents",
        content = "## Overview\n\nLangChain is a framework for building LLM apps.\n\n## Key Points\n- Supports agents\n- Works with many LLMs\n"
    )

    print(f"\n✅ Saved to: {test_path}")
    print(f"\n📂 All saved reports: {list_reports()}")
