# agents/manager_agent.py
# ─────────────────────────────────────────────────────────────────────────────
# THE SUPERVISOR / MANAGER AGENT
#
# Role: The brain of the whole system. It does NOT do any real work itself.
# It reads the task + current state, then decides which agent should run next.
# It returns ONE word: "research" / "writer" / "github" / "FINISH"
#
# Called by: graph/pipeline_graph.py → every time a node finishes, LangGraph
# calls this again to decide what to do next. This loop continues until the
# supervisor returns "FINISH".
# ─────────────────────────────────────────────────────────────────────────────

# ── Imports ──────────────────────────────────────────────────────────────────

from langchain_groq import ChatGroq
# ChatGroq lets us talk to Groq's LLM (which runs Llama). Think of it like
# an object that wraps the Groq API — we give it our key and model name and
# it handles the HTTP requests to the AI for us.

from langchain.schema import SystemMessage, HumanMessage
# These are two kinds of messages we can send to the LLM:
#
#   SystemMessage  → sets the rules / instructions (LLM treats this as its
#                    "job description"). The LLM never ignores this.
#
#   HumanMessage   → the actual input coming "from the user" in a given turn.
#                    Here we'll fill it with the current state snapshot.

from graph.state import AgentState
# AgentState is the TypedDict we already built in state.py.
# It is the shared whiteboard: task / research_notes / final_report /
# github_result / next
# We import it here so Python knows the exact shape of the dict we receive.

import os
from dotenv import load_dotenv
# os.getenv() reads environment variables (like secrets) from the shell.
# load_dotenv() reads those same variables from a .env file on disk and
# loads them INTO the environment, so os.getenv() can find them.
# This keeps your API key out of the source code.

# ── Load secrets from .env ───────────────────────────────────────────────────
load_dotenv()
# After this line, os.getenv("GROQ_API_KEY") will return the key you put in
# your .env file, e.g.:
#   GROQ_API_KEY=gsk_...


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
        # Which model to use. llama-3.3-70b is Groq's large, fast model.
        # You can swap this for "llama-3.1-8b-instant" if you want cheaper/
        # faster calls during testing (less accurate routing).

        temperature=0,
        # 0 = fully deterministic. The same input → ALWAYS the same output.
        # This is critical for a supervisor — you don't want random routing
        # decisions. Never set this above 0 for the supervisor.

        api_key=os.getenv("GROQ_API_KEY")
        # Reads the key from your .env file. Never hardcode secrets here.
    )

    # ── Step 2: Write the system prompt ──────────────────────────────────────
    # This is the "rules of the game" we give the LLM. It never changes
    # between calls — it always defines the same four routing options.
    #
    # IMPORTANT: The LLM will only do what this prompt tells it to.
    # The more specific you are here, the more reliable the routing.
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
    # Why temperature=0 matters here: if the LLM says "github." instead of
    # "github" or adds a sentence, our routing breaks. Low temperature + a
    # strict prompt = reliable single-word output every time.

    # ── Step 3: Build the human message with current state ───────────────────
    # We summarise the state into a short human-readable snapshot.
    # The LLM reads this snapshot alongside the system prompt to decide.
    human_message = f"""
Task: {state['task']}

Current state:
  - research_notes  exists: {bool(state['research_notes'])}
  - final_report    exists: {bool(state['final_report'])}
  - github_result   exists: {bool(state['github_result'])}

Based on the rules, what should run next? (one word only)
"""
    # bool(state['research_notes']) converts the string to True/False:
    #   ""          → False   (agent hasn't run yet)
    #   "## Notes…" → True    (agent already ran)
    # This gives the LLM a simple yes/no snapshot instead of dumping the full
    # content of every field (which wastes tokens and confuses it).

    # ── Step 4: Send the messages to the LLM ─────────────────────────────────
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_message),
    ]
    # We always send BOTH messages together. SystemMessage first, then
    # HumanMessage. This is the standard "chat" format for all LangChain LLMs.

    response = llm.invoke(messages)
    # llm.invoke() makes the actual API call to Groq and blocks until it
    # gets a response back. response is a langchain AIMessage object.
    # response.content is the raw text the LLM returned (e.g. "research").

    # ── Step 5: Parse and clean the response ─────────────────────────────────
    decision = response.content.strip().lower()
    # .strip()  → removes any leading/trailing whitespace or newlines
    # .lower()  → converts to lowercase ("FINISH" → "finish")
    #
    # Wait — but the routing map uses "FINISH" (uppercase). We handle this
    # in pipeline_graph.py by mapping "finish" → END. But to be safe, let's
    # handle the FINISH case here specifically:
    if decision == "finish":
        decision = "FINISH"
    # This way state['next'] will always be "FINISH" (uppercase) which
    # matches what LangGraph expects in the conditional edges map.

    # Validate the decision is one of the four expected values
    valid_decisions = {"research", "writer", "github", "FINISH"}
    if decision not in valid_decisions:
        # If the LLM returns something unexpected (rare but can happen),
        # default to FINISH to avoid an infinite loop.
        print(f"[Supervisor] WARNING: Unexpected decision '{decision}'. Defaulting to FINISH.")
        decision = "FINISH"

    # ── Step 6: Log and return ───────────────────────────────────────────────
    print(f"[Supervisor] Task: '{state['task'][:60]}...' → Decision: {decision}")
    # This print appears in your terminal while the system runs, so you can
    # watch the routing decisions happen in real time.

    # Return the FULL state with 'next' updated.
    # **state unpacks every existing key-value pair, then we override 'next'.
    # This is equivalent to copying the dict and changing one field.
    # We NEVER modify state directly — always return a new dict.
    return {**state, "next": decision}