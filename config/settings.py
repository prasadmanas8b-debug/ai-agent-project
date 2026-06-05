"""
config/settings.py — Centralized configuration for the AI Agent Orchestration Framework.

All environment variables are validated at startup. No agent should call
os.getenv() directly — import from here instead.

Usage:
    from config.settings import settings
    api_key = settings.GROQ_API_KEY
"""

from __future__ import annotations
import os
import sys
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    """Get a required env var or exit with a clear error message."""
    val = os.getenv(key, "").strip()
    if not val:
        print(f"[Config] FATAL: Required environment variable '{key}' is not set.")
        print(f"[Config] Copy .env.example to .env and fill in all required values.")
        sys.exit(1)
    return val


def _optional(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


def _optional_bool(key: str, default: bool = False) -> bool:
    val = os.getenv(key, "").strip().lower()
    if val in ("1", "true", "yes"):
        return True
    if val in ("0", "false", "no"):
        return False
    return default


def _optional_int(key: str, default: int = 0) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    # ── LLM ──────────────────────────────────────────────────────────────────
    GROQ_API_KEY: str = field(default_factory=lambda: _require("GROQ_API_KEY"))

    MODEL_DEFAULT: str = field(default_factory=lambda: _optional("MODEL_DEFAULT", "llama-3.3-70b-versatile"))
    MODEL_SCOUT: str   = field(default_factory=lambda: _optional("MODEL_SCOUT", "meta-llama/llama-4-scout-17b-16e-instruct"))

    MAX_TOKENS_DEFAULT: int  = field(default_factory=lambda: _optional_int("MAX_TOKENS_DEFAULT", 4096))
    LLM_TIMEOUT_SECONDS: int = field(default_factory=lambda: _optional_int("LLM_TIMEOUT_SECONDS", 30))
    LLM_MAX_RETRIES: int     = field(default_factory=lambda: _optional_int("LLM_MAX_RETRIES", 3))

    # ── Research / Web Search ─────────────────────────────────────────────────
    TAVILY_API_KEY: str     = field(default_factory=lambda: _optional("TAVILY_API_KEY"))
    TAVILY_MAX_RESULTS: int = field(default_factory=lambda: _optional_int("TAVILY_MAX_RESULTS", 5))
    TAVILY_SEARCH_DEPTH: str = field(default_factory=lambda: _optional("TAVILY_SEARCH_DEPTH", "advanced"))

    # ── GitHub ────────────────────────────────────────────────────────────────
    GITHUB_TOKEN: str = field(default_factory=lambda: _optional("GITHUB_TOKEN"))
    GITHUB_REPO: str  = field(default_factory=lambda: _optional("GITHUB_REPO"))

    # ── Email ─────────────────────────────────────────────────────────────────
    EMAIL_ADDRESS: str  = field(default_factory=lambda: _optional("EMAIL_ADDRESS"))
    EMAIL_PASSWORD: str = field(default_factory=lambda: _optional("EMAIL_PASSWORD"))
    SMTP_HOST: str      = field(default_factory=lambda: _optional("SMTP_HOST", "smtp.gmail.com"))
    SMTP_PORT: int      = field(default_factory=lambda: _optional_int("SMTP_PORT", 587))
    IMAP_HOST: str      = field(default_factory=lambda: _optional("IMAP_HOST", "imap.gmail.com"))
    IMAP_PORT: int      = field(default_factory=lambda: _optional_int("IMAP_PORT", 993))

    # Also support EMAIL_SMTP_HOST / EMAIL_IMAP_HOST aliases used in email_agent.py
    EMAIL_SMTP_HOST: str = field(default_factory=lambda: _optional("EMAIL_SMTP_HOST") or _optional("SMTP_HOST", "smtp.gmail.com"))
    EMAIL_SMTP_PORT: int = field(default_factory=lambda: _optional_int("EMAIL_SMTP_PORT") or _optional_int("SMTP_PORT", 587))
    EMAIL_IMAP_HOST: str = field(default_factory=lambda: _optional("EMAIL_IMAP_HOST") or _optional("IMAP_HOST", "imap.gmail.com"))
    EMAIL_IMAP_PORT: int = field(default_factory=lambda: _optional_int("EMAIL_IMAP_PORT") or _optional_int("IMAP_PORT", 993))

    # ── Database ──────────────────────────────────────────────────────────────
    DB_TYPE: str        = field(default_factory=lambda: _optional("DB_TYPE", "sqlite"))
    DB_SQLITE_PATH: str = field(default_factory=lambda: _optional("DB_SQLITE_PATH", "database.db"))
    DB_HOST: str        = field(default_factory=lambda: _optional("DB_HOST", "localhost"))
    DB_PORT: int        = field(default_factory=lambda: _optional_int("DB_PORT", 5432))
    DB_NAME: str        = field(default_factory=lambda: _optional("DB_NAME"))
    DB_USER: str        = field(default_factory=lambda: _optional("DB_USER"))
    DB_PASSWORD: str    = field(default_factory=lambda: _optional("DB_PASSWORD"))
    DB_READ_ONLY: bool  = field(default_factory=lambda: _optional_bool("DB_READ_ONLY", False))
    DB_AUDIT_LOG: str   = field(default_factory=lambda: _optional("DB_AUDIT_LOG", "outputs/db_audit.log"))

    # ── Observability ─────────────────────────────────────────────────────────
    LOG_LEVEL: str           = field(default_factory=lambda: _optional("LOG_LEVEL", "INFO"))
    LANGSMITH_API_KEY: str   = field(default_factory=lambda: _optional("LANGSMITH_API_KEY"))
    LANGSMITH_PROJECT: str   = field(default_factory=lambda: _optional("LANGSMITH_PROJECT", "ai-agent-system"))
    ENABLE_TRACING: bool     = field(default_factory=lambda: _optional_bool("ENABLE_TRACING", False))

    # ── Output ────────────────────────────────────────────────────────────────
    OUTPUTS_DIR: str = field(default_factory=lambda: _optional("OUTPUTS_DIR", "outputs"))


# Singleton — import this everywhere
settings = Settings()
