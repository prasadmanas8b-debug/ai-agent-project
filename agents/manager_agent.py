"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              MANAGER AGENT (SUPERVISOR) — Phase 3                           ║
║              agents/manager_agent.py                                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  WHAT THIS FILE IS:                                                          ║
║  The Supervisor — the only agent whose job is to decide what OTHER           ║
║  agents should do. It NEVER does any research, writing, or GitHub            ║
║  actions itself.                                                             ║
║                                                                              ║
║  ANALOGY:                                                                    ║
║  Think of it as a project manager at a company.                              ║
║  The manager reads the client's request and assigns it to the right          ║
║  team member. The manager does not do the work themselves.                   ║
║                                                                              ║
║  HOW IT WORKS:                                                               ║
║  1. Receives the full AgentState (shared whiteboard)                         ║
║  2. Reads the task + what has already been done                              ║
║  3. LLM decides: which agent should run next?                                ║
║  4. Writes that decision into state["next"]                                  ║
║  5. The graph routes to that agent                                           ║
║  6. After that agent runs, Supervisor is called AGAIN                        ║
║  7. Loop continues until Supervisor says "FINISH"                            ║
║                                                                              ║
║  OUTPUT VALUES:                                                              ║
║  "research" → route to Research Agent                                        ║
║  "writer"   → route to Writer Agent                                          ║
║  "github"   → route to GitHub Agent                                          ║
║  "FINISH"   → end the graph                                                  ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from graph.state import AgentState

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: SETUP
# ─────────────────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    print("❌  GROQ_API_KEY missing from .env")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2: SUPERVISOR SYSTEM PROMPT
# This prompt is the ENTIRE brain of the routing logic.
# More examples = better routing decisions.
# ─────────────────────────────────────────────────────────────────────────────
SUPERVISOR_SYSTEM_PROMPT = """
You are a Supervisor managing a team of three AI agents:
  - research → searches the web and collects raw information on a topic
  - writer   → takes research notes and writes a clean structured report
  - github   → performs actions on a GitHub repository (create/update files, list files, create branches)

Your ONLY job is to decide which agent should run next, based on:
  1. The user's original task
  2. What has already been completed (shown in the context)

You must respond with EXACTLY ONE word — no explanation, no punctuation, no extra text.
Your response must be one of: research / writer / github / FINISH

Routing rules:
  - If the task asks to research / find / explain / summarize a topic AND research_notes is empty → respond: research
  - If research_notes is filled but final_report is empty AND the task needs a written report → respond: writer
  - If the task mentions GitHub / saving to repo / committing / creating files / listing files / creating branches → respond: github
  - If "save to github" or "push to github" is in the task AND final_report is filled but github_result is empty → respond: github
  - If all required steps are done OR the task only needed one agent and that agent ran → respond: FINISH

Decision examples:
  Task: "Research the history of the internet"
    → research_notes empty? → research
    → research_notes filled, final_report empty? → writer
    → final_report filled? → FINISH

  Task: "List all files in the agents folder"
    → github (immediately, no research needed)
    → github ran? → FINISH

  Task: "Create a branch called feature/new-ui"
    → github
    → github ran? → FINISH

  Task: "Research quantum computing and save the report to docs/quantum.md on GitHub"
    → research_notes empty? → research
    → research_notes filled, final_report empty? → writer
    → final_report filled, github_result empty? → github
    → github_result filled? → FINISH

  Task: "Do something useful" or vague input
    → research (default — when in doubt, research)

Remember: respond with ONE word only. No explanation.
"""

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3: MAIN FUNCTION — run_supervisor()
# ─────────────────────────────────────────────────────────────────────────────
def run_supervisor(state: AgentState) -> AgentState:
    """
    The Supervisor node function for LangGraph.

    Reads the current state, decides which agent should run next,
    and writes that decision into state["next"].

    This function is called by LangGraph:
      - At the very start (to decide the first agent)
      - After EVERY agent finishes (to decide the next step)
      - Until it returns "FINISH"

    Args:
        state (AgentState): The full shared state with all fields.

    Returns:
        AgentState: Updated state with state["next"] filled in.
    """
    print(f"\n[Supervisor] Evaluating task: '{state['task'][:80]}...' " if len(state['task']) > 80 else f"\n[Supervisor] Evaluating task: '{state['task']}'")
    print(f"[Supervisor] Status — research_notes: {'✅' if state.get('research_notes') else '⬜'}  "
          f"final_report: {'✅' if state.get('final_report') else '⬜'}  "
          f"github_result: {'✅' if state.get('github_result') else '⬜'}")

    # ── Build context for the LLM ─────────────────────────────────────────
    # Tell the Supervisor what's already been completed
    context_parts = [f"Original Task: {state['task']}\n"]

    if state.get("research_notes"):
        context_parts.append(f"✅ Research Agent has completed. Notes collected ({len(state['research_notes'])} chars).")
    else:
        context_parts.append("⬜ Research Agent has NOT run yet.")

    if state.get("final_report"):
        context_parts.append(f"✅ Writer Agent has completed. Report written ({len(state['final_report'])} chars).")
    else:
        context_parts.append("⬜ Writer Agent has NOT run yet.")

    if state.get("github_result"):
        context_parts.append(f"✅ GitHub Agent has completed. Result: {state['github_result'][:100]}")
    else:
        context_parts.append("⬜ GitHub Agent has NOT run yet.")

    context = "\n".join(context_parts)

    # ── LLM Setup ─────────────────────────────────────────────────────────
    llm = ChatGroq(
        api_key    = GROQ_API_KEY,
        model      = "llama-3.3-70b-versatile",
        temperature= 0.0,    # 0 = fully deterministic routing
        max_tokens = 10,     # We only need ONE word back
    )

    messages = [
        SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT),
        HumanMessage(content=context),
    ]

    # ── Call LLM ──────────────────────────────────────────────────────────
    try:
        response = llm.invoke(messages)
        decision = response.content.strip().lower().replace(".", "").replace(":", "")
    except Exception as e:
        print(f"[Supervisor] ❌ LLM call failed: {e}. Defaulting to FINISH.")
        decision = "FINISH"

    # ── Validate the decision ─────────────────────────────────────────────
    valid_decisions = {"research", "writer", "github", "finish"}
    if decision not in valid_decisions:
        print(f"[Supervisor] ⚠️  Unexpected response '{decision}'. Defaulting to FINISH.")
        decision = "FINISH"

    # Normalise capitalisation of FINISH
    if decision == "finish":
        decision = "FINISH"

    print(f"[Supervisor] → Decision: {decision}")

    return {**state, "next": decision}

