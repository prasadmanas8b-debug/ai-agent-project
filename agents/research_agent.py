"""
agents/research_agent.py — Research Agent (redirects to dynamic_research_agent)

NOTE: The active implementation is in agents/dynamic_research_agent.py
This file is kept for backward compatibility only.
Import run_research_agent from dynamic_research_agent directly.
"""

from agents.dynamic_research_agent import run_research_agent  # noqa: F401

__all__ = ["run_research_agent"]
