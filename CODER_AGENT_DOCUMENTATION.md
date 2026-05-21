# Coder Agent — Technical Documentation

**Project:** AI Agent System  
**File:** `agents/coder_agent.py`  
**Author:** AI Agent Project Team  
**Last Updated:** May 2026  
**Version:** 1.0

---

## 1. Overview

The **Coder Agent** is a specialized AI-powered module within the multi-agent pipeline. Its sole responsibility is to **automatically generate clean, working, well-commented Python code** based on a user's task and any available research context — and then **commit that code directly to the GitHub repository**.

It acts as the "engineering arm" of the system: once the Research Agent has gathered information and the Writer Agent has produced a report, the Coder Agent translates those findings into executable Python code, no human intervention required.

---

## 2. Role in the System

```
User Input
    ↓
Supervisor Agent  ──→  Research Agent  ──→  Writer Agent  ──→  Coder Agent  ──→  GitHub
                                                                    ↑
                                               (also triggered directly for coding tasks)
```

The Supervisor Agent routes to the Coder Agent when it detects that the user's task involves:
- Implementing an algorithm or data structure
- Building a script or program
- Writing code for a researched concept

---

## 3. How It Works — Step by Step

### Step 1 — Receive Task Context
The agent receives the shared pipeline state, which contains:
| Field | Description |
|---|---|
| `task` | The original user instruction (e.g. "Implement binary search") |
| `final_report` | Polished research report from Writer Agent (used as context) |
| `research_notes` | Raw research from Research Agent (fallback context) |

### Step 2 — Build Prompt for LLM
The agent assembles a prompt combining:
- The task description
- Up to 3,000 characters of the research report (if available) as coding context
- A strict system prompt enforcing code quality rules

### Step 3 — Generate Code via LLM
The agent calls **Groq's LLM** (`llama-3.3-70b-versatile`) with the prompt.  
The LLM returns raw Python code following strict output rules:
- Starts with a module docstring
- Uses only approved libraries (stdlib, requests, numpy, pandas, langchain, groq)
- Includes inline comments on non-obvious lines
- Always includes a runnable `if __name__ == "__main__":` demo block
- 50–200 lines — no bloat

### Step 4 — Clean Output
Any accidental Markdown code fences (` ``` `) the LLM may have added are automatically stripped, ensuring the output is pure `.py` content.

### Step 5 — Save to GitHub
The generated code is saved directly to the GitHub repository under `git_agent_output/` using the GitHub Tools module.  
- Filename is auto-generated from the task name (e.g. `code_binary_search_algorithm.py`)
- A descriptive commit message is auto-written (e.g. `feat(coder): generate code for 'implement binary search'`)
- Uses **upsert logic** — creates the file if new, updates if it already exists

### Step 6 — Return Result
The agent updates `state["code_result"]` with:
- The GitHub commit status (success/failure)
- The number of lines of code generated

---

## 4. Key Technical Details

| Property | Value |
|---|---|
| **LLM Model** | `llama-3.3-70b-versatile` (via Groq API) |
| **Temperature** | `0.3` (slightly creative but mostly deterministic) |
| **Max Input Context** | 3,000 characters of research report |
| **Output Folder** | `git_agent_output/` (on GitHub) |
| **Filename Format** | `code_<sanitized_task_name>.py` |
| **Commit Message Format** | `feat(coder): generate code for '<task>'` |

---

## 5. Dependencies

| Library | Purpose |
|---|---|
| `langchain-groq` | LLM interface to Groq API |
| `langchain-core` | Message formatting (SystemMessage, HumanMessage) |
| `python-dotenv` | Load API keys from `.env` file |
| `tools.github_tools` | Save generated code to GitHub |

**Required environment variable:**
```
GROQ_API_KEY=your_groq_api_key_here
```

---

## 6. Input & Output

### Input (from pipeline state)
```python
{
    "task":           "implement a binary search algorithm",
    "final_report":   "## Binary Search\n Binary search is...",  # optional
    "research_notes": "",                                          # fallback
    "code_result":    "",
    "github_result":  "",
    "next":           ""
}
```

### Output (updated pipeline state)
```python
{
    ...
    "code_result": "✅ File 'git_agent_output/code_binary_search.py' created — commit: 'feat(coder): ...' | 87 lines generated."
}
```

---

## 7. Error Handling

| Scenario | Behaviour |
|---|---|
| LLM API call fails | Returns error message in `code_result`, does not crash pipeline |
| GitHub save fails | Returns GitHub error string in `code_result` |
| No task provided | Generates code with empty context — may produce generic output |
| LLM returns markdown fences | Automatically stripped before saving |

---

## 8. Limitations & Known Issues

1. **LLM initialized at module level** — The `_llm` instance is created when the module is imported. If `GROQ_API_KEY` is missing from `.env` at import time, this will raise an error immediately. *(Recommend: convert to lazy initialization, same pattern as `github_agent.py`)*

2. **Context window cap** — Research reports are truncated to 3,000 characters. Very long reports may lose detail in the code generation context.

3. **Library restriction** — The agent only uses stdlib + a small whitelist of packages. Code requiring other third-party packages may not run correctly without manual installation.

4. **No code execution / validation** — The agent generates code but does not run or test it. Output correctness depends on LLM quality.

---

## 9. Standalone Usage (for testing)

The agent can be run independently without the full pipeline:

```bash
python agents/coder_agent.py
```

This runs a built-in test that generates code for `"implement a binary search algorithm"` and commits it to GitHub.

To test with a custom task, modify the `test_state` dict at the bottom of the file:

```python
test_state = {
    "task": "build a web scraper for news headlines",
    ...
}
```

---

## 10. Output Example

**User task:** `"Research neural networks and write code for it"`

**Generated file:** `git_agent_output/code_research_neural_networks_and_write_code.py`

**Commit:** `feat(coder): generate code for 'Research neural networks and write code'`

**Code preview:**
```python
"""
Neural Network Simulation using NumPy.
Demonstrates a simple feedforward network with backpropagation.
"""
import numpy as np
import os

# Sigmoid activation function
def sigmoid(x):
    return 1 / (1 + np.exp(-x))
...
```

---

## 11. Suggested Improvements (Roadmap)

- [ ] Convert LLM initialization to lazy pattern (fix known issue #1)
- [ ] Add code syntax validation before committing (using `ast.parse`)
- [ ] Support additional output languages (JavaScript, SQL, Bash)
- [ ] Add unit test generation alongside the main code file
- [ ] Stream LLM output to terminal for real-time feedback

---

*Documentation prepared for internal review. Part of the AI Agent System project.*
