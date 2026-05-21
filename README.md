<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=200&section=header&text=AI%20Agent%20System&fontSize=56&fontColor=fff&animation=twinkling&fontAlignY=38&desc=Production-Grade%20Multi-Agent%20AI%20%7C%20Research%20%C2%B7%20Code%20%C2%B7%20PDF%20%C2%B7%20Email%20%C2%B7%20GitHub&descAlignY=62&descSize=16" width="100%"/>

<br/>

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-Orchestration-00C7B7?style=for-the-badge&logo=graphql&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![Groq](https://img.shields.io/badge/Groq-llama--4--scout-F55036?style=for-the-badge&logo=meta&logoColor=white)](https://groq.com)
[![React](https://img.shields.io/badge/React-Frontend-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](LICENSE)
[![Stars](https://img.shields.io/github/stars/prasadmanas8b-debug/ai-agent-project?style=for-the-badge&logo=github&color=fbbf24)](https://github.com/prasadmanas8b-debug/ai-agent-project/stargazers)

<br/>

> **A production-ready Multi-Agent AI system** where specialized agents collaborate under a smart supervisor to research, write code, manage PDFs, handle emails, and interact with GitHub — all orchestrated through a dynamic LangGraph state machine.
>
> *Think of it as a full AI engineering team running on autopilot.*

<br/>

[🚀 Quick Start](#-quick-start) · [🧠 Agents](#-agents) · [📄 PDF Agent](#-pdf-agent--43-features) · [📧 Email Agent](#-email-agent--38-features) · [🏗️ Architecture](#️-architecture) · [📡 API Reference](#-api-reference) · [🛣️ Roadmap](#️-roadmap)

</div>

---

## 📊 System Overview

| Metric | Value |
|--------|-------|
| 🤖 Total Agents | **7** (Research, Writer, Coder, GitHub, PDF, Email, Convo) |
| ⚡ LLM | **Groq · meta-llama/llama-4-scout-17b-16e-instruct** |
| 📄 PDF Features | **43 handlers** across 14 categories |
| 📧 Email Features | **38 handlers** across 11 categories |
| 🧩 Orchestration | **LangGraph** state machine with dynamic routing |
| 🌐 API | **Flask + FastAPI** dual support |
| 🎨 Frontend | **React + Tailwind CSS** |
| 📦 Transport | **SMTP + IMAP** (stdlib, zero extra dependencies) |

---

## 🧠 Agents

### Supervisor (Manager Agent)
The **brain** of the system. Reads the task + current state and decides which agent runs next using a priority-based routing ruleset. Powered by `llama-3.3-70b-versatile` for precise decisions.

```
task → Supervisor → research | writer | coder | github | pdf | email | convo → Supervisor → FINISH
```

---

### 🔍 Research Agent
Searches the web via **Tavily API**, synthesizes findings, and writes structured research notes into state.

**Triggers:** tasks containing `research`, `what is`, `explain`, `latest`, `trends`, `history`, `compare`

---

### ✍️ Writer Agent
Transforms research notes into polished, well-structured reports. Handles formatting, tone, and length.

**Triggers:** runs after Research Agent completes, or for direct writing tasks

---

### 🧑‍💻 Coder Agent
Reads research notes or direct task instructions and generates **working Python code**, saving it to `git_agent_output/`.

**Triggers:** tasks containing `code`, `implement`, `build`, `script`, `program`

---

### 🐙 GitHub Agent
Interacts with GitHub — reads repos, lists files, creates/updates files, manages branches. Uses the **PyGitHub** library.

**Triggers:** `github`, `save to repo`, `commit`, `push`, `list files`, `create branch`

---

### 📄 PDF Agent
**43 feature handlers** across 14 categories. See the [full section below](#-pdf-agent--43-features).

**Triggers:** `pdf`, `summarize pdf`, `extract`, `ocr`, `compress`, `watermark`, etc.

---

### 📧 Email Agent
**38 feature handlers** across 11 categories. See the [full section below](#-email-agent--38-features).

**Triggers:** `email`, `inbox`, `compose`, `send`, `reply`, `forward`, `phishing`, `drip campaign`, etc.

---

### 💬 Convo Agent
Handles greetings, small-talk, clarifications, and general chat. Maintains conversation history across turns.

**Triggers:** `hi`, `hello`, `thanks`, `what can you do`, simple one-off questions

---

## 📄 PDF Agent — 43 Features

> Full documentation: [`PDF_AGENT_DOCUMENTATION.md`](PDF_AGENT_DOCUMENTATION.md)

<details>
<summary><b>Core Operations (6)</b></summary>

| Mode | Description |
|------|-------------|
| `read` | Parse PDF — page count, word count, text preview, scanned detection |
| `create` | Generate PDF from a text prompt (ReportLab code + content plan) |
| `summarize` | Executive summary, key points, topics, sentiment, document type |
| `qa` | Q&A over PDF content with source section citations |
| `translate` | Translate PDF to any language |
| `extract` | Tables, key-values, named entities, lists |

</details>

<details>
<summary><b>Text Operations (6)</b></summary>

| Mode | Description |
|------|-------------|
| `search` | Full-text search across all pages with bounding box coordinates |
| `find_replace` | Find & replace text — returns occurrence count + Python code |
| `watermark` | Add diagonal watermark text (e.g. CONFIDENTIAL) |
| `page_numbers` | Add page numbers to all pages |
| `header_footer` | Add custom header and/or footer |
| `rewrite` | AI rewrite in a different style/tone |

</details>

<details>
<summary><b>Page Management (4)</b></summary>

| Mode | Description |
|------|-------------|
| `page_ops` | Rotate, extract, remove, add blank pages — returns modified PDF |
| `split` | Split by page range — returns array of PDF parts |
| `merge` | Merge two PDFs (pass `pdf_bytes` + `pdf2_bytes`) |
| `merge_plan` | AI merge strategy + pypdf code (no file needed) |

</details>

<details>
<summary><b>Images (2)</b></summary>

| Mode | Description |
|------|-------------|
| `extract_images` | Extract all embedded images as base64 |
| `pdf_to_images` | Convert each page to PNG/JPG at 2× resolution |

</details>

<details>
<summary><b>AI-Powered (7)</b></summary>

| Mode | Description |
|------|-------------|
| `classify` | Document type, language, topics, reasoning |
| `sentiment` | Emotion breakdown, tone, key positive/negative phrases |
| `ner` | People, orgs, locations, dates, emails, phones, URLs |
| `compare` | Diff two PDFs — similarity %, unique content, key differences |
| `autotag` | Auto-tags, categories, department, priority, action required |
| `reformat` | AI restructure + new ReportLab code |
| `md_to_pdf` | Generate Markdown + PDF code from a prompt |

</details>

<details>
<summary><b>Data, Metadata, Security, OCR, Annotations, Optimization, Forms, Accessibility, Batch (18)</b></summary>

| Mode | Description |
|------|-------------|
| `tables_to_csv` | Extract all tables as downloadable CSV |
| `to_markdown` | Convert PDF content to Markdown |
| `to_html` | Convert PDF content to semantic HTML5 |
| `metadata` | Read metadata, suggest improvements, SEO score |
| `set_metadata` | Write/update title, author, subject, keywords |
| `protect` | Password-encrypt PDF |
| `decrypt` | Remove password from PDF |
| `redact` | Permanently black out sensitive text |
| `signature` | Generate digital signature code (pyhanko) |
| `ocr` | Extract text from scanned PDFs via pytesseract |
| `annotate` | Highlight text, add sticky notes |
| `bookmarks` | Read bookmarks or auto-generate TOC |
| `compress` | Lossless compression — reports size reduction % |
| `repair` | Fix corrupted PDFs via PyMuPDF rebuild |
| `linearize` | Optimize for fast web view |
| `forms` | Detect fillable fields, extract values, generate fill code |
| `accessibility` | WCAG/PDF-UA audit — issues, severity, fixes |
| `batch` | Generate Python batch processing scripts |

</details>

**Quick example:**
```python
from agents.pdf_agent import run_pdf_agent

result = run_pdf_agent({
    "task":      "Summarize this document",
    "pdf_mode":  "summarize",
    "pdf_bytes": open("report.pdf", "rb").read(),
    # ... other state fields
})
import json
print(json.loads(result["pdf_result"])["summary"])
```

---

## 📧 Email Agent — 38 Features

> Full documentation: [`EMAIL_AGENT_DOCUMENTATION.md`](EMAIL_AGENT_DOCUMENTATION.md)

<details>
<summary><b>Core Ops (4)</b></summary>

| Mode | Description |
|------|-------------|
| `compose` | Write a new email from a prompt — subject, body, HTML body |
| `reply` | AI-powered reply with threading support |
| `forward` | Forward with auto-generated intro note |
| `send` | Compose + send immediately via SMTP |

</details>

<details>
<summary><b>AI Writing (8)</b></summary>

| Mode | Description |
|------|-------------|
| `rewrite_tone` | Rewrite for formal / casual / assertive / friendly / empathetic |
| `resize` | Shorten or expand while preserving meaning |
| `fix_grammar` | Correct all grammar, spelling, and punctuation |
| `improve_clarity` | Improve structure, flow, readability score |
| `translate` | Translate to any language |
| `suggest_subject` | 5 subject lines with open-rate predictions |
| `from_bullets` | Convert bullet points to a full email |
| `match_style` | Mirror the recipient's writing style |

</details>

<details>
<summary><b>Inbox Management (3)</b></summary>

| Mode | Description |
|------|-------------|
| `read` | Fetch emails from INBOX / Sent / Drafts / Spam via IMAP |
| `search` | Search by sender, subject, keyword, date |
| `digest` | AI-powered daily/weekly inbox digest |

</details>

<details>
<summary><b>Analysis (6)</b></summary>

| Mode | Description |
|------|-------------|
| `summarize` | Summary + action items + deadlines + priority |
| `summarize_thread` | Full thread summary — participants, timeline, open questions |
| `extract_actions` | Tasks, deadlines, commitments, follow-ups |
| `extract_entities` | People, orgs, emails, phones, dates, amounts |
| `analyze` | Sentiment, intent, urgency, tone, emotion |
| `classify` | Category, type, labels, priority, calendar flag |

</details>

<details>
<summary><b>Smart, Templates, Scheduling, Security, Integrations, Bulk, Output (17)</b></summary>

| Mode | Description |
|------|-------------|
| `smart_reply` | 3 one-click reply options |
| `auto_reply` | Out-of-office / auto-reply generator |
| `follow_up` | Write a follow-up for N days after no reply |
| `template` | Create reusable templates with `{{placeholders}}` |
| `mail_merge` | Personalized bulk email + Python CSV code |
| `drip` | Design a 4-step email sequence with APScheduler code |
| `ab_test` | 3 A/B subject line variants with predictions |
| `schedule` | Parse scheduling request → ISO datetime + code |
| `best_time` | Predict best send time for max open rate |
| `security_check` | Detect phishing, spam, suspicious links — verdict + score |
| `sensitive_data` | Find SSNs, credit cards, phone numbers via regex |
| `gdpr` | GDPR compliance audit — risks, score, required actions |
| `crm_log` | Extract Salesforce/HubSpot CRM fields |
| `meeting` | Detect meeting request + generate `.ics` file |
| `unsubscribe` | Find unsubscribe links + opt-out instructions |
| `bulk` | Generate IMAP code for bulk delete/archive/mark |
| `export` | Export as `.eml`, `.txt`, `.html`, `.csv` |
| `signature` | Professional email signature (plain + HTML) |

</details>

**Quick example:**
```python
from agents.email_agent import run_email_agent

result = run_email_agent({
    "task":          "Write a follow-up email to the investor about Q1 results",
    "email_mode":    "compose",
    "email_context": {"to": "investor@vc.com", "tone": "formal"},
    # ... other state fields
})
import json
r = json.loads(result["email_result"])
print(r["subject"])
print(r["body"])
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Input                           │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   Supervisor Agent                          │
│         (llama-3.3-70b · priority-based routing)           │
└──┬──────┬──────┬──────┬──────┬──────┬──────┬───────────────┘
   │      │      │      │      │      │      │
   ▼      ▼      ▼      ▼      ▼      ▼      ▼
Research Writer Coder GitHub  PDF   Email  Convo
Agent   Agent  Agent  Agent  Agent  Agent  Agent
   │      │      │      │      │      │      │
   └──────┴──────┴──────┴──────┴──────┴──────┘
                      │
                      ▼
              Supervisor → FINISH
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              AgentState (shared whiteboard)                 │
│  task · research_notes · final_report · code_result        │
│  github_result · pdf_result · email_result · convo_result  │
│  pdf_bytes · pdf2_bytes · pdf_mode · pdf_text              │
│  email_mode · email_context · conversation_history        │
└─────────────────────────────────────────────────────────────┘
```

### State Machine Flow

```python
# LangGraph compiles to a directed cyclic graph
graph = StateGraph(AgentState)
graph.add_node("supervisor", supervisor_node)
graph.add_node("research",   research_node)
# ... all 7 agents
graph.set_entry_point("supervisor")
graph.add_conditional_edges("supervisor", route, {
    "research": "research", "writer": "writer",
    "coder":    "coder",    "github": "github",
    "pdf":      "pdf",      "email":  "email",
    "convo":    "convo",    "FINISH": END,
})
# Each agent loops back to supervisor
```

---

## 🗂️ Project Structure

```
ai-agent-project/
│
├── 🤖 agents/
│   ├── manager_agent.py          # Supervisor — routing + orchestration
│   ├── dynamic_research_agent.py # Web research via Tavily
│   ├── writer_agent.py           # Report + content generation
│   ├── coder_agent.py            # Python code generation
│   ├── github_agent.py           # GitHub file/branch operations
│   ├── pdf_agent.py              # PDF Agent — 43 features
│   ├── email_agent.py            # Email Agent — 38 features
│   └── convo_agent.py            # Conversational chat
│
├── 🔧 tools/
│   ├── web_search.py             # Tavily web search
│   ├── file_saver.py             # File I/O utilities
│   ├── dynamic_file_saver.py     # Dynamic file saving
│   └── github_tools.py           # GitHub API helpers
│
├── 🧩 graph/
│   ├── state.py                  # AgentState TypedDict (shared whiteboard)
│   └── pipeline_graph.py         # LangGraph state machine
│
├── 🌐 api/
│   ├── pdf_endpoint.py           # PDF Agent API (Flask + FastAPI)
│   └── email_endpoint.py         # Email Agent API (Flask + FastAPI)
│
├── 🎨 frontend/
│   ├── PDFAgent.jsx              # PDF Agent React UI (100+ feature UI)
│   └── EmailAgent.jsx            # Email Agent React UI (38 feature UI)
│
├── 📁 outputs/                   # Agent output files (auto-created)
├── 📁 uploads/                   # PDF uploads directory
├── 📁 git_agent_output/          # Coder agent output files
├── 📁 memory/                    # Agent memory storage
├── 📁 tests/                     # Test suite
├── 📁 notebooks/                 # Jupyter experiments
│
├── 📄 PDF_AGENT_DOCUMENTATION.md # PDF Agent full docs
├── 📄 EMAIL_AGENT_DOCUMENTATION.md # Email Agent full docs
├── 📄 requirements.txt           # Python dependencies
├── 📄 requirements_new_deps.txt  # New deps for PDF/Email agents
├── 📄 .env.example               # API key template
└── 🚀 main.py                    # CLI entry point
```

---

## 🚀 Quick Start

### Prerequisites
- Python **3.10+**
- [Groq API key](https://console.groq.com) (free tier available)
- [Tavily API key](https://tavily.com) (for web research)
- GitHub Personal Access Token (for GitHub agent)

### 1. Clone & Install

```bash
git clone https://github.com/prasadmanas8b-debug/ai-agent-project.git
cd ai-agent-project

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

pip install -r requirements.txt
pip install pymupdf pypdf reportlab pillow pytesseract   # PDF Agent extras
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
# ── Core (required) ──────────────────────
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
GITHUB_TOKEN=your_github_personal_access_token

# ── Email Agent (optional — AI features work without these) ──
EMAIL_ADDRESS=you@gmail.com
EMAIL_PASSWORD=xxxx xxxx xxxx xxxx     # Gmail App Password
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_IMAP_HOST=imap.gmail.com
```

### 3. Run

```bash
python main.py
```

**Example prompts:**
```
Research the latest developments in transformer architectures
Implement a LRU cache in Python
Summarize PDF at uploads/report.pdf
Compose a follow-up email to the investor about Q1
Check this email for phishing [paste email]
Create a professional project proposal PDF
```

---

## 📡 API Reference

### Start the API server

```bash
# Flask
python -c "from flask import Flask; from api.pdf_endpoint import pdf_bp; from api.email_endpoint import email_bp; app=Flask(__name__); app.register_blueprint(pdf_bp); app.register_blueprint(email_bp); app.run(port=5000)"

# FastAPI
uvicorn main_api:app --reload --port 8000
```

### PDF Agent API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/pdf` | Run any PDF feature (JSON body) |
| `POST` | `/api/pdf/upload` | Run with file upload (multipart) |
| `GET` | `/api/pdf/modes` | List all 43 modes |

```bash
# Summarize a PDF via URL
curl -X POST http://localhost:5000/api/pdf \
  -H "Content-Type: application/json" \
  -d '{"task": "summarize this", "pdf_mode": "summarize", "pdf_b64": "<base64>"}'

# Upload and compress
curl -X POST http://localhost:5000/api/pdf/upload \
  -F "task=compress this PDF" \
  -F "pdf_mode=compress" \
  -F "file=@large_document.pdf"
```

### Email Agent API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/email` | Run any email feature (JSON body) |
| `POST` | `/api/email/send` | Send email directly |
| `GET` | `/api/email/inbox` | Fetch inbox |
| `POST` | `/api/email/upload` | With attachment |
| `GET` | `/api/email/modes` | List all 38 modes |

```bash
# Compose an email
curl -X POST http://localhost:5000/api/email \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Write a follow-up to the investor",
    "email_mode": "compose",
    "email_context": {"to": "investor@vc.com", "tone": "formal"}
  }'

# Fetch inbox
curl "http://localhost:5000/api/email/inbox?folder=INBOX&limit=10"
```

---

## 🎨 Frontend

Both agents come with full **React + Tailwind CSS** UIs.

### PDF Agent UI Features
- 📂 Drag-and-drop PDF upload (primary + secondary for compare/merge)
- 🗂️ 14-category sidebar with live feature search
- 📊 Smart result panels: image grids, CSV downloads, code blocks, HTML/Markdown previews
- ⬇️ Direct download for output PDFs, images, CSVs, HTML, Markdown
- 🕘 Session history with quick-replay

### Email Agent UI Features
- 🎭 Tone selector: formal / casual / friendly / assertive / empathetic / concise
- 📧 Recipient fields (To, CC) with auto-send toggle
- 📋 Original email paste box for reply/rewrite/analyze operations
- 💬 Smart reply cards with one-click copy
- 🛡️ Security verdict banners (safe / suspicious / dangerous)
- 🌐 HTML email preview via sandboxed iframe

---

## 🔑 Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | ✅ Yes | Groq LLM API key — get at [console.groq.com](https://console.groq.com) |
| `TAVILY_API_KEY` | ✅ Yes | Web search API — get at [tavily.com](https://tavily.com) |
| `GITHUB_TOKEN` | ✅ Yes | GitHub PAT with `repo` scope |
| `EMAIL_ADDRESS` | ⚡ Optional | Your email address for SMTP/IMAP |
| `EMAIL_PASSWORD` | ⚡ Optional | App password (not your main password) |
| `EMAIL_SMTP_HOST` | ⚡ Optional | SMTP host (default: `smtp.gmail.com`) |
| `EMAIL_SMTP_PORT` | ⚡ Optional | SMTP port (default: `587`) |
| `EMAIL_IMAP_HOST` | ⚡ Optional | IMAP host (default: `imap.gmail.com`) |

> **Note:** Email AI features (compose, analyze, rewrite, etc.) work without SMTP/IMAP. Only `read` and `send` require credentials.

---

## 📦 Dependencies

### Core
| Package | Purpose |
|---------|---------|
| `langgraph` | State machine orchestration |
| `langchain-groq` | Groq LLM integration |
| `langchain` | Agent framework |
| `python-dotenv` | Environment management |
| `tavily-python` | Web search |
| `PyGithub` | GitHub API |

### PDF Agent
| Package | Purpose |
|---------|---------|
| `pymupdf` | PDF read, annotate, compress, watermark, images |
| `pypdf` | Merge, split, encrypt, metadata |
| `reportlab` | PDF creation from scratch |
| `pillow` | Image processing |
| `pytesseract` | OCR for scanned PDFs |

### API / Frontend
| Package | Purpose |
|---------|---------|
| `flask` / `fastapi` | API server |
| `uvicorn` | ASGI server for FastAPI |
| React + Tailwind | Frontend UI |

---

## 🧪 Testing

```bash
# Run test suite
python -m pytest tests/ -v

# Run a specific agent test
python -m pytest tests/test_suite.py -k "pdf" -v

# Quick smoke test
python main.py
# > Research quantum computing
```

---

## 🛣️ Roadmap

| Status | Feature |
|--------|---------|
| ✅ Done | Research + Writer + Coder agents |
| ✅ Done | GitHub agent (read/write/branch) |
| ✅ Done | Conversational agent with history |
| ✅ Done | **PDF Agent — 43 features** |
| ✅ Done | **Email Agent — 38 features** |
| ✅ Done | LangGraph state machine (7 agents) |
| ✅ Done | Flask + FastAPI dual API support |
| ✅ Done | React frontend for PDF + Email agents |
| 🔜 Next | Streamlit UI overhaul |
| 🔜 Next | Persistent vector memory (ChromaDB) |
| 🔜 Next | Docker + docker-compose support |
| 🔜 Next | GitHub Actions CI/CD pipeline |
| 🔜 Next | Calendar Agent (Google Calendar / Outlook) |
| 🔜 Next | Slack Agent (send messages, read channels) |
| 🔜 Next | Browser Agent (web automation) |
| 🔜 Next | Voice input/output |

---

## 📁 Output Files

The system auto-saves agent outputs to the `outputs/` directory:

| Output | Location |
|--------|----------|
| PDF files (watermark, compress, merge, etc.) | `outputs/pdf_agent_output.pdf` |
| Split PDF parts | `outputs/split_part_N_pages_X-Y.pdf` |
| Extracted images | `outputs/images/page_N.png` |
| CSV tables | `outputs/table_N_Title.csv` |
| Markdown export | `outputs/output.md` |
| HTML export | `outputs/output.html` |
| Email HTML | `outputs/email_output.html` |
| Email Python code | `outputs/email_code.py` |
| Coder agent output | `git_agent_output/` |

---

## 🤝 Contributing

Contributions are welcome! Here's how to add a new agent:

1. Create `agents/your_agent.py` with a `run_your_agent(state: AgentState) -> AgentState` function
2. Add `your_result: str` to `AgentState` in `graph/state.py`
3. Register the node in `graph/pipeline_graph.py`
4. Add routing rules to `agents/manager_agent.py`
5. Update `initial_state` in `main.py`
6. Add API endpoint in `api/`
7. Add React UI in `frontend/`

```bash
# Fork → branch → PR
git checkout -b feat/your-agent
git commit -m "feat(agent): add YourAgent with N features"
git push origin feat/your-agent
```

---

## 👥 Contributors

<a href="https://github.com/prasadmanas8b-debug/ai-agent-project/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=prasadmanas8b-debug/ai-agent-project" />
</a>

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=100&section=footer" width="100%"/>

**Built with ❤️ by [Kunal Roy](https://github.com/prasadmanas8b-debug)**

⭐ Star this repo if you find it useful · 🐛 [Report a bug](https://github.com/prasadmanas8b-debug/ai-agent-project/issues) · 💡 [Request a feature](https://github.com/prasadmanas8b-debug/ai-agent-project/issues)

*7 agents · 43 PDF features · 38 email features · production-ready*

</div>
