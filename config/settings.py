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
from pathlib import Path
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
    """Get an optional env var with a fallback."""
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

    # Model names (can be overridden per deployment)
    MODEL_DEFAULT: str = field(default_factory=lambda: _optional("MODEL_DEFAULT", "llama-3.3-70b-versatile"))
    MODEL_SCOUT: str   = field(default_factory=lambda: _optional("MODEL_SCOUT",   "meta-llama/llama-4-scout-17b-16e-instruct"))

    # LLM limits
    MAX_TOKENS_DEFAULT: int  = field(default_factory=lambda: _optional_int("MAX_TOKENS_DEFAULT", 4096))
    LLM_TIMEOUT_SECONDS: int = field(default_factory=lambda: _optional_int("LLM_TIMEOUT_SECONDS", 30))
    LLM_MAX_RETRIES: int     = field(default_factory=lambda: _optional_int("LLM_MAX_RETRIES", 3))

    # ── Research / Web Search ─────────────────────────────────────────────────
    TAVILY_API_KEY: str           = field(default_factory=lambda: _optional("TAVILY_API_KEY"))
    TAVILY_MAX_RESULTS: int       = field(default_factory=lambda: _optional_int("TAVILY_MAX_RESULTS", 5))
    TAVILY_SEARCH_DEPTH: str      = field(default_factory=lambda: _optional("TAVILY_SEARCH_DEPTH", "advanced"))
    RESEARCH_CACHE_TTL_SECONDS: int = field(default_factory=lambda: _optional_int("RESEARCH_CACHE_TTL_SECONDS", 3600))

    # ── GitHub ────────────────────────────────────────────────────────────────
    GITHUB_TOKEN: str  = field(default_factory=lambda: _optional("GITHUB_TOKEN"))
    GITHUB_REPO: str   = field(default_factory=lambda: _optional("GITHUB_REPO"))
    GITHUB_OUTPUT_FOLDER: str = field(default_factory=lambda: _optional("GITHUB_OUTPUT_FOLDER", "git_agent_output"))

    # ── Email ─────────────────────────────────────────────────────────────────
    EMAIL_ADDRESS: str       = field(default_factory=lambda: _optional("EMAIL_ADDRESS"))
    EMAIL_PASSWORD: str      = field(default_factory=lambda: _optional("EMAIL_PASSWORD"))
    EMAIL_SMTP_HOST: str     = field(default_factory=lambda: _optional("EMAIL_SMTP_HOST", "smtp.gmail.com"))
    EMAIL_SMTP_PORT: int     = field(default_factory=lambda: _optional_int("EMAIL_SMTP_PORT", 587))
    EMAIL_IMAP_HOST: str     = field(default_factory=lambda: _optional("EMAIL_IMAP_HOST", "imap.gmail.com"))
    EMAIL_MAX_SIZE_KB: int   = field(default_factory=lambda: _optional_int("EMAIL_MAX_SIZE_KB", 10240))

    # ── Database ──────────────────────────────────────────────────────────────
    DB_TYPE: str        = field(default_factory=lambda: _optional("DB_TYPE", "sqlite"))
    DB_SQLITE_PATH: str = field(default_factory=lambda: _optional("DB_SQLITE_PATH", "database.db"))
    DB_URL: str         = field(default_factory=lambda: _optional("DB_URL"))
    DB_READ_ONLY: bool  = field(default_factory=lambda: _optional_bool("DB_READ_ONLY", False))
    DB_AUDIT_LOG: str   = field(default_factory=lambda: _optional("DB_AUDIT_LOG", "outputs/db_audit.log"))
    DB_MAX_ROWS: int    = field(default_factory=lambda: _optional_int("DB_MAX_ROWS", 1000))

    # ── Security / Input validation ───────────────────────────────────────────
    MAX_TASK_LENGTH: int          = field(default_factory=lambda: _optional_int("MAX_TASK_LENGTH", 2000))
    ENABLE_PROMPT_GUARD: bool     = field(default_factory=lambda: _optional_bool("ENABLE_PROMPT_GUARD", True))
    ENABLE_INPUT_SANITIZATION: bool = field(default_factory=lambda: _optional_bool("ENABLE_INPUT_SANITIZATION", True))

    # ── Orchestration ─────────────────────────────────────────────────────────
    MAX_GRAPH_ITERATIONS: int = field(default_factory=lambda: _optional_int("MAX_GRAPH_ITERATIONS", 10))

    # ── Paths ─────────────────────────────────────────────────────────────────
    OUTPUTS_DIR: str = field(default_factory=lambda: _optional("OUTPUTS_DIR", "outputs"))
    MEMORY_DIR: str  = field(default_factory=lambda: _optional("MEMORY_DIR",  "memory"))
    TRACES_DIR: str  = field(default_factory=lambda: _optional("TRACES_DIR",  "outputs/traces"))
    LOGS_DIR: str    = field(default_factory=lambda: _optional("LOGS_DIR",    "outputs/logs"))

    # ── Observability ─────────────────────────────────────────────────────────
    LOG_LEVEL: str         = field(default_factory=lambda: _optional("LOG_LEVEL", "INFO"))
    LOG_FORMAT: str        = field(default_factory=lambda: _optional("LOG_FORMAT", "json"))
    ENABLE_TRACING: bool   = field(default_factory=lambda: _optional_bool("ENABLE_TRACING", True))
    ENABLE_METRICS: bool   = field(default_factory=lambda: _optional_bool("ENABLE_METRICS", True))

    def validate(self) -> None:
        """Run validation checks and ensure required directories exist."""
        # Create output directories
        for dir_path in [self.OUTPUTS_DIR, self.MEMORY_DIR, self.TRACES_DIR, self.LOGS_DIR]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)

        # Warn about missing optional but important keys
        if not self.TAVILY_API_KEY:
            print("[Config] WARNING: TAVILY_API_KEY not set — Research Agent will use LLM fallback only.")
        if not self.GITHUB_TOKEN or not self.GITHUB_REPO:
            print("[Config] WARNING: GITHUB_TOKEN/GITHUB_REPO not set — GitHub Agent will be unavailable.")
        if not self.EMAIL_ADDRESS:
            print("[Config] WARNING: EMAIL_ADDRESS not set — Email Agent will run in mock mode.")

    def __repr__(self) -> str:
        """Safe repr that masks secrets."""
        return (
            f"Settings("
            f"groq={'SET' if self.GROQ_API_KEY else 'UNSET'}, "
            f"tavily={'SET' if self.TAVILY_API_KEY else 'UNSET'}, "
            f"github={'SET' if self.GITHUB_TOKEN else 'UNSET'}, "
            f"email={'SET' if self.EMAIL_ADDRESS else 'UNSET'}, "
            f"db_type={self.DB_TYPE!r}"
            f")"
        )


# Singleton — import this everywhere
settings = Settings()
