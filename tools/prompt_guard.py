"""
tools/prompt_guard.py — Prompt injection defense and input sanitization.

Protects the system against:
  - Prompt injection (override instructions)
  - Jailbreak attempts
  - Role-play injection ("you are now...")
  - System prompt leakage attempts
  - Token flooding (unbounded input length)
  - Control character injection
  - Null byte injection

Usage:
    from tools.prompt_guard import sanitize_input, PromptInjectionError

    try:
        clean_task = sanitize_input(user_input, max_length=2000)
    except PromptInjectionError as e:
        return f"Input rejected: {e}"
"""

from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass
from typing import List, Tuple

logger = logging.getLogger(__name__)


class PromptInjectionError(ValueError):
    """Raised when a potential prompt injection attempt is detected."""
    pass


@dataclass
class GuardResult:
    is_safe: bool
    cleaned_text: str
    warnings: List[str]
    blocked_patterns: List[str]


# ── Injection pattern library ─────────────────────────────────────────────────

# Patterns that suggest an attempt to override system instructions
_INJECTION_PATTERNS: List[Tuple[str, str]] = [
    # Classic instruction overrides
    (r"ignore\s+(all\s+)?(previous|above|prior|earlier)\s+(instructions?|prompts?|rules?|context)",
     "instruction override attempt"),
    (r"disregard\s+(all\s+)?(previous|above|prior)\s+(instructions?|prompts?)",
     "instruction override attempt"),
    (r"forget\s+(everything|all)\s+(you\s+)?(know|were told|learned)",
     "memory wipe attempt"),

    # Role injection
    (r"you\s+are\s+now\s+(?!a\s+(?:research|writing|coding|github|pdf|email|convo|database)\s+agent)",
     "role injection attempt"),
    (r"act\s+as\s+(?:a\s+)?(?:different|evil|uncensored|unrestricted|jailbroken)",
     "role injection attempt"),
    (r"pretend\s+(you\s+are|to\s+be)\s+(?!a\s+helpful)",
     "persona injection attempt"),
    (r"from\s+now\s+on\s+you\s+(are|will be|must)",
     "persistent instruction injection"),

    # Jailbreak markers
    (r"\bDAN\s+mode\b",                          "jailbreak attempt (DAN)"),
    (r"\bjailbreak\b",                            "jailbreak keyword"),
    (r"\bdeveloper\s+mode\b",                    "developer mode unlock attempt"),
    (r"\bgrandma\s+trick\b",                     "known jailbreak pattern"),
    (r"as\s+an\s+AI\s+without\s+restrictions",   "restriction bypass attempt"),
    (r"without\s+(any\s+)?(ethical\s+)?restrictions", "restriction bypass attempt"),

    # System prompt extraction
    (r"(reveal|show|print|output|display|repeat)\s+(your\s+)?(system|initial|original)\s+prompt",
     "system prompt extraction attempt"),
    (r"what\s+(are|were)\s+your\s+(original\s+)?instructions",
     "instruction extraction attempt"),
    (r"(ignore|skip)\s+(the\s+)?(?:safety|content)\s+filter",
     "safety filter bypass attempt"),

    # Template injection (LangChain-specific)
    (r"\{[^}]*\{",                               "nested template injection"),
    (r"<\|im_start\|>",                          "OpenAI chat template injection"),
    (r"<\|im_end\|>",                            "OpenAI chat template injection"),
    (r"\[INST\]",                                "Llama instruction injection"),
    (r"\[/INST\]",                               "Llama instruction injection"),
    (r"<<SYS>>",                                 "system prompt injection marker"),
    (r"<</SYS>>",                                "system prompt injection marker"),

    # Script/code injection into prompts
    (r"```python\s+import\s+os",                 "potential command injection in code block"),
    (r"__import__\s*\(",                         "Python import injection"),
    (r"exec\s*\(",                               "exec() injection attempt"),
    (r"eval\s*\(",                               "eval() injection attempt"),
]

# Patterns that are suspicious but not blocking (generate warnings only)
_WARNING_PATTERNS: List[Tuple[str, str]] = [
    (r"what\s+is\s+your\s+(name|model|version)",  "capability probing"),
    (r"translate\s+this\s+to\s+\w+\s+and\s+execute", "translate-execute chain"),
    (r"in\s+\w+\s+language.*execute",             "cross-language execution"),
]


# ── Main sanitization function ────────────────────────────────────────────────

def sanitize_input(
    text: str,
    max_length: int = 2000,
    allow_code_blocks: bool = False,
    raise_on_injection: bool = True,
) -> str:
    """
    Sanitize user input before it reaches any LLM prompt.

    Steps:
        1. Enforce length limit
        2. Strip null bytes and control characters
        3. Check for prompt injection patterns
        4. Optionally block code blocks

    Args:
        text:                 Raw user input.
        max_length:           Maximum allowed character length.
        allow_code_blocks:    If False, strips markdown code fences.
        raise_on_injection:   If True, raises PromptInjectionError on detection.
                              If False, sanitizes the input and logs a warning.

    Returns:
        Cleaned, safe input string.

    Raises:
        PromptInjectionError: If injection detected and raise_on_injection=True.
    """
    result = _check_input(text, max_length, allow_code_blocks)

    if result.blocked_patterns:
        pattern_summary = "; ".join(result.blocked_patterns[:3])
        log_msg = f"[prompt_guard] Injection attempt detected — {pattern_summary} | input[:100]: {text[:100]!r}"
        logger.warning(log_msg)

        if raise_on_injection:
            raise PromptInjectionError(
                f"Input contains potentially malicious content ({result.blocked_patterns[0]}). "
                f"Please rephrase your request."
            )

    for warning in result.warnings:
        logger.info("[prompt_guard] Warning: %s | input[:100]: %s", warning, text[:100])

    return result.cleaned_text


def check_input(text: str, max_length: int = 2000) -> GuardResult:
    """
    Check input without raising — returns a GuardResult with details.
    Useful for logging pipelines where you want to proceed but track issues.
    """
    return _check_input(text, max_length, allow_code_blocks=True)


def _check_input(text: str, max_length: int, allow_code_blocks: bool) -> GuardResult:
    """Internal implementation."""
    warnings: List[str] = []
    blocked: List[str]  = []

    # Step 1: Length enforcement
    if len(text) > max_length:
        logger.warning(
            "[prompt_guard] Input truncated from %d to %d chars", len(text), max_length
        )
        text = text[:max_length]

    # Step 2: Remove null bytes and dangerous control characters
    # Keep: tab (\x09), newline (\x0a), carriage return (\x0d)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # Step 3: Check injection patterns
    for pattern, description in _INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
            blocked.append(description)

    # Step 4: Check warning patterns
    for pattern, description in _WARNING_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            warnings.append(description)

    # Step 5: Strip code fences if not allowed
    if not allow_code_blocks:
        text = re.sub(r"```[a-zA-Z0-9_\-]*\n?.*?```", "[code block removed]", text, flags=re.DOTALL)

    is_safe = len(blocked) == 0

    return GuardResult(
        is_safe=is_safe,
        cleaned_text=text,
        warnings=warnings,
        blocked_patterns=blocked,
    )


# ── SQL-specific protection ───────────────────────────────────────────────────

def validate_llm_sql(sql: str, read_only: bool = False) -> str:
    """
    Validate LLM-generated SQL before execution.

    Prevents:
        - Direct SQL injection via LLM hallucination
        - DML in read-only mode
        - Dangerous administrative commands

    Args:
        sql:       The SQL string generated by an LLM.
        read_only: If True, only SELECT/SHOW/DESCRIBE are allowed.

    Returns:
        The original SQL string (if valid).

    Raises:
        ValueError: If the SQL is invalid or dangerous.
    """
    try:
        import sqlparse
    except ImportError:
        logger.warning("[prompt_guard] sqlparse not installed — SQL validation skipped")
        return sql

    sql = sql.strip().rstrip(";")  # normalize

    if not sql:
        raise ValueError("Empty SQL query")

    # Check for multiple statements (common injection vector)
    statements = [s for s in sqlparse.split(sql) if s.strip()]
    if len(statements) > 1:
        raise ValueError(
            f"Multiple SQL statements not allowed (got {len(statements)}). "
            f"Execute one statement at a time."
        )

    parsed = sqlparse.parse(sql)
    if not parsed:
        raise ValueError("Could not parse SQL")

    stmt_type = parsed[0].get_type()

    # Block dangerous administrative commands
    dangerous_keywords = [
        "DROP DATABASE", "DROP SCHEMA", "TRUNCATE",
        "ALTER USER", "CREATE USER", "DROP USER",
        "GRANT", "REVOKE",
        "EXEC", "EXECUTE",
        "xp_cmdshell", "sp_executesql",
    ]
    sql_upper = sql.upper()
    for kw in dangerous_keywords:
        if kw in sql_upper:
            raise ValueError(f"Dangerous SQL keyword blocked: {kw}")

    # Read-only enforcement
    if read_only and stmt_type not in ("SELECT", "SHOW", "DESCRIBE", None):
        raise ValueError(
            f"Read-only mode active: only SELECT/SHOW/DESCRIBE allowed, got {stmt_type}"
        )

    return sql
