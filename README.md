<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=200&section=header&text=AI%20Agent%20System&fontSize=56&fontColor=fff&animation=twinkling&fontAlignY=38&desc=Research%20%C2%B7%20Writer%20%C2%B7%20GitHub%20%7C%20Powered%20by%20LangGraph%20%2B%20Groq&descAlignY=62&descSize=16" width="100%"/>

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-Orchestration-00C7B7?style=for-the-badge&logo=graphql&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![Groq](https://img.shields.io/badge/Groq-llama--3.3--70b-F55036?style=for-the-badge&logo=meta&logoColor=white)](https://groq.com)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](LICENSE)

</div>

---

## What This Does

A 3-agent AI system where a smart supervisor routes your task to the right specialist:

| Agent | What it does |
|---|---|
| Research | Web search via Tavily → structured markdown report |
| Writer | Turns research notes into polished reports, blogs, summaries |
| GitHub | List/read/create/update files and branches on GitHub |

---

## Quick Start

```bash
git clone https://github.com/prasadmanas8b-debug/ai-agent-project
cd ai-agent-project

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env — add GROQ_API_KEY, TAVILY_API_KEY, GITHUB_TOKEN, GITHUB_REPO

python main.py
```

---

## Example Tasks

```
Research quantum computing
Research AI trends and save to GitHub
Write a report on machine learning
List files in the agents folder
Create a new branch called feature/my-feature
```

---

## Project Structure

```
ai-agent-project/
├── agents/
│   ├── manager_agent.py           ← Supervisor / router
│   ├── dynamic_research_agent.py  ← Research Agent (Tavily + Groq)
│   ├── writer_agent.py            ← Writer Agent
│   └── github_agent.py            ← GitHub Agent
├── graph/
│   ├── pipeline_graph.py          ← LangGraph pipeline (3 agents)
│   └── state.py                   ← Shared state
├── tools/
│   ├── github_tools.py            ← GitHub API helpers
│   ├── text_utils.py              ← Shared utilities
│   └── prompt_guard.py            ← Security
├── outputs/                       ← Generated reports (git-ignored)
├── main.py                        ← Entry point
├── requirements.txt
└── .env.example
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| GROQ_API_KEY | Yes | Get free at console.groq.com |
| TAVILY_API_KEY | Yes | Get free at tavily.com |
| GITHUB_TOKEN | Yes | github.com/settings/tokens |
| GITHUB_REPO | Yes | e.g. username/repo-name |

---

## How It Works

```
Your task
    ↓
Supervisor (LLM router)
    ↓
Research Agent → Writer Agent → GitHub Agent
    ↓
FINISH → result shown + saved to outputs/
```

The supervisor chains agents automatically. For example:
- "Research AI trends and save to GitHub" → research → github
- "Research X" → research → writer (auto report)
