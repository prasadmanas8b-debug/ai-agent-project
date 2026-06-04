"""
agents/convo_agent.py — Conversation Agent.

Handles multi-turn dialogue, clarifications, and general chat without
triggering the research/code/github/pdf pipeline.
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from graph.state import AgentState

load_dotenv()

_llm: ChatGroq | None = None  # lazy init


def _get_llm() -> ChatGroq:
    global _llm
    if _llm is None:
        _llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            api_key=os.getenv("GROQ_API_KEY"),
        )
    return _llm


_SYSTEM_PROMPT = """
You are a helpful, friendly Conversation Agent — the human-facing interface of a
multi-agent AI system.

Your responsibilities:
  1. Handle greetings, small-talk, and general questions warmly.
  2. Clarify ambiguous requests before passing them to other agents.
  3. Explain what the system can and cannot do.

Keep replies concise (3-5 sentences max). Be direct and friendly.
Do NOT perform research, write code, or interact with GitHub — just converse.
"""


def run_convo_agent(state: AgentState) -> AgentState:
    """
    Generate a conversational reply and update conversation_history.

    Returns:
        Updated state with convo_result and conversation_history set.
    """
    task    = state.get("task", "")
    history = list(state.get("conversation_history") or [])

    print(f"\n💬 Convo Agent — task: {task[:100]}")

    # Build message list: system + history + new user message
    messages = [SystemMessage(content=_SYSTEM_PROMPT)]
    for turn in history:
        if turn.get("role") == "user":
            messages.append(HumanMessage(content=turn["content"]))
        elif turn.get("role") == "assistant":
            messages.append(AIMessage(content=turn["content"]))
    messages.append(HumanMessage(content=task))

    try:
        response = _get_llm().invoke(messages)
        reply    = response.content.strip()
    except Exception as exc:
        reply = f"[Convo Agent ERROR] {exc}"

    # Append this turn to history
    history.append({"role": "user",      "content": task})
    history.append({"role": "assistant", "content": reply})

    print(f"💬 Convo Agent — replied ({len(reply)} chars)")
    return {**state, "convo_result": reply, "conversation_history": history}
