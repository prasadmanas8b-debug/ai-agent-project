"""
main.py — Entry point for the AI Agent System.
Supports: research, writer, github, coder, email agents.
"""

from graph.pipeline_graph import build_graph, initial_state


def main():
    graph = build_graph()

    print("\n" + "=" * 60)
    print("  🤖 AI Agent System  |  5 Agents Ready")
    print("=" * 60)
    print("Examples:")
    print("  Research → 'Research quantum computing trends'")
    print("  Writer   → 'Write a blog post about LangGraph'")
    print("  GitHub   → 'List files in agents folder'")
    print("  Coder    → 'Write a Python function to reverse a string'")
    print("  Coder    → 'Debug this code: def add(a,b) return a+b'")
    print("  Email    → 'Draft an email asking my manager for a day off'")
    print("  Email    → 'Send email to john@example.com about project update'")
    print("=" * 60 + "\n")

    user_input = input("What do you want to do? ").strip()
    if not user_input:
        print("No input. Exiting.")
        return

    state = initial_state(user_input)

    print("\n[System] Starting graph...\n")
    result = graph.invoke(state)

    print("\n" + "=" * 60)
    print("  DONE")
    print("=" * 60)

    # Print whichever output was populated
    if result.get("code_result"):
        print("\n🖥️  CODER AGENT OUTPUT:")
        print(result["code_result"][:1200])
        if result.get("code_output"):
            print(f"\n📄 Full code saved to: outputs/generated_code.py")
            _save_output(result["code_output"], "outputs/generated_code.py")

    if result.get("email_result"):
        print("\n📧 EMAIL AGENT OUTPUT:")
        print(result["email_result"][:1200])
        if result.get("email_draft"):
            _save_output(result["email_draft"], "outputs/email_draft.txt")
            print(f"\n📄 Draft saved to: outputs/email_draft.txt")

    if result.get("final_report"):
        print("\n✍️  WRITER OUTPUT:")
        print(result["final_report"][:800])

    if result.get("research_notes"):
        print("\n🔍 RESEARCH OUTPUT:")
        print(result["research_notes"][:800])

    if result.get("github_result"):
        print(f"\n✅ GITHUB: {result['github_result']}")


def _save_output(content: str, path: str):
    import os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    main()
