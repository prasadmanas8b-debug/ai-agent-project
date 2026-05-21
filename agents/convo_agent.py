"""
agents/convo_agent.py  --  Conversation Agent: handles multi-turn dialogue,
clarifications, and general chat without needing research/code/github/pdf ops.
"""
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from graph.state import AgentState

load_dotenv()

_llm = None  # lazy init -- prevents crash on import when GROQ_API_KEY is absent

def _get_llm():
    global _llm
    if _llm is None:
        _llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            api_key=os.getenv("GROQ_API_KEY"),
        )
    return _llm

_SYSTEM_PROMPT = """
You are a helpful, friendly Conversation Agent -- the human-facing interface of a
multi-agent AI system.

Your responsibilities:
  1. Handle greetings, small-talk, and general questions the user asks.
  2. Clarify ambiguous tasks before routing to specialist agents.
  3. Summarise what the system has already done when the user asks.
  4. Answer simple factual questions that do not need web research.
  5. Keep the conversation natural, concise, and on-topic.

Tone: warm, professional, succinct. Avoid repeating the user's words back verbatim.
Never reveal internal system details (agent names, LangGraph, state keys).
If the user asks something that needs deep research, code, GitHub, or PDF work,
say: "Let me hand that off to the right specialist -- one moment."
Keep replies under 150 words unless the user explicitly asks for more detail.
"""

def run_convo_agent(state: AgentState) -> AgentState:
    """
    Handles conversational turns.
    Reads conversation_history (list of {role, content} dicts) from state,
    generates a reply, appends both turns to history, stores reply in convo_result.
    """
    task    = state.get("task", "")
    history = state.get("conversation_history", [])

    messages = [SystemMessage(content=_SYSTEM_PROMPT)]
    for turn in history:
        role    = turn.get("role", "user")
        content = turn.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        else:
            messages.append(AIMessage(content=content))

    messages.append(HumanMessage(content=task))

    print(f"\n\U0001f4ac Convo Agent -- responding to: {task[:100]}")

    try:
        response = _get_llm().invoke(messages)
        reply    = response.content.strip()
    except Exception as e:
        reply = f"Sorry, I ran into an issue: {e}"
        print(f"[Convo Agent] ERROR: {e}")

    updated_history = list(history) + [
        {"role": "user",      "content": task},
        {"role": "assistant", "content": reply},
    ]

    print(f"\U0001f4ac Convo Agent -- reply: {reply[:120]}")
    return {
        **state,
        "convo_result":         reply,
        "conversation_history": updated_history,
    }


if __name__ == "__main__":
    test_state: AgentState = {
        "task":                 "Hey, what can you help me with?",
        "research_notes":       "",
        "final_report":         "",
        "code_result":          "",
        "github_result":        "",
        "pdf_result":           "",
        "convo_result":         "",
        "conversation_history": [],
        "next":                 "",
    }
    out = run_convo_agent(test_state)
    print("\n--- Convo Agent Reply ---")
    print(out["convo_result"])
