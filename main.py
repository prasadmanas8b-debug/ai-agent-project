"""
main.py — Entry point for the AI Agent System.
"""
from graph.pipeline_graph import build_graph

def main():
    graph = build_graph()

    print("\n" + "="*50)
    print("  AI Agent System")
    print("="*50)
    print("Examples:")
    print("  Research quantum computing")
    print("  List files in agents folder")
    print("  Research AI trends and save to GitHub")
    print("="*50 + "\n")

    user_input = input("What do you want to do? ").strip()
    if not user_input:
        print("No input. Exiting.")
        return

    initial_state = {
        "task":           user_input,
        "research_notes": "",
        "final_report":   "",
        "github_result":  "",
        "next":           "",
    }

    print("\n[System] Starting graph...\n")
    result = graph.invoke(initial_state)

    print("\n" + "="*50)
    print("  DONE")
    print("="*50)

    if result.get("final_report"):
        print(result["final_report"][:800])

    if result.get("github_result"):
        print(f"\n✅ GitHub: {result['github_result']}")

if __name__ == "__main__":
    main()
