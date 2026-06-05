"""
conftest.py — Pytest configuration and shared fixtures.

Auto-discovered by pytest. Provides:
  - Project root on sys.path
  - Shared fixtures: empty_state, mock_groq_llm
  - Environment setup for tests (mock API keys if not set)
"""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# Add project root to path so all imports work
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# ── Mock environment variables for testing ────────────────────────────────────
# These prevent tests from failing due to missing real API keys
os.environ.setdefault("GROQ_API_KEY", "test-groq-key-placeholder")
os.environ.setdefault("TAVILY_API_KEY", "test-tavily-key-placeholder")
os.environ.setdefault("GITHUB_TOKEN", "test-github-token-placeholder")
os.environ.setdefault("GITHUB_REPO", "testuser/test-repo")
os.environ.setdefault("DB_TYPE", "sqlite")
os.environ.setdefault("DB_SQLITE_PATH", ":memory:")


# ── Shared fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def empty_state():
    """Return a fully populated empty AgentState dict."""
    return {
        "task":                 "",
        "next":                 "",
        "research_notes":       "",
        "final_report":         "",
        "code_result":          "",
        "github_result":        "",
        "pdf_result":           "",
        "email_result":         "",
        "convo_result":         "",
        "db_result":            "",
        "conversation_history": [],
        "pdf_mode":             "auto",
        "pdf_text":             "",
        "pdf_bytes":            b"",
        "pdf2_bytes":           b"",
        "email_mode":           "auto",
        "email_context":        {},
        "db_mode":              "auto",
        "db_context":           {},
    }


@pytest.fixture
def mock_llm_response():
    """Return a mock ChatGroq that returns a fixed response."""
    mock = MagicMock()
    mock.invoke.return_value = MagicMock(content="Mock LLM response for testing.")
    return mock


@pytest.fixture
def research_state(empty_state):
    """State with research notes pre-filled."""
    return {**empty_state, "task": "Research quantum computing", "research_notes": "Quantum computing uses qubits..."}
