"""
observability/logger.py — Structured JSON logging for the AI Agent Framework.

Provides:
  - StructuredLogger: Agent lifecycle events as structured JSON
  - get_logger(): Standard Python logger configured for the framework
  - LogContext: Context manager for scoped logging (run_id propagation)

Log levels:
  DEBUG   — Tool call details, LLM inputs
  INFO    — Agent start/stop, routing decisions
  WARNING — Retries, fallbacks, truncations
  ERROR   — Agent failures, LLM errors, tool errors
  CRITICAL — Circuit breaker open, fatal config errors

Usage:
    from observability.logger import get_agent_logger, structured_log

    log = get_agent_logger("research")
    log.agent_start("research quantum computing", run_id="abc123")
    log.agent_success(duration_ms=4200, output_len=2847)
"""

from __future__ import annotations

import json
import logging
import logging.handlers
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ── Base logging setup ────────────────────────────────────────────────────────

class JsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON for structured log ingestion."""

    SKIP_FIELDS = frozenset({
        "args", "exc_info", "exc_text", "filename", "funcName",
        "levelno", "lineno", "module", "msecs", "msg",
        "pathname", "process", "processName", "relativeCreated",
        "stack_info", "thread", "threadName",
    })

    def format(self, record: logging.LogRecord) -> str:
        log_obj: dict[str, Any] = {
            "ts":      datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level":   record.levelname,
            "logger":  record.name,
            "message": record.getMessage(),
        }

        # Include extra fields set via logger.info(..., extra={...})
        for key, val in vars(record).items():
            if key not in self.SKIP_FIELDS and not key.startswith("_"):
                try:
                    json.dumps(val)  # ensure serializable
                    log_obj[key] = val
                except (TypeError, ValueError):
                    log_obj[key] = str(val)

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj, ensure_ascii=False)


class HumanFormatter(logging.Formatter):
    """Human-readable formatter for console output during development."""

    COLORS = {
        "DEBUG":    "\033[36m",   # cyan
        "INFO":     "\033[32m",   # green
        "WARNING":  "\033[33m",   # yellow
        "ERROR":    "\033[31m",   # red
        "CRITICAL": "\033[35m",   # magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color  = self.COLORS.get(record.levelname, "")
        reset  = self.RESET
        ts     = datetime.fromtimestamp(record.created, tz=timezone.utc).strftime("%H:%M:%S")
        return f"{color}[{ts}] [{record.levelname:<8}] [{record.name}] {record.getMessage()}{reset}"


def _setup_root_logger(
    level: str = "INFO",
    log_format: str = "json",
    logs_dir: str = "outputs/logs",
) -> None:
    """Configure the root logger once at startup."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    root = logging.getLogger()
    root.setLevel(numeric_level)

    # Clear any existing handlers
    root.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    if log_format == "json":
        console_handler.setFormatter(JsonFormatter())
    else:
        console_handler.setFormatter(HumanFormatter())
    root.addHandler(console_handler)

    # File handler (rotating, 10MB × 5 files)
    Path(logs_dir).mkdir(parents=True, exist_ok=True)
    log_file = Path(logs_dir) / "agent_framework.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(JsonFormatter())
    root.addHandler(file_handler)


# ── Public getter ─────────────────────────────────────────────────────────────

def get_logger(name: str) -> logging.Logger:
    """Get a standard Python logger for the given name."""
    return logging.getLogger(name)


# ── Structured agent logger ───────────────────────────────────────────────────

class AgentLogger:
    """
    Structured event logger for a specific agent.

    All events are emitted as structured JSON with consistent fields.
    """

    def __init__(self, agent_name: str) -> None:
        self.agent_name = agent_name
        self._log       = logging.getLogger(f"agent.{agent_name}")
        self._run_id: str | None   = None
        self._start_time: float | None = None

    def bind_run(self, run_id: str) -> None:
        """Associate this logger with a specific run ID."""
        self._run_id = run_id

    def agent_start(self, task: str, run_id: str | None = None) -> float:
        """Log agent start. Returns the start timestamp."""
        self._start_time = time.monotonic()
        if run_id:
            self._run_id = run_id
        self._log.info(
            "Agent started",
            extra={
                "event":      "agent_start",
                "agent":      self.agent_name,
                "task":       task[:200],
                "run_id":     self._run_id or "unknown",
            }
        )
        return self._start_time

    def agent_success(self, output_len: int = 0, notes: str = "") -> float:
        """Log successful agent completion. Returns duration in ms."""
        duration_ms = self._elapsed_ms()
        self._log.info(
            "Agent succeeded",
            extra={
                "event":       "agent_success",
                "agent":       self.agent_name,
                "duration_ms": duration_ms,
                "output_len":  output_len,
                "notes":       notes,
                "run_id":      self._run_id or "unknown",
            }
        )
        return duration_ms

    def agent_failure(self, error: str, notes: str = "") -> float:
        """Log agent failure. Returns duration in ms."""
        duration_ms = self._elapsed_ms()
        self._log.error(
            "Agent failed",
            extra={
                "event":       "agent_failure",
                "agent":       self.agent_name,
                "duration_ms": duration_ms,
                "error":       str(error)[:500],
                "notes":       notes,
                "run_id":      self._run_id or "unknown",
            }
        )
        return duration_ms

    def routing_decision(self, task: str, decision: str, confidence: float = 1.0) -> None:
        """Log a supervisor routing decision."""
        self._log.info(
            "Routing decision",
            extra={
                "event":      "routing_decision",
                "agent":      self.agent_name,
                "task":       task[:200],
                "decision":   decision,
                "confidence": confidence,
                "run_id":     self._run_id or "unknown",
            }
        )

    def tool_call(
        self,
        tool_name: str,
        args: dict | None = None,
        result_preview: str = "",
        duration_ms: float = 0.0,
        success: bool = True,
    ) -> None:
        """Log a tool invocation."""
        self._log.debug(
            "Tool called",
            extra={
                "event":          "tool_call",
                "agent":          self.agent_name,
                "tool":           tool_name,
                "args_preview":   str(args or {})[:200],
                "result_preview": result_preview[:200],
                "duration_ms":    duration_ms,
                "success":        success,
                "run_id":         self._run_id or "unknown",
            }
        )

    def retry(self, attempt: int, max_attempts: int, error: str) -> None:
        """Log a retry event."""
        self._log.warning(
            "Retrying after failure",
            extra={
                "event":       "retry",
                "agent":       self.agent_name,
                "attempt":     attempt,
                "max_attempts": max_attempts,
                "error":       str(error)[:200],
                "run_id":      self._run_id or "unknown",
            }
        )

    def circuit_breaker(self, service: str, state: str) -> None:
        """Log a circuit breaker state change."""
        self._log.warning(
            "Circuit breaker state change",
            extra={
                "event":   "circuit_breaker",
                "agent":   self.agent_name,
                "service": service,
                "state":   state,
                "run_id":  self._run_id or "unknown",
            }
        )

    def _elapsed_ms(self) -> float:
        """Return elapsed milliseconds since agent_start() was called."""
        if self._start_time is None:
            return 0.0
        return round((time.monotonic() - self._start_time) * 1000, 2)


# ── Logger registry ───────────────────────────────────────────────────────────

_agent_loggers: dict[str, AgentLogger] = {}


def get_agent_logger(agent_name: str) -> AgentLogger:
    """Get or create a structured AgentLogger for the given agent."""
    if agent_name not in _agent_loggers:
        _agent_loggers[agent_name] = AgentLogger(agent_name)
    return _agent_loggers[agent_name]


# ── Run context ───────────────────────────────────────────────────────────────

def new_run_id() -> str:
    """Generate a unique run ID for tracing a complete pipeline execution."""
    return uuid.uuid4().hex[:12]


def bind_run_to_all_loggers(run_id: str) -> None:
    """Propagate a run_id to all registered agent loggers."""
    for logger_instance in _agent_loggers.values():
        logger_instance.bind_run(run_id)


# ── Initialization ────────────────────────────────────────────────────────────

def init_logging(
    level: str = "INFO",
    log_format: str = "json",
    logs_dir: str = "outputs/logs",
) -> None:
    """
    Initialize the logging system. Call this once at startup (in main.py).

    Args:
        level:      Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_format: "json" for structured logs, "human" for readable console output.
        logs_dir:   Directory where log files are written.
    """
    _setup_root_logger(level=level, log_format=log_format, logs_dir=logs_dir)
    logger = logging.getLogger("framework")
    logger.info(
        "Logging initialized",
        extra={
            "event":      "logging_init",
            "level":      level,
            "log_format": log_format,
            "logs_dir":   logs_dir,
        }
    )
