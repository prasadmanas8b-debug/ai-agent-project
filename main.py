"""
main.py  --  Entry point for the AI Agent System.
Agents: Research -> Writer -> Coder -> GitHub  (orchestrated by Supervisor)
"""
from graph.pipeline_graph import build_graph

def main():
    graph = build_graph()

    print("\n" + "="*56)
    print("  AI Agent System  --  Research . Write . Code . Act")
    print("="*56)
    print("Try:")
    print("  Research quantum computing")
    print("  Implement a binary search in Python")
    print("  Research neural networks and write code for it")
    print("  Research AI trends and save to GitHub")
    print("  List files in agents folder")
    print("="*56 + "\n")

    user_input = input("What do you want to do? ").strip()
    if not user_input:
        print("No input. Exiting.")
        return

    initial_state = {
        "task":           user_input,
        "research_notes": "",
        "final_report":   "",
        "code_result":    "",
        "github_result":  "",
        "next":           "",
    }

    print("\n[System] Starting graph...\n")
    result = graph.invoke(initial_state)

    print("\n" + "="*56)
    print("  DONE")
    print("="*56)

    if result.get("final_report"):
        print("\n--- Report Preview ---")
        print(result["final_report"][:800])

    if result.get("code_result"):
        print(f"\n--- Code Agent ---\n{result['code_result']}")

    if result.get("github_result"):
        print(f"\n--- GitHub ---\n{result['github_result']}")

if __name__ == "__main__":
    main()
