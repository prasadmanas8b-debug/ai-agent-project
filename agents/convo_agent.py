"""
agents/convo_agent.py — Conversation Agent

The friendly face of the system. Handles multi-turn dialogue, greetings,
questions about the system, and clarifications.

Key upgrades:
  - Understands typos and informal language naturally
  - Knows exactly what the system can do and explains it clearly
  - Maintains conversation history across turns
  - Suggests what the user can try next based on context
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from graph.state import AgentState

load_dotenv()

_llm: ChatGroq | None = None


def _get_llm() -> ChatGroq:
    global _llm
    if _llm is None:
        _llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=1024,
            api_key=os.getenv("GROQ_API_KEY"),
        )
    return _llm


_SYSTEM_PROMPT = """
You are the friendly, knowledgeable front-end of a powerful multi-agent AI system.
You speak naturally, handle typos gracefully, and always give helpful, direct answers.

WHAT THIS SYSTEM CAN DO:
  🔍 Research    — Search the web and produce structured research reports on any topic
  ✍️  Write       — Turn research into polished reports, blog posts, summaries, explainers
  💻 Code        — Write Python scripts, algorithms, automation tools, API clients
  🐙 GitHub      — List, read, create, update, delete files and branches on GitHub
  📄 PDF         — Summarize, extract, OCR, convert, merge, split, create PDFs
  📧 Email       — Compose, send, read, analyze, reply, templates, phishing detection
  🗄️  Database   — Query SQLite/PostgreSQL/MySQL, export data, run NL-to-SQL
  💬 Chat        — Answer questions, clarify, explain — that's what you're doing now!

YOUR BEHAVIOR:
  - Be warm, direct, and concise (3-5 sentences per reply)
  - If the user asks what the system can do, give examples, not just a list
  - If the user's request is unclear, ask ONE clarifying question
  - If you can tell the user should actually be using another agent, gently say so:
    e.g. "Sounds like you want me to write some code — just say 'write a [thing]' and I'll do it!"
  - Never say you can't do something that's in the list above
  - Typos in the user's message are fine — understand their intent and respond normally

TONE: Helpful engineer-friend. Not corporate, not sycophantic. Real.
"""


def run_convo_agent(state: AgentState) -> AgentState:
    """
    Generate a conversational reply and update conversation history.

    Returns:
        Updated state with convo_result and conversation_history set.
    """
    task    = state.get("task", "")
    history = list(state.get("conversation_history") or [])

    print(f"\n💬 Convo Agent — task: {task[:100]}")

    # Build full message list: system + history + current message
    messages = [SystemMessage(content=_SYSTEM_PROMPT)]
    for turn in history:
        role = turn.get("role", "")
        content = turn.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
    messages.append(HumanMessage(content=task))

    try:
        response = _get_llm().invoke(messages)
        reply    = response.content.strip()
    except Exception as exc:
        reply = f"Sorry, I ran into an issue: {exc}. Try rephrasing your request."

    # Append this exchange to history
    history.append({"role": "user",      "content": task})
    history.append({"role": "assistant", "content": reply})

    print(f"💬 Convo Agent — replied ({len(reply)} chars)")
    return {**state, "convo_result": reply, "conversation_history": history}
