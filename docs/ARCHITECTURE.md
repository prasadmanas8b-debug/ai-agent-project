# Architecture Documentation
**AI Agent Orchestration Framework — v2.0**

---

## System Overview

A **LangGraph-based multi-agent orchestration framework** that accepts natural language tasks and dispatches them to specialist AI agents via a supervisor router.

```
┌─────────────────────────────────────────────────────────────┐
│                     User / API / CLI                        │
└───────────────────────────┬─────────────────────────────────┘
                            │ task (natural language)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    main.py / API endpoint                   │
│  • Input sanitization (prompt_guard)                        │
│  • State initialization (make_initial_state)                │
│  • Observability init (logging + tracing + metrics)         │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              LangGraph StateGraph (pipeline_graph_v2)       │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐  │
│   │               Supervisor Node                       │  │
│   │   • LLM-based intent routing (Groq llama-3.3-70b)  │  │
│   │   • Deadlock detection                              │  │
│   │   • Max iteration guard (10 iterations)             │  │
│   │   • Circuit breaker (groq_breaker)                  │  │
│   └──────────────────────┬──────────────────────────────┘  │
│                          │ conditional edge (state["next"]) │
│         ┌────────────────┼──────────────────┐              │
│         ▼                ▼                  ▼              │
│   ┌──────────┐   ┌──────────────┐   ┌──────────────┐      │
│   │ research │   │    writer    │   │    coder     │      │
│   └────┬─────┘   └──────┬───────┘   └──────┬───────┘      │
│        │                │                   │              │
│   ┌──────────┐   ┌──────────────┐   ┌──────────────┐      │
│   │  github  │   │     pdf      │   │    email     │      │
│   └────┬─────┘   └──────┬───────┘   └──────┬───────┘      │
│        │                │                   │              │
│   ┌──────────┐   ┌──────────────┐           │              │
│   │  convo   │   │   database   │           │              │
│   └────┬─────┘   └──────┬───────┘           │              │
│        └────────────────┴───────────────────┘              │
│                          │ all loop back to supervisor      │
│                          ▼                                  │
│              supervisor → FINISH → END                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Observability Layer                      │
│   • Structured JSON logging (observability/logger.py)       │
│   • Metrics collection (observability/metrics.py)           │
│   • Execution tracing (observability/tracer.py)             │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Map

| Component | File | Responsibility |
|---|---|---|
| Entry Point | `main.py` | CLI interface, state init, output rendering |
| Graph Builder | `graph/pipeline_graph_v2.py` | LangGraph state machine |
| State Schema | `graph/state_v2.py` | Shared AgentState TypedDict + helpers |
| Supervisor | `agents/manager_agent.py` | LLM-based routing, fuzzy resolution |
| Research | `agents/dynamic_research_agent.py` | Tavily web search, structured reports |
| Writer | `agents/writer_agent.py` | Markdown report/blog/summary generation |
| Coder | `agents/coder_agent.py` | Python code generation + GitHub push |
| GitHub | `agents/github_agent.py` | GitHub CRUD via natural language |
| PDF | `agents/pdf_agent.py` | 100+ PDF operations |
| Email | `agents/email_agent.py` | SMTP/IMAP + AI composition |
| Convo | `agents/convo_agent.py` | General conversation with history |
| Database | `agents/database_agent.py` | NL-to-SQL + DB management |
| GitHub Tools | `tools/github_tools.py` | PyGithub wrappers (path-locked) |
| Web Search | `tools/web_search.py` | Tavily search wrapper |
| Text Utils | `tools/text_utils.py` | Shared: strip_fences, make_slug, safe_path |
| Retry Utils | `tools/retry_utils.py` | Retry, timeout, circuit breaker |
| Prompt Guard | `tools/prompt_guard.py` | Injection defense, SQL validation |
| Config | `config/settings.py` | Centralized env var management |
| Logger | `observability/logger.py` | Structured JSON logging |
| Metrics | `observability/metrics.py` | Performance counters |
| Tracer | `observability/tracer.py` | Per-run execution traces |
| Base Agent | `agents/_base_agent.py` | Abstract base with retry + circuit breaker |

---

## State Machine

### AgentState Fields

**Original fields (backward compatible):**
- `task: str` — user's natural language input (never mutated)
- `next: str` — routing decision from supervisor
- `research_notes`, `final_report`, `code_result`, `github_result`, `pdf_result`, `email_result`, `convo_result`, `db_result` — agent outputs
- `conversation_history`, `pdf_mode`, `pdf_bytes`, `pdf2_bytes`, `email_mode`, `email_context`, `db_mode`, `db_context` — agent-specific context

**New fields (v2.0):**
- `run_id: str` — unique trace ID for observability
- `iteration_count: int` — supervisor loop counter (guards against infinite loops)
- `agent_history: List[str]` — ordered list of agents that have run
- `error_log: List[str]` — accumulated non-fatal errors
- `has_error: bool` — true if any agent errored
- `context_summary: str` — compressed research context for token efficiency
- `task_plan: List[str]` — optional explicit multi-step plan

### Routing Logic

1. Supervisor reads current state (what's filled, what's empty)
2. LLM returns one word: `research | writer | coder | github | pdf | email | convo | database | FINISH`
3. Fuzzy resolver maps partial/mangled responses to valid names
4. Conditional edge routes to the correct agent node
5. Agent runs, updates its output field in state
6. Loops back to supervisor
7. Supervisor decides next step or returns FINISH → END

### Infinite Loop Prevention

- Hard limit: `MAX_ITERATIONS = 10` — if supervisor loops more than 10 times, force FINISH
- Deadlock detection: if the same agent appears twice consecutively in `agent_history` with no output, force FINISH

---

## Security Architecture

### Defense Layers

```
User Input
    │
    ▼
[Layer 1] prompt_guard.sanitize_input()
    • Length enforcement (2000 chars max)
    • Null byte / control char stripping
    • 18 injection pattern checks
    • Template injection detection
    │
    ▼
[Layer 2] Agent routing (supervisor)
    • Intent-based routing prevents arbitrary code execution
    • Fuzzy resolver limits to known agent names only
    │
    ▼
[Layer 3] Tool-level validation
    • safe_github_path() blocks path traversal
    • validate_llm_sql() validates SQL before execution
    • Path enforcement: all writes locked to git_agent_output/
    │
    ▼
[Layer 4] Circuit breakers
    • Prevent cascade failures from service outages
    • Automatic recovery after timeout window
```

---

## Reliability Architecture

### Retry Strategy

All LLM calls use:
- Max 3 attempts
- Exponential backoff: 1s → 2s → 4s
- Only retries on transient errors (connection, timeout, 429)

### Circuit Breakers

| Service | Failure Threshold | Recovery Timeout |
|---|---|---|
| Groq | 5 failures | 60 seconds |
| Tavily | 3 failures | 30 seconds |
| GitHub | 5 failures | 120 seconds |
| SMTP | 3 failures | 60 seconds |
| IMAP | 3 failures | 60 seconds |

### Graceful Degradation

- If any agent throws an exception, the error is recorded in `error_log` and the pipeline continues
- If Tavily is unavailable, Research Agent falls back to LLM-only knowledge
- If GitHub is unavailable, Coder Agent still saves code locally
- If Groq circuit breaker is open, supervisor defaults to FINISH

---

## Observability Architecture

### Logging

Format: structured JSON (one line per event)
Location: `outputs/logs/agent_framework.log` (rotating, 10MB × 5 files)

Key events:
- `agent_start` — when an agent begins
- `agent_success` — agent completed with duration_ms
- `agent_failure` — agent failed with error
- `routing_decision` — supervisor routing choice
- `tool_call` — each tool invocation
- `circuit_breaker` — state changes
- `retry` — retry attempts

### Metrics

Collected per agent:
- `success_count`, `failure_count`, `success_rate_pct`
- `latency_ms.avg`, `latency_ms.p95`, `latency_ms.min`, `latency_ms.max`
- `llm_calls`, `estimated_tokens`
- Per-tool: `calls`, `failures`, `avg_duration_ms`

Available at runtime: `from observability.metrics import metrics; metrics.report()`
Persisted to: `outputs/metrics.json`

### Tracing

Each run produces a trace file: `outputs/traces/run_{run_id}.json`

Contains:
- Full ordered step list with agent, decision, status, duration
- Total run duration
- Agents used
- Error summary

---

## Data Flow Examples

### Research + Write Flow
```
User: "Research AI trends and write a report"
  │
  Supervisor → research
  Research Agent: Tavily search × 3 → research_notes
  │
  Supervisor → writer
  Writer Agent: research_notes → final_report (saved to outputs/)
  │
  Supervisor → FINISH
```

### Code + GitHub Flow
```
User: "Write a Python binary search and save to GitHub"
  │
  Supervisor → coder
  Coder Agent: generate code → save to outputs/ → push to git_agent_output/
  │
  Supervisor → FINISH  (github_result already set by coder)
```

### Multi-step: Research → Code
```
User: "Research merge sort algorithms then write the code"
  │
  Supervisor → research
  Research Agent: Tavily × 3 → research_notes
  │
  Supervisor → coder  (has research context → informs code generation)
  Coder Agent: generate code with research context
  │
  Supervisor → FINISH
```
