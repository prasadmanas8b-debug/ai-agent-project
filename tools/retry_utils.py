"""
tools/retry_utils.py — Retry, timeout, and circuit breaker utilities.

Provides:
  - @retry decorator with exponential backoff
  - with_timeout() context manager
  - CircuitBreaker class for external service protection

Usage:
    from tools.retry_utils import retry, with_timeout, CircuitBreaker

    @retry(max_attempts=3, backoff_factor=2.0)
    def call_llm(): ...

    with with_timeout(seconds=30):
        response = llm.invoke(messages)
"""

from __future__ import annotations

import functools
import logging
import signal
import threading
import time
from enum import Enum
from typing import Callable, Type, Tuple, Any

logger = logging.getLogger(__name__)


# ── Retry Decorator ───────────────────────────────────────────────────────────

def retry(
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Callable[[int, Exception], None] | None = None,
) -> Callable:
    """
    Decorator that retries a function on failure with exponential backoff.

    Args:
        max_attempts:   Total number of attempts (including the first call).
        backoff_factor: Multiplier for delay after each failure.
        initial_delay:  Seconds to wait after the first failure.
        max_delay:      Cap on retry delay.
        exceptions:     Exception types to catch and retry.
        on_retry:       Optional callback(attempt_number, exception) called before each retry.

    Example:
        @retry(max_attempts=3, backoff_factor=2.0, exceptions=(ConnectionError, TimeoutError))
        def fetch_data(url): ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = initial_delay
            last_exc: Exception | None = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt == max_attempts:
                        logger.error(
                            "[retry] %s failed after %d attempts. Last error: %s",
                            func.__name__, max_attempts, exc
                        )
                        raise

                    sleep_time = min(delay, max_delay)
                    logger.warning(
                        "[retry] %s attempt %d/%d failed: %s — retrying in %.1fs",
                        func.__name__, attempt, max_attempts, exc, sleep_time
                    )

                    if on_retry:
                        on_retry(attempt, exc)

                    time.sleep(sleep_time)
                    delay = min(delay * backoff_factor, max_delay)

            raise last_exc  # unreachable, but satisfies type checker

        return wrapper
    return decorator


# ── Timeout Context Manager ───────────────────────────────────────────────────

class TimeoutError(Exception):
    """Raised when an operation exceeds its time limit."""
    pass


class with_timeout:
    """
    Context manager that enforces a wall-clock timeout on a block of code.

    Uses threading.Event for cross-platform compatibility (POSIX + Windows).
    Note: Python cannot interrupt C-extension code (e.g. network I/O in progress)
    mid-call; this works best with cooperative code or in a thread.

    Usage:
        try:
            with with_timeout(seconds=30):
                result = llm.invoke(messages)
        except TimeoutError:
            result = "LLM timed out — please try again."
    """

    def __init__(self, seconds: float) -> None:
        self.seconds = seconds
        self._timer: threading.Timer | None = None
        self._timed_out = False

    def _raise_timeout(self) -> None:
        self._timed_out = True

    def __enter__(self) -> "with_timeout":
        self._timed_out = False
        self._timer = threading.Timer(self.seconds, self._raise_timeout)
        self._timer.daemon = True
        self._timer.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        if self._timer:
            self._timer.cancel()
        if self._timed_out and exc_type is None:
            raise TimeoutError(f"Operation timed out after {self.seconds}s")
        return False

    def check(self) -> None:
        """Call periodically inside the block to check for timeout."""
        if self._timed_out:
            raise TimeoutError(f"Operation timed out after {self.seconds}s")


# ── Circuit Breaker ───────────────────────────────────────────────────────────

class CircuitState(Enum):
    CLOSED   = "closed"    # Normal operation
    OPEN     = "open"      # Failing — reject calls immediately
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker pattern for protecting external service calls.

    States:
        CLOSED   → Normal operation. Tracks failures.
        OPEN     → Too many failures. Rejects calls for `recovery_timeout` seconds.
        HALF_OPEN → One test call allowed. If it succeeds, returns to CLOSED.

    Usage:
        groq_breaker = CircuitBreaker(name="groq", failure_threshold=5, recovery_timeout=60)

        try:
            with groq_breaker:
                response = llm.invoke(messages)
        except CircuitBreakerOpenError:
            return "Groq service temporarily unavailable. Please try again later."
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        success_threshold: int = 1,
    ) -> None:
        self.name              = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout  = recovery_timeout
        self.success_threshold = success_threshold

        self._state            = CircuitState.CLOSED
        self._failure_count    = 0
        self._success_count    = 0
        self._last_failure_time: float | None = None
        self._lock             = threading.Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if self._state == CircuitState.OPEN:
                if (
                    self._last_failure_time is not None
                    and time.monotonic() - self._last_failure_time >= self.recovery_timeout
                ):
                    self._state         = CircuitState.HALF_OPEN
                    self._success_count = 0
                    logger.info("[circuit_breaker] %s → HALF_OPEN (testing recovery)", self.name)
            return self._state

    def _on_success(self) -> None:
        with self._lock:
            self._failure_count = 0
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    self._state = CircuitState.CLOSED
                    logger.info("[circuit_breaker] %s → CLOSED (recovered)", self.name)
            else:
                self._state = CircuitState.CLOSED

    def _on_failure(self, exc: Exception) -> None:
        with self._lock:
            self._failure_count    += 1
            self._last_failure_time = time.monotonic()
            logger.warning(
                "[circuit_breaker] %s failure %d/%d: %s",
                self.name, self._failure_count, self.failure_threshold, exc
            )
            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                logger.error(
                    "[circuit_breaker] %s → OPEN (threshold %d reached)",
                    self.name, self.failure_threshold
                )

    def __enter__(self) -> "CircuitBreaker":
        if self.state == CircuitState.OPEN:
            raise CircuitBreakerOpenError(
                f"Circuit breaker '{self.name}' is OPEN — service is temporarily unavailable."
            )
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        if exc_type is None:
            self._on_success()
        elif exc_type is not CircuitBreakerOpenError:
            self._on_failure(exc_val)
        return False

    def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Convenience method: call a function through the circuit breaker."""
        with self:
            return func(*args, **kwargs)

    def status(self) -> dict:
        return {
            "name":           self.name,
            "state":          self.state.value,
            "failure_count":  self._failure_count,
            "threshold":      self.failure_threshold,
            "last_failure":   self._last_failure_time,
        }


class CircuitBreakerOpenError(Exception):
    """Raised when a call is rejected because the circuit breaker is OPEN."""
    pass


# ── Pre-built breakers for all external services ──────────────────────────────

groq_breaker    = CircuitBreaker(name="groq",    failure_threshold=5, recovery_timeout=60)
tavily_breaker  = CircuitBreaker(name="tavily",  failure_threshold=3, recovery_timeout=30)
github_breaker  = CircuitBreaker(name="github",  failure_threshold=5, recovery_timeout=120)
smtp_breaker    = CircuitBreaker(name="smtp",    failure_threshold=3, recovery_timeout=60)
imap_breaker    = CircuitBreaker(name="imap",    failure_threshold=3, recovery_timeout=60)


def get_all_breaker_status() -> dict:
    """Return health status of all circuit breakers."""
    return {
        cb.name: cb.status()
        for cb in [groq_breaker, tavily_breaker, github_breaker, smtp_breaker, imap_breaker]
    }
