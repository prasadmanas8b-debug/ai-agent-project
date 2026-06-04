# AI Agent System — Complete Documentation

> **Version:** 2.0 (Production-ready refactor)  
> **Stack:** Python 3.11+ · LangGraph · LangChain · Groq (Llama 3.3 / Llama 4 Scout) · Tavily · PyGithub  
> **Architecture:** Supervisor-routed multi-agent pipeline (LangGraph StateGraph)

---

## Table of Contents

1. [What This Project Does](#1-what-this-project-does)
2. [Architecture Overview](#2-architecture-overview)
3. [Agent Reference](#3-agent-reference)
4. [Quick Start](#4-quick-start)
5. [Environment Variables](#5-environment-variables)
6. [File Structure](#6-file-structure)
7. [How the Pipeline Works](#7-how-the-pipeline-works)
8. [Shared State (AgentState)](#8-shared-state-agentstate)
9. [Tools Reference](#9-tools-reference)
10. [Running Tests](#10-running-tests)
11. [Common Use Cases](#11-common-use-cases)
12. [Troubleshooting](#12-troubleshooting)
13. [Production Checklist](#13-production-checklist)
14. [What Was Improved in v2.0](#14-what-was-improved-in-v20)

---

## 1. What This Project Does

This is a **multi-agent AI system** that routes any natural language task to the right
specialist agent automatically. You type one line. The system figures out which agent(s)
to use, runs them in order, and delivers the result.

**Supported task types:**

| Category | Example |
|---|---|
| Research | "Research the latest AI trends" |
| Writing | "Turn my research into a report" |
| Coding | "Implement a binary search in Python" |
| GitHub | "List files in the agents folder" |
| PDF | "Summarize the PDF at uploads/report.pdf" |
| Email | "Compose a follow-up email to the investor" |
| Conversation | "What can this system do?" |
| Database | "List all tables in the database" |

---

## 2. Architecture Overview

```
User Input
    │
    ▼
┌─────────────┐
│  Supervisor │  ← LLM-powered router (llama-3.3-70b)
└──────┬──────┘
       │  routes to one of:
       ▼
┌──────────────────────────────────────────────────────┐
│  research │ writer │ coder │ github │ pdf │ email     │
│  convo    │ database                                  │
└──────────────────────────────────────────────────────┘
       │
       └── loops back to Supervisor until FINISH
```

The pipeline is built with **LangGraph** (`StateGraph`). Each node is an agent.
The Supervisor runs after every agent and decides: run another agent, or finish.

---

## 3. Agent Reference

### Supervisor (`agents/manager_agent.py`)
- **Model:** llama-3.3-70b-versatile (temperature=0 for deterministic routing)
- **Job:** Read the current `AgentState` and return the name of the next agent (or `FINISH`)
- **Input:** Full state snapshot with boolean flags for each result field
- **Output:** Sets `state["next"]`

### Research Agent (`agents/dynamic_research_agent.py`)
- **Model:** llama-3.3-70b-versatile + Tavily web search
- **Job:** Search the web and produce a structured markdown research report
- **Output:** Sets `state["research_notes"]`
- **Max iterations:** 6 (prevents infinite loops)

### Writer Agent (`agents/writer_agent.py`)
- **Model:** llama-3.3-70b-versatile (temperature=0.4)
- **Job:** Transform `research_notes` into a polished markdown report
- **Output:** Sets `state["final_report"]`

### Coder Agent (`agents/coder_agent.py`)
- **Model:** llama-3.3-70b-versatile (temperature=0.3)
- **Job:** Generate clean Python code for the task; push it to `git_agent_output/` on GitHub
- **Output:** Sets `state["code_result"]`

### GitHub Agent (`agents/github_agent.py`)
- **Model:** llama-3.3-70b-versatile (temperature=0)
- **Job:** Translate natural language into GitHub API actions (create/update/read/delete files, list, branch)
- **Output:** Sets `state["github_result"]`
- **Safety:** All writes are locked to `git_agent_output/`

### PDF Agent (`agents/pdf_agent.py`)
- **Model:** meta-llama/llama-4-scout-17b-16e-instruct
- **Job:** 100+ PDF operations — summarize, OCR, compress, convert, merge, split, extract tables, create PDFs, and more
- **Output:** Sets `state["pdf_result"]` (JSON string)

### Email Agent (`agents/email_agent.py`)
- **Model:** meta-llama/llama-4-scout-17b-16e-instruct
- **Job:** 80+ email operations — compose, send (SMTP), read (IMAP), analyze, templates, campaigns, phishing detection
- **Output:** Sets `state["email_result"]` (JSON string)

### Conversation Agent (`agents/convo_agent.py`)
- **Model:** llama-3.3-70b-versatile (temperature=0.7)
- **Job:** Multi-turn chat, greetings, clarifications, and general questions
- **Output:** Sets `state["convo_result"]` and `state["conversation_history"]`

### Database Agent (`agents/database_agent.py`)
- **Model:** llama-3.3-70b-versatile
- **Job:** 42+ database operations — query, insert, update, delete, export, NL-to-SQL, health checks, analytics
- **Supports:** SQLite (default), PostgreSQL, MySQL
- **Output:** Sets `state["db_result"]` (JSON string)

---

## 4. Quick Start

### Prerequisites

- Python 3.11+
- A [Groq API key](https://console.groq.com) (free)
- A [Tavily API key](https://tavily.com) (free tier available)
- A GitHub Personal Access Token with `repo` scope

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/prasadmanas8b-debug/ai-agent-project
cd ai-agent-project

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env and fill in your API keys (see Section 5)

# 5. Run the system
python main.py
```

---

## 5. Environment Variables

Copy `.env.example` to `.env` and fill in the values below.

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | ✅ Yes | API key from console.groq.com |
| `TAVILY_API_KEY` | ✅ Yes | API key from tavily.com (for web search) |
| `GITHUB_TOKEN` | ✅ Yes | GitHub PAT with `repo` scope |
| `GITHUB_REPO` | ✅ Yes | `username/repo-name` (e.g. `prasadmanas8b-debug/ai-agent-project`) |
| `EMAIL_ADDRESS` | Optional | Your email address (for SMTP/IMAP) |
| `EMAIL_PASSWORD` | Optional | App password (Gmail: enable 2FA → generate App Password) |
| `EMAIL_SMTP_HOST` | Optional | Default: `smtp.gmail.com` |
| `EMAIL_SMTP_PORT` | Optional | Default: `587` |
| `EMAIL_IMAP_HOST` | Optional | Default: `imap.gmail.com` |
| `DB_TYPE` | Optional | `sqlite` (default) \| `postgresql` \| `mysql` |
| `DB_SQLITE_PATH` | Optional | Path to SQLite file, default `database.db` |
| `DB_HOST` | Optional | PostgreSQL/MySQL host |
| `DB_PORT` | Optional | PostgreSQL/MySQL port |
| `DB_NAME` | Optional | Database name |
| `DB_USER` | Optional | Database user |
| `DB_PASSWORD` | Optional | Database password |
| `DB_READ_ONLY` | Optional | `true` to disable writes, default `false` |
| `DB_AUDIT_LOG` | Optional | Path for audit log, default `outputs/db_audit.log` |

> **Note:** Email and Database features degrade gracefully — if credentials are not set,
> the agents will compose/analyze but skip the actual send/connect steps and return a
> descriptive mock result.

---

## 6. File Structure

```
ai-agent-project/
├── main.py                        # Entry point — run this
├── requirements.txt               # Pinned dependencies
├── .env.example                   # Template for environment variables
├── .gitignore
│
├── graph/
│   ├── __init__.py
│   ├── state.py                   # AgentState TypedDict (shared whiteboard)
│   └── pipeline_graph.py          # LangGraph StateGraph definition
│
├── agents/
│   ├── manager_agent.py           # Supervisor / router
│   ├── dynamic_research_agent.py  # Research Agent (ReAct + Tavily)
│   ├── writer_agent.py            # Writer Agent
│   ├── coder_agent.py             # Coder Agent
│   ├── github_agent.py            # GitHub Agent
│   ├── pdf_agent.py               # PDF Agent (100+ features)
│   ├── email_agent.py             # Email Agent (80+ features)
│   ├── convo_agent.py             # Conversation Agent
│   └── database_agent.py          # Database Agent (42+ features)
│
├── tools/
│   ├── web_search.py              # Tavily search wrapper
│   ├── github_tools.py            # PyGithub low-level helpers
│   ├── file_saver.py              # Local file save utilities
│   └── dynamic_file_saver.py      # Dynamic output saver
│
├── api/
│   ├── email_endpoint.py          # FastAPI endpoint for Email Agent
│   └── pdf_endpoint.py            # FastAPI endpoint for PDF Agent
│
├── frontend/
│   ├── EmailAgent.jsx             # React UI for Email Agent
│   └── PDFAgent.jsx               # React UI for PDF Agent
│
├── tests/
│   ├── test_suite.py              # Main test suite (pytest / unittest)
│   └── test_database_agent.py     # Database Agent tests
│
├── outputs/                       # Local outputs (auto-created, gitignored)
└── git_agent_output/              # GitHub Agent output files (on remote repo)
```

---

## 7. How the Pipeline Works

1. **User** types a task in `main.py`.
2. An `AgentState` dict is created with the task and all empty result fields.
3. The **Supervisor** reads the state and decides which agent to run.
4. The chosen **agent** runs, fills its result field, and returns the updated state.
5. Control returns to the **Supervisor**, which evaluates the new state.
6. Steps 4–5 repeat until the Supervisor returns `FINISH`.
7. `main.py` prints a formatted summary of all results.

### Routing Logic (simplified)

| Condition | Routes to |
|---|---|
| Any result field is non-empty | `FINISH` (task done) |
| Task mentions `pdf` / `summarize pdf` | `pdf` |
| Task mentions `email` / `compose` / `inbox` | `email` |
| Task mentions `database` / `sql` / `table` | `database` |
| Task needs information & no research yet | `research` |
| Research done & no report yet | `writer` |
| Report done & task needs code | `coder` |
| Report/code done & task needs GitHub save | `github` |
| Greeting, question, clarification | `convo` |

---

## 8. Shared State (AgentState)

`graph/state.py` defines the `AgentState` TypedDict — the single shared object
passed between all agents. Each agent **reads** the full state and **writes** only
its own field. No agent mutates another agent's field.

```python
class AgentState(TypedDict):
    task: str                    # Original user input (immutable)
    next: str                    # Supervisor's routing decision

    research_notes: str          # Raw research text
    final_report: str            # Polished markdown report
    code_result: str             # Code save confirmation
    github_result: str           # GitHub operation result
    pdf_result: str              # JSON with PDF data
    email_result: str            # JSON with email data
    convo_result: str            # Conversational reply
    db_result: str               # JSON with DB result

    conversation_history: list   # Multi-turn chat history
    pdf_mode: str                # PDF feature selector
    pdf_bytes: bytes             # Primary PDF file bytes
    pdf2_bytes: bytes            # Secondary PDF bytes
    email_mode: str              # Email feature selector
    email_context: dict          # Email extra context
    db_mode: str                 # DB feature selector
    db_context: dict             # DB extra context
```

---

## 9. Tools Reference

### `tools/web_search.py`

```python
from tools.web_search import search_web, search_web_raw

# Returns formatted string
text = search_web("LangChain agents tutorial", max_results=5)

# Returns raw list of result dicts
results = search_web_raw("quantum computing", max_results=3)
```

### `tools/github_tools.py`

```python
from tools.github_tools import (
    create_file, update_file, create_or_update_file,
    list_files, create_branch, read_file, delete_file,
)

# All write paths are auto-locked to git_agent_output/
result = create_or_update_file("my_report.md", "# Hello", "Add report")
listing = list_files("agents")
```

### `tools/file_saver.py`

```python
from tools.file_saver import save_report, list_reports

path    = save_report("AI Trends", "# Report\n…")  # saves to outputs/
reports = list_reports()                             # list all saved files
```

---

## 10. Running Tests

```bash
# Run all tests (verbose)
pytest tests/test_suite.py -v

# Run a specific test class
pytest tests/test_suite.py::TestSupervisorRouting -v

# Run database tests
pytest tests/test_database_agent.py -v

# Run without pytest (plain unittest)
python tests/test_suite.py
```

All tests use `unittest.mock.patch` — **no real API calls are made during tests**.
This means tests run instantly and work offline without any API keys.

---

## 11. Common Use Cases

### Research a topic
```
What do you want to do? Research the latest developments in quantum computing
```
Flow: `supervisor → research → supervisor → writer → supervisor → FINISH`

### Research and save to GitHub
```
What do you want to do? Research AI trends and save the report to GitHub
```
Flow: `supervisor → research → supervisor → writer → supervisor → github → supervisor → FINISH`

### Generate code
```
What do you want to do? Implement a merge sort algorithm in Python
```
Flow: `supervisor → research → supervisor → writer → supervisor → coder → supervisor → FINISH`

### Summarize a PDF
```
What do you want to do? Summarize PDF at uploads/report.pdf
```
Flow: `supervisor → pdf → supervisor → FINISH`

### Compose an email
```
What do you want to do? Compose a follow-up email to a potential investor
```
Flow: `supervisor → email → supervisor → FINISH`

### Query a database
```
What do you want to do? List all tables in the database
```
Flow: `supervisor → database → supervisor → FINISH`

### Chat / general question
```
What do you want to do? What agents are available in this system?
```
Flow: `supervisor → convo → supervisor → FINISH`

---

## 12. Troubleshooting

### `GROQ_API_KEY not found`
Ensure `.env` exists and contains `GROQ_API_KEY=your_key`. Run `source .env` or
let `python-dotenv` load it automatically (already done in every agent).

### `TAVILY_API_KEY not found`
Sign up at [tavily.com](https://tavily.com) and add the key to `.env`.

### `GITHUB_TOKEN not found` / `GITHUB_REPO not found`
Create a GitHub PAT at Settings → Developer Settings → Personal Access Tokens.
Grant `repo` scope. Add both `GITHUB_TOKEN` and `GITHUB_REPO` to `.env`.

### PDF agent can't read a file
Ensure the file exists at the path you specified relative to the project root
(e.g. `uploads/report.pdf`). Create the `uploads/` folder if needed.

### Email sends in mock mode
This is expected when `EMAIL_ADDRESS` or `EMAIL_PASSWORD` are not set in `.env`.
The agent will compose the email and show a preview — no email is actually sent.
To enable real sending, add SMTP credentials to `.env`.

### `outputs` is a file, not a directory
This is a known git artifact issue. `main.py` detects and fixes this automatically
on startup. You can also fix it manually: `rm outputs && mkdir outputs`.

### Supervisor loops indefinitely
This should not happen with the current routing rules. If it does, check that
the relevant agent is actually setting its result field (non-empty string).
Add a print statement in the agent to debug.

---

## 13. Production Checklist

- [ ] All required API keys are in `.env` (never committed to git)
- [ ] `.gitignore` includes `.env`, `outputs/`, `__pycache__/`, `*.pyc`
- [ ] `requirements.txt` is up to date (`pip freeze > requirements.txt`)
- [ ] Tests pass: `pytest tests/ -v`
- [ ] `DB_READ_ONLY=true` is set if the database agent should not modify data
- [ ] `DB_AUDIT_LOG` is set to a writable path for audit trail
- [ ] Email credentials use App Passwords (not your real password) for Gmail
- [ ] GitHub token has minimal required scope (`repo` only)
- [ ] `outputs/` and `git_agent_output/` are in `.gitignore` if they contain sensitive data

---

## 14. What Was Improved in v2.0

### Bugs Fixed

| File | Issue | Fix |
|---|---|---|
| `agents/research_agent.py` | Entire file was commented out — agent was dead | Replaced with clean `dynamic_research_agent.py` |
| `agents/writer_agent2.py` | Duplicate writer agent with no routing | Removed; consolidated into `writer_agent.py` |
| `tools/dynamic_file_saver.py` | File was 0 bytes (empty) | Implemented fully |
| `main.py` | `_ensure_outputs_dir` called twice | Deduplicated |
| `tools/github_tools.py` | `_repo` was fetched fresh on every call | Cached as module-level singleton |
| `graph/pipeline_graph.py` | `route()` function was not private | Renamed to `_route()` |
| `agents/coder_agent.py` | Saved to `outputs/` but github_tools redirected to `git_agent_output/` | Corrected path directly |

### Complexity Reduced

- `requirements.txt` — was 60+ packages with specific pinned versions causing conflicts; simplified to explicit direct dependencies
- `agents/research_agent.py` — was 300+ lines of mostly commented-out dead code; replaced with 60 clean lines
- `main.py` — PDF/Email/DB output handling extracted into `_save_pdf_outputs()` and helpers; banner extracted to `_print_banner()`
- `agents/manager_agent.py` — `valid` set replaced with `frozenset` (immutable, hashable); `{**state, "next": decision}` pattern used consistently

### Code Quality Improvements

- All files have consistent module-level docstrings
- All public functions have type annotations and docstrings
- All lazy `_llm` globals use `Type | None` annotations
- `_get_llm()` / `_get_client()` / `_get_repo()` pattern applied uniformly
- Error messages are consistent: `❌ AgentName: description`
- Print logs use consistent emoji prefixes for easy grep (`🔍`, `✍️`, `💻`, `🐙`, `💬`)

### Tests Improved

- `make_state()` helper now returns a fully valid `AgentState` (all fields present)
- Added `TestWriterAgent`, `TestCoderAgent`, `TestPipelineIntegration` test classes
- Added `test_invalid_decision_defaults_to_finish` supervisor edge case
- All tests pass with zero real API calls

---

*Generated by the AI Agent System v2.0 — June 2026*
