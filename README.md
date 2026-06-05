# 🔍 AI Research Pipeline — Phase 1 & 2

> **Team of 3 CSE Students | Groq (LLaMA3) + Tavily Search + LangChain**

A two-agent sequential pipeline that takes any research topic, searches the web, then rewrites the raw findings into a clean professional report — all automatically.

---

## 📋 Table of Contents

- [How It Works](#-how-it-works)
- [Project Structure](#-project-structure)
- [Team Roles & Ownership](#-team-roles--ownership)
- [Getting Started](#-getting-started)
- [API Keys Setup](#-api-keys-setup)
- [Running the Pipeline](#-running-the-pipeline)
- [Output Files](#-output-files)
- [Git Workflow](#-git-workflow-no-conflicts-guide)
- [Merging Without Conflicts](#-merging-without-conflicts)
- [Weekly Schedule](#-phase-2-weekly-schedule)
- [Lessons Learned](#-lessons-learned)
- [Troubleshooting](#-troubleshooting)
- [Git Cheat Sheet](#-git-cheat-sheet)
- [What's Next — Phase 3](#-whats-next--phase-3)

---

## ⚙️ How It Works

### Phase 1 — Single Agent

```
You type a topic
       ↓
Research Agent (Groq + Tavily)
  → searches web 2-3 times (ReAct loop)
  → writes raw notes
  → saves outputs/report_{topic}.md ✅
```

### Phase 2 — Sequential Pipeline

```
You type a topic
       ↓
[ Stage 1 ] Research Agent
  → searches web, collects raw notes
  → saves outputs/report_{topic}.md
       ↓
  (raw notes passed as input)
       ↓
[ Stage 2 ] Writer Agent
  → reads raw notes
  → rewrites into clean structured report (4 sections)
  → saves outputs/final_report_{topic}.md ✅
```

**Two output files per run:**
| File | What it contains | Who creates it |
|------|-----------------|----------------|
| `outputs/report_{topic}.md` | Raw research notes from web search | Research Agent |
| `outputs/final_report_{topic}.md` | Polished 4-section markdown report | Writer Agent |

---

## 📁 Project Structure

```
ai-agent-project/
│
├── agents/
│   ├── research_agent.py     ✅ Phase 1 — main brain, searches the web
│   ├── writer_agent.py       ✅ Phase 2 — rewrites notes into a clean report
│   └── manager_agent.py      🔒 Phase 3 — leave empty for now
│
├── tools/
│   ├── web_search.py         ✅ Phase 1 — Tavily web search (Member 2)
│   └── file_saver.py         ✅ Phase 2 updated — saves with custom filenames
│
├── outputs/                  ← auto-generated reports saved here (gitignored)
├── notebooks/                ← experiments & testing
│
├── main.py                   ✅ Phase 2 — pipeline runner (connects both agents)
├── .env                      ← your real API keys (NEVER commit this)
├── .env.example              ← safe template to share with teammates
├── .gitignore                ← blocks .env and outputs/ from GitHub
└── requirements.txt          ← all dependencies
```

---

## 👥 Team Roles & Ownership

| Member | Role | File | API Key |
|--------|------|------|---------|
| **Member 1 (Leader)** | Research Agent + Writer Agent + Pipeline | `agents/research_agent.py`, `agents/writer_agent.py`, `main.py` | `GROQ_API_KEY` |
| **Member 2** | Web Search Tool | `tools/web_search.py` | `TAVILY_API_KEY` |
| **Member 3** | Output & File Saver | `tools/file_saver.py` | None |

> ⚠️ **Golden Rule:** Each member owns their file. **Never edit someone else's file without telling them first.**

---

## 🚀 Getting Started

### Step 1 — Clone & Open in Codespaces

```bash
git clone https://github.com/prasadmanas8b-debug/ai-agent-project.git
cd ai-agent-project
```

### Step 2 — Install Dependencies

All 3 members run this once:

```bash
pip install -r requirements.txt
```

If it completes with no red errors → environment is ready ✔

### Step 3 — Set Up Your Branch

```bash
git checkout main
git pull origin main
git checkout -b feature/your-branch-name
```

---

## 🔑 API Keys Setup

> ⚠️ The `.env` file contains your real keys. **NEVER push it to GitHub.** It is blocked by `.gitignore`.

### Where to Get Your Keys

| Key | Where to Get It | Free? | Who Needs It |
|-----|----------------|-------|--------------|
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) → Sign up → API Keys | ✅ 100% free | Member 1 |
| `TAVILY_API_KEY` | [tavily.com](https://tavily.com) → Sign up → API Keys | ✅ Free tier | Member 2 |
| `GITHUB_TOKEN` | GitHub → Settings → Developer Settings → Tokens | ✅ Free | All 3 (optional) |

### Create Your `.env` File

```env
GROQ_API_KEY=gsk_...your_groq_key_here
TAVILY_API_KEY=tvly-...your_tavily_key_here
GITHUB_TOKEN=ghp_...your_github_token_here
```

---

## ▶️ Running the Pipeline

### Full Pipeline (Phase 2 — recommended)

```bash
python main.py
# → Enter your topic when prompted
# → Two files are created in outputs/
```

### Research Agent only (Phase 1)

```bash
python agents/research_agent.py
```

### Writer Agent only (standalone test)

```bash
python agents/writer_agent.py
```

### Streamlit Web UI

```bash
streamlit run agents/research_agent.py
```

---

## 📄 Output Files

After running `python main.py` with topic `"artificial intelligence"`:

```
outputs/
├── report_artificial_intelligence.md        ← raw research notes
└── final_report_artificial_intelligence.md  ← polished 4-section report
```

The final report always has these four sections:

```markdown
## Overview
## Key Findings
## Detailed Analysis
## Conclusion
```

---

## 🧠 What Makes the Writer Agent Different?

Both agents use the same Groq LLM. What makes them behave completely differently is two things: **system prompt** and **tools**.

| | Research Agent | Writer Agent |
|--|---------------|--------------|
| **System Prompt** | "Search the web, collect information" | "Take notes, write a structured report" |
| **Tools Available** | `web_search`, `file_saver` | `file_saver` only |
| **Input** | A topic string | Raw research notes (string) |
| **Output** | Raw research text + dict | Polished markdown report |
| **Browses web?** | ✅ Yes | ❌ Never |
| **LLM Model** | `llama-3.1-8b-instant` | `llama-3.3-70b-versatile` |

> **Key insight:** Specialization = a different system prompt + different tools. That's it. No magic.

> ⚠️ **Never give the Writer Agent web search access.** It will go off-script and add information that was never actually researched.

---

## 🛡️ How the Pipeline Handles Failures

`main.py` has a 3-step cleaning layer between Stage 1 and Stage 2:

```python
# Step 1: Remove LangChain internal debug text
# Step 2: Remove duplicate lines from repeated searches
# Step 3: Detect agent failure messages and stop cleanly
```

If the Research Agent returns nothing or an error message, the pipeline stops with a warning — **it never crashes.**

**The three tests to run before calling Phase 2 done:**

| Test | Input | Expected |
|------|-------|----------|
| ✅ Normal run | `artificial intelligence in healthcare` | Full 4-section report saved |
| ✅ Vague topic | `dogs` | Short but valid report, no crash |
| ✅ Empty input | Simulate `research_notes = ""` in main.py | Warning printed, no crash |

---

## 🌿 Git Workflow (No Conflicts Guide)

### Branch Names — Use These Exactly

| Member | Branch Name |
|--------|------------|
| Member 1 (Leader) | `feature/research-agent` |
| Member 2 | `feature/web-search-tool` |
| Member 3 | `feature/file-saver-tool` |

### Daily Workflow

**START of day:**
```bash
git checkout main
git pull origin main
git checkout feature/your-branch-name
git merge main
```

**DURING the day:**
```bash
git add .
git commit -m "feat: describe what you did"
```

**END of day:**
```bash
git push origin feature/your-branch-name
```

### Good Commit Messages

| ❌ Bad | ✅ Good |
|--------|---------|
| `update` | `feat: add writer_agent.py with 4-section report format` |
| `fix` | `fix: handle empty research notes in writer agent` |
| `done` | `Phase 2: Add writer_agent.py and main.py pipeline` |

---

## 🔀 Merging Without Conflicts

**Step 1 — Push your final code:**
```bash
git add .
git commit -m "Phase 2: complete my part"
git push origin feature/your-branch-name
```

**Step 2 — Open a Pull Request on GitHub** (yellow banner → "Compare & pull request")

**Step 3 — Member 1 (Leader) merges in this order:**

```
1️⃣  Member 3's PR  →  file_saver.py    (no dependencies)
2️⃣  Member 2's PR  →  web_search.py
3️⃣  Member 1's PR  →  research_agent.py, writer_agent.py, main.py
```

---

## 📅 Phase 2 Weekly Schedule

| Day | All 3 Together | Member 1 | Member 2 | Member 3 |
|-----|---------------|----------|----------|----------|
| **Day 1** | Review Phase 1, plan Phase 2 | Read Phase 2 spec | — | — |
| **Day 2** | — | Build `writer_agent.py` skeleton | Test `web_search.py` | Add `save_to_file()` to `file_saver.py` |
| **Day 3** | — | Complete `writer_agent.py` logic | — | Test `save_to_file()` works |
| **Day 4** | Connect all pieces | Build `main.py` pipeline | Test search returns full content | Test both save functions |
| **Day 5** | Run all 3 tests together | Run full pipeline | Fix any search bugs | Check both output files look good |

---

## 💡 Lessons Learned (Phase 2)

| Lesson | What It Taught Us |
|--------|------------------|
| **Understand before building** | Mental models first. Jumping to code without understanding ReAct causes confusion. |
| **Fix at source** | When research_agent returned a dict, fixing it in main.py was a workaround. Real fix is at source. |
| **Model size matters for ReAct** | Small fast models (8b) often fail strict ReAct format. Use 70b or mixtral for agents. |
| **Rate limits are real** | Free tier APIs have token-per-minute limits. Agents make multiple calls. Plan for retries. |
| **Validate agent output** | Never blindly pass agent output to the next step. Always check: is this research or an error? |
| **One file per agent** | Keeping each agent in its own file with clear ownership prevents confusion and merge conflicts. |
| **Two outputs not one** | Research notes and final report are different things. Save them separately with different names. |

---

## 🛠️ Troubleshooting

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| `ModuleNotFoundError` | Wrong import path | Run from root folder, not inside `agents/` |
| API key not working | `.env` formatting issue | Check no spaces around `=`. Restart Codespaces. |
| Report is empty | LLM returned blank | Print `response.content` before saving to debug |
| Report has hallucinated facts | Writer went off-script | Check system prompt has "do not search" rule |
| File not saved | `outputs/` folder issue | Check `file_saver.py` has `os.makedirs(exist_ok=True)` |
| `dict object has no attribute strip` | research_agent returns dict, not string | Extract with `research_result["report"]` |
| `git push` rejected | Need to sync first | Run `git pull origin main` then push again |
| Codespace timed out | Inactivity | GitHub → Codespaces → Resume your codespace |

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
| [Groq](https://console.groq.com) | Ultra-fast LLaMA3 AI — the "brain" of both agents | ✅ |
| [Tavily](https://tavily.com) | Web search built for AI agents | ✅ |
| [LangChain](https://langchain.com) | Framework connecting AI + tools + agents | ✅ |
| [Streamlit](https://streamlit.io) | Turns script into a web app | ✅ |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | Safe API key loading from `.env` | ✅ |

---

## ➡️ What's Next — Phase 3

In Phase 3, you will build the **Manager Agent** — an orchestrator that:
- Receives the task from the user
- Decides which agent to call and in what order
- Passes data between agents automatically
- Returns the final result

The tool for this is **LangGraph** — a framework built on LangChain for building agent graphs and orchestration flows.

📖 Start reading: [LangGraph docs](https://langchain-ai.github.io/langgraph/)

---

<p align="center">
  <i>AI Agent Project — Phase 1 & 2 | Sequential Multi-Agent Pipeline</i>
</p>
