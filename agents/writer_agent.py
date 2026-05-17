# Writer Agent
# agents/writer_agent.py

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv
import os

load_dotenv()

def run_writer_agent(research_notes: str, topic: str) -> str:

    if not research_notes or len(research_notes.strip()) < 50:
        print("[Writer Agent] ⚠️  Notes too short or empty. Stopping.")
        return "Error: Not enough research data to write a report."

    llm = ChatGroq(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        temperature=0.4,
        api_key=os.getenv("GROQ_API_KEY")
    )

    system_prompt = """
You are a professional research report writer, like a senior journalist or analyst.

Your job is to take raw research notes and transform them into a
clean, well-structured, engaging markdown report.

STRUCTURE RULES — pick subheadings that fit THIS specific topic:
- Person:      Early Life | Rise to Prominence | Achievements | Controversies | Legacy
- Technology:  What It Is | How It Works | Who Uses It | Limitations | Future Outlook
- Concept:     Core Idea | History | How It Works | Applications | Open Questions
- Event:       Background | What Happened | Key Players | Impact | Long-Term Effects
- Comparison:  At a Glance | Option A | Option B | Head-to-Head | Verdict
- Other:       use your best judgment — pick whatever serves the reader best

WRITING RULES:
1. Write full paragraphs under each subheading — not just bullet dumps
2. Use ## for main subheadings, ### for sub-points if needed
3. Include real facts, numbers, names, dates from the notes
4. Remove duplicate or repeated information
5. DO NOT search the web — only use what is in the notes given to you
6. DO NOT invent or guess any facts — only use what you are given
7. Minimum 450 words in the final report
8. End with a ## Bottom Line section — one tight paragraph of key takeaways

BANNED — never use these headings, ever:
Overview, Key Findings, Detailed Analysis, Conclusion
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"""
Topic: {topic}

Raw Research Notes:
{research_notes}

Write the full structured report now based only on the notes above.
        """)
    ]

    print("[Writer Agent] ✍️  Writing report...")
    response = llm.invoke(messages)
    report = response.content

    from tools.file_saver import save_to_file
    safe_topic = topic.strip().lower().replace(" ", "_")
    filename = f"report_{safe_topic}.md"
    save_to_file(content=report, filename=filename)

    print(f"[Writer Agent] ✅ Report saved as: {filename}")
    return report
