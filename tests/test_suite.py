"""
tests/test_suite.py — Full test suite for all agents and the pipeline.

Run with:
    pytest tests/test_suite.py -v
Or directly:
    python tests/test_suite.py
"""

import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from graph.state import AgentState


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_state(**kwargs) -> AgentState:
    """Return a minimal valid AgentState with overrides applied."""
    base: AgentState = {
        "task":                 "",
        "research_notes":       "",
        "final_report":         "",
        "code_result":          "",
        "github_result":        "",
        "pdf_result":           "",
        "email_result":         "",
        "convo_result":         "",
        "db_result":            "",
        "conversation_history": [],
        "next":                 "",
        "pdf_mode":             "auto",
        "pdf_text":             "",
        "pdf_bytes":            b"",
        "pdf2_bytes":           b"",
        "email_mode":           "auto",
        "email_context":        {},
        "db_mode":              "auto",
        "db_context":           {},
    }
    base.update(kwargs)
    return base


# ── Test 1: Supervisor routing ────────────────────────────────────────────────

class TestSupervisorRouting(unittest.TestCase):
    """Supervisor should route tasks to the correct agent."""

    def _mock_supervisor(self, decision: str, task: str) -> AgentState:
        with patch("agents.manager_agent._llm") as mock_llm:
            mock_llm.invoke.return_value = MagicMock(content=decision)
            from agents.manager_agent import run_supervisor
            return run_supervisor(make_state(task=task))

    def test_routes_to_research(self):
        result = self._mock_supervisor("research", "Research quantum computing")
        self.assertEqual(result["next"], "research")

    def test_routes_to_github(self):
        result = self._mock_supervisor("github", "List files in the agents folder")
        self.assertEqual(result["next"], "github")

    def test_routes_to_convo(self):
        result = self._mock_supervisor("convo", "Hello there")
        self.assertEqual(result["next"], "convo")

    def test_routes_to_pdf(self):
        result = self._mock_supervisor("pdf", "Summarize PDF at uploads/report.pdf")
        self.assertEqual(result["next"], "pdf")

    def test_routes_to_email(self):
        result = self._mock_supervisor("email", "Compose a follow-up email to the investor")
        self.assertEqual(result["next"], "email")

    def test_invalid_decision_defaults_to_finish(self):
        result = self._mock_supervisor("gibberish", "Do something weird")
        self.assertEqual(result["next"], "FINISH")


# ── Test 2: Research Agent ────────────────────────────────────────────────────

class TestResearchAgent(unittest.TestCase):
    """Research Agent should return a non-empty string."""

    def test_returns_string(self):
        with patch("agents.dynamic_research_agent._agent") as mock_agent:
            mock_agent.invoke.return_value = {"output": "## Quantum Computing\nQubits…"}
            from agents.dynamic_research_agent import run_research_agent
            result = run_research_agent("quantum computing")
            self.assertIsInstance(result, str)
            self.assertGreater(len(result), 5)

    def test_stored_in_state(self):
        with patch("agents.dynamic_research_agent._agent") as mock_agent:
            mock_agent.invoke.return_value = {"output": "Research notes about AI trends"}
            from graph.pipeline_graph import research_node
            state  = make_state(task="Research AI trends")
            result = research_node(state)
            self.assertIn("research_notes", result)
            self.assertGreater(len(result["research_notes"]), 0)


# ── Test 3: Writer Agent ──────────────────────────────────────────────────────

class TestWriterAgent(unittest.TestCase):
    """Writer Agent should produce a report string."""

    def test_returns_report(self):
        with patch("agents.writer_agent._llm") as mock_llm:
            mock_llm.invoke.return_value = MagicMock(content="# AI Report\n\n## Overview\n…")
            from agents.writer_agent import run_writer_agent
            result = run_writer_agent("Some research notes", "Research AI")
            self.assertIsInstance(result, str)
            self.assertGreater(len(result), 5)


# ── Test 4: GitHub Agent ──────────────────────────────────────────────────────

class TestGitHubAgent(unittest.TestCase):
    """GitHub Agent should parse LLM JSON and call the correct tool."""

    def test_list_files(self):
        with patch("agents.github_agent._llm") as mock_llm, \
             patch("agents.github_agent.list_files") as mock_list:
            mock_llm.invoke.return_value  = MagicMock(content='{"action":"list_files","folder_path":"agents"}')
            mock_list.return_value        = "📂 agents: manager_agent.py"
            from agents.github_agent import run_github_agent
            result = run_github_agent(make_state(task="List files in agents folder"))
            self.assertNotIn("❌", result["github_result"])

    def test_bad_json_returns_error(self):
        with patch("agents.github_agent._llm") as mock_llm:
            mock_llm.invoke.return_value = MagicMock(content="not json at all")
            from agents.github_agent import run_github_agent
            result = run_github_agent(make_state(task="Do something"))
            self.assertIn("❌", result["github_result"])


# ── Test 5: Coder Agent ───────────────────────────────────────────────────────

class TestCoderAgent(unittest.TestCase):
    """Coder Agent should generate code and push it to GitHub."""

    def test_generates_code(self):
        sample_code = 'def binary_search(arr, t):\n    pass\n\nif __name__ == "__main__":\n    pass'
        with patch("agents.coder_agent._llm") as mock_llm, \
             patch("agents.coder_agent.create_or_update_file") as mock_push:
            mock_llm.invoke.return_value = MagicMock(content=sample_code)
            mock_push.return_value       = "✅ created"
            from agents.coder_agent import run_coder_agent
            result = run_coder_agent(make_state(task="implement binary search"))
            self.assertIn("code_result", result)
            self.assertIn("✅", result["code_result"])


# ── Test 6: Convo Agent ───────────────────────────────────────────────────────

class TestConvoAgent(unittest.TestCase):
    """Convo Agent should return a reply and update history."""

    def test_returns_reply(self):
        with patch("agents.convo_agent._llm") as mock_llm:
            mock_llm.invoke.return_value = MagicMock(content="Hello! How can I help?")
            from agents.convo_agent import run_convo_agent
            result = run_convo_agent(make_state(task="Hello"))
            self.assertGreater(len(result["convo_result"]), 0)
            self.assertEqual(len(result["conversation_history"]), 2)

    def test_history_accumulates(self):
        history = [
            {"role": "user",      "content": "Hi"},
            {"role": "assistant", "content": "Hey!"},
        ]
        with patch("agents.convo_agent._llm") as mock_llm:
            mock_llm.invoke.return_value = MagicMock(content="Sure!")
            from agents.convo_agent import run_convo_agent
            result = run_convo_agent(make_state(task="Thanks", conversation_history=history))
            self.assertEqual(len(result["conversation_history"]), 4)


# ── Test 7: Pipeline integration ─────────────────────────────────────────────

class TestPipelineIntegration(unittest.TestCase):
    """End-to-end graph should run without raising exceptions."""

    def test_convo_pipeline(self):
        with patch("agents.manager_agent._llm") as mock_sup, \
             patch("agents.convo_agent._llm")    as mock_convo:

            # First call: supervisor returns "convo"
            # Second call: supervisor returns "FINISH"
            mock_sup.invoke.side_effect = [
                MagicMock(content="convo"),
                MagicMock(content="FINISH"),
            ]
            mock_convo.invoke.return_value = MagicMock(content="Hello! How can I help?")

            from graph.pipeline_graph import build_graph
            graph  = build_graph()
            state  = make_state(task="Hello")
            result = graph.invoke(state)

            self.assertGreater(len(result.get("convo_result", "")), 0)


# ── Runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    unittest.main(verbosity=2)
