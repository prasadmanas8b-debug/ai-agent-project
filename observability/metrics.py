"""
observability/metrics.py — Agent performance metrics collection.

Tracks per-agent:
  - Success / failure counts
  - Latency (min, max, avg, p95)
  - Tool call counts and success rates
  - LLM call counts and estimated token usage
  - Retry counts
  - Circuit breaker open events

Metrics are in-memory (reset on restart) and optionally persisted to JSON.

Usage:
    from observability.metrics import metrics

    metrics.record_success("research", duration_ms=4200)
    metrics.record_failure("github", error="timeout")
    metrics.record_tool_call("web_search", success=True, duration_ms=1200)
    report = metrics.report()
"""

from __future__ import annotations

import json
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class AgentStats:
    """Per-agent statistics."""
    name: str

    success_count: int = 0
    failure_count: int = 0
    retry_count: int   = 0

    durations_ms: List[float] = field(default_factory=list)

    tool_calls: Dict[str, int]          = field(default_factory=lambda: defaultdict(int))
    tool_failures: Dict[str, int]       = field(default_factory=lambda: defaultdict(int))
    tool_durations: Dict[str, List[float]] = field(default_factory=lambda: defaultdict(list))

    llm_call_count: int = 0
    estimated_tokens: int = 0

    last_success_ts: Optional[float] = None
    last_failure_ts: Optional[float] = None
    last_error: str = ""

    @property
    def total_calls(self) -> int:
        return self.success_count + self.failure_count

    @property
    def success_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return round(self.success_count / self.total_calls * 100, 2)

    @property
    def avg_duration_ms(self) -> float:
        if not self.durations_ms:
            return 0.0
        return round(sum(self.durations_ms) / len(self.durations_ms), 2)

    @property
    def p95_duration_ms(self) -> float:
        if not self.durations_ms:
            return 0.0
        sorted_d = sorted(self.durations_ms)
        idx = max(0, int(len(sorted_d) * 0.95) - 1)
        return round(sorted_d[idx], 2)

    @property
    def min_duration_ms(self) -> float:
        return round(min(self.durations_ms), 2) if self.durations_ms else 0.0

    @property
    def max_duration_ms(self) -> float:
        return round(max(self.durations_ms), 2) if self.durations_ms else 0.0

    def to_dict(self) -> dict:
        return {
            "name":             self.name,
            "total_calls":      self.total_calls,
            "success_count":    self.success_count,
            "failure_count":    self.failure_count,
            "success_rate_pct": self.success_rate,
            "retry_count":      self.retry_count,
            "latency_ms": {
                "avg":  self.avg_duration_ms,
                "p95":  self.p95_duration_ms,
                "min":  self.min_duration_ms,
                "max":  self.max_duration_ms,
            },
            "llm_calls":         self.llm_call_count,
            "estimated_tokens":  self.estimated_tokens,
            "tools": {
                tool: {
                    "calls":       self.tool_calls[tool],
                    "failures":    self.tool_failures.get(tool, 0),
                    "success_rate_pct": round(
                        (1 - self.tool_failures.get(tool, 0) / max(self.tool_calls[tool], 1)) * 100, 2
                    ),
                    "avg_duration_ms": round(
                        sum(self.tool_durations.get(tool, [0])) /
                        max(len(self.tool_durations.get(tool, [1])), 1), 2
                    ),
                }
                for tool in self.tool_calls
            },
            "last_success":  time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self.last_success_ts))
                             if self.last_success_ts else None,
            "last_failure":  time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self.last_failure_ts))
                             if self.last_failure_ts else None,
            "last_error":    self.last_error[:200] if self.last_error else None,
        }


class MetricsCollector:
    """
    Thread-safe metrics collector for the agent framework.

    All methods are safe to call from multiple threads.
    """

    def __init__(self) -> None:
        self._lock  = Lock()
        self._stats: Dict[str, AgentStats] = {}
        self._start_time = time.time()

        # Global counters
        self._total_runs    = 0
        self._successful_runs = 0
        self._failed_runs   = 0
        self._circuit_breaker_opens: Dict[str, int] = defaultdict(int)

    def _get_stats(self, agent_name: str) -> AgentStats:
        """Get or create stats for an agent (must be called with lock held)."""
        if agent_name not in self._stats:
            self._stats[agent_name] = AgentStats(name=agent_name)
        return self._stats[agent_name]

    # ── Agent events ──────────────────────────────────────────────────────────

    def record_success(self, agent_name: str, duration_ms: float = 0.0) -> None:
        """Record a successful agent invocation."""
        with self._lock:
            stats = self._get_stats(agent_name)
            stats.success_count    += 1
            stats.last_success_ts   = time.time()
            if duration_ms > 0:
                stats.durations_ms.append(duration_ms)
                # Keep only last 1000 measurements to cap memory
                if len(stats.durations_ms) > 1000:
                    stats.durations_ms = stats.durations_ms[-1000:]

    def record_failure(self, agent_name: str, error: str = "", duration_ms: float = 0.0) -> None:
        """Record a failed agent invocation."""
        with self._lock:
            stats = self._get_stats(agent_name)
            stats.failure_count   += 1
            stats.last_failure_ts  = time.time()
            stats.last_error       = error
            if duration_ms > 0:
                stats.durations_ms.append(duration_ms)

    def record_retry(self, agent_name: str) -> None:
        """Record a retry attempt."""
        with self._lock:
            self._get_stats(agent_name).retry_count += 1

    # ── Tool events ───────────────────────────────────────────────────────────

    def record_tool_call(
        self,
        agent_name: str,
        tool_name: str,
        success: bool = True,
        duration_ms: float = 0.0,
    ) -> None:
        """Record a tool invocation."""
        with self._lock:
            stats = self._get_stats(agent_name)
            stats.tool_calls[tool_name] += 1
            if not success:
                stats.tool_failures[tool_name] = stats.tool_failures.get(tool_name, 0) + 1
            if duration_ms > 0:
                stats.tool_durations[tool_name].append(duration_ms)
                # Cap at 200 per tool
                if len(stats.tool_durations[tool_name]) > 200:
                    stats.tool_durations[tool_name] = stats.tool_durations[tool_name][-200:]

    # ── LLM events ────────────────────────────────────────────────────────────

    def record_llm_call(self, agent_name: str, estimated_tokens: int = 0) -> None:
        """Record an LLM call."""
        with self._lock:
            stats = self._get_stats(agent_name)
            stats.llm_call_count   += 1
            stats.estimated_tokens += estimated_tokens

    # ── Circuit breaker events ────────────────────────────────────────────────

    def record_circuit_breaker_open(self, service_name: str) -> None:
        """Record when a circuit breaker trips open."""
        with self._lock:
            self._circuit_breaker_opens[service_name] += 1

    # ── Run-level events ──────────────────────────────────────────────────────

    def record_run_start(self) -> None:
        with self._lock:
            self._total_runs += 1

    def record_run_success(self) -> None:
        with self._lock:
            self._successful_runs += 1

    def record_run_failure(self) -> None:
        with self._lock:
            self._failed_runs += 1

    # ── Reporting ─────────────────────────────────────────────────────────────

    def report(self) -> dict:
        """Return a full metrics report as a dictionary."""
        with self._lock:
            uptime_seconds = round(time.time() - self._start_time, 2)
            return {
                "generated_at":  time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "uptime_seconds": uptime_seconds,
                "runs": {
                    "total":      self._total_runs,
                    "successful": self._successful_runs,
                    "failed":     self._failed_runs,
                    "success_rate_pct": round(
                        self._successful_runs / max(self._total_runs, 1) * 100, 2
                    ),
                },
                "circuit_breakers": dict(self._circuit_breaker_opens),
                "agents": {
                    name: stats.to_dict()
                    for name, stats in self._stats.items()
                },
            }

    def print_summary(self) -> None:
        """Print a human-readable summary to stdout."""
        report = self.report()
        print(f"\n{'='*60}")
        print(f"  METRICS SUMMARY")
        print(f"  Uptime: {report['uptime_seconds']}s")
        print(f"  Runs: {report['runs']['total']} total, "
              f"{report['runs']['successful']} succeeded, "
              f"{report['runs']['failed']} failed "
              f"({report['runs']['success_rate_pct']}% success)")
        print(f"{'='*60}")
        for agent_name, agent_data in report["agents"].items():
            print(f"\n  [{agent_name}]")
            print(f"    Calls:       {agent_data['total_calls']} "
                  f"({agent_data['success_rate_pct']}% success)")
            print(f"    Latency:     avg {agent_data['latency_ms']['avg']}ms, "
                  f"p95 {agent_data['latency_ms']['p95']}ms")
            print(f"    LLM Calls:   {agent_data['llm_calls']}")
            print(f"    Est. Tokens: {agent_data['estimated_tokens']:,}")
            if agent_data["last_error"]:
                print(f"    Last Error:  {agent_data['last_error'][:80]}")
        print(f"{'='*60}\n")

    def save_to_file(self, path: str = "outputs/metrics.json") -> None:
        """Persist the current metrics report to a JSON file."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        report = self.report()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info("[metrics] Report saved to %s", path)

    def reset(self) -> None:
        """Reset all metrics (useful between test runs)."""
        with self._lock:
            self._stats.clear()
            self._total_runs      = 0
            self._successful_runs = 0
            self._failed_runs     = 0
            self._circuit_breaker_opens.clear()
            self._start_time = time.time()


# Singleton — import this everywhere
metrics = MetricsCollector()
