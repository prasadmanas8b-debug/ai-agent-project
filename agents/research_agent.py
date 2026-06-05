"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              AI RESEARCH AGENT — FULLY EXPLAINED VERSION                   ║
║              agents/research_agent.py                                       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  WHAT THIS FILE DOES (Simple Version):                                       ║
║  ─────────────────────────────────────                                       ║
║  You type a topic (e.g. "climate change") → this agent:                      ║
║    1. Searches the web 2-3 times using Tavily                                ║
║    2. Reads the results using Groq's LLaMA3 AI                               ║
║    3. Thinks and reasons (ReAct loop)                                        ║
║    4. Writes a structured markdown report                                    ║
║    5. Saves it as a .md file in outputs/                                     ║
║                                                                              ║
║  WHO OWNS WHAT (Team Structure):                                             ║
║  ─────────────────────────────────────                                       ║
║  Member 1 → this file (research_agent.py) ← YOU ARE HERE                   ║
║  Member 2 → tools/web_search.py           ← search helper                  ║
║  Member 3 → tools/file_saver.py           ← file saving helper             ║
║                                                                              ║
║  HOW TO RUN:                                                                 ║
║  ─────────────────────────────────────                                       ║
║    Terminal mode  →  python agents/research_agent.py                        ║
║    Web app mode   →  streamlit run agents/research_agent.py                 ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  TOOLS & LIBRARIES USED:                                                     ║
║  ─────────────────────────────────────                                       ║
║  • Groq API       — Ultra-fast free AI (LLaMA3 model). The "brain".         ║
║  • Tavily API     — Search engine built for AI agents. The "eyes".           ║
║  • LangChain      — Framework that connects AI + tools together.             ║
║  • langchain_groq — LangChain plugin for Groq LLM.                          ║
║  • langchain_community.tools.tavily_search — Tavily plugin for LangChain.   ║
║  • python-dotenv  — Reads .env file for secret API keys safely.             ║
║  • Streamlit      — Turns Python script into a web app instantly.            ║
║  • os / sys       — Standard Python: file paths, environment variables.     ║
║  • re             — Regular expressions: used for safe filename creation.    ║
║                                                                              ║
║  ADVANTAGES:                                                                 ║
║  ─────────────────────────────────────                                       ║
║  ✅ Fully automated — topic in, report out, no manual effort                 ║
║  ✅ Modular team design — each member works independently                    ║
║  ✅ Smart fallbacks — works even if teammate files are missing               ║
║  ✅ ReAct loop — agent searches multiple times, not just once                ║
║  ✅ Dual mode — works as terminal app AND web app (Streamlit)                ║
║  ✅ Free tier friendly — Groq + Tavily both have free API plans              ║
║  ✅ Readable output — structured markdown with clear sections                ║
║                                                                              ║
║  DISADVANTAGES:                                                              ║
║  ─────────────────────────────────────                                       ║
║  ❌ Slow — multiple web searches = 20-40 seconds per report                  ║
║  ❌ No internet = no results. Fully depends on online APIs                   ║
║  ❌ AI can hallucinate — may add incorrect facts confidently                 ║
║  ❌ No memory — forgets previous research sessions completely                ║
║  ❌ API rate limits — free tiers have daily/monthly usage caps               ║
║  ❌ No source citations in output — can't verify where facts came from       ║
║  ❌ Single-threaded — can't research multiple topics at once                 ║
║                                                                              ║
║  FUTURE SCOPE (What Can Be Added):                                           ║
║  ─────────────────────────────────────                                       ║
║  🔮 Memory system — remember previous research using ChromaDB/FAISS          ║
║  🔮 Multi-agent — one searches, one fact-checks, one formats                 ║
║  🔮 PDF/DOCX export — download polished formatted documents                  ║
║  🔮 Auto citations — every fact links back to its source URL                 ║
║  🔮 Scheduled runs — auto-research topics every morning                      ║
║  🔮 Voice input — speak your topic instead of typing                         ║
║  🔮 Multi-language — research and write reports in any language               ║
║  🔮 Image search — add images to reports from the web                        ║
║                                                                              ║
║  BETTER VERSION IDEAS:                                                       ║
║  ─────────────────────────────────────                                       ║
║  ⭐ Use GPT-4o or Claude 3.5 Sonnet for smarter reasoning                    ║
║  ⭐ Add LangGraph for more complex multi-step agent flows                    ║
║  ⭐ Use async/await for faster parallel web searches                          ║
║  ⭐ Add a vector database to store and search past reports                   ║
║  ⭐ Implement source ranking — trust .edu/.gov more than blogs               ║
║  ⭐ Add human-in-the-loop — ask user to approve before saving                ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: STANDARD LIBRARY IMPORTS
# These come built-in with Python — no need to install anything
# ─────────────────────────────────────────────────────────────────────────────
import os    # os = Operating System module
             # Used to: read environment variables (API keys), create folders,
             # build file paths that work on Windows AND Mac/Linux

import sys   # sys = System module
             # Used to: stop the program early (sys.exit), add folders to
             # Python's search path so we can import from tools/

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2: LOADING ENVIRONMENT VARIABLES
# What is a .env file?
#   A hidden text file that stores your secret API keys like:
#     GROQ_API_KEY=gsk_abc123...
#     TAVILY_API_KEY=tvly-xyz456...
# Why not just write keys directly in the code?
#   NEVER hardcode API keys! If you push to GitHub, everyone can see and
#   steal your keys. The .env file is kept private (added to .gitignore).
# python-dotenv reads the .env file and loads those values into os.environ
# so we can safely access them with os.getenv()
# ─────────────────────────────────────────────────────────────────────────────
from dotenv import load_dotenv  # pip install python-dotenv

load_dotenv()
# ↑ This one line reads your .env file and makes all its key=value pairs
#   available via os.getenv(). Must be called BEFORE reading any keys.

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3: READING API KEYS
# os.getenv("KEY_NAME") → returns the value if found, or None if missing
# We store them in UPPERCASE variables (Python convention for constants)
# ─────────────────────────────────────────────────────────────────────────────
GROQ_API_KEY   = os.getenv("GROQ_API_KEY")    # Your Groq AI key
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")  # Your Tavily search key

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4: VALIDATION — FAIL FAST IF KEYS ARE MISSING
# "Fail fast" = detect problems immediately at startup, not halfway through
# running when it's harder to debug.
# If either key is None (missing from .env), we:
#   1. Print a helpful error message telling the user where to get the key
#   2. Exit the program with code 1 (non-zero = something went wrong)
# ─────────────────────────────────────────────────────────────────────────────
if not GROQ_API_KEY:
    # "not None" is True, so "not GROQ_API_KEY" is True when it's missing
    print("❌  GROQ_API_KEY missing from .env — get it free at https://console.groq.com")
    sys.exit(1)
    # sys.exit(1) → stops the entire program RIGHT HERE. Code below never runs.

if not TAVILY_API_KEY:
    print("❌  TAVILY_API_KEY missing from .env — get it free at https://tavily.com")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5: FIXING THE PYTHON IMPORT PATH
# PROBLEM: This file lives at  agents/research_agent.py
#          The tools live at   tools/web_search.py
#                              tools/file_saver.py
# When Python runs agents/research_agent.py, it only knows to look for
# imports inside the agents/ folder by default. It can't see tools/ yet.
# SOLUTION: Add the project root folder to sys.path (Python's list of
# folders to search when you write "import something")
#   os.path.dirname(__file__)  → folder containing THIS file → "agents/"
#   os.path.join(..., "..")    → go UP one level → project root "/"
#   os.path.abspath(...)       → convert to absolute path → "/full/path/to/project"
#   sys.path.insert(0, ...)    → add it as the FIRST place Python looks
# ─────────────────────────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
# Now Python can find anything in the project root, including tools/

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6: IMPORTING MEMBER 2's WEB SEARCH TOOL
# We use try/except to handle the case where Member 2 hasn't created their
# file yet. This is called "graceful degradation" — the system downgrades
# to a backup instead of crashing.
# SEARCH_READY = True  → use Member 2's custom search function
# SEARCH_READY = False → use Tavily's built-in LangChain tool as fallback
# ─────────────────────────────────────────────────────────────────────────────
try:
    from tools.web_search import search_web      # Member 2's function
    print("✅  Connected to tools/web_search.py (Member 2)")
    SEARCH_READY = True   # Flag: Member 2's tool is available

except ImportError as e:
    # ImportError happens when the file doesn't exist or has a syntax error
    print(f"⚠️   tools/web_search.py not found ({e}). Using built-in Tavily fallback.")
    SEARCH_READY = False  # Flag: will use built-in Tavily instead

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 7: IMPORTING MEMBER 3's FILE SAVER TOOL
# Same pattern as above — try to use Member 3's code, fallback if missing.
# save_report(topic, content) → saves the report to a file, returns path
# list_reports()              → returns list of all saved report filenames
# ─────────────────────────────────────────────────────────────────────────────
try:
    from tools.file_saver import save_report, list_reports
    print("✅  Connected to tools/file_saver.py (Member 3)")
    SAVER_READY = True    # Flag: Member 3's tool is available

except ImportError as e:
    print(f"⚠️   tools/file_saver.py not found ({e}). Using built-in file saver fallback.")
    SAVER_READY = False   # Flag: will use _builtin_save() instead

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 8: LANGCHAIN + GROQ IMPORTS
# These are the core AI libraries. Install with:
#   pip install langchain langchain-groq langchain-community
# ChatGroq             → Connects to Groq's fast LLaMA3 AI model
# TavilySearchResults  → Built-in LangChain tool for Tavily web search
# AgentExecutor        → The engine that runs the agent's think-search loop
# create_react_agent   → Builds a ReAct-style reasoning agent
# tool                 → Decorator that turns a Python function into a LangChain tool
# PromptTemplate       → Creates reusable, structured prompts with variables
# ─────────────────────────────────────────────────────────────────────────────
from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

# ═════════════════════════════════════════════════════════════════════════════
# SECTION 9: FALLBACK FUNCTIONS
# Used ONLY when teammate files (Member 2/3) are not yet available.
# Think of these as "emergency backup" versions of the real tools.
# ═════════════════════════════════════════════════════════════════════════════
def _builtin_save(topic: str, content: str) -> str:
    """
    FALLBACK file saver — used only if Member 3's file_saver.py is missing.

    What it does:
      1. Creates an 'outputs/' folder if it doesn't exist yet
      2. Converts the topic into a safe filename (removes special chars)
         e.g. "Climate Change!" → "climate_change"
      3. Writes the report as a .md (Markdown) file
      4. Returns the file path so the caller knows where it was saved

    Args:
        topic   (str): The research topic — used to name the file
        content (str): The full markdown report text to save

    Returns:
        str: The path to the saved file, e.g. "outputs/report_climate_change.md"
    """
    import re  # re = Regular Expressions. Used to find/replace text patterns.

    # Create 'outputs/' folder. exist_ok=True means: don't crash if it already exists
    os.makedirs("outputs", exist_ok=True)

    # Clean the topic for use as a filename:
    # re.sub(r"[^\w\s]", "", ...) → remove anything that's NOT a word char or space
    # .lower()                    → convert to lowercase
    # .strip()                    → remove leading/trailing spaces
    # .replace(" ", "_")          → replace spaces with underscores
    # [:50]                       → limit to 50 characters (filenames can't be too long)
    safe = re.sub(r"[^\w\s]", "", topic.lower()).strip().replace(" ", "_")[:50]
    path = f"outputs/report_{safe}.md"  # f-string: inserts variable into string

    # Write the file
    # open(path, "w") → open for Writing (creates file if not exists, overwrites if it does)
    # encoding="utf-8" → support international characters like é, ñ, 中文, etc.
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Research Report: {topic}\n\n{content}\n")
        # \n = newline character. \n\n = blank line between title and content.

    return path  # Return the saved file path


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 10: LLM (LANGUAGE MODEL) SETUP
# What is an LLM?
#   A Large Language Model — the AI that reads text and generates responses.
#   Think of it as the "brain" that does all the reasoning and writing.
# Why Groq?
#   Groq provides free, EXTREMELY fast inference for open-source models.
#   LLaMA3-8b-instant can generate 800+ tokens/second (vs ~50 for most APIs).
# Model Parameters Explained:
#   temperature=0.2  → Controls randomness. 0=very focused/deterministic,
#                      1=creative/random. Low is better for factual research.
#   max_tokens=2048  → Maximum length of the response (~1500 words).
# ═════════════════════════════════════════════════════════════════════════════
def _create_llm() -> ChatGroq:
    """
    Creates and returns a configured Groq LLM instance.

    Returns:
        ChatGroq: A ready-to-use LLM object that can process prompts.
    """
    return ChatGroq(
        api_key=GROQ_API_KEY,              # Your Groq API key from .env
        model="llama-3.1-8b-instant",     # Model name: 8 billion parameter LLaMA3
                                           # "instant" = optimized for speed
        temperature=0.2,                   # Low temp = consistent, factual outputs
        max_tokens=2048,                   # Max ~1500 words per response
    )


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 11: TOOLS SETUP
# What is a "Tool" in LangChain?
#   A tool is a function the AI agent can CHOOSE to call during its thinking.
#   The agent sees the tool's name and description, decides if it's useful,
#   then calls it with specific input. Like giving the AI a calculator or
#   a search engine it can use whenever it needs to.
# This function returns ONE tool: web search.
# It wraps Member 2's search_web() as a proper LangChain tool, OR falls
# back to Tavily's ready-made tool if Member 2's file isn't ready.
# ═════════════════════════════════════════════════════════════════════════════
def _create_tools() -> list:
    """
    Builds and returns the list of tools available to the agent.

    If Member 2's tools/web_search.py is ready:
        → Wraps their search_web() function as a LangChain @tool
    Otherwise:
        → Uses TavilySearchResults directly (built-in LangChain tool)

    Returns:
        list: A list of LangChain tool objects the agent can use.
    """
    if SEARCH_READY:
        # ── PATH A: Use Member 2's custom search function ──────────────────
        # The @tool decorator transforms a regular Python function into
        # something LangChain's agent can discover, call, and parse results from.
        # The docstring becomes the tool's "description" — the agent reads
        # this description to decide when to use the tool.
        @tool
        def web_search(query: str) -> str:
            """
            Search the web for up-to-date information on any topic.
            Input should be a clear, specific search query.
            """
            # Call Member 2's function, request top 5 results
            return search_web(query, max_results=5)

        return [web_search]  # Return as a list (agents expect a list of tools)
    else:
        # ── PATH B: Fallback — use Tavily's built-in LangChain tool ────────
        # TavilySearchResults is a pre-built LangChain tool that:
        #   1. Takes a search query string
        #   2. Calls the Tavily API
        #   3. Returns top N search results as readable text
        return [TavilySearchResults(
            api_key=TAVILY_API_KEY,  # Authenticate with Tavily
            max_results=5,           # Return top 5 results per search
        )]


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 12: THE PROMPT TEMPLATE
# What is a Prompt Template?
#   A pre-written instruction set for the AI with "fill-in-the-blank" slots.
#   Think of it as a form letter — the structure is fixed, but {variables}
#   get replaced with real values each time.
# Variables in this template (wrapped in {curly braces}):
#   {tools}            → filled with: list of available tools + their descriptions
#   {tool_names}       → filled with: just the names of tools (e.g. "web_search")
#   {input}            → filled with: the user's research topic
#   {agent_scratchpad} → filled with: the agent's thinking-in-progress
# The ReAct Format (Reason + Act):
#   This prompt enforces a specific THOUGHT → ACTION → OBSERVATION cycle.
#   This is the "ReAct" pattern — the agent must show its reasoning at each step.
# ═════════════════════════════════════════════════════════════════════════════
RESEARCH_SYSTEM_PROMPT = """
You are a thorough and accurate research assistant.

Your job is to research a given topic and produce a well-structured markdown report.

Report structure (always use this exact format):

## Overview
A 2-3 sentence introduction to the topic.

## Key Findings
Bullet points of the most important facts.

## Details & Examples
More in-depth information, examples, or use cases.

## Conclusion
A brief summary of what was found.

Rules:
- Always search at least 2 times with DIFFERENT queries before writing the report
- Use specific search queries, not just the topic title
- Write the report in clean markdown format
- If search returns no results, try a different query
- After gathering enough information, write the complete markdown report
"""


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 13: THE MAIN FUNCTION — run_research_agent()
# This is the CORE of the entire file. Everything above was setup.
# This function orchestrates the full research pipeline:
#   Step 1: Create the AI (LLM)
#   Step 2: Create the tools (web search)
#   Step 3: Assemble the agent (LLM + tools + prompt)
#   Step 4: Run the agent (it searches and thinks automatically)
#   Step 5: Save the output report
#   Step 6: Return results
# ═════════════════════════════════════════════════════════════════════════════
def run_research_agent(topic: str) -> dict:
    """
    The main pipeline: researches a topic end-to-end and returns the report.

    How it works internally:
      1. Creates a Groq LLM instance
      2. Creates web search tools
      3. Builds a ReAct agent (LLM + tools + prompt)
      4. Runs AgentExecutor — the agent searches 2-3x and writes a report
      5. Saves the report using Member 3's tool (or built-in fallback)
      6. Returns a dict with the topic, report text, and file path

    Args:
        topic (str): What to research. E.g. "LangChain ReAct agents"

    Returns:
        dict: {
            "topic":    str,   # The original research topic
            "report":   str,   # Full markdown report text
            "saved_to": str    # Path to the saved .md file
        }

    Example usage:
        result = run_research_agent("quantum computing")
        print(result["report"])    # Print the report
        print(result["saved_to"])  # Print where it was saved
    """
    # Print a visual separator so terminal output is easy to read
    print(f"\n{'='*55}")
    print(f"  🔍 Research Agent Starting")
    print(f"  Topic: {topic}")
    print(f"{'='*55}\n")

    # ── STEP 1: Create the LLM ────────────────────────────────────────────
    llm = _create_llm()

    # ── STEP 2: Create the tools ─────────────────────────────────────────
    tools = _create_tools()

    # ── STEP 3: Build the ReAct Agent (LangGraph prebuilt) ──────────────
    # create_react_agent is the modern stable API from langgraph.prebuilt.
    # It replaces the old AgentExecutor + create_react_agent from langchain.agents.
    # Takes: model (LLM), tools (list), prompt (system message string)
    agent = create_react_agent(
        model  = llm,
        tools  = tools,
        prompt = RESEARCH_SYSTEM_PROMPT,
    )

    # ── STEP 4: RUN THE AGENT ─────────────────────────────────────────────
    print("🤖  Agent is working...\n")
    result = agent.invoke({"messages": [("human", topic)]})

    # result["messages"] is a list. The last message is the agent's final answer.
    last_message = result["messages"][-1]
    report = last_message.content if hasattr(last_message, "content") else str(last_message)
    if not report:
        report = "⚠️ No report was generated."

    # ── STEP 6: SAVE THE REPORT ───────────────────────────────────────────
    if SAVER_READY:
        saved_to = save_report(topic, report)  # Member 3's implementation
    else:
        saved_to = _builtin_save(topic, report)  # Our fallback

    # Print completion message
    print(f"\n{'='*55}")
    print(f"  ✅ Done! Report saved to: {saved_to}")
    print(f"{'='*55}\n")

    # ── STEP 7: RETURN RESULTS ────────────────────────────────────────────
    return {
        "topic":    topic,
        "report":   report,
        "saved_to": saved_to,
    }


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 14: STREAMLIT WEB UI
# Run it with: streamlit run agents/research_agent.py
# ═════════════════════════════════════════════════════════════════════════════
def _run_streamlit():
    """
    Launches the Streamlit web application interface.
    Only called when this script is run via: streamlit run agents/research_agent.py
    """
    import streamlit as st

    st.set_page_config(
        page_title="AI Research Agent",
        page_icon="🔍",
        layout="wide"
    )

    st.title("🔍 AI Research Agent")
    st.caption("Phase 1 — Powered by Groq (LLaMA3) + Tavily Search")

    col1, col2, col3 = st.columns(3)
    col1.metric("Groq LLM",
                "✅ Connected" if GROQ_API_KEY   else "❌ Missing")
    col2.metric("Web Search",
                "✅ Ready"     if SEARCH_READY   else "⚠️ Fallback")
    col3.metric("File Saver",
                "✅ Ready"     if SAVER_READY    else "⚠️ Fallback")

    st.markdown("---")

    topic = st.text_input(
        "Enter a research topic:",
        placeholder="e.g.  LangChain agents,  quantum computing,  climate change",
    )

    col_a, col_b = st.columns([1, 4])
    run_btn = col_a.button("🚀 Research", type="primary", use_container_width=True)

    if run_btn and topic.strip():
        with st.spinner("🤖 Agent is searching and writing your report... (20-40 sec)"):
            result = run_research_agent(topic.strip())

        st.success(f"✅ Report saved to `{result['saved_to']}`")
        st.markdown("---")
        st.subheader("📄 Research Report")
        st.markdown(result["report"])

        st.download_button(
            label     = "⬇️ Download Report (.md)",
            data      = result["report"],
            file_name = os.path.basename(result["saved_to"]),
            mime      = "text/markdown",
        )
    elif run_btn:
        st.warning("Please enter a topic first.")

    if SAVER_READY:
        reports = list_reports()
        if reports:
            st.markdown("---")
            st.subheader("📂 Previously Saved Reports")
            for r in reports:
                st.write(f"• `{r}`")


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 15: ENTRY POINT
# ═════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":

    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        if get_script_run_ctx():
            _run_streamlit()
            raise SystemExit
    except (ImportError, SystemExit):
        pass
    except Exception:
        pass

    print("\n╔═══════════════════════════════════════╗")
    print("║     AI Research Agent — Phase 1       ║")
    print("╚═══════════════════════════════════════╝")

    print("\nConnected tools:")
    print(f"  web_search.py : {'✅ Member 2' if SEARCH_READY else '⚠️  Fallback'}")
    print(f"  file_saver.py : {'✅ Member 3' if SAVER_READY  else '⚠️  Fallback'}")

    topic = input("\n📝  Enter research topic: ").strip()

    if not topic:
        print("No topic entered. Exiting.")
        sys.exit(0)

    result = run_research_agent(topic)

    print("\n--- REPORT PREVIEW (first 600 chars) ---")
    print(result["report"][:600] + "\n...")
    print(f"\n📁  Full report: {result['saved_to']}")

