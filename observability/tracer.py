"""
observability/tracer.py — Execution trace recorder for the AI Agent Framework.

Records a complete trace of every pipeline run:
  - Each agent invocation (start, end, result)
  - Each supervisor routing decision
  - Each tool call
  - Final run status and total duration

Traces are saved as JSON files: outputs/traces/run_{run_id}.json

Usage:
    from observability.tracer import tracer, new_run_id

    run_id = new_run_id()
    tracer.start_run(run_id, task="Research quantum computing")
    tracer.record_step(run_id, agent="supervisor", decision="research")
    tracer.record_step(run_id, agent="research", status="success", duration_ms=4200)
    tracer.finish_run(run_id, status="success")
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ── Data models ───────────────────────────────────────────────────────────────

@dataclass
class TraceStep:
    """A single step in a pipeline execution trace."""
    step_number: int
    agent: str
    timestamp: str
    duration_ms: float = 0.0
    status: str = ""          # "success", "failure", "skipped"
    decision: str = ""        # For supervisor steps
    output_preview: str = ""  # First 200 chars of output
    error: str = ""
    tool_calls: List[dict] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RunTrace:
    """Complete trace of a single pipeline run."""
    run_id: str
    task: str
    start_time: str
    end_time: str = ""
    total_duration_ms: float = 0.0
    status: str = "running"   # "running", "success", "failure", "partial"
    steps: List[TraceStep] = field(default_factory=list)
    final_agents_used: List[str] = field(default_factory=list)
    error_summary: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Internal tracking
    _start_ts: float = field(default_factory=time.monotonic, repr=False)
    _step_counter: int = field(default=0, repr=False)

    def add_step(self, step: TraceStep) -> None:
        self.steps.append(step)
        if step.agent not in ("supervisor",) and step.status == "success":
            if step.agent not in self.final_agents_used:
                self.final_agents_used.append(step.agent)

    def to_dict(self) -> dict:
        return {
            "run_id":            self.run_id,
            "task":              self.task,
            "start_time":        self.start_time,
            "end_time":          self.end_time,
            "total_duration_ms": self.total_duration_ms,
            "status":            self.status,
            "agents_used":       self.final_agents_used,
            "step_count":        len(self.steps),
            "error_summary":     self.error_summary,
            "metadata":          self.metadata,
            "steps":             [s.to_dict() for s in self.steps],
        }


# ── Tracer class ──────────────────────────────────────────────────────────────

class ExecutionTracer:
    """
    Records and persists execution traces for all pipeline runs.

    Thread-safe: each run_id has its own lock.
    """

    def __init__(self, traces_dir: str = "outputs/traces") -> None:
        self.traces_dir = Path(traces_dir)
        self._runs: Dict[str, RunTrace] = {}
        self._lock = Lock()

    def start_run(
        self,
        run_id: str,
        task: str,
        metadata: Dict[str, Any] | None = None,
    ) -> None:
        """Start recording a new run."""
        self.traces_dir.mkdir(parents=True, exist_ok=True)
        ts = _utc_now()
        run = RunTrace(
            run_id=run_id,
            task=task,
            start_time=ts,
            metadata=metadata or {},
        )
        with self._lock:
            self._runs[run_id] = run
        logger.debug("[tracer] Run started: %s | task: %s", run_id, task[:100])

    def record_supervisor_decision(
        self,
        run_id: str,
        decision: str,
        duration_ms: float = 0.0,
    ) -> None:
        """Record a supervisor routing decision."""
        self._append_step(
            run_id=run_id,
            agent="supervisor",
            status="success",
            decision=decision,
            duration_ms=duration_ms,
        )

    def record_agent_start(self, run_id: str, agent: str) -> float:
        """Record agent start. Returns start timestamp for duration calculation."""
        return time.monotonic()

    def record_agent_success(
        self,
        run_id: str,
        agent: str,
        start_ts: float,
        output_preview: str = "",
        tool_calls: List[dict] | None = None,
    ) -> None:
        """Record successful agent completion."""
        duration_ms = round((time.monotonic() - start_ts) * 1000, 2)
        self._append_step(
            run_id=run_id,
            agent=agent,
            status="success",
            duration_ms=duration_ms,
            output_preview=output_preview[:200] if output_preview else "",
            tool_calls=tool_calls or [],
        )

    def record_agent_failure(
        self,
        run_id: str,
        agent: str,
        start_ts: float,
        error: str,
    ) -> None:
        """Record agent failure."""
        duration_ms = round((time.monotonic() - start_ts) * 1000, 2)
        self._append_step(
            run_id=run_id,
            agent=agent,
            status="failure",
            duration_ms=duration_ms,
            error=str(error)[:300],
        )

    def finish_run(
        self,
        run_id: str,
        status: str = "success",
        error_summary: str = "",
    ) -> Optional[dict]:
        """
        Finalize a run trace, persist it to disk, and return the trace dict.

        Args:
            run_id:        The run ID to finalize.
            status:        "success", "failure", or "partial".
            error_summary: Brief description of any errors.

        Returns:
            The trace as a dict, or None if run_id not found.
        """
        with self._lock:
            run = self._runs.get(run_id)
            if not run:
                logger.warning("[tracer] finish_run called for unknown run_id: %s", run_id)
                return None

            run.end_time          = _utc_now()
            run.total_duration_ms = round((time.monotonic() - run._start_ts) * 1000, 2)
            run.status            = status
            run.error_summary     = error_summary

            trace_dict = run.to_dict()

        # Persist outside the lock
        self._save_trace(run_id, trace_dict)

        logger.info(
            "[tracer] Run finished: %s | status: %s | duration: %.0fms | agents: %s",
            run_id, status, trace_dict["total_duration_ms"],
            ", ".join(trace_dict["agents_used"])
        )

        return trace_dict

    def get_run_trace(self, run_id: str) -> Optional[dict]:
        """Return the current trace for a run (may be in progress)."""
        with self._lock:
            run = self._runs.get(run_id)
            return run.to_dict() if run else None

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _append_step(
        self,
        run_id: str,
        agent: str,
        status: str = "",
        decision: str = "",
        duration_ms: float = 0.0,
        output_preview: str = "",
        error: str = "",
        tool_calls: List[dict] | None = None,
        notes: str = "",
    ) -> None:
        with self._lock:
            run = self._runs.get(run_id)
            if not run:
                return
            run._step_counter += 1
            step = TraceStep(
                step_number    = run._step_counter,
                agent          = agent,
                timestamp      = _utc_now(),
                duration_ms    = duration_ms,
                status         = status,
                decision       = decision,
                output_preview = output_preview,
                error          = error,
                tool_calls     = tool_calls or [],
                notes          = notes,
            )
            run.add_step(step)

    def _save_trace(self, run_id: str, trace_dict: dict) -> None:
        """Save a trace to disk as JSON."""
        try:
            path = self.traces_dir / f"run_{run_id}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(trace_dict, f, indent=2, ensure_ascii=False)
            logger.debug("[tracer] Trace saved: %s", path)
        except Exception as exc:
            logger.warning("[tracer] Failed to save trace %s: %s", run_id, exc)

    def load_trace(self, run_id: str) -> Optional[dict]:
        """Load a persisted trace from disk."""
        path = self.traces_dir / f"run_{run_id}.json"
        if not path.exists():
            return None
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            logger.warning("[tracer] Failed to load trace %s: %s", run_id, exc)
            return None

    def list_traces(self, limit: int = 20) -> List[dict]:
        """List recent trace summaries (newest first)."""
        traces = []
        try:
            files = sorted(self.traces_dir.glob("run_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
            for f in files[:limit]:
                try:
                    with open(f, encoding="utf-8") as fp:
                        data = json.load(fp)
                    traces.append({
                        "run_id":       data.get("run_id"),
                        "task":         data.get("task", "")[:100],
                        "status":       data.get("status"),
                        "duration_ms":  data.get("total_duration_ms"),
                        "agents_used":  data.get("agents_used", []),
                        "start_time":   data.get("start_time"),
                    })
                except Exception:
                    pass
        except Exception as exc:
            logger.warning("[tracer] Failed to list traces: %s", exc)
        return traces


# ── Helpers ───────────────────────────────────────────────────────────────────

def _utc_now() -> str:
    """Return current UTC time as ISO 8601 string."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def new_run_id() -> str:
    """Generate a unique 12-character run ID."""
    return uuid.uuid4().hex[:12]


# Singleton
tracer = ExecutionTracer()
