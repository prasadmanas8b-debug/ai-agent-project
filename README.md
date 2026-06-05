# 🔍 AI Research Agent — Phase 1

> **Team of 3 CSE Students | Powered by Groq (LLaMA3) + Tavily Search + LangChain**

An AI agent that takes any research topic, searches the web multiple times, reasons through the results using a ReAct loop, and saves a clean markdown report to the `outputs/` folder — all automatically.

---

## 📋 Table of Contents

- [How It Works](#-how-it-works)
- [Project Structure](#-project-structure)
- [Team Roles & Ownership](#-team-roles--ownership)
- [Getting Started](#-getting-started)
- [API Keys Setup](#-api-keys-setup)
- [Running the Agent](#-running-the-agent)
- [Git Workflow (No Conflicts Guide)](#-git-workflow-no-conflicts-guide)
- [Merging Without Conflicts](#-merging-without-conflicts)
- [Weekly Schedule](#-phase-1-weekly-schedule)
- [Troubleshooting](#-troubleshooting)
- [Git Cheat Sheet](#-git-cheat-sheet)

---

## ⚙️ How It Works

```
You type a topic
       ↓
Agent searches the web 2-3 times (Tavily)
       ↓
LLaMA3 via Groq reads & reasons through results (ReAct loop)
       ↓
Writes a structured markdown report
       ↓
Saves it to outputs/report_<topic>.md ✅
```

**Two ways to run it:**
- **Terminal mode** → `python agents/research_agent.py`
- **Web app mode** → `streamlit run agents/research_agent.py`

---

## 📁 Project Structure

```
ai-agent-project/
├── agents/
│   └── research_agent.py      ← Member 1 owns this (main brain)
├── tools/
│   ├── web_search.py          ← Member 2 owns this (Tavily search)
│   └── file_saver.py          ← Member 3 owns this (saves reports)
├── outputs/                   ← reports saved here (auto-generated)
├── notebooks/                 ← experiments & testing
├── .env                       ← your real API keys (NEVER push to GitHub)
├── .env.example               ← template (safe to push)
├── .gitignore                 ← already set up
└── requirements.txt           ← all dependencies
```

---

## 👥 Team Roles & Ownership

| Member | Role | File | API Key Needed |
|--------|------|------|----------------|
| **Member 1 (Leader)** | Research Agent — main brain | `agents/research_agent.py` | `GROQ_API_KEY` |
| **Member 2** | Web Search Tool | `tools/web_search.py` | `TAVILY_API_KEY` |
| **Member 3** | Output & File Saver | `tools/file_saver.py` | None |

> ⚠️ **Golden Rule:** Each member owns their file. **Never edit someone else's file without telling them first.**

---

## 🚀 Getting Started

### Step 1 — Clone & Open in Codespaces

```bash
# Open the repo in GitHub Codespaces (recommended)
# Or clone locally:
git clone https://github.com/prasadmanas8b-debug/ai-agent-project.git
cd ai-agent-project
```

### Step 2 — Install Dependencies

All 3 members run this once in their Codespaces terminal:

```bash
pip install -r requirements.txt
```

If install completes with no red errors → your environment is ready ✔

### Step 3 — Set Up Your Branch

```bash
git checkout main
git pull origin main
git checkout -b feature/your-branch-name   # see branch names below
```

---

## 🔑 API Keys Setup

> ⚠️ The `.env` file contains your real keys. **NEVER share it. NEVER push it to GitHub.** It is already blocked by `.gitignore`.

### Where to Get Your Keys

| Key | Where to Get It | Free? | Who Needs It |
|-----|----------------|-------|--------------|
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) → Sign up → API Keys | ✅ Yes, 100% free | Member 1 |
| `TAVILY_API_KEY` | [tavily.com](https://tavily.com) → Sign up → API Keys | ✅ Free tier available | Member 2 |
| `GITHUB_TOKEN` | GitHub → Settings → Developer Settings → Tokens | ✅ Free | All 3 (optional) |

### Create Your `.env` File

Inside Codespaces, create a file called exactly `.env` and paste this (replace with your real keys):

```env
GROQ_API_KEY=gsk_...your_groq_key_here
TAVILY_API_KEY=tvly-...your_tavily_key_here
GITHUB_TOKEN=ghp_...your_github_token_here   # optional for now
```

> The `.env.example` file already in the repo shows you this template — it's safe to push because it has no real keys.

---

## ▶️ Running the Agent

### Terminal Mode

```bash
python agents/research_agent.py
# → Type your topic when prompted
# → Report saves to outputs/report_<topic>.md
```

### Web App Mode (Streamlit)

```bash
streamlit run agents/research_agent.py
# → Opens a browser UI at localhost:8501
```

### Full Pipeline Test (Day 5 Goal)

```
You type: "Research about LangChain agents"
    → Agent searches web
    → Reads results
    → Writes summary
    → Saves to outputs/report_langchain_agents.md ✅
```

---

## 🌿 Git Workflow (No Conflicts Guide)

> Follow this and you will **never** have conflicts.

### Branch Names — Use These Exactly

| Member | Branch Name |
|--------|------------|
| Member 1 (Leader) | `feature/research-agent` |
| Member 2 | `feature/web-search-tool` |
| Member 3 | `feature/file-saver-tool` |

### First Time Setup (All 3 do this once)

```bash
# Step 1 — Get latest code
git checkout main
git pull origin main

# Step 2 — Create YOUR branch (only once!)
git checkout -b feature/your-branch-name
```

### Daily Workflow

**START of day — Sync with teammates:**
```bash
git checkout main
git pull origin main
git checkout feature/your-branch-name
git merge main
```

**DURING the day — Save your work often:**
```bash
git add .
git commit -m "feat: describe what you did"
```

**END of day — Push to GitHub:**
```bash
git push origin feature/your-branch-name
```

### Good Commit Messages

| ❌ Bad | ✅ Good |
|--------|---------|
| `update` | `feat: add web search function using Tavily` |
| `fix` | `fix: handle empty search results in web_search.py` |
| `changes` | `feat: save research output as markdown file` |
| `done` | `feat: complete research_agent with groq integration` |

---

## 🔀 Merging Without Conflicts

Since each person owns a **different file**, conflicts should almost never happen.

### When Everyone is Ready to Merge

**Step 1 — Each person pushes their final code:**
```bash
git add .
git commit -m "feat: complete my part of phase 1"
git push origin feature/your-branch-name
```

**Step 2 — Each person opens a Pull Request on GitHub:**
1. Go to the repo on github.com
2. Click **"Compare & pull request"** (yellow banner at top)
3. Title: `feat: add web search tool` (describe your part)
4. Click **"Create pull request"**

**Step 3 — Member 1 (Leader) merges in this order:**

```
1️⃣  Merge Member 3's PR first  →  file_saver.py   (no dependencies)
2️⃣  Merge Member 2's PR second →  web_search.py
3️⃣  Merge Member 1's PR last   →  research_agent.py  (depends on both)
```

> Merge in this order to avoid dependency issues. File saver first, search tool second, main agent last.

### If a Conflict Happens (Rare)

A conflict only happens if 2 people edited the **same file**. If you follow the ownership rule, this should never happen.

If it does, GitHub will show:
```
<<<<<<< HEAD
your version of the code
=======
teammate's version of the code
>>>>>>> feature/their-branch
```

**How to fix:**
1. Open the conflicted file in Codespaces
2. Delete the `<<<<<<<`, `=======`, `>>>>>>>` lines
3. Keep the correct version (or combine both)
4. Save the file, then:
```bash
git add .
git commit -m "fix: resolve merge conflict"
git push
```

> When in doubt — call your teammate and decide together which version to keep.

---

## 📅 Phase 1 Weekly Schedule

| Day | All 3 Together | Member 1 | Member 2 | Member 3 |
|-----|---------------|----------|----------|----------|
| **Day 1** | Get API keys, pip install, confirm setup works | Get Groq key | Get Tavily key | Create outputs/ folder |
| **Day 2** | — | Start `research_agent.py` | Start `web_search.py` | Start `file_saver.py` |
| **Day 3** | — | Build agent logic + Groq | Connect Tavily API | Build file save function |
| **Day 4** | Connect all 3 pieces together | Import tools into agent | Test search returns results | Test file saves correctly |
| **Day 5** | Test full pipeline end to end | Run full test: research a topic | Fix any search bugs | Check output file looks good |

---

## 🛠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| `pip install` fails | Check your internet. Try: `pip install --upgrade pip` first |
| API key not working | Check `.env` has no spaces around `=` sign. Restart Codespaces. |
| `git push` rejected | Run `git pull origin main` first, then push again |
| Conflict on merge | Follow the conflict section above. Call teammate if unsure. |
| `Module not found` error | Run `pip install -r requirements.txt` again |
| Codespace timed out | Go to GitHub → Codespaces → Resume your codespace |
| No report generated | Check your `.env` keys are correct and APIs are reachable |

---

## 📖 Git Cheat Sheet

| What You Want to Do | Command |
|--------------------|---------|
| See what files you changed | `git status` |
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
| [Groq](https://console.groq.com) | Ultra-fast LLaMA3 AI — the "brain" | ✅ |
| [Tavily](https://tavily.com) | Web search built for AI agents — the "eyes" | ✅ |
| [LangChain](https://langchain.com) | Connects AI + tools together | ✅ |
| [Streamlit](https://streamlit.io) | Turns script into a web app | ✅ |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | Safe API key loading | ✅ |

---

<p align="center">
  <i>AI Agent Project — Phase 1 Team Workflow</i>
</p>
