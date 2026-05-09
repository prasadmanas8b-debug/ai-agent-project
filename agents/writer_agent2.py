# Writer Agent
# agents/writer_agent.py

from langchain_groq import ChatGroq
# ChatGroq → the Groq LLM class from LangChain
# Same one your research agent used

from langchain.schema import SystemMessage, HumanMessage
# SystemMessage → sets the agent's personality and rules
# HumanMessage  → the actual input/task we give the agent

from dotenv import load_dotenv
# load_dotenv → reads your .env file and loads API keys into memory

import os
# os → to read environment variables like GROQ_API_KEY

load_dotenv()
# Call this BEFORE using any API key
# Without this, os.getenv("GROQ_API_KEY") returns None
def _detect_format(topic: str) -> str:
    
    """
    Detects what kind of output format suits the query.
    Returns a format instruction string.
    """
    topic_lower = topic.lower()

    # Comparison queries
    if any(word in topic_lower for word in ["vs", "versus", "compare", "difference between", "better"]):
        return """
Use a COMPARISON TABLE format:
- Start with a brief ## Overview (2 sentences)
- Create a markdown table comparing the two subjects
- Add ## Key Differences section with bullet points
- End with ## Verdict — which is better and why
"""

    # Timeline / history queries
    elif any(word in topic_lower for word in ["history", "timeline", "evolution", "when did", "year"]):
        return """
Use a TIMELINE format:
- Start with ## Overview
- Create a chronological ## Timeline section with years as headers
- Add ## Impact section explaining significance
- End with ## Conclusion
"""

    # Person / who queries
    elif any(word in topic_lower for word in ["who is", "who was", "who became", "cm", "president", "ceo", "founder"]):
        return """
Use a PERSON PROFILE format:
- Start with ## Overview (who they are, current role)
- Add ## Background (education, early career)
- Add ## Key Achievements as bullet points
- End with ## Current Role & Responsibilities
"""

    # Statistics / market queries
    elif any(word in topic_lower for word in ["market", "size", "revenue", "growth", "statistics", "data", "numbers"]):
        return """
Use a DATA & STATS format:
- Start with ## Overview
- Add ## Key Statistics with a markdown table of numbers
- Add ## Market Breakdown section
- End with ## Future Outlook
"""

    # Default format
    else:
        return """
Use this standard format:
- ## Overview
- ## Key Findings (bullet points)
- ## Detailed Analysis
- ## Conclusion
"""
def run_writer_agent(research_notes: str, topic: str) -> str:
    format_instructions = _detect_format(topic)
    # research_notes → the text your research agent returned
    # topic          → the original topic (used for naming the file)
    # -> str         → returns the final report as a string

    # ── GUARD CLAUSE ──────────────────────────────────────────
    if not research_notes or len(research_notes.strip()) < 50:
        print("[Writer Agent] ⚠️  Notes too short or empty. Stopping.")
        return "Error: Not enough research data to write a report."
    # Why? → If research agent returned nothing or very little,
    # the writer will hallucinate facts. We stop it early instead.
    # .strip() → removes blank spaces before checking length

    # ── LLM SETUP ─────────────────────────────────────────────
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        # same model your research agent used
        # 70b = 70 billion parameters (smarter, slower)
        # 8192 = max tokens it can handle at once

        temperature=0.4,
        # temperature controls creativity vs precision
        # 0.0 = very precise, robotic, repetitive
        # 1.0 = very creative, unpredictable
        # 0.4 = slightly creative but mostly factual — good for reports

        api_key=os.getenv("GROQ_API_KEY")
        # reads GROQ_API_KEY from your .env file
        # never hardcode the actual key string here
    )

    # ── SYSTEM PROMPT ─────────────────────────────────────────
    system_prompt = f"""
You are a professional technical report writer.
Your job is to take raw research notes and write a clean report.

{format_instructions}
note: try to add a header and footer to the output for better clerification and better view and make it more attractive 
Rules:
1. Use markdown formatting throughout
2. Remove duplicate information
3. Professional, neutral tone
4. DO NOT search the web — only use the notes given
5. DO NOT invent facts — only use what you are given
"""
    # Why a strict system prompt?
    # The LLM is the same model as your research agent
    # The ONLY thing making this agent behave differently is this prompt
    # Without rule 5 and 6, it will add made-up facts — very dangerous

    # ── BUILD THE MESSAGES ────────────────────────────────────
    messages = [
        SystemMessage(content=system_prompt),
        # SystemMessage → tells the LLM WHO it is and WHAT rules to follow
        # This is like the agent's job description

        HumanMessage(content=f"""
Topic: {topic}

Raw Research Notes:
{research_notes}

Write the full structured report now based only on the notes above.
        """)
        # HumanMessage → the actual task we're giving the agent
        # We pass the topic AND the research notes together
        # f-string → inserts the actual values of topic and research_notes
    ]

    # ── CALL THE LLM ──────────────────────────────────────────
    print("[Writer Agent] ✍️  Writing report...")
    response = llm.invoke(messages)
    # .invoke() → sends the messages to Groq API
    # waits for the full response
    # returns a response object

    report = response.content
    # .content → extracts just the text string from the response object
    # response also has metadata, token counts etc — we don't need those

    # ── SAVE THE REPORT ───────────────────────────────────────
    from tools.file_saver import save_to_file
    # imported here (not at top) to avoid circular import issues
    # circular import = A imports B, B imports A = crash

    safe_topic = topic.strip().lower().replace(" ", "_")
    # .strip()      → removes leading/trailing spaces
    # .lower()      → converts to lowercase
    # .replace()    → replaces spaces with underscores
    # Example: "AI in Healthcare" → "ai_in_healthcare"

    filename = f"report_{safe_topic}.md"
    # Final filename example: "report_ai_in_healthcare.md"

    save_to_file(content=report, filename=filename)
    # calls the updated file_saver function
    # saves the report in outputs/ folder

    print(f"[Writer Agent] ✅ Report saved as: {filename}")
    return report
    # return the report text so main.py can preview it  
