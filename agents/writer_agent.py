"""
agents/writer_agent.py — Writer Agent

A senior technical writer. Turns raw research into polished documents.
Detects output type from the task (report, blog, summary, explainer).
Saves the output locally to outputs/report_<slug>.md automatically.
"""

import os
import re
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

_llm: ChatGroq | None = None


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
You are a senior technical writer and editor.

STEP 1 — Detect output type from the task:
  "blog" / "article" / "post"          → engaging blog post
  "summary" / "summarize" / "tldr"     → concise executive summary (< 250 words)
  "explain" / "how does" / "what is"   → clear, beginner-friendly explainer
  default                               → formal research report

STEP 2 — Write the document using this structure (for formal report):

# [Clear, Descriptive Title]

## Executive Summary
2-3 sentences. The most important points, right up front.

## Key Findings
- 5-10 specific, factual bullet points from the research.

## Analysis
Detailed explanation in logical sub-sections. Use headers. Be specific.

## Implications
What this means — who should care and why.

## Conclusion
2-3 clear, actionable takeaways.

QUALITY RULES:
  - Be specific: use numbers, names, dates when available
  - No filler ("It is worth noting…", "In today's world…")
  - Explain all jargon on first use
  - Do NOT speculate beyond the research notes provided
  - Target 500-900 words for reports; 150-250 for summaries
"""


def _make_slug(task: str) -> str:
    slug = re.sub(r"[^\w\s]", "", task.lower())
    slug = re.sub(r"\s+", "_", slug.strip())[:50].strip("_")
    return slug or "report"


def _save_locally(slug: str, content: str) -> str:
    os.makedirs("outputs", exist_ok=True)
    path = os.path.join("outputs", f"report_{slug}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def run_writer_agent(research_notes: str, task: str) -> str:
    """
    Convert research notes into a polished markdown document.

    Saves the result to outputs/report_<slug>.md.

    Args:
        research_notes: Raw text from the Research Agent.
        task:           Original user task (determines output style).

    Returns:
        Markdown-formatted document string.
    """
    print(f"\n✍️  Writer Agent — task: {task[:100]}")

    user_msg = (
        f"USER TASK: {task}\n\n"
        f"RESEARCH NOTES:\n{research_notes[:6000]}\n\n"
        f"Write the document now."
    )

    try:
        response = _get_llm().invoke([
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=user_msg),
        ])
        report = response.content.strip()
    except Exception as exc:
        msg = f"[Writer Agent ERROR] {exc}"
        print(msg)
        return msg

    if not report:
        report = f"# {task}\n\n{research_notes[:2000]}"

    slug       = _make_slug(task)
    local_path = _save_locally(slug, report)
    print(f"✍️  Writer Agent — saved: {local_path} ({len(report)} chars)")
    return report
