"""
main.py — Phase 2 Pipeline Runner
AI Agent Project | Root folder

This file connects the Research Agent and Writer Agent into a sequential pipeline.

Pipeline:
    User types a topic
         ↓
    [ Stage 1 ] research_agent.py  →  searches web → returns research_notes
         ↓  (output of Stage 1 becomes input of Stage 2)
    [ Stage 2 ] writer_agent.py    →  rewrites notes → saves final_report_{topic}.md
         ↓
    outputs/
      report_{topic}.md            ←  raw research    (Research Agent)
      final_report_{topic}.md      ←  polished report (Writer Agent)

How to run:
    python main.py

Key concepts demonstrated:
    - Sequential pipeline: Agent A output → Agent B input
    - Input validation: never pass raw/dirty output between agents
    - Graceful failure: bad input stops the pipeline cleanly, no crash
    - Separation of concerns: each agent does exactly one job
"""

import re
import sys
import os

# Fix import path — must be run from project root
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, PROJECT_ROOT)

from agents.research_agent import run_research_agent
from agents.writer_agent   import run_writer_agent


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: INPUT CLEANING
# Never blindly pass research agent output to the writer.
# Always clean and validate first.
# ─────────────────────────────────────────────────────────────────────────────
def _clean_research_notes(raw: str) -> str:
    """
    Cleans raw output from the Research Agent before passing to Writer Agent.

    Problems this solves:
      1. LangChain sometimes appends internal debug text ("Invalid Format:...")
      2. The agent occasionally duplicates lines when searching multiple times
      3. Error messages ("agent stopped due to iteration limit") must be caught

    Args:
        raw (str): Raw string output from research_agent.

    Returns:
        str: Cleaned string, or empty string if it looks like an error.
    """
    # Step 1: Remove LangChain internal debug / error text
    # re.DOTALL makes . match newlines too, so multi-line blocks are caught
    cleaned = re.sub(r'Invalid Format:.*?(?=##|\Z)', '', raw, flags=re.DOTALL)
    cleaned = re.sub(r'Agent stopped.*?(?=##|\Z)', '', cleaned, flags=re.DOTALL)

    # Step 2: Remove duplicate lines (agent sometimes repeats search results)
    lines = cleaned.split('\n')
    seen, deduped = set(), []
    for line in lines:
        key = line.strip()
        if key not in seen or key == '':
            deduped.append(line)
            seen.add(key)
    cleaned = '\n'.join(deduped)

    # Step 3: Safety check — if the output is actually an agent failure message,
    # return empty string so the pipeline stops cleanly
    failed_keywords = ['iteration limit', 'time limit', 'agent stopped', 'could not complete']
    if any(kw in cleaned.lower() for kw in failed_keywords):
        print("[Pipeline] ⚠️  Research notes contain agent failure message. Stopping pipeline.")
        return ''

    return cleaned.strip()


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2: MAIN PIPELINE — run_pipeline()
# ─────────────────────────────────────────────────────────────────────────────
def run_pipeline(topic: str) -> str:
    """
    Full sequential pipeline: Research → Clean → Write → Save

    Stage 1: Research Agent searches the web and collects raw notes.
    Stage 2: Writer Agent reads those notes and produces a polished report.

    Args:
        topic (str): The research topic entered by the user.

    Returns:
        str: The final polished report as a markdown string.
             Empty string if pipeline failed at any stage.
    """
    print(f"\n{'='*55}")
    print(f"  PIPELINE STARTED")
    print(f"  Topic: {topic}")
    print(f"{'='*55}\n")

    # ── STAGE 1: RESEARCH ─────────────────────────────────────────────────
    print("[ STAGE 1 ] Running Research Agent...\n")

    # research_agent returns a dict: {topic, report, saved_to}
    research_result = run_research_agent(topic)

    # Extract the report string from the dict
    # (Lesson learned: research_agent returns dict, not raw string)
    if isinstance(research_result, dict):
        raw_notes = research_result.get("report", "")
    else:
        raw_notes = str(research_result)  # fallback if it ever returns a string

    # Validate: did we get anything?
    if not raw_notes:
        print("[ PIPELINE ] ❌ Research Agent returned nothing. Stopping.")
        return ""

    print("\n[ STAGE 1 ] ✅ Research complete.\n")
    print("-" * 55)

    # ── CLEAN: Sanitise research notes before passing to writer ───────────
    print("\n[ PIPELINE ] Cleaning research notes...")
    research_notes = _clean_research_notes(raw_notes)

    if not research_notes:
        print("[ PIPELINE ] ❌ Research notes were empty after cleaning. Stopping.")
        return ""

    print(f"[ PIPELINE ] Notes ready — {len(research_notes)} characters.\n")
    print("-" * 55)

    # ── STAGE 2: WRITE ────────────────────────────────────────────────────
    print("\n[ STAGE 2 ] Running Writer Agent...\n")

    final_report = run_writer_agent(
        research_notes=research_notes,
        topic=topic
    )

    # Check if writer returned an error string instead of a real report
    if final_report.startswith("Error:"):
        print(f"[ PIPELINE ] ❌ Writer Agent failed: {final_report}")
        return ""

    print("\n[ STAGE 2 ] ✅ Report written.\n")
    print("=" * 55)
    print("  PIPELINE COMPLETE")
    print("  Two files saved in outputs/:")
    print(f"    report_{{topic}}.md       ← raw research notes")
    print(f"    final_report_{{topic}}.md ← polished final report")
    print("=" * 55)

    return final_report


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3: ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":

    print("\n╔═══════════════════════════════════════╗")
    print("║  AI Research Pipeline — Phase 2       ║")
    print("║  Research Agent → Writer Agent        ║")
    print("╚═══════════════════════════════════════╝")

    topic = input("\nEnter a topic to research: ").strip()

    if not topic:
        print("No topic entered. Exiting.")
        sys.exit(0)

    report = run_pipeline(topic)

    if report:
        print("\n--- FINAL REPORT PREVIEW (first 1000 chars) ---\n")
        print(report[:1000])
        print("\n[Full report saved in outputs/ folder]")
    else:
        print("\n[ PIPELINE ] No report was generated. Check the logs above for errors.")
