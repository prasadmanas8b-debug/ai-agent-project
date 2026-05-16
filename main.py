# main.py
# Phase 3 entry point — replaces hardcoded pipeline with graph.invoke()

from graph.pipeline_graph import build_graph
# imports the compiled LangGraph pipeline
# this single import replaces all individual agent imports from Phase 2
# the graph internally handles research, writer, and github agents

def main():

    graph = build_graph()
    # build_graph() wires all 4 nodes together and compiles them
    # this is where LangGraph validates the graph — missing edges, etc.
    # compile() is called inside build_graph(), so what you get back
    # is already a runnable object, not a builder

    print('\n' + '='*50)
    print('  AI Agent System — Phase 3')
    print('='*50)
    print('Examples:')
    print('  Research quantum computing')
    print('  List files in agents folder')
    print('  Research AI trends and save to GitHub')
    print('='*50 + '\n')

    user_input = input('What do you want to do? ').strip()
    # Phase 2 asked: "Enter a topic to research"
    # Phase 3 asks open-ended natural language — the Supervisor figures out what to do

    if not user_input:
        print('No input. Exiting.')
        return

    # ── INITIAL STATE ──────────────────────────────────────────────
    initial_state = {
        'task':           user_input,   # the only field with a value
        'research_notes': '',           # Research Agent will fill this
        'final_report':   '',           # Writer Agent will fill this
        'github_result':  '',           # GitHub Agent will fill this
        'next':           ''            # Supervisor will fill this each loop
    }
    # every field must exist even if empty
    # LangGraph passes this entire dict into every node
    # missing fields = KeyError when any agent reads state

    print('\n[System] Starting graph...\n')

    result = graph.invoke(initial_state)
    # this is the ONE line that replaced the entire run_pipeline() function
    # internally: Supervisor → agent → Supervisor → agent → ... → FINISH
    # result is the final AgentState dict after the graph exits

    # ── RESULTS ───────────────────────────────────────────────────
    print('\n' + '='*50)
    print('  DONE')
    print('='*50)

    if result.get('final_report'):
        print(result['final_report'][:800])
        # [:800] preview — same as Phase 2

    if result.get('github_result'):
        print(f"GitHub: {result['github_result']}")
    # conditional prints — not every task produces every output
    # a GitHub-only task won't have a final_report
    # a research-only task won't have a github_result
    # printing blindly would show empty strings or crash


# ── ENTRY POINT ───────────────────────────────────────────────────
if __name__ == '__main__':
    main()
    # same pattern as Phase 2 — only runs when you do: python main.py
    # does NOT run when another file imports main.py