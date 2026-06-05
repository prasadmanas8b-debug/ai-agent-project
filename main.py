"""
main.py — AI Agent System (Research · Writer · GitHub)

Usage:
    python main.py
"""

import os
import json
from graph.pipeline_graph import build_graph


def _ensure_outputs_dir() -> None:
    if os.path.isfile("outputs"):
        os.remove("outputs")
    os.makedirs("outputs", exist_ok=True)


def _print_banner() -> None:
    line = "=" * 60
    print(f"\n{line}")
    print("  AI Agent System — Research · Writer · GitHub")
    print(line)
    print()
    print("Example tasks:")
    print("  Research quantum computing")
    print("  Research AI trends and save to GitHub")
    print("  List files in the agents folder")
    print("  Write a report on machine learning")
    print(f"{line}\n")


def _build_state(task: str) -> dict:
    return {
        "task":           task,
        "next":           "",
        "research_notes": "",
        "final_report":   "",
        "github_result":  "",
    }


def _print_results(result: dict) -> None:
    sep = "=" * 60
    print(f"\n{sep}\n  DONE\n{sep}")

    if result.get("final_report"):
        print("\n--- Report (first 800 chars) ---")
        print(result["final_report"][:800])
        # Save full report
        os.makedirs("outputs", exist_ok=True)
        slug = result["task"][:40].replace(" ", "_").lower()
        path = f"outputs/report_{slug}.md"
        with open(path, "w", encoding="utf-8") as f:
            f.write(result["final_report"])
        print(f"\n  Full report saved → {path}")

    if result.get("github_result"):
        print(f"\n--- GitHub ---\n{result['github_result']}")

    if result.get("research_notes") and not result.get("final_report"):
        print("\n--- Research Notes (first 500 chars) ---")
        print(result["research_notes"][:500])


def main() -> None:
    _ensure_outputs_dir()
    _print_banner()

    try:
        graph = build_graph()
    except Exception as exc:
        print(f"\n[FATAL] Could not build graph: {exc}")
        raise

    print("Type your task and press Enter. Type 'exit' to quit.\n")

    while True:
        try:
            task = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not task:
            continue
        if task.lower() in ("exit", "quit", "q"):
            print("Goodbye!")
            break

        state = _build_state(task)
        print("\nProcessing...\n")

        try:
            result = graph.invoke(state)
            _print_results(result)
        except Exception as exc:
            print(f"\n[ERROR] {exc}")
            import traceback
            traceback.print_exc()
        print()


if __name__ == "__main__":
    main()
