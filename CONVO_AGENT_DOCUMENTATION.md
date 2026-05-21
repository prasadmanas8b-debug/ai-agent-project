# Conversation Agent — Technical Documentation

**Project:** AI Agent System  
**File:** `agents/convo_agent.py`  
**Author:** AI Agent Project Team  
**Last Updated:** May 2026  
**Version:** 1.0

---

## 1. Overview

The **Conversation Agent** is the human-facing interface of the multi-agent AI pipeline. While every other agent in the system focuses on a narrow technical task — researching, writing, coding, reading PDFs, or interacting with GitHub — the Conversation Agent handles everything that doesn't require specialist work: **greetings, small-talk, clarifications, follow-up questions, status summaries, and simple factual Q&A**.

It acts as the "front desk" of the system. Before the Supervisor routes a task to a heavyweight specialist, it checks whether the input is simply a conversational message. If so, the Conversation Agent handles it directly — instantly, without burning API calls on research or code generation.

It also supports **multi-turn dialogue** by maintaining a running `conversation_history` in the shared pipeline state, allowing it to remember context across multiple exchanges within the same session.

---

## 2. Role in the System

```
User Input
    ↓
Supervisor Agent
    ├── "research quantum computing"   → Research Agent
    ├── "implement binary search"      → Coder Agent
    ├── "summarize report.pdf"         → PDF Agent
    ├── "list files on GitHub"         → GitHub Agent
    └── "hi / what can you do? / thanks / explain briefly"
                                       → Conversation Agent
                                            ↓
                                       Reply stored in convo_result
                                            ↓
                                       Supervisor → FINISH
```

The Supervisor routes to the Conversation Agent when the task is any of:
- A **greeting** (hi, hello, hey, good morning)
- **Small-talk** (how are you, thanks, nice work)
- A **clarification request** (what do you mean, can you explain, what exactly does X do)
- A **simple factual question** that doesn't require live web research
- A **status enquiry** (what have you done so far, what was the last result)
- Any **ambiguous input** that needs to be resolved before specialist routing

---

## 3. How It Works — Step by Step

### Step 1 — Receive Task Context
The agent receives the shared pipeline state containing the user's current message and the full conversation history so far.

| Field | Description |
|---|---|
| `task` | The current user message (e.g. "Hey, what can you help me with?") |
| `conversation_history` | List of past `{role, content}` turns from this session |

---

### Step 2 — Reconstruct Conversation Thread
The agent rebuilds the full message thread for the LLM by converting `conversation_history` into a sequence of `HumanMessage` and `AIMessage` objects, then appending the current `task` as the latest `HumanMessage`.

```
SystemMessage   ← persona + behaviour rules
HumanMessage    ← turn 1 user
AIMessage       ← turn 1 assistant
HumanMessage    ← turn 2 user
AIMessage       ← turn 2 assistant
...
HumanMessage    ← current task  (newest)
```

This gives the LLM full conversational context so replies stay coherent and don't repeat information already shared.

---

### Step 3 — Generate Reply via LLM
The agent calls **Groq's LLM** (`llama-3.3-70b-versatile`, temperature `0.7`) with the constructed message list.

The system prompt enforces the following behaviour rules:
- Warm, professional, succinct tone
- Replies capped at **150 words** (unless user explicitly asks for more)
- Never expose internal system details (agent names, LangGraph, state keys)
- If the user asks something that needs research/code/GitHub/PDF, acknowledges and signals handoff: *"Let me hand that off to the right specialist — one moment."*
- No repeating the user's words verbatim

---

### Step 4 — Update Conversation History
After generating the reply, both the user's message and the assistant's reply are appended to `conversation_history`:

```python
updated_history = previous_history + [
    {"role": "user",      "content": task},
    {"role": "assistant", "content": reply},
]
```

This ensures the next turn has full context, enabling natural multi-turn dialogue.

---

### Step 5 — Return Result
The agent updates two state fields and returns the full state:

| Field | Value |
|---|---|
| `convo_result` | The latest assistant reply (shown to user) |
| `conversation_history` | Updated list with both new turns appended |

---

## 4. Key Technical Details

| Property | Value |
|---|---|
| **LLM Model** | `llama-3.3-70b-versatile` (via Groq API) |
| **Temperature** | `0.7` (warm, natural conversational tone) |
| **Initialization** | Lazy — LLM created only on first call, not at import |
| **Max reply length** | 150 words (enforced by system prompt) |
| **History format** | `List[Dict[str, str]]` — each dict: `{role, content}` |
| **Valid roles** | `"user"` and `"assistant"` |
| **State key written** | `convo_result`, `conversation_history` |

---

## 5. System Prompt (Summary)

The Conversation Agent operates under the following persona rules:

> *"You are a helpful, friendly Conversation Agent — the human-facing interface of a multi-agent AI system.*
>
> *Handle greetings, small-talk, clarifications, status summaries, and simple factual questions. Never expose internal system details. If the task needs deep research, code, GitHub, or PDF work, say: 'Let me hand that off to the right specialist.' Keep replies under 150 words unless the user asks for more."*

---

## 6. Supervisor Routing Rules (Manager Agent)

The following rules in `manager_agent.py` govern when the Conversation Agent is selected:

```
Rule 13: task is a greeting, small-talk, clarification, or simple question
         (hi / hello / thanks / what is X / tell me / explain briefly / help / can you)
         AND no specialist work is needed
         → convo

Rule 14: convo_result is not empty
         → FINISH
```

The Conversation Agent always runs **after** all specialist checks — it is the fallback for human-facing interaction that doesn't fit any other agent's remit.

---

## 7. Dependencies

| Library | Purpose |
|---|---|
| `langchain-groq` | LLM interface to Groq API |
| `langchain-core` | Message types: `SystemMessage`, `HumanMessage`, `AIMessage` |
| `python-dotenv` | Load API keys from `.env` file |

**Required environment variable:**
```
GROQ_API_KEY=your_groq_api_key_here
```

No additional packages are required beyond what the rest of the pipeline already uses.

---

## 8. Input & Output

### Input (from pipeline state)
```python
{
    "task":                 "Hey, what can you help me with?",
    "research_notes":       "",
    "final_report":         "",
    "code_result":          "",
    "github_result":        "",
    "pdf_result":           "",
    "convo_result":         "",
    "conversation_history": [],   # empty on first turn
    "next":                 "convo"
}
```

### Output (updated pipeline state)
```python
{
    ...
    "convo_result": "Hey! I can help you research topics, write reports, generate Python code, interact with GitHub, or extract and summarize PDFs. What would you like to do?",
    "conversation_history": [
        {"role": "user",      "content": "Hey, what can you help me with?"},
        {"role": "assistant", "content": "Hey! I can help you research topics..."}
    ]
}
```

---

## 9. Multi-Turn Dialogue Example

The Conversation Agent retains context across multiple user messages within a session:

```
Turn 1
  User:      "Hi there!"
  Agent:     "Hey! Great to have you here. What would you like to do today?"

Turn 2
  User:      "What did you just say?"
  Agent:     "I greeted you and asked what you'd like to work on today."

Turn 3
  User:      "Can you research AI trends for me?"
  Agent:     "Absolutely — let me hand that off to the right specialist. One moment."
              → Supervisor re-routes to Research Agent
```

On Turn 3 the Conversation Agent correctly signals a handoff rather than trying to answer a research question itself.

---

## 10. Error Handling

| Scenario | Behaviour |
|---|---|
| LLM API call fails | Returns a polite error string in `convo_result`; does not crash the pipeline |
| `conversation_history` missing from state | Defaults to empty list `[]`; first turn works normally |
| `task` is empty string | LLM receives an empty HumanMessage; typically replies with a prompt for input |
| GROQ_API_KEY missing | `_get_llm()` raises on first call; caught by `except` block, error returned in `convo_result` |

---

## 11. State Schema Changes

Adding the Conversation Agent required two new fields in `graph/state.py`:

```python
class AgentState(TypedDict):
    ...
    convo_result: str
    # Written by Convo Agent — latest conversational reply shown to the user.

    conversation_history: List[Dict[str, str]]
    # Maintained by Convo Agent — running list of {role, content} turn dicts.
    # role is "user" or "assistant".
```

All existing agents are unaffected — they simply ignore these two new fields.

---

## 12. Pipeline Graph Changes

The following changes were made to `graph/pipeline_graph.py` to wire in the Conversation Agent:

```python
# New import
from agents.convo_agent import run_convo_agent

# New node
def convo_node(state: AgentState) -> AgentState:
    return run_convo_agent(state)

g.add_node("convo", convo_node)

# New conditional edge (in supervisor routing)
g.add_conditional_edges("supervisor", route, {
    ...
    "convo":  "convo",    # ← added
    "FINISH": END,
})

# New edge back to supervisor (standard pattern)
g.add_edge("convo", "supervisor")
```

---

## 13. Standalone Usage (for testing)

The agent can be run independently without the full pipeline:

```bash
python agents/convo_agent.py
```

This runs a built-in test responding to: `"Hey, what can you help me with?"`

To test multi-turn dialogue, pass in a pre-populated `conversation_history`:

```python
test_state = {
    "task": "What did I just ask?",
    "conversation_history": [
        {"role": "user",      "content": "What is quantum computing?"},
        {"role": "assistant", "content": "Quantum computing uses quantum bits..."},
    ],
    ...
}
out = run_convo_agent(test_state)
print(out["convo_result"])
```

---

## 14. How It Fits — Full System Overview

With the Conversation Agent added, the system now has **six specialist agents** all coordinated by the Supervisor:

| Agent | Trigger Keywords / Signals | Output Field |
|---|---|---|
| **Research Agent** | what / who / how / explain / trends / history / compare | `research_notes` |
| **Writer Agent** | *(research_notes filled, final_report empty)* | `final_report` |
| **Coder Agent** | code / implement / build / script / program | `code_result` |
| **GitHub Agent** | github / save / commit / push / list files | `github_result` |
| **PDF Agent** | pdf / summarize pdf / extract pdf / read pdf | `pdf_result` |
| **Conversation Agent** | hi / hello / thanks / what is / explain briefly / help | `convo_result` |

The Conversation Agent is always the **last fallback** — if none of the five specialist agents match, the Supervisor routes here. This ensures no user message ever goes unanswered.

---

## 15. Suggested Improvements (Roadmap)

- [ ] Persist `conversation_history` across sessions (save to file or database)
- [ ] Add intent detection: if user describes a new task mid-conversation, extract and re-route it automatically
- [ ] Support a "recap" command: summarise all previous agent outputs in plain English
- [ ] Add a confidence threshold — if the Convo Agent is uncertain, ask a clarifying question before answering
- [ ] Stream reply tokens to terminal for real-time output

---

*Documentation prepared for internal review. Part of the AI Agent System project.*
