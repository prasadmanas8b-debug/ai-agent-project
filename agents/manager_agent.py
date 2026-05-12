from langchain_groq import ChatGroq
from langchain.schema import SystemMessage, HumanMessage
from graph.state import AgentState
import os
from dotenv import load_dotenv
load_dotenv()
# ─────────────────────────────────────────────────────────────────────────────
# MAIN FUNCTION: run_supervisor
# ─────────────────────────────────────────────────────────────────────────────

def run_supervisor(state: AgentState) -> AgentState:
    """
    Reads the current state of the pipeline and decides which agent to call
    next. Returns an updated state dict with the 'next' field set to one of:
        "research" | "writer" | "github" | "FINISH"

    LangGraph will read state['next'] and route to the correct node.

    Parameters
    ----------
    state : AgentState
        The full shared state — all fields that exist at this point in time.
        Some fields will be empty strings ("") if those agents haven't run yet.

    Returns
    -------
    AgentState
        Same state dict, but with state['next'] filled in with the routing
        decision. The **state spread operator keeps every OTHER field intact.
    """
    # ── Step 1: Initialise the LLM ───────────────────────────────────────────
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        api_key=os.getenv("GROQ_API_KEY")
    )
    system_prompt = """
You are a supervisor managing three specialized agents:
  - research : searches the web and writes research notes into research_notes
  - writer   : takes research_notes and writes a polished report into final_report
  - github   : performs GitHub actions (create files, list files, commit, push)

Your ONLY job is to read the task and current state, then decide which agent
should run next.

Decision rules (apply in order, top to bottom):
  1. If the task needs research AND research_notes is empty        → return: research
  2. If research_notes exists AND final_report is empty            → return: writer
  3. If the task mentions GitHub / saving / committing / push      → return: github
  4. If all required work is complete                              → return: FINISH

CRITICAL RULES:
  - Respond with EXACTLY ONE word, nothing else.
  - Valid responses: research | writer | github | FINISH
  - Do NOT explain your answer. Do NOT add punctuation. ONE word only.
  - You do NO actual work yourself. You only route.
"""
    human_message = f"""
    Task: {state['task']}

    Current state:
    - research_notes  exists: {bool(state['research_notes'])}
    - final_report    exists: {bool(state['final_report'])}
    - github_result   exists: {bool(state['github_result'])}

    Based on the rules, what should run next? (one word only)
    """
    # ── Step 4: Send the messages to the LLM ─────────────────────────────────
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_message),
    ]
    response = llm.invoke(messages)
    # ── Step 5: Parse and clean the response ─────────────────────────────────
    decision = response.content.strip().lower()
    if decision == "finish":
        decision = "FINISH"
    valid_decisions = {"research", "writer", "github", "FINISH"}
    if decision not in valid_decisions:
        print(f"[Supervisor] WARNING: Unexpected decision '{decision}'. Defaulting to FINISH.")
        decision = "FINISH"

    # ── Step 6: Log and return ───────────────────────────────────────────────
    print(f"[Supervisor] Task: '{state['task'][:60]}...' → Decision: {decision}")
    return {**state, "next": decision}