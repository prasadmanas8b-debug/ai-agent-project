"""
agents/writer_agent.py
Takes raw research notes and produces a polished markdown report.
Uses lazy LLM initialization so it's testable without API keys.
"""
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

_llm = None

def _get_llm():
    global _llm
    if _llm is None:
        _llm = ChatGroq(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            temperature=0.4,
            api_key=os.getenv("GROQ_API_KEY"),
        )
    return _llm

_SYSTEM_PROMPT = """
You are a professional research report writer — like a senior journalist or analyst.
Take raw research notes and transform them into a clean, structured, engaging markdown report.

STRUCTURE — pick subheadings that fit the topic:
- Person:      Early Life | Rise to Prominence | Achievements | Controversies | Legacy
- Technology:  What It Is | How It Works | Who Uses It | Limitations | Future Outlook
- Concept:     Core Idea | History | How It Works | Applications | Open Questions
- Event:       Background | What Happened | Key Players | Impact | Long-Term Effects
- Comparison:  At a Glance | Option A | Option B | Head-to-Head | Verdict
- Other:       use your best judgment

WRITING RULES:
1. Full paragraphs under each subheading — no bullet dumps
2. Use ## for main subheadings, ### for sub-points if needed
3. Include real facts, numbers, names, dates from the notes
4. Remove duplicate or repeated information
5. DO NOT search the web — use only the notes given
6. DO NOT invent facts — only use what is provided
7. Minimum 450 words
8. End with ## Bottom Line — one tight paragraph of key takeaways

BANNED headings: Overview | Key Findings | Detailed Analysis | Conclusion
"""

def run_writer_agent(research_notes: str, topic: str) -> str:
    if not research_notes or len(research_notes.strip()) < 50:
        print("[Writer Agent] ⚠️  Notes too short or empty. Stopping.")
        return "Error: Not enough research data to write a report."

    messages = [
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=(
            f"Topic: {topic}\n\n"
            f"Raw Research Notes:\n{research_notes}\n\n"
            f"Write the full structured report now based only on the notes above."
        )),
    ]
    print("[Writer Agent] ✍️  Writing report...")
    response = _get_llm().invoke(messages)
    report   = response.content

    try:
        from tools.file_saver import save_to_file
        safe   = topic.strip().lower().replace(" ", "_")[:50]
        fname  = f"report_{safe}.md"
        save_to_file(content=report, filename=fname)
        print(f"[Writer Agent] ✅ Report saved locally as: {fname}")
    except Exception as e:
        print(f"[Writer Agent] ⚠️  Could not save locally: {e}")

    return report
