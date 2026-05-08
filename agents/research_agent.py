"""
agents/research_agent.py — Member 1 owns this file
AI Agent Project | Phase 1

The main research brain. Connects to:
  ← tools/web_search.py  (Member 2)
  ← tools/file_saver.py  (Member 3)

How to run:
  python agents/research_agent.py
  streamlit run agents/research_agent.py
"""

import os
import sys
from dotenv import load_dotenv

# ── Load .env ─────────────────────────────────────────────────────────────────
load_dotenv()

GROQ_API_KEY   = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not GROQ_API_KEY:
    print("❌  GROQ_API_KEY missing from .env — get it free at console.groq.com")
    sys.exit(1)

if not TAVILY_API_KEY:
    print("❌  TAVILY_API_KEY missing from .env — get it free at tavily.com")
    sys.exit(1)

# ── Add project root to path so tools/ can be imported ───────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

# ── Import Member 2's web search tool ────────────────────────────────────────
try:
    from tools.web_search import search_web
    print("✅  Connected to tools/web_search.py (Member 2)")
    SEARCH_READY = True
except ImportError as e:
    print(f"⚠️   tools/web_search.py not found ({e}). Using built-in Tavily fallback.")
    SEARCH_READY = False

# ── Import Member 3's file saver tool ────────────────────────────────────────
try:
    from tools.file_saver import save_report, list_reports
    print("✅  Connected to tools/file_saver.py (Member 3)")
    SAVER_READY = True
except ImportError as e:
    print(f"⚠️   tools/file_saver.py not found ({e}). Using built-in file saver fallback.")
    SAVER_READY = False

# ── LangChain + Groq imports ──────────────────────────────────────────────────
from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import tool
from langchain_core.prompts import PromptTemplate


# ═════════════════════════════════════════════════════════════════════════════
#  FALLBACKS (used only when Member 2/3 files are missing)
# ═════════════════════════════════════════════════════════════════════════════

def _builtin_save(topic: str, content: str) -> str:
    """Fallback file saver if Member 3's file isn't ready."""
    import re
    os.makedirs("outputs", exist_ok=True)
    safe = re.sub(r"[^\w\s]", "", topic.lower()).strip().replace(" ", "_")[:50]
    path = f"outputs/report_{safe}.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Research Report: {topic}\n\n{content}\n")
    return path


# ═════════════════════════════════════════════════════════════════════════════
#  LLM
# ═════════════════════════════════════════════════════════════════════════════

def _create_llm() -> ChatGroq:
    """Returns a Groq LLM instance (llama3-8b — fast & free)."""
    return ChatGroq(
        api_key=GROQ_API_KEY,
        model="llama-3.1-8b-instant",
        temperature=0.2,
        max_tokens=2048,
    )


# ═════════════════════════════════════════════════════════════════════════════
#  TOOLS — wraps Member 2's search_web as a LangChain tool
# ═════════════════════════════════════════════════════════════════════════════

def _create_tools() -> list:
    """
    Builds the LangChain tool list.
    Uses Member 2's search_web() if available, else TavilySearchResults.
    """
    if SEARCH_READY:
        # Wrap Member 2's function as a proper LangChain @tool
        @tool
        def web_search(query: str) -> str:
            """
            Search the web for up-to-date information on any topic.
            Input should be a clear, specific search query.
            """
            return search_web(query, max_results=5)

        return [web_search]

    else:
        # Built-in fallback — works directly without Member 2
        return [TavilySearchResults(
            api_key=TAVILY_API_KEY,
            max_results=5,
        )]


# ═════════════════════════════════════════════════════════════════════════════
#  AGENT PROMPT
# ═════════════════════════════════════════════════════════════════════════════

RESEARCH_PROMPT = PromptTemplate.from_template("""
You are a thorough and accurate research assistant.

Your job is to research a given topic and produce a well-structured markdown report.

Report structure (always use this):
## Overview
A 2-3 sentence introduction to the topic.

## Key Findings
- Bullet points of the most important facts.

## Details & Examples
More in-depth information, examples, or use cases.

## Conclusion
A brief summary of what was found.

---

You have access to these tools:
{tools}

Tool names available: {tool_names}

Use this EXACT format for every step:

Question: the research topic
Thought: what I need to find out
Action: [tool name from {tool_names}]
Action Input: my search query
Observation: the search results
... (repeat as needed — search 2-3 times for different aspects)
Thought: I now have enough information to write the full report
Final Answer: [complete markdown research report]

Important rules:
- Always search at least 2 times with different queries before writing the report
- Use specific search queries, not just the topic title
- Write the report in clean markdown format
- If search returns no results, try a different query

Begin!

Question: {input}
Thought: {agent_scratchpad}
""")


# ═════════════════════════════════════════════════════════════════════════════
#  CORE FUNCTION — run_research_agent()
# ═════════════════════════════════════════════════════════════════════════════

def run_research_agent(topic: str) -> dict:
    """
    Research a topic end-to-end:
      1. Agent searches the web (via tools/web_search.py)
      2. Agent writes a structured markdown report
      3. Report is saved to outputs/ (via tools/file_saver.py)

    Args:
        topic (str): Research topic. E.g. "LangChain ReAct agents"

    Returns:
        dict: {
            "topic":    str,   # original topic
            "report":   str,   # full markdown report
            "saved_to": str    # path to saved .md file
        }
    """
    print(f"\n{'='*55}")
    print(f"  🔍 Research Agent Starting")
    print(f"  Topic: {topic}")
    print(f"{'='*55}\n")

    # 1. Setup
    llm   = _create_llm()
    tools = _create_tools()

    # 2. Build ReAct agent
    agent = create_react_agent(
        llm=llm,
        tools=tools,
        prompt=RESEARCH_PROMPT,
    )

    # 3. Execute
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,              # shows every step in terminal
        max_iterations=8,          # max search rounds
        handle_parsing_errors=True,
    )

    print("🤖  Agent is working...\n")
    result = executor.invoke({"input": topic})
    report = result.get("output", "⚠️ No report was generated.")

    # 4. Save the report
    if SAVER_READY:
        saved_to = save_report(topic, report)
    else:
        saved_to = _builtin_save(topic, report)

    print(f"\n{'='*55}")
    print(f"  ✅ Done! Report saved to: {saved_to}")
    print(f"{'='*55}\n")

    return {
        "topic":    topic,
        "report":   report,
        "saved_to": saved_to,
    }


# ═════════════════════════════════════════════════════════════════════════════
#  STREAMLIT UI (run with: streamlit run agents/research_agent.py)
# ═════════════════════════════════════════════════════════════════════════════

def _run_streamlit():
    import streamlit as st

    st.set_page_config(page_title="AI Research Agent", page_icon="🔍", layout="wide")

    # Header
    st.title("🔍 AI Research Agent")
    st.caption("Phase 1 — Powered by Groq (LLaMA3) + Tavily Search")

    # Status badges
    col1, col2, col3 = st.columns(3)
    col1.metric("Groq LLM",   "✅ Connected" if GROQ_API_KEY   else "❌ Missing")
    col2.metric("Web Search",  "✅ Ready"     if SEARCH_READY   else "⚠️ Fallback")
    col3.metric("File Saver",  "✅ Ready"     if SAVER_READY    else "⚠️ Fallback")

    st.markdown("---")

    # Input
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

        # Show report
        st.subheader("📄 Research Report")
        st.markdown(result["report"])

        # Download
        st.download_button(
            label     = "⬇️ Download Report (.md)",
            data      = result["report"],
            file_name = os.path.basename(result["saved_to"]),
            mime      = "text/markdown",
        )

    elif run_btn:
        st.warning("Please enter a topic first.")

    # Show saved reports
    if SAVER_READY:
        reports = list_reports()
        if reports:
            st.markdown("---")
            st.subheader("📂 Previously Saved Reports")
            for r in reports:
                st.write(f"• `{r}`")


# ═════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Detect if running inside Streamlit
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        if get_script_run_ctx():
            _run_streamlit()
            raise SystemExit  # let streamlit take over
    except (ImportError, SystemExit):
        pass
    except Exception:
        pass

    # ── Terminal mode ─────────────────────────────────────────────────────────
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
