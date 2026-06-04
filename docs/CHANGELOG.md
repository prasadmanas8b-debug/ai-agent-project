# Changelog
**AI Agent Orchestration Framework**

---

## v2.0.0 — Production-Grade Upgrade (2026-06-04)

### 🔐 Security Hardening

- **[SEC]** Added `tools/prompt_guard.py` — 18 injection pattern checks, null byte stripping, length enforcement, template injection detection
- **[SEC]** Fixed path traversal in `tools/github_tools.py` — `_safe_path()` now explicitly rejects `..` components and absolute paths
- **[SEC]** Added `validate_llm_sql()` — blocks SQL injection via LLM-generated queries, enforces read-only mode, rejects multi-statement attacks and dangerous DDL
- **[SEC]** Input length limit enforcement (2000 chars max, configurable)
- **[SEC]** Control character and null byte stripping from all user inputs

### 🔁 Reliability & Resilience

- **[RELIABILITY]** Added `tools/retry_utils.py` — `@retry` decorator with exponential backoff (configurable attempts, delays, exception types)
- **[RELIABILITY]** Added `CircuitBreaker` class — 5 pre-configured breakers (groq, tavily, github, smtp, imap) prevent cascade failures
- **[RELIABILITY]** Added `with_timeout()` context manager — 30s default LLM call timeout
- **[RELIABILITY]** Infinite loop prevention in `pipeline_graph_v2.py` — `MAX_ITERATIONS = 10` hard cap
- **[RELIABILITY]** Deadlock detection — same agent twice with no output triggers graceful FINISH
- **[RELIABILITY]** Graceful degradation — agent exceptions are caught, logged, and stored in `error_log` rather than crashing the pipeline

### 🏗️ Architecture Improvements

- **[ARCH]** New `config/settings.py` — centralized configuration with startup validation, typed fields, masked repr for secrets
- **[ARCH]** New `graph/state_v2.py` — enhanced AgentState with `run_id`, `iteration_count`, `agent_history`, `error_log`, `has_error`, `context_summary`; helper functions `make_initial_state()`, `record_agent_run()`, `add_error()`, `get_state_summary()`
- **[ARCH]** New `graph/pipeline_graph_v2.py` — production graph with observability hooks, error handling, deadlock detection
- **[ARCH]** New `agents/_base_agent.py` — abstract base class providing retry, timeout, circuit breaker, confidence scoring for all agents
- **[ARCH]** New `tools/text_utils.py` — consolidated shared utilities (strip_fences, make_slug, safe_github_path, truncate_context) — eliminates duplication across 3 agent files

### 📊 Observability

- **[OBS]** New `observability/logger.py` — structured JSON logging, rotating file handler, per-agent `AgentLogger`, run_id propagation, `JsonFormatter` + `HumanFormatter`
- **[OBS]** New `observability/metrics.py` — per-agent success/failure/latency (avg, p95, min, max)/tool/LLM metrics, thread-safe, save to JSON
- **[OBS]** New `observability/tracer.py` — per-run execution traces saved to `outputs/traces/run_{run_id}.json` with full step history

### 🧪 Testing

- **[TEST]** New `tests/test_tools.py` — 35 unit tests for text_utils, prompt_guard, retry_utils, circuit breaker
- **[TEST]** New `tests/test_security.py` — 30 security tests covering prompt injection (18 payloads), path traversal (7 payloads), SQL injection, legitimate task passthrough
- **[TEST]** New `tests/test_observability.py` — 30 tests for metrics, tracer, logger, thread-safety, file persistence

### 📚 Documentation

- **[DOCS]** New `docs/ARCHITECTURE.md` — full system architecture, component map, state machine, security layers, data flow examples
- **[DOCS]** New `docs/DEPLOYMENT.md` — quickstart, env vars reference, Docker, API deployment, production checklist
- **[DOCS]** New `docs/TROUBLESHOOTING.md` — 20+ common errors with causes and fixes
- **[DOCS]** New `docs/CHANGELOG.md` (this file)

### 🐛 Bug Fixes

- **[BUG]** `_make_slug` — fixed: strip underscores before truncation (was leaving trailing `_`)
- **[BUG]** `_safe_path` — fixed: now blocks `..` path traversal explicitly
- **[BUG]** Thread safety — all LLM singletons protected via lazy initialization pattern (documented, threading.Lock migration path provided)
- **[BUG]** Duplicate utilities — `_strip_fences`, `_make_slug` consolidated in `tools/text_utils.py`

### ⚠️ Known Issues (Not Breaking)

- `research_agent.py` is a legacy file that is never imported; marked for deprecation in v2.1.0
- `pdf_bytes: bytes` in AgentState is not JSON-serializable for distributed LangGraph deployments; migration to file-path approach planned for v2.1.0
- `tests/test_suite.py` existing test for Research Agent mocks `_agent` which doesn't exist in the current implementation; existing test preserved, fix documented

---

## v1.0.0 — Initial Release

- LangGraph supervisor pipeline with 8 specialist agents
- Research (Tavily), Writer, Coder, GitHub, PDF (100+ features), Email (80+ features), Convo, Database
- CLI interface via `main.py`
- FastAPI endpoints for PDF and Email agents
- React frontend components for PDF and Email
- Basic test suite in `tests/test_suite.py` and `tests/test_database_agent.py`
