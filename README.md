<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=200&section=header&text=AI%20Agent%20System&fontSize=56&fontColor=fff&animation=twinkling&fontAlignY=38&desc=Production-Grade%20Multi-Agent%20AI%20%7C%20Research%20%C2%B7%20Code%20%C2%B7%20PDF%20%C2%B7%20Email%20%C2%B7%20GitHub%20%C2%B7%20Database&descAlignY=62&descSize=16" width="100%"/>

<br/>

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-Orchestration-00C7B7?style=for-the-badge&logo=graphql&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![Groq](https://img.shields.io/badge/Groq-llama--3.3--70b-F55036?style=for-the-badge&logo=meta&logoColor=white)](https://groq.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-REST%20API-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![Tests](https://img.shields.io/badge/Tests-Passing-22c55e?style=for-the-badge&logo=pytest)](tests/)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](LICENSE)

<br/>

> **A production-ready Multi-Agent AI system** where 8 specialist agents collaborate under a smart supervisor to research, write, generate code, manage PDFs, handle emails, interact with GitHub, and query databases — all orchestrated through a LangGraph state machine.
>
> *Think of it as a full AI engineering team, running on a single command.*

<br/>

[🚀 Quick Start](#-quick-start) · [🏗️ Architecture](#️-architecture) · [🤖 Agents](#-agents) · [🐳 Docker](#-docker) · [🔌 API](#-api) · [🧪 Tests](#-tests) · [⚙️ Config](#️-configuration)

</div>

---

## 📊 System at a Glance

| Property | Value |
|---|---|
| 🤖 Agents | **8** — Research, Writer, Coder, GitHub, PDF, Email, Convo, Database |
| 🧠 LLM (default) | **Groq · llama-3.3-70b-versatile** |
| 🦙 LLM (heavy) | **Groq · llama-4-scout-17b** (PDF, Email, Database) |
| 🔄 Orchestration | **LangGraph** StateGraph with supervisor routing |
| 🔌 API | **FastAPI** — `/api/agent`, `/api/email`, `/api/pdf`, `/api/modes` |
| 🐳 Deployment | **Docker** + docker-compose |
| 🛡️ Security | Prompt injection guard, path traversal prevention, SQL injection protection |
| 📊 Observability | Structured JSON logging, metrics, tracing |
| 🧪 Tests | pytest + coverage — unit, integration, security |

---

## 🚀 Quick Start

### Option 1 — One-command setup (recommended)

```bash
git clone https://github.com/prasadmanas8b-debug/ai-agent-project
cd ai-agent-project
bash setup.sh
# Edit .env with your API keys
python main.py
```

### Option 2 — Docker

```bash
git clone https://github.com/prasadmanas8b-debug/ai-agent-project
cd ai-agent-project
cp .env.example .env
# Edit .env with your API keys
docker-compose up
```

### Option 3 — API server

```bash
bash setup.sh
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
# Visit http://localhost:8000/docs
```

---

## 🏗️ Architecture

```
User Input (CLI or API)
        │
        ▼
┌─────────────────┐
│   Supervisor    │  ← LLM-powered router (llama-3.3-70b)
│  manager_agent  │    Understands typos, vague phrasing, chained tasks
└────────┬────────┘
         │ routes to one of 8 agents:
         ▼
┌────────────────────────────────────────────────────┐
│  research │ writer │ coder │ github │ pdf │ email   │
│  convo    │ database                               │
└────────────────────────────────────────────────────┘
         │ each agent loops back to supervisor
         ▼
     FINISH → output to user
```

**Key design patterns:**
- **BaseAgent** — all agents inherit retry logic, circuit breaker, structured logging
- **Centralized config** — `config/settings.py` — no scattered `os.getenv()` calls
- **Prompt guard** — all user input sanitized before reaching any LLM
- **Path enforcement** — all GitHub writes confined to `git_agent_output/`
- **Mock/demo mode** — Email and DB agents work without real credentials

---

## 🤖 Agents

| Agent | Trigger words | Key features |
|---|---|---|
| **Research** | research, find, explain, news | Tavily search, LLM fallback, markdown output |
| **Writer** | write, report, blog, summarize | Detects output type (report/blog/summary/explainer) |
| **Coder** | code, script, implement, write a | Typo-tolerant, saves to local + GitHub |
| **GitHub** | list files, push, create branch | Path-locked to `git_agent_output/` |
| **PDF** | pdf, summarize pdf, extract | 100+ features — OCR, merge, split, convert |
| **Email** | email, compose, inbox, send | 80+ features — SMTP/IMAP, mock mode |
| **Convo** | hi, what can you do, help | Multi-turn history, system Q&A |
| **Database** | database, sql, query, tables | NL→SQL, SQLite/PostgreSQL/MySQL |

---

## 🐳 Docker

```bash
# Run interactive CLI
docker-compose up agent

# Run API server
docker-compose up api

# Run both
docker-compose up
```

---

## 🔌 API

After starting the API server (`uvicorn api.main:app`):

```bash
# Health check
curl http://localhost:8000/

# Run any task
curl -X POST http://localhost:8000/api/agent \
  -H "Content-Type: application/json" \
  -d '{"task": "Research the latest AI trends"}'

# List agent modes
curl http://localhost:8000/api/modes

# Interactive docs
open http://localhost:8000/docs
```

---

## 🧪 Tests

```bash
# Run all tests
bash run_tests.sh

# Run specific test file
pytest tests/test_suite.py -v
pytest tests/test_security.py -v
pytest tests/test_tools.py -v

# Run with coverage
pytest tests/ --cov=agents --cov=tools --cov-report=term-missing
```

---

## ⚙️ Configuration

All config lives in `.env`. Copy `.env.example` to start:

```bash
cp .env.example .env
```

**Required:**
- `GROQ_API_KEY` — get free at https://console.groq.com

**Optional (enable features):**
- `TAVILY_API_KEY` — web search (tavily.com)
- `GITHUB_TOKEN` + `GITHUB_REPO` — GitHub operations
- `EMAIL_ADDRESS` + `EMAIL_PASSWORD` — email send/receive
- `DB_TYPE` = `sqlite` (default) / `postgresql` / `mysql`

---

## 📁 Project Structure

```
ai-agent-project/
├── agents/              ← 8 specialist agents + base class
│   ├── _base_agent.py   ← Abstract base: retry, circuit breaker, logging
│   ├── manager_agent.py ← Supervisor / router
│   ├── research_agent.py
│   ├── dynamic_research_agent.py  ← Active research implementation
│   ├── writer_agent.py
│   ├── coder_agent.py
│   ├── github_agent.py
│   ├── pdf_agent.py
│   ├── email_agent.py
│   ├── convo_agent.py
│   └── database_agent.py
├── graph/               ← LangGraph pipeline
│   ├── pipeline_graph.py
│   └── state.py
├── tools/               ← Shared utilities
│   ├── text_utils.py    ← strip_fences, make_slug, safe_github_path
│   ├── prompt_guard.py  ← Injection protection
│   ├── retry_utils.py   ← Retry, circuit breaker
│   ├── github_tools.py
│   ├── web_search.py
│   └── file_saver.py
├── config/
│   └── settings.py      ← Centralized config (import from here only)
├── api/
│   ├── main.py          ← FastAPI app
│   ├── email_endpoint.py
│   └── pdf_endpoint.py
├── observability/       ← Logging, metrics, tracing
├── tests/               ← pytest suite
├── frontend/            ← React components
├── outputs/             ← Generated files (git-ignored)
├── uploads/             ← Input files (git-ignored)
├── main.py              ← CLI entry point
├── setup.sh             ← One-command setup
├── run_tests.sh         ← Test runner with coverage
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## 🛡️ Security

- **Prompt injection** — every user input sanitized via `tools/prompt_guard.py`
- **Path traversal** — GitHub writes confined to `git_agent_output/`
- **SQL injection** — dangerous SQL statements blocked before execution
- **Secrets** — never hardcoded, always via `.env` → `config/settings.py`
- **Docker** — non-root user, minimal attack surface

---

## 📄 License

MIT — see [LICENSE](LICENSE)

---

<div align="center">
Built with ❤️ using LangGraph · Groq · FastAPI · Python 3.11
</div>
