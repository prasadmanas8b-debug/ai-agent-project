"""
agents/writer_agent.py — Writer Agent.

Takes raw research notes and the original task, then produces a polished,
well-structured markdown report via Groq (llama-3.3-70b).
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

_llm: ChatGroq | None = None  # lazy init


def _get_llm() -> ChatGroq:
    global _llm
    if _llm is None:
        _llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.4,
            max_tokens=4096,
            api_key=os.getenv("GROQ_API_KEY"),
        )
    return _llm


_SYSTEM_PROMPT = """
You are a professional technical writer.

Given research notes and a user task, write a polished, well-structured markdown
report. Follow this structure exactly:

# [Descriptive Title]

## Executive Summary
2-3 sentence overview of the most important points.

## Key Findings
- Concise bullet points (5-10 items).

## Analysis
Detailed explanation organized into logical sub-sections.

## Conclusion
Actionable takeaways in 2-3 sentences.

Rules:
- Use clear, plain language — no jargon without explanation.
- Do NOT include opinions or speculation beyond the research notes.
- Format numbers, dates, and technical terms consistently.
- Aim for 400-800 words total.
"""


def run_writer_agent(research_notes: str, task: str) -> str:
    """
    Turn research notes into a polished markdown report.

    Args:
        research_notes: Raw text from the Research Agent.
        task:           Original user task (used for context / title).

    Returns:
        Markdown-formatted report string, or an error message.
    """
    print(f"\n✍️  Writer Agent — task: {task[:100]}")

    user_msg = (
        f"Task / Topic: {task}\n\n"
        f"Research Notes:\n{research_notes[:6000]}"
    )

    try:
        response = _get_llm().invoke([
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=user_msg),
        ])
        report = response.content.strip()
        print(f"✍️  Writer Agent — done ({len(report)} chars)")
        return report
    except Exception as exc:
        msg = f"[Writer Agent ERROR] {exc}"
        print(msg)
        return msg
