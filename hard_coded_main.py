# main.py
# This is the pipeline runner — the file YOU run every time

from agents.research_agent import run_research_agent
# imports your Phase 1 research agent function

from agents.writer_agent2 import run_writer_agent
# imports the new writer agent function

def run_pipeline(topic: str) -> str:
    # topic  → the subject the user wants to research
    # -> str → returns the final report text

    print(f"\n{'='*50}")
    print(f"  PIPELINE STARTED")
    print(f"  Topic: {topic}")
    print(f"{'='*50}\n")
    # just visual separators so terminal output is readable

   # ── STAGE 1: RESEARCH ─────────────────────────────────────
    print("[ STAGE 1 ] 🔍 Research Agent starting...\n")

    research_result = run_research_agent(topic)
    research_notes = research_result["report"]

    # ── CLEAN STEP 1: Remove LangChain debug errors ───────────
    import re
    research_notes = re.sub(r'Invalid Format:.*?(?=##|\Z)', '', research_notes, flags=re.DOTALL)

    # ── CLEAN STEP 2: Remove duplicate lines ──────────────────
    lines = research_notes.split('\n')
    seen = []
    cleaned_lines = []
    for line in lines:
        if line.strip() not in seen or line.strip() == '':
            cleaned_lines.append(line)
            seen.append(line.strip())
    research_notes = '\n'.join(cleaned_lines)

    # ── CLEAN STEP 3: Final trim ───────────────────────────────
    research_notes = research_notes.strip()

# ── SAFETY CHECK ──────────────────────────────────────────
# Also catch cases where agent returned an error message instead of research
    failed_keywords = ["iteration limit", "time limit", "agent stopped", "no report"]
    if not research_notes or any(kw in research_notes.lower() for kw in failed_keywords):
        print("[ PIPELINE ] ❌ Research agent did not complete. Try again.")
        return ""
    print(f"[ STAGE 1 ] 📁 Research saved to: {research_result['saved_to']}")
    print("\n[ STAGE 1 ] ✅ Research complete.\n")
    print("-" * 50)
        # ── STAGE 2: WRITE ────────────────────────────────────────
    print("\n[ STAGE 2 ] ✍️  Writer Agent starting...\n")

    final_report = run_writer_agent(
        research_notes=research_notes,
        # passes the output of stage 1 directly into stage 2
        # this is the pipeline connection — output of A → input of B

        topic=topic
        # also pass the topic so writer can name the file correctly
    )

    print("\n[ STAGE 2 ] ✅ Report written.\n")
    print("=" * 50)
    print("  PIPELINE COMPLETE ✅")
    print("=" * 50)

    return final_report

# ── ENTRY POINT ───────────────────────────────────────────────
if __name__ == "__main__":
    # this block only runs when YOU run: python main.py
    # it does NOT run when another file imports main.py
    # this is standard Python — always use this pattern

    topic = input("\nEnter a topic to research: ").strip()
    # input() → waits for you to type something and press Enter
    # .strip() → removes accidental spaces

    if topic:
        report = run_pipeline(topic)
        
        print("\n--- REPORT PREVIEW (first 800 chars) ---\n")
        print(report[:800])
        # [:800] → prints first 800 characters as a preview
        # full report is saved in outputs/ folder

        print(f"\n📁 Research notes → outputs/report_{topic.strip().lower().replace(' ', '_')[:60]}.md")
        print(f"📄 Final report   → outputs/final_report_{topic.strip().lower().replace(' ', '_')[:60]}.md")
        print("\n✅ Both files saved in outputs/ folder")
    else:
        print("No topic entered. Please try again.")