# 🤖 AI Agent Pipeline — Phase 1, 2 & 3

> **Team of 3 CSE Students | Groq LLaMA3 + Tavily Search + LangChain + LangGraph**

A multi-agent pipeline that takes any natural language command, routes it to the right agents automatically, and produces research reports — saving them locally and optionally to GitHub.

---

## 📋 Table of Contents

- [How It Works](#-how-it-works)
- [Project Structure](#-project-structure)
- [Team Roles](#-team-roles--ownership)
- [Getting Started](#-getting-started)
- [API Keys Setup](#-api-keys-setup)
- [Running the Pipeline](#-running-the-pipeline)
- [Output Files](#-output-files)
- [LangGraph — The Core Concept](#-langgraph--the-core-concept)
- [Agent Comparison Table](#-agent-comparison-table)
- [Git Workflow](#-git-workflow-no-conflicts-guide)
- [Merging Without Conflicts](#-merging-without-conflicts)
- [Weekly Schedule](#-phase-3-weekly-schedule)
- [Lessons Learned](#-lessons-learned)
- [Troubleshooting](#-troubleshooting)
- [Git Cheat Sheet](#-git-cheat-sheet)
- [What's Next — Phase 4](#-whats-next--phase-4)

---

## ⚙️ How It Works

### Phase 1 — Single Research Agent
```
You type a topic → Research Agent searches web → saves raw notes
```

### Phase 2 — Sequential Pipeline
```
Research Agent → Writer Agent → saves polished report
```

### Phase 3 — LangGraph Orchestrated System (current)
```
You type ANYTHING in natural language
         ↓
[ Supervisor ] ← decides everything
    ↓       ↓       ↓
Research  Writer  GitHub
    ↓       ↓       ↓
    └───────→ END ←──┘

The Supervisor runs after EVERY agent to decide the next step.
```

**Examples of what you can type:**
| Input | What runs |
|-------|-----------|
| `Research the history of AI` | Research → Writer → FINISH |
| `List files in the agents folder` | GitHub → FINISH |
| `Research quantum computing and save to GitHub` | Research → Writer → GitHub → FINISH |
| `Create a branch called feature/phase-4` | GitHub → FINISH |
| `Do something useful` | Defaults to Research → Writer → FINISH |

---

## 📁 Project Structure

```
ai-agent-project/
│
├── agents/
│   ├── research_agent.py     ✅ Phase 1 — searches web, collects raw notes
│   ├── writer_agent.py       ✅ Phase 2 — rewrites notes into polished report
│   ├── manager_agent.py      ✅ Phase 3 — Supervisor, decides routing
│   └── github_agent.py       ✅ Phase 3 — performs GitHub repo actions
│
├── tools/
│   ├── web_search.py         ✅ Phase 1 — Tavily web search wrapper
│   ├── file_saver.py         ✅ Phase 2 — saves files with custom names
│   └── github_tools.py       ✅ Phase 3 — PyGithub API functions
│
├── graph/
│   ├── state.py              ✅ Phase 3 — shared AgentState TypedDict
│   └── pipeline_graph.py     ✅ Phase 3 — LangGraph graph definition
│
├── outputs/                  ← auto-generated reports (gitignored)
├── notebooks/                ← experiments & testing
│
├── main.py                   ✅ Phase 3 — single entry point, graph-driven
├── .env                      ← your real API keys (NEVER commit this)
├── .env.example              ← safe template to share with teammates
├── .gitignore                ← blocks .env, outputs/, pycache from GitHub
└── requirements.txt          ← all dependencies
```

---

## 👥 Team Roles & Ownership

| Member | Role | Files | API Key |
|--------|------|-------|---------|
| **Member 1 (Leader)** | All agents + graph + pipeline | `agents/`, `graph/`, `main.py` | `GROQ_API_KEY` |
| **Member 2** | Web Search Tool | `tools/web_search.py` | `TAVILY_API_KEY` |
| **Member 3** | File Saver + GitHub Tools | `tools/file_saver.py`, `tools/github_tools.py` | `GITHUB_TOKEN` |

> ⚠️ **Golden Rule:** Each member owns their file. **Never edit someone else's file without telling them first.**

---

## 🚀 Getting Started

```bash
git clone https://github.com/prasadmanas8b-debug/ai-agent-project.git
cd ai-agent-project
pip install -r requirements.txt
```

---

## 🔑 API Keys Setup

> ⚠️ The `.env` file contains your real keys. **NEVER push it to GitHub.** It is blocked by `.gitignore`.

### Keys You Need

| Key | Where to Get It | Free? | Who Needs It |
|-----|----------------|-------|--------------|
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) → API Keys | ✅ 100% free | Member 1 |
| `TAVILY_API_KEY` | [tavily.com](https://tavily.com) → API Keys | ✅ Free tier | Member 2 |
| `GITHUB_TOKEN` | GitHub → Settings → Developer Settings → Personal Access Tokens (classic) → give **repo** scope | ✅ Free | Member 3 |

### Create Your `.env` File

```env
GROQ_API_KEY=gsk_...your_groq_key_here
TAVILY_API_KEY=tvly-...your_tavily_key_here
GITHUB_TOKEN=ghp_...your_github_token_here
GITHUB_REPO=prasadmanas8b-debug/ai-agent-project
```

---

## ▶️ Running the Pipeline

### Full Graph Pipeline (Phase 3 — recommended)

```bash
python main.py
# → Type anything in natural language
# → Graph decides which agents to run
```

### Standalone Agent Tests

```bash
python agents/github_agent.py     # test GitHub agent independently
python tools/github_tools.py      # test raw GitHub API connection
python graph/pipeline_graph.py    # test graph builds without errors
```

### Phase 2 style (research + write only)

```bash
python agents/research_agent.py   # terminal mode
streamlit run agents/research_agent.py  # web UI
```

---

## 📄 Output Files

After running `python main.py` with `"Research artificial intelligence in healthcare and save to GitHub"`:

```
outputs/
├── report_artificial_intelligence_in_healthcare.md        ← raw research notes
└── final_report_artificial_intelligence_in_healthcare.md  ← polished 4-section report

GitHub repo:
└── docs/artificial_intelligence_in_healthcare.md  ← saved by GitHub Agent
```

The final report always has four sections:
```markdown
## Overview
## Key Findings
## Detailed Analysis
## Conclusion
```

---

## 🧠 LangGraph — The Core Concept

### Why Not Just More Python Functions?

Phase 2 was hardcoded: Research always ran first, Writer always second. Fine for two agents. But with three agents and different task types, you can't hardcode all the flows:

- Research-only task → just Research + Writer
- GitHub-only task → just GitHub Agent
- Research + save to GitHub → Research + Writer + GitHub

LangGraph solves this by making the flow **dynamic** — the Supervisor decides at runtime.

### The Graph

```
START → Supervisor → [conditional edge based on state["next"]]
           ↓               ↓               ↓               ↓
       research_node   writer_node   github_node          END
           ↓               ↓               ↓
           └───────────────┴───────────────┘
                           ↓
                       Supervisor (again)
```

After EVERY agent runs, control returns to the Supervisor. The Supervisor then re-reads the state and decides the next step. This loop is what makes the system truly agentic.

### Shared State — The Whiteboard

```python
class AgentState(TypedDict):
    task:           str   # ← set once, never changes
    research_notes: str   # ← Research Agent fills this
    final_report:   str   # ← Writer Agent fills this
    github_result:  str   # ← GitHub Agent fills this
    next:           str   # ← Supervisor fills this ("research"/"writer"/"github"/"FINISH")
```

Agents **never talk to each other directly**. They only read and write to this shared state.

### The Supervisor's Decision Logic

| Task Contains | Supervisor Routes To |
|--------------|---------------------|
| "research", "find", "what is", "explain" | `research` → `writer` → `FINISH` |
| "list files", "create branch", "show repo" | `github` → `FINISH` |
| "save to github", "commit", "push" | `research` → `writer` → `github` → `FINISH` |
| Vague / unclear | Defaults to `research` → `writer` → `FINISH` |

---

## 🤖 Agent Comparison Table

| | Research Agent | Writer Agent | GitHub Agent | Supervisor |
|--|---------------|--------------|--------------|------------|
| **Job** | Search web, collect notes | Rewrite notes into report | Perform GitHub actions | Decide who runs next |
| **Tools** | web_search, file_saver | file_saver only | github_tools only | None |
| **Input** | topic string | research_notes from state | task + optional report | full state |
| **Output** | raw notes dict | polished markdown | action result string | "next" agent name |
| **Browses web?** | ✅ Yes | ❌ Never | ❌ Never | ❌ Never |
| **LLM Model** | llama-3.1-8b-instant | llama-3.3-70b-versatile | llama-3.3-70b-versatile | llama-3.3-70b-versatile |

> **The most important rule:** Never give an agent tools it doesn't need. A constrained agent is a predictable agent.

---

## 🍽️ The Restaurant Analogy (GitHub Agent)

`github_tools.py` = **the kitchen** — raw cooking functions (create file, delete branch, list files). Knows nothing about intent.

`github_agent.py` = **the waiter** — reads the customer's natural language order, translates it into a kitchen ticket (JSON action), and brings back the result.

The LLM is the translator: it converts `"save the report to docs/"` → `{"action": "create_or_update_file", "path": "docs/report.md", "content": "..."}`.

---

## 🌿 Git Workflow (No Conflicts Guide)

### Branch Names

| Member | Branch Name |
|--------|------------|
| Member 1 (Leader) | `feature/research-agent` |
| Member 2 | `feature/web-search-tool` |
| Member 3 | `feature/file-saver-tool` |

### Daily Workflow

```bash
# START of day
git checkout main && git pull origin main
git checkout feature/your-branch-name && git merge main

# DURING the day
git add . && git commit -m "feat: describe what you did"

# END of day
git push origin feature/your-branch-name
```

---

## 🔀 Merging Without Conflicts

**Merge order (Member 1 does this):**
```
1️⃣  Member 3 PR  →  file_saver.py, github_tools.py   (no dependencies)
2️⃣  Member 2 PR  →  web_search.py
3️⃣  Member 1 PR  →  all agents, graph/, main.py       (depends on both)
```

---

## 📅 Phase 3 Weekly Schedule

| Day | All 3 Together | Member 1 | Member 2 | Member 3 |
|-----|---------------|----------|----------|----------|
| **Day 1** | Read LangGraph concepts, install deps | Study State + Supervisor logic | — | Build `github_tools.py` skeleton |
| **Day 2** | — | Build `graph/state.py` | — | Complete `github_tools.py` + test |
| **Day 3** | — | Build `manager_agent.py` (Supervisor) | Test web_search edge cases | Build `github_agent.py` |
| **Day 4** | — | Build `graph/pipeline_graph.py` | — | Test `github_agent.py` standalone |
| **Day 5** | Connect all pieces | Update `main.py` | — | — |
| **Day 6–7** | Run all 5 tests together | Fix routing bugs | — | Fix GitHub errors |

**5 tests before Phase 3 is done:**
| Test | Input | Expected |
|------|-------|----------|
| 1 | `Research the history of the internet` | Research + Writer run, report saved |
| 2 | `List all files in the agents folder` | GitHub runs, shows file list |
| 3 | `Research quantum computing and save to docs/quantum.md` | Research → Writer → GitHub |
| 4 | `Do something useful` | Defaults to research gracefully, no crash |
| 5 | `Create a file that already exists` | GitHub Agent returns error message, no crash |

---

## 💡 Lessons Learned

| Phase | Lesson | What It Taught Us |
|-------|--------|------------------|
| Phase 1 | Understand before building | Mental models first. Jumping to code without understanding ReAct causes confusion. |
| Phase 2 | Fix at source | When research_agent returned a dict, fixing in main.py was a workaround. Real fix is at source. |
| Phase 2 | Model size matters | Small models (8b) fail strict ReAct format. Use 70b for agents that need structured output. |
| Phase 2 | Validate agent output | Never blindly pass agent output to the next step. Always check: is this research or an error? |
| Phase 3 | Supervisor does NO work | The moment the Supervisor tries to also research or write, the architecture collapses. |
| Phase 3 | State between nodes | Always print state after each node during testing. Silent failures are the hardest to debug. |
| Phase 3 | One tool per agent | Never give an agent tools it doesn't need. Constrained = predictable. |

---

## 🛠️ Troubleshooting

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| `ModuleNotFoundError: langgraph` | Not installed | `pip install langgraph` |
| Supervisor loops forever | `FINISH` condition missing or unclear | Check Supervisor prompt — ensure "FINISH" rule is explicit |
| `GitHub 401 Unauthorized` | Token wrong or expired | Regenerate token on GitHub, update `.env` |
| `GitHub 404 Not Found` | Wrong repo name | Check `GITHUB_REPO=username/reponame` exactly in `.env` |
| State field is `None` | Agent didn't update state | Check agent node returns `{**state, "field": value}` |
| Writer runs before research | Conditional edge wrong | Check routing logic in `pipeline_graph.py` |
| `dict object has no attribute strip` | research_agent returns dict | Extract with `result["report"]` in the node wrapper |
| LLM returns non-JSON for GitHub | Model formatting issue | Prompt says "ONLY JSON" — also strip code fences before parsing |
| `git push` rejected | Need to sync first | `git pull origin main` then push again |

---

## 📖 Git Cheat Sheet

| What You Want to Do | Command |
|--------------------|---------|
| See changed files | `git status` |
| Save changes locally | `git add .` then `git commit -m "message"` |
| Upload to GitHub | `git push origin feature/your-branch-name` |
| Get latest from teammates | `git pull origin main` |
| Switch to your branch | `git checkout feature/your-branch-name` |
| See all branches | `git branch` |
| Undo last commit (careful!) | `git reset --soft HEAD~1` |

---

## 🧰 Tech Stack

| Tool | Purpose | Free? |
|------|---------|-------|
| [Groq](https://console.groq.com) | Ultra-fast LLaMA3 AI for all three agents | ✅ |
| [Tavily](https://tavily.com) | Web search built for AI agents | ✅ |
| [LangChain](https://langchain.com) | Framework connecting LLM + tools | ✅ |
| [LangGraph](https://langchain-ai.github.io/langgraph/) | Graph-based multi-agent orchestration | ✅ |
| [PyGithub](https://pygithub.readthedocs.io/) | Python wrapper for GitHub API | ✅ |
| [Streamlit](https://streamlit.io) | Web UI for research agent | ✅ |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | Safe API key loading | ✅ |

---

## ➡️ What's Next — Phase 4

Phase 4 is the **UI layer** — a Streamlit chat interface where:
- User types naturally and sees the pipeline run in real time
- Live status updates show which agent is running
- Rendered report preview appears on the page
- Download button for the final `.md` file

The backend (all agents + graph) is already done. Phase 4 is putting a clean face on it.

📖 Start reading: [Streamlit docs](https://docs.streamlit.io) | [st.status](https://docs.streamlit.io/library/api-reference/status)

---

<p align="center">
  <i>AI Agent Project — Phase 1, 2 & 3 | LangGraph Multi-Agent Pipeline</i>
</p>
