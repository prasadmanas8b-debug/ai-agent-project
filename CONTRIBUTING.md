# Contributing to AI Agent System

> A guide for team members and open-source contributors.

---

## Project Structure

```
ai-agent-project/
├── agents/          ← One file per specialist agent
├── graph/           ← LangGraph pipeline and shared state
├── tools/           ← Reusable utilities (search, file I/O, retry, security)
├── config/          ← Centralized settings (settings.py)
├── api/             ← FastAPI endpoints (PDF, Email)
├── frontend/        ← React UI (EmailAgent, PDFAgent)
├── observability/   ← Logging, metrics, tracing
├── tests/           ← Unit + integration tests
├── outputs/         ← Generated files (git-ignored)
└── main.py          ← Entry point
```

---

## How to Add a New Agent

### Step 1 — Create the agent file

Create `agents/my_agent.py`:

```python
from agents._base_agent import BaseAgent, AgentOutput
from graph.state import AgentState
from langchain_core.messages import SystemMessage, HumanMessage

class MyAgent(BaseAgent):
    name = "my_agent"

    def run(self, state: AgentState) -> AgentState:
        with self.llm_call("my task description") as ctx:
            response = self.invoke_llm([
                SystemMessage(content="You are a specialist in X."),
                HumanMessage(content=state["task"])
            ])
            ctx.output = AgentOutput(result=response.content)
            return {**state, "my_result": response.content}

def run_my_agent(state: AgentState) -> AgentState:
    return MyAgent().run(state)
```

### Step 2 — Add the result field to AgentState

In `graph/state.py`, add:
```python
my_result: str   # Result from My Agent
```

### Step 3 — Register in the pipeline graph

In `graph/pipeline_graph.py`:
```python
from agents.my_agent import run_my_agent

def my_node(state: AgentState) -> AgentState:
    return run_my_agent(state)

# In build_graph():
g.add_node("my_agent", my_node)
g.add_conditional_edges("supervisor", _route, {
    ...,
    "my_agent": "my_agent",
})
g.add_edge("my_agent", "supervisor")
```

### Step 4 — Update the supervisor routing

In `agents/manager_agent.py`, add the agent to the system prompt:
```
my_agent → describe what tasks it handles
```

### Step 5 — Write tests

In `tests/test_my_agent.py`:
```python
def test_my_agent_basic():
    from agents.my_agent import run_my_agent
    state = {...}
    result = run_my_agent(state)
    assert "my_result" in result
```

---

## How to Add a New Tool

Create `tools/my_tool.py` with a single responsibility.
Import only what you need — no circular imports.
Write a docstring explaining inputs, outputs, and error cases.
Add it to the relevant agent's imports.

---

## Code Standards

1. All agents MUST inherit BaseAgent — never define a standalone _llm.
2. All config MUST come from `from config.settings import settings` — never os.getenv() directly.
3. Every function needs a docstring (even one line).
4. No hardcoded strings — use constants or settings.
5. All new files must have a module docstring at the top.
6. Run tests before pushing: `python -m pytest tests/ -v`

---

## Environment Setup

```bash
git clone https://github.com/prasadmanas8b-debug/ai-agent-project
cd ai-agent-project
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Fill in your API keys in .env
python main.py
```

---

## Team Roles (Original)
- Member 1 — Research Agent + Dynamic Research
- Member 2 — Web Search Tool + GitHub Tools
- Member 3 — File Saver + Config

All members should follow this guide when adding new features.

