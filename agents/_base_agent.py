"""
agents/_base_agent.py — Abstract base class for all agents.

Provides every agent with:
  - Retry logic with exponential backoff (via @retry decorator)
  - Timeout protection on LLM calls (30s default)
  - Circuit breaker integration (groq_breaker)
  - Structured output validation
  - Consistent error formatting
  - Confidence scoring scaffold
  - Structured logging

Usage:
    from agents._base_agent import BaseAgent, AgentOutput
    from graph.state import AgentState

    class MyAgent(BaseAgent):
        name = "my_agent"

        def run(self, state: AgentState) -> AgentState:
            with self.llm_call("my task") as ctx:
                response = self.invoke_llm([SystemMessage(...), HumanMessage(...)])
                return {**state, "my_result": response}
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Generator, List, Optional

from langchain_core.messages import BaseMessage
from tools.retry_utils import retry, with_timeout, groq_breaker, CircuitBreakerOpenError

logger = logging.getLogger(__name__)

LLM_TIMEOUT_SECONDS = 30
LLM_MAX_RETRIES = 3


@dataclass
class AgentOutput:
    """
    Structured output from any agent.

    Carries both the result and metadata about how it was produced.
    """
    result: str                        # The main output string
    success: bool = True               # Whether the agent succeeded
    confidence: float = 1.0           # 0.0–1.0 confidence in output quality
    error: Optional[str] = None       # Error message if success=False
    metadata: dict = field(default_factory=dict)  # Agent-specific extra data
    duration_ms: float = 0.0          # Time taken to produce this output
    llm_calls: int = 0                # Number of LLM calls made
    tool_calls: List[str] = field(default_factory=list)  # Tool names used

    def to_result_string(self) -> str:
        """Return result or error message as a plain string."""
        if self.success:
            return self.result
        return f"❌ {self.error or 'Unknown error'}"


class BaseAgent(ABC):
    """
    Abstract base class for all AI agents in the framework.

    Subclasses must implement: name (class var) and run(state) method.
    """

    name: str = "base"

    def __init__(self) -> None:
        self._log = logging.getLogger(f"agent.{self.name}")
        self._llm = None
        self._start_time: Optional[float] = None
        self._llm_call_count = 0

    @abstractmethod
    def run(self, state: Any) -> Any:
        """
        Execute the agent's main task.

        Args:
            state: The current AgentState dict.

        Returns:
            Updated AgentState dict.
        """
        ...

    def __call__(self, state: Any) -> Any:
        """Make agents callable — delegates to run()."""
        return self.run(state)

    # ── LLM invocation with protections ──────────────────────────────────────

    def invoke_llm(self, messages: List[BaseMessage], timeout: int = LLM_TIMEOUT_SECONDS) -> str:
        """
        Invoke the LLM with:
          - Circuit breaker protection
          - Timeout enforcement
          - Retry with exponential backoff
          - Structured error reporting

        Args:
            messages: List of LangChain message objects.
            timeout:  Max seconds to wait for LLM response.

        Returns:
            LLM response content as a string.

        Raises:
            RuntimeError: On circuit breaker open or all retries exhausted.
        """
        self._llm_call_count += 1

        @retry(max_attempts=LLM_MAX_RETRIES, backoff_factor=2.0, initial_delay=1.0)
        def _call() -> str:
            try:
                with groq_breaker:
                    llm = self._get_llm()
                    call_start = time.monotonic()
                    response = llm.invoke(messages)
                    duration = round((time.monotonic() - call_start) * 1000, 2)
                    self._log.debug(
                        "[%s] LLM call #%d completed in %.0fms",
                        self.name, self._llm_call_count, duration
                    )
                    return response.content
            except CircuitBreakerOpenError as e:
                raise RuntimeError(f"Groq service temporarily unavailable: {e}") from e

        try:
            return _call()
        except Exception as exc:
            self._log.error("[%s] LLM invocation failed after %d retries: %s",
                           self.name, LLM_MAX_RETRIES, exc)
            raise

    @abstractmethod
    def _get_llm(self) -> Any:
        """Return the LLM instance for this agent."""
        ...

    # ── Context managers ──────────────────────────────────────────────────────

    @contextmanager
    def execution_context(self, task: str) -> Generator["BaseAgent", None, None]:
        """
        Context manager for a full agent execution.

        Logs start/end, tracks timing, and handles top-level exceptions.

        Usage:
            with self.execution_context(task) as ctx:
                ... do work ...
        """
        self._start_time = time.monotonic()
        self._llm_call_count = 0
        self._log.info("[%s] Starting | task: %s", self.name, task[:100])
        try:
            yield self
            duration = round((time.monotonic() - self._start_time) * 1000, 2)
            self._log.info("[%s] Completed | duration: %.0fms | llm_calls: %d",
                          self.name, duration, self._llm_call_count)
        except Exception as exc:
            duration = round((time.monotonic() - self._start_time) * 1000, 2)
            self._log.error("[%s] Failed | duration: %.0fms | error: %s",
                           self.name, duration, exc, exc_info=True)
            raise

    # ── Output helpers ────────────────────────────────────────────────────────

    def make_error_output(self, error: str, state: Any) -> Any:
        """Return a state dict with an error result for this agent."""
        result_key = f"{self.name}_result"
        self._log.error("[%s] Returning error: %s", self.name, error[:200])
        return {**state, result_key: f"❌ [{self.name.upper()} ERROR] {error}"}

    def validate_non_empty(self, value: str, field_name: str) -> str:
        """Validate that a string output is non-empty. Raises ValueError if not."""
        if not value or not value.strip():
            raise ValueError(f"{self.name}: {field_name} is empty — LLM returned no content")
        return value.strip()

    def score_output_confidence(self, output: str, min_length: int = 100) -> float:
        """
        Heuristic confidence score for an LLM output.

        Returns a float 0.0–1.0 based on simple heuristics:
          - 1.0 if output is substantial and structured
          - 0.5 if output is short or missing expected structure
          - 0.1 if output looks like an error or refusal
        """
        if not output:
            return 0.0

        # Error indicators
        error_phrases = ["i cannot", "i can't", "i'm unable", "error:", "sorry,"]
        if any(p in output.lower()[:100] for p in error_phrases):
            return 0.1

        # Length check
        if len(output) < min_length:
            return 0.5

        # Structure check (markdown headers or bullets)
        has_structure = any(marker in output for marker in ["##", "- ", "* ", "1."])
        if has_structure and len(output) > 500:
            return 0.95

        return 0.8

    # ── Elapsed time helper ───────────────────────────────────────────────────

    @property
    def elapsed_ms(self) -> float:
        """Milliseconds since execution_context was entered."""
        if self._start_time is None:
            return 0.0
        return round((time.monotonic() - self._start_time) * 1000, 2)
