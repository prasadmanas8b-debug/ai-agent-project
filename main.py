"""
main.py — Phase 3 Pipeline Runner
AI Agent Project | Root folder

Phase 3 upgrade: The hardcoded pipeline from Phase 2 is replaced with
a LangGraph-powered graph. One line to run everything.

Phase 2 (hardcoded):
    research_notes = run_research_agent(topic)
    final_report   = run_writer_agent(research_notes, topic)

Phase 3 (graph-driven):
    result = graph.invoke({"task": user_input, ...})

The graph handles:
  - Which agents to run (and in what order)
  - Passing data between agents via shared state
  - Deciding when the task is done (FINISH)
  - Routing different task types to different agents

How to run:
    python main.py

Supported task types:
  "Research the history of AI"                        → Research + Write
  "List files in the agents folder"                   → GitHub only
  "Research quantum computing and save to GitHub"     → Research + Write + GitHub
  "Create a branch called feature/phase-4"            → GitHub only
"""

import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv()

from graph.pipeline_graph import build_graph

# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":

    print("\n╔════════════════════════════════════════════════════╗")
    print("║   AI Agent Pipeline — Phase 3                      ║")
    print("║   Powered by LangGraph + Groq + Tavily             ║")
    print("╠════════════════════════════════════════════════════╣")
    print("║  Examples:                                         ║")
    print("║  • Research the history of the internet            ║")
    print("║  • List files in the agents folder                 ║")
    print("║  • Research AI in healthcare and save to GitHub    ║")
    print("║  • Create a branch called feature/phase-4          ║")
    print("╚════════════════════════════════════════════════════╝\n")

    user_input = input("What do you want to do? ").strip()

    if not user_input:
        print("No input entered. Exiting.")
        sys.exit(0)

    # ── Build the graph ───────────────────────────────────────────────────
    graph = build_graph()

    # ── Initial state — all agent fields start empty ──────────────────────
    # The Supervisor reads the task and fills "next" to kick things off.
    initial_state = {
        "task":           user_input,
        "research_notes": "",
        "final_report":   "",
        "github_result":  "",
        "next":           "",
    }

    print(f"\n{'='*55}")
    print(f"  PIPELINE STARTED")
    print(f"  Task: {user_input}")
    print(f"{'='*55}\n")

    # ── Run the graph ─────────────────────────────────────────────────────
    # graph.invoke() runs the full pipeline — Supervisor decides everything
    try:
        result = graph.invoke(initial_state)
    except Exception as e:
        print(f"\n❌ Pipeline error: {e}")
        sys.exit(1)

    # ── Display results ───────────────────────────────────────────────────
    print(f"\n{'='*55}")
    print("  PIPELINE COMPLETE — RESULTS")
    print(f"{'='*55}\n")

    if result.get("research_notes"):
        print(f"📚 Research:   ✅ Collected ({len(result['research_notes'])} chars)")

    if result.get("final_report"):
        print(f"📝 Report:     ✅ Written ({len(result['final_report'])} chars)")
        print(f"\n--- REPORT PREVIEW (first 800 chars) ---\n")
        print(result["final_report"][:800])
        print("\n[Full report saved in outputs/ folder]")

    if result.get("github_result"):
        print(f"\n🐙 GitHub:     {result['github_result']}")

    if not any([result.get("research_notes"), result.get("final_report"), result.get("github_result")]):
        print("⚠️  No output was generated. Check the logs above for errors.")
