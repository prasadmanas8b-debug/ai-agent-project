# 🤖 AI Agent Project

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-Orchestration-00C7B7?style=for-the-badge)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**A production-ready Multi-Agent AI system powered by LangGraph**

*Research · Write · Act — intelligently orchestrated.*

</div>

---

## ✨ What is this?

A **multi-agent AI system** where specialized agents collaborate under a smart manager to research, write, and interact with GitHub — all coordinated through a dynamic LangGraph state machine.

> Think of it as a small AI team running on autopilot.

---

## 🧠 Agents

| Agent | Role |
|-------|------|
| 🔍 **Research Agent** | Searches the web, gathers information, summarizes findings |
| ✍️ **Writer Agent** | Generates polished content based on research output |
| 🐙 **GitHub Agent** | Interacts with GitHub — reads repos, pushes content |
| 🧑‍💼 **Manager Agent** | Orchestrates all agents, routes tasks, manages state |

---

## 🏗️ Project Structure

```
ai-agent-project/
├── 🤖 agents/
│   ├── research_agent.py     # Web research & summarization
│   ├── writer_agent.py       # Content generation
│   ├── github_agent.py       # GitHub interactions
│   └── manager_agent.py      # Orchestration & routing
│
├── 🔧 tools/
│   ├── web_search.py         # Web search tool
│   └── file_saver.py         # File I/O tool
│
├── 🧩 graph/
│   └── state_graph.py        # LangGraph state machine (dynamic)
│
├── 🧠 memory/                # Agent memory & storage
├── 🖥️  ui/                   # Streamlit frontend
├── 🧪 tests/                 # Test suite
├── 📓 notebooks/             # Jupyter experiments
├── .env.example              # API key template
├── requirements.txt          # Python dependencies
└── main.py                   # Entry point
```

---

## ⚙️ How It Works

```
User Input
    │
    ▼
Manager Agent  ──►  Research Agent  ──►  Writer Agent
    │                                        │
    └──────────►  GitHub Agent  ◄────────────┘
                      │
                      ▼
                   Output
```

1. **Manager** receives the user task and decides which agents to invoke
2. **Research Agent** gathers relevant data from the web
3. **Writer Agent** produces structured output from research
4. **GitHub Agent** can push results, read repos, or interact with code
5. All state is managed dynamically via **LangGraph**

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- API keys for your LLM provider (OpenAI / Groq / etc.)

### Installation

```bash
# 1. Clone the repo
git clone https://github.com/prasadmanas8b-debug/ai-agent-project.git
cd ai-agent-project

# 2. Set up environment
cp .env.example .env
# Fill in your API keys in .env

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the system
python main.py
```

### Launch the UI

```bash
streamlit run ui/app.py
```

---

## 🔑 Environment Variables

```env
OPENAI_API_KEY=your_key_here
GITHUB_TOKEN=your_github_token
TAVILY_API_KEY=your_tavily_key   # for web search
```

---

## 🛣️ Roadmap

- [x] Manager + Research + Writer agents
- [x] Dynamic LangGraph state machine
- [x] GitHub agent integration
- [x] Streamlit UI
- [ ] Persistent vector memory (ChromaDB / Pinecone)
- [ ] Docker support
- [ ] CI/CD pipeline
- [ ] More tool integrations

---

## 👥 Contributors

<a href="https://github.com/prasadmanas8b-debug/ai-agent-project/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=prasadmanas8b-debug/ai-agent-project" />
</a>

---

## 📄 License

This project is licensed under the MIT License.

---

<div align="center">
  <sub>Built with ❤️ by the ai-agent-project team</sub>
</div>
