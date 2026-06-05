"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              WRITER AGENT — Phase 2                                         ║
║              agents/writer_agent.py                                         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  WHAT THIS FILE DOES:                                                        ║
║  ─────────────────────────────────────                                       ║
║  Receives raw research notes from the Research Agent and rewrites them       ║
║  into a clean, structured markdown report with 4 sections:                   ║
║    1. Overview                                                               ║
║    2. Key Findings                                                           ║
║    3. Detailed Analysis                                                      ║
║    4. Conclusion                                                             ║
║                                                                              ║
║  WHO OWNS THIS FILE:                                                         ║
║  Member 1 (Leader) — this is the second agent you build                     ║
║                                                                              ║
║  HOW IT DIFFERS FROM RESEARCH AGENT:                                         ║
║  ─────────────────────────────────────                                       ║
║  Same LLM model family, completely different behavior because of:            ║
║    • Different system prompt → "write a report", not "search the web"       ║
║    • No web search tool → it ONLY has access to file_saver                  ║
║    • Input is research notes, not a topic string                             ║
║                                                                              ║
║  KEY PRINCIPLE:                                                              ║
║  Specialization = different system prompt + different tools. That's it.     ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
import os
import sys

# Fix import path so we can import from tools/ when running from any directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv()

# LangChain imports for the LLM
from langchain_groq import ChatGroq
from langchain.schema import SystemMessage, HumanMessage

# Member 3's file saver tool
from tools.file_saver import save_to_file

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2: API KEY VALIDATION
# ─────────────────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    print("❌  GROQ_API_KEY missing from .env — get it free at https://console.groq.com")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3: SYSTEM PROMPT
# This is the core of the Writer Agent's behavior.
# Same LLM, completely different personality because of this prompt.
# ─────────────────────────────────────────────────────────────────────────────
WRITER_SYSTEM_PROMPT = """
You are a professional report writer.

You receive raw research notes on a topic and your job is to:
1. Write a clean, structured report in markdown format
2. Always include these FOUR sections with these EXACT headings:
   ## Overview
   ## Key Findings
   ## Detailed Analysis
   ## Conclusion
3. Use clear headings and bullet points where helpful
4. Remove redundant or repeated information
5. Keep a professional, neutral tone
6. Do NOT search the web — only use what is given to you in the notes
7. Do NOT make up facts — only use information present in the research notes
8. If the notes mention conflicting information, acknowledge it honestly
9. Minimum length: 300 words. Maximum: 1000 words.

Your output must be a complete markdown document ready to save as a .md file.
"""

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4: MAIN FUNCTION — run_writer_agent()
# ─────────────────────────────────────────────────────────────────────────────
def run_writer_agent(research_notes: str, topic: str) -> str:
    """
    Takes raw research notes and a topic.
    Writes a clean structured markdown report.
    Saves it to the outputs/ folder as final_report_{topic}.md
    Returns the report as a string.

    Args:
        research_notes (str): Raw notes returned by the Research Agent.
        topic          (str): The original research topic.

    Returns:
        str: The complete markdown report, or an error message string if failed.

    Pipeline position:
        Research Agent → [ Writer Agent ] → saved .md file
    """

    print(f"\n[Writer Agent] Starting for topic: '{topic}'")

    # ── GUARD CLAUSE: Validate input BEFORE doing any work ────────────────
    # This is called "fail fast" — check for bad input immediately.
    # Never pass garbage to an LLM — it will produce garbage output.
    if not research_notes or len(research_notes.strip()) < 50:
        msg = "[Writer Agent] ⚠️  Research notes too short or empty. Cannot write report."
        print(msg)
        return "Error: Insufficient research data to generate a report."

    # ── STEP 1: Set up the LLM ────────────────────────────────────────────
    # Using a larger model (70b) for better writing quality.
    # Writer agents need more reasoning capacity than search agents.
    # llama-3.3-70b-versatile = better at following complex formatting rules.
    llm = ChatGroq(
        api_key=GROQ_API_KEY,
        model="llama-3.3-70b-versatile",  # Larger model → better report quality
        temperature=0.4,                   # Slight creativity for natural writing
        max_tokens=2048,
    )

    # ── STEP 2: Build the messages ────────────────────────────────────────
    # SystemMessage → sets the agent's role and rules (loaded once)
    # HumanMessage  → the actual content to process (changes each run)
    messages = [
        SystemMessage(content=WRITER_SYSTEM_PROMPT),
        HumanMessage(content=f"""
Topic: {topic}

Raw Research Notes:
{research_notes}

Write the full structured report now. Include all four sections: Overview, Key Findings, Detailed Analysis, and Conclusion.
        """)
    ]

    # ── STEP 3: Call the LLM ─────────────────────────────────────────────
    print("[Writer Agent] Sending notes to LLM for report generation...")
    try:
        response = llm.invoke(messages)
        report = response.content
    except Exception as e:
        print(f"[Writer Agent] ❌ LLM call failed: {e}")
        return f"Error: LLM call failed — {str(e)}"

    # ── STEP 4: Validate the output ───────────────────────────────────────
    if not report or len(report.strip()) < 100:
        print("[Writer Agent] ⚠️  LLM returned an empty or very short response.")
        return "Error: LLM returned an empty report."

    # ── STEP 5: Save the report ───────────────────────────────────────────
    # Use "final_report_" prefix to distinguish from raw research notes.
    # Research Agent saves → report_{topic}.md
    # Writer Agent saves   → final_report_{topic}.md
    # Two separate, clean files in outputs/.
    safe_topic = topic.strip().replace(" ", "_").lower()[:60]
    filename   = f"final_report_{safe_topic}.md"

    saved_path = save_to_file(content=report, filename=filename)

    print(f"[Writer Agent] ✅ Report complete → {saved_path}")
    return report


# ── Quick standalone test ──────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing writer_agent.py with dummy notes...\n")

    dummy_notes = """
    LangChain is an open-source framework for building applications with large language models.
    It provides tools for chaining LLM calls, connecting to external data sources, and building agents.
    Key features include: prompt templates, memory, agents, and chains.
    Agents in LangChain can use tools like web search, calculators, and custom functions.
    The ReAct pattern (Reason + Act) is the most common agent pattern in LangChain.
    LangChain supports multiple LLM providers: OpenAI, Groq, Anthropic, and others.
    It is widely used in production AI applications for RAG, chatbots, and automation pipelines.
    """

    result = run_writer_agent(
        research_notes=dummy_notes,
        topic="LangChain agents"
    )
    print("\n--- REPORT PREVIEW ---")
    print(result[:500])
    print("\n✅ writer_agent.py is working!")
