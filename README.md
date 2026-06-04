<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=200&section=header&text=AI%20Agent%20System&fontSize=56&fontColor=fff&animation=twinkling&fontAlignY=38&desc=Production-Grade%20Multi-Agent%20AI%20%7C%20Research%20%C2%B7%20Code%20%C2%B7%20PDF%20%C2%B7%20Email%20%C2%B7%20GitHub%20%C2%B7%20Database&descAlignY=62&descSize=16" width="100%"/>

<br/>

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-Orchestration-00C7B7?style=for-the-badge&logo=graphql&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![Groq](https://img.shields.io/badge/Groq-llama--3.3--70b-F55036?style=for-the-badge&logo=meta&logoColor=white)](https://groq.com)
[![React](https://img.shields.io/badge/React-Frontend-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](LICENSE)

<br/>

> **A production-ready Multi-Agent AI system** where 8 specialist agents collaborate under a smart supervisor to research, write, generate code, manage PDFs, handle emails, interact with GitHub, and query databases — all orchestrated through a LangGraph state machine.
>
> *Think of it as a full AI engineering team, running on a single command.*

<br/>

[🚀 Quick Start](#-quick-start) · [🏗️ Architecture](#️-architecture) · [🤖 Agents](#-agents) · [📁 Folder Structure](#-folder-structure) · [🔄 Workflow](#-how-the-workflow-works) · [⚙️ Setup](#️-environment-setup)

</div>

---

## 📊 System at a Glance

| Property | Value |
|---|---|
| 🤖 Agents | **8** — Research, Writer, Coder, GitHub, PDF, Email, Convo, Database |
| 🧠 LLM | **Groq · llama-3.3-70b-versatile** (supervisor, coder, research, writer, convo, github, database) |
| 🦙 LLM (heavy agents) | **Groq · llama-4-scout-17b** (PDF, Email — 100+ feature handlers) |
| 🔍 Web Search | **Tavily API** with LLM fallback if unavailable |
| 🧩 Orchestration | **LangGraph** `StateGraph` — supervisor-routed pipeline |
| 📄 PDF Features | **100+** handlers across 20 categories |
| 📧 Email Features | **80+** handlers across 18 categories |
| 🗄️ Database | **SQLite / PostgreSQL / MySQL** — 42+ operations |
| 🌐 API | **FastAPI** endpoints for PDF and Email agents |
| 🎨 Frontend | **React + Tailwind CSS** (EmailAgent.jsx, PDFAgent.jsx) |
| 🔒 Safety | GitHub writes locked to `git_agent_output/`, DB read-only mode |
| 🛡️ Typo Tolerance | All agents understand misspellings and informal phrasing |

---

## 🏗️ Architecture

The system uses a **Supervisor → Agent → Supervisor** loop powered by LangGraph.

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Input                              │
│              "Research AI trends and write a report"            │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    🧠 SUPERVISOR                                 │
│              (agents/manager_agent.py)                          │
│                                                                 │
│  • Reads full task text + state                                 │
│  • Understands intent even with typos / vague language          │
│  • Decides: which agent runs next?                              │
│  • Returns ONE word: research | writer | coder | … | FINISH    │
└────────┬──────────────────────────────────────────┬────────────┘
         │  routes to                               │  loops back
         ▼                                          │
┌────────────────────────────────────────────┐      │
│              SPECIALIST AGENTS              │      │
│                                            │      │
│  🔍 research   ──→  research_notes         │      │
│  ✍️  writer     ──→  final_report           │──────┘
│  💻 coder      ──→  code_result            │
│  🐙 github     ──→  github_result          │
│  📄 pdf        ──→  pdf_result             │
│  📧 email      ──→  email_result           │
│  💬 convo      ──→  convo_result           │
│  🗄️  database  ──→  db_result              │
└────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ✅ FINISH                                     │
│              Results printed + saved to outputs/                │
└─────────────────────────────────────────────────────────────────┘
```

### Key Design Principles

- **Single shared state** — `AgentState` (a TypedDict) is the only thing passed between agents. Each agent reads the full state and writes only its own field.
- **Supervisor is the only router** — no agent decides what happens next. Only the Supervisor does.
- **Loop until done** — every agent returns to the Supervisor after finishing. The Supervisor decides if another agent is needed or if it's time to FINISH.
- **Typo-tolerant** — the Supervisor uses an LLM to *understand intent*, not keyword matching. Misspellings and vague prompts are handled gracefully.
- **Graceful fallbacks** — if Tavily is unavailable, Research falls back to LLM knowledge. If email/DB credentials aren't set, agents mock the operation and explain why.

---

## 📁 Folder Structure

```
ai-agent-project/
│
├── main.py                          # ← Entry point. Run this to start the system.
├── requirements.txt                 # All Python dependencies
├── .env.example                     # Template — copy to .env and fill in your keys
├── .gitignore
├── README.md                        # This file
├── DOCUMENTATION.md                 # Full technical documentation
│
├── graph/                           # LangGraph pipeline definition
│   ├── __init__.py
│   ├── state.py                     # AgentState TypedDict — the shared whiteboard
│   └── pipeline_graph.py            # StateGraph: nodes, edges, routing logic
│
├── agents/                          # All specialist agents live here
│   ├── manager_agent.py             # 🧠 Supervisor — routes tasks to agents
│   ├── dynamic_research_agent.py    # 🔍 Research Agent (ReAct + Tavily)
│   ├── writer_agent.py              # ✍️  Writer Agent
│   ├── coder_agent.py               # 💻 Coder Agent — generates & saves Python code
│   ├── github_agent.py              # 🐙 GitHub Agent — file/branch operations
│   ├── pdf_agent.py                 # 📄 PDF Agent — 100+ features
│   ├── email_agent.py               # 📧 Email Agent — 80+ features
│   ├── convo_agent.py               # 💬 Conversation Agent
│   └── database_agent.py            # 🗄️  Database Agent — SQLite/PG/MySQL
│
├── tools/                           # Reusable utility functions used by agents
│   ├── web_search.py                # Tavily API wrapper → search_web()
│   ├── github_tools.py              # PyGithub wrappers → create/read/update/delete
│   ├── file_saver.py                # Local file save → save_report(), list_reports()
│   └── dynamic_file_saver.py        # Dynamic output saver with auto-naming
│
├── api/                             # FastAPI HTTP endpoints
│   ├── email_endpoint.py            # POST /email — Email Agent over HTTP
│   └── pdf_endpoint.py              # POST /pdf — PDF Agent over HTTP
│
├── frontend/                        # React UI components
│   ├── EmailAgent.jsx               # Email Agent chat interface
│   └── PDFAgent.jsx                 # PDF Agent upload + result interface
│
├── tests/                           # Test suite
│   ├── test_suite.py                # Main tests — all agents (pytest + unittest)
│   └── test_database_agent.py       # Database Agent specific tests
│
├── outputs/                         # ← Auto-created. All local outputs land here.
│   ├── code_*.py                    # Generated Python code files
│   ├── report_*.md                  # Generated research reports
│   ├── email_output.html            # HTML email outputs
│   ├── pdf_agent_output.pdf         # PDF agent outputs
│   └── ...
│
└── git_agent_output/                # ← Files saved to GitHub by Coder/GitHub agents
    ├── code_*.py
    └── report_*.md
```

> 📌 `outputs/` is local only (gitignored). `git_agent_output/` is committed to the repo by the agents themselves.

---

## 🔄 How the Workflow Works

Here's how the system handles different types of tasks, step by step.

### Example 1 — Research + Report

**Task:** `"Research the latest trends in quantum computing"`

```
1. main.py         Builds initial AgentState with task set, all results empty
2. Supervisor      Reads task → no results yet → routes to: research
3. Research Agent  Searches Tavily (3-4 queries) → fills research_notes
4. Supervisor      Reads state → research_notes filled, final_report empty → routes to: writer
5. Writer Agent    Reads research_notes → generates polished report → fills final_report
                   Also saves: outputs/report_research_the_latest_trends_in_quantum.md
6. Supervisor      Reads state → final_report filled, no code/github task → FINISH
7. main.py         Prints report preview
```

---

### Example 2 — Direct Coding Task

**Task:** `"wrtie a bianry serach algortihm"` *(typos intentional)*

```
1. main.py         Builds initial AgentState
2. Supervisor      LLM reads task → understands "binary search" → routes to: coder
                   (No research step needed — it's a direct coding task)
3. Coder Agent     LLM silently corrects typos → generates binary_search.py
                   Saves to: outputs/code_wrtie_a_bianry_serach_algortihm.py (local)
                   Pushes to: git_agent_output/code_wrtie_a_bianry_serach_algortihm.py (GitHub)
4. Supervisor      code_result filled, no github push requested → FINISH
5. main.py         Prints: "✅ Code generated (X lines) | Local: ... | GitHub: ..."
```

---

### Example 3 — Research → Code → GitHub

**Task:** `"Research merge sort, implement it, and save to GitHub"`

```
1. Supervisor      → research
2. Research Agent  → fills research_notes
3. Supervisor      → writer (research done, report needed first)
4. Writer Agent    → fills final_report
5. Supervisor      → coder (report done + task mentions "implement")
6. Coder Agent     → fills code_result, saves .py locally + GitHub
7. Supervisor      → FINISH (github push already done by Coder Agent)
```

---

### Example 4 — PDF Task

**Task:** `"Summarize the PDF at uploads/report.pdf"`

```
1. Supervisor      Sees "pdf" in task → routes directly to: pdf
2. PDF Agent       Loads file → extracts text → LLM summarizes → fills pdf_result
3. Supervisor      pdf_result filled → FINISH
4. main.py         Prints summary (skips large base64 fields)
```

---

### Example 5 — Chat / General Question

**Task:** `"What can this system do?"` or `"hi"`

```
1. Supervisor      No specific agent keyword → routes to: convo
2. Convo Agent     Knows the full system capabilities → gives a helpful reply
                   Maintains conversation_history for multi-turn context
3. Supervisor      convo_result filled → FINISH
4. main.py         Prints the reply
```

---

## 🤖 Agents

### 🧠 Supervisor — `agents/manager_agent.py`
The central router. Uses `llama-3.3-70b` (temperature=0) to read the task and current state, then return the name of the next agent to run. Handles typos and vague phrasing through LLM understanding, with a fuzzy fallback map for edge cases.

**Input:** Full `AgentState` (task text + boolean flags for each result field)  
**Output:** Sets `state["next"]` to one of: `research | writer | coder | github | pdf | email | convo | database | FINISH`

---

### 🔍 Research Agent — `agents/dynamic_research_agent.py`
A ReAct agent that searches the web via Tavily (up to 8 iterations, 6 results per search). Produces a structured markdown report. If Tavily is unavailable, falls back to LLM training knowledge and clearly labels the output.

**Output:** Sets `state["research_notes"]`  
**Saved to:** (in-memory only — passed to Writer Agent)

---

### ✍️ Writer Agent — `agents/writer_agent.py`
Transforms research notes into a polished document. Detects the desired output type from the task (report, blog, summary, explainer) and adapts structure and tone accordingly.

**Output:** Sets `state["final_report"]`  
**Saved to:** `outputs/report_<slug>.md`

---

### 💻 Coder Agent — `agents/coder_agent.py`
Generates clean, production-quality Python code. Silently corrects typos. Handles algorithms, automation scripts, API clients, data tools, and more. Saves to two places.

**Output:** Sets `state["code_result"]`  
**Saved to:**
- `outputs/code_<slug>.py` (local)
- `git_agent_output/code_<slug>.py` (GitHub)

---

### 🐙 GitHub Agent — `agents/github_agent.py`
Translates natural language into GitHub API calls. Handles listing, reading, creating, updating, and deleting files, as well as branch management. All writes are locked to `git_agent_output/`.

**Output:** Sets `state["github_result"]`  
**Actions:** `list_files`, `read_file`, `create_or_update_file`, `create_branch`, `delete_file`

---

### 📄 PDF Agent — `agents/pdf_agent.py`
100+ features across 20 categories — summarize, OCR, compress, convert, merge, split, extract tables, create PDFs from scratch, redact text, add watermarks, and more. Powered by PyMuPDF, pypdf, reportlab, and Groq.

**Output:** Sets `state["pdf_result"]` (JSON string)  
**Saved to:** `outputs/pdf_agent_output.pdf`, `outputs/images/`, `outputs/output.md`, etc.

---

### 📧 Email Agent — `agents/email_agent.py`
80+ features across 18 categories — compose, send (SMTP), read (IMAP), reply, forward, analyze, detect phishing, generate templates, drip campaigns, A/B test subject lines, and more. Works in mock mode when SMTP credentials aren't set.

**Output:** Sets `state["email_result"]` (JSON string)  
**Saved to:** `outputs/email_output.html`

---

### 💬 Convo Agent — `agents/convo_agent.py`
The friendly front-end. Handles greetings, questions about the system, and clarifications. Maintains multi-turn conversation history and knows the full capability set of the system so it can guide users.

**Output:** Sets `state["convo_result"]` and `state["conversation_history"]`

---

### 🗄️ Database Agent — `agents/database_agent.py`
42+ database operations — query, insert, update, delete, NL-to-SQL, health check, find duplicates, export (CSV/JSON/Excel), trend analysis, data quality reports. Supports SQLite (default), PostgreSQL, and MySQL.

**Output:** Sets `state["db_result"]` (JSON string)  
**Saved to:** `outputs/*.csv`, `outputs/*.xlsx`, etc.

---

## ⚙️ Environment Setup

### 1. Clone & install

```bash
git clone https://github.com/prasadmanas8b-debug/ai-agent-project
cd ai-agent-project
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure `.env`

```bash
cp .env.example .env
# Open .env and fill in your keys
```

| Variable | Required | Where to get it |
|---|---|---|
| `GROQ_API_KEY` | ✅ | [console.groq.com](https://console.groq.com) — free |
| `TAVILY_API_KEY` | ✅ | [tavily.com](https://tavily.com) — free tier |
| `GITHUB_TOKEN` | ✅ | GitHub → Settings → Developer Settings → PAT (`repo` scope) |
| `GITHUB_REPO` | ✅ | `username/repo-name` |
| `EMAIL_ADDRESS` | Optional | Your Gmail address |
| `EMAIL_PASSWORD` | Optional | Gmail App Password (not your real password) |
| `DB_TYPE` | Optional | `sqlite` (default) / `postgresql` / `mysql` |
| `DB_SQLITE_PATH` | Optional | Path to `.db` file, default `database.db` |

### 3. Run

```bash
python main.py
```

---

## 🚀 Quick Start — Example Tasks

Once running, type any of these at the prompt:

```bash
# Research
Research the latest developments in quantum computing

# Coding (typos are fine!)
wrtie a bianry serach algortihm in python

# Research + Code
Research neural networks and implement a simple one in Python

# PDF
Summarize PDF at uploads/report.pdf

# Email
Compose a professional follow-up email to an investor

# GitHub
List all files in the agents folder

# Database
List all tables in the database

# Chat
What can this system do?
```

---

## 🧪 Running Tests

```bash
# Run all tests
pytest tests/test_suite.py -v

# Run database tests
pytest tests/test_database_agent.py -v

# Without pytest
python tests/test_suite.py
```

All tests use `unittest.mock` — **no API keys needed, no network calls, instant results**.

---

## 🔗 API Endpoints

The `api/` folder exposes the PDF and Email agents over HTTP via FastAPI.

```bash
# Start the API server
uvicorn api.pdf_endpoint:app --reload --port 8001
uvicorn api.email_endpoint:app --reload --port 8002
```

| Endpoint | Method | Description |
|---|---|---|
| `POST /pdf` | POST | Run any PDF Agent feature via HTTP |
| `POST /email` | POST | Run any Email Agent feature via HTTP |

---

## 🌐 Frontend

The `frontend/` folder contains React components that provide a chat/upload UI for the PDF and Email agents.

```bash
# From the frontend/ directory
npm install
npm run dev
```

- **PDFAgent.jsx** — drag-and-drop PDF upload + result viewer
- **EmailAgent.jsx** — email composition and inbox viewer

---

## 🔒 Security Notes

- **Never commit `.env`** — it's gitignored. Use `.env.example` as a template.
- **GitHub Token** — use the minimum scope needed (`repo` only). Rotate it periodically.
- **Email Password** — use a Gmail App Password, not your real password. Enable 2FA first.
- **Database** — set `DB_READ_ONLY=true` in `.env` if the Database Agent should never write.
- **GitHub writes** — all agent file writes are locked to `git_agent_output/` — they cannot modify source files.

---

## 🛣️ How to Explain This to Your Team

**The 30-second pitch:**
> "It's a Python system where you type one sentence and an AI supervisor figures out which specialist agents to run — in sequence if needed. Need research? It searches the web. Need code? It generates and saves a `.py` file. Need a PDF summarized? Done. All agents share a single state object and the supervisor loops until the job is complete."

**Key concepts to highlight:**

| Concept | What it means |
|---|---|
| `AgentState` | A shared Python `dict` that all agents read from and write to |
| `Supervisor` | An LLM that reads the state and decides what runs next |
| `LangGraph` | The framework that wires agents into a controllable loop |
| `outputs/` | Everything the agents produce ends up here (code, reports, PDFs) |
| Typo tolerance | The Supervisor uses an LLM — it understands intent, not exact keywords |

---

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=100&section=footer" width="100%"/>

<br/>

Built with ❤️ using **LangGraph · Groq · Tavily · PyGithub · FastAPI**

</div>
