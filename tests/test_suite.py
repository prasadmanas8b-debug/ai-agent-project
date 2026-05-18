"""
tests/test_suite.py
Full test suite — 7 tests covering all agent scenarios.
Run with: pytest tests/test_suite.py -v
Or directly: python tests/test_suite.py
"""
import os, sys, json, unittest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from unittest.mock import patch, MagicMock
from graph.state import AgentState


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def make_state(**kwargs) -> AgentState:
    base = {"task": "", "research_notes": "", "final_report": "", "github_result": "", "next": ""}
    base.update(kwargs)
    return base


# ─────────────────────────────────────────────────────────────────────────────
# Test 1 — Research Only (Baseline)
# ─────────────────────────────────────────────────────────────────────────────

class Test1ResearchOnly(unittest.TestCase):
    """Supervisor should route to research when task needs it and notes are empty."""

    def test_supervisor_routes_to_research(self):
        with patch("agents.manager_agent._llm") as mock_llm:
            mock_llm.invoke.return_value = MagicMock(content="research")
            from agents.manager_agent import run_supervisor
            state = make_state(task="Research quantum computing")
            result = run_supervisor(state)
            self.assertEqual(result["next"], "research")

    def test_research_agent_returns_string(self):
        with patch("agents.dynamic_research_agent._agent") as mock_agent:
            mock_agent.invoke.return_value = {
                "messages": [MagicMock(content="## Quantum Computing\nQuantum computers use qubits...")]
            }
            from agents.dynamic_research_agent import run_research_agent
            result = run_research_agent("quantum computing")
            self.assertIsInstance(result, str)
            self.assertGreater(len(result), 10)

    def test_research_output_stored_in_state(self):
        with patch("agents.dynamic_research_agent._agent") as mock_agent:
            mock_agent.invoke.return_value = {
                "messages": [MagicMock(content="Research notes about AI trends")]
            }
            from graph.pipeline_graph import research_node
            state = make_state(task="Research AI trends")
            result = research_node(state)
            self.assertIn("research_notes", result)
            self.assertGreater(len(result["research_notes"]), 0)


# ─────────────────────────────────────────────────────────────────────────────
# Test 2 — GitHub Only (No Research)
# ─────────────────────────────────────────────────────────────────────────────

class Test2GitHubOnly(unittest.TestCase):
    """Supervisor should route directly to github for list/file tasks."""

    def test_supervisor_routes_to_github_for_list(self):
        with patch("agents.manager_agent._llm") as mock_llm:
            mock_llm.invoke.return_value = MagicMock(content="github")
            from agents.manager_agent import run_supervisor
            state = make_state(task="List files in the agents folder")
            result = run_supervisor(state)
            self.assertEqual(result["next"], "github")

    def test_github_agent_list_files(self):
        with patch("agents.github_agent._llm") as mock_llm, \
             patch("agents.github_agent.list_files") as mock_list:
            mock_llm.invoke.return_value = MagicMock(
                content='{"action": "list_files", "folder_path": "agents"}'
            )
            mock_list.return_value = "📂 Files in 'agents': manager_agent.py, research_agent.py"
            from agents.github_agent import run_github_agent
            state = make_state(task="List files in agents folder")
            result = run_github_agent(state)
            self.assertIn("github_result", result)
            self.assertNotIn("❌", result["github_result"])

    def test_github_agent_read_file(self):
        with patch("agents.github_agent._llm") as mock_llm, \
             patch("agents.github_agent.read_file") as mock_read:
            mock_llm.invoke.return_value = MagicMock(
                content='{"action": "read_file", "path": "git_agent_output/report.md"}'
            )
            mock_read.return_value = "📄 Content of 'git_agent_output/report.md':\n\n# Report"
            from agents.github_agent import run_github_agent
            state = make_state(task="Read the report file")
            result = run_github_agent(state)
            self.assertIn("github_result", result)


# ─────────────────────────────────────────────────────────────────────────────
# Test 3 — Research + Save (Full Pipeline)
# ─────────────────────────────────────────────────────────────────────────────

class Test3FullPipeline(unittest.TestCase):
    """Full flow: research → writer → github → FINISH."""

    def test_writer_agent_produces_report(self):
        with patch("agents.writer_agent._llm") as mock_llm:
            mock_llm.invoke.return_value = MagicMock(
                content="## AI Trends\nAI is advancing rapidly...\n## Bottom Line\nAI is transforming industries."
            )
            from agents.writer_agent import run_writer_agent
            result = run_writer_agent("Some research notes about AI", "AI Trends")
            self.assertIsInstance(result, str)
            self.assertGreater(len(result), 20)

    def test_writer_output_stored_in_state(self):
        with patch("agents.writer_agent._llm") as mock_llm:
            mock_llm.invoke.return_value = MagicMock(content="# Final Report\n\nAI is changing the world.")
            from graph.pipeline_graph import writer_node
            state = make_state(task="Research AI and save to GitHub", research_notes="AI notes here")
            result = writer_node(state)
            self.assertIn("final_report", result)
            self.assertGreater(len(result["final_report"]), 0)

    def test_supervisor_routes_to_github_after_report(self):
        with patch("agents.manager_agent._llm") as mock_llm:
            mock_llm.invoke.return_value = MagicMock(content="github")
            from agents.manager_agent import run_supervisor
            state = make_state(
                task="Research AI trends and save to GitHub",
                research_notes="Some notes",
                final_report="## Report\nContent here."
            )
            result = run_supervisor(state)
            self.assertEqual(result["next"], "github")

    def test_github_saves_report(self):
        with patch("agents.github_agent._llm") as mock_llm, \
             patch("agents.github_agent.create_or_update_file") as mock_save:
            mock_llm.invoke.return_value = MagicMock(
                content='{"action": "create_or_update_file", "path": "git_agent_output/report_ai.md", "content": "# Report", "commit_message": "Add AI report"}'
            )
            mock_save.return_value = "✅ File 'git_agent_output/report_ai.md' created"
            from agents.github_agent import run_github_agent
            state = make_state(
                task="Save this report to GitHub",
                final_report="# AI Report\n\nContent..."
            )
            result = run_github_agent(state)
            self.assertIn("✅", result["github_result"])


# ─────────────────────────────────────────────────────────────────────────────
# Test 4 — Ambiguous Input (Stress Test)
# ─────────────────────────────────────────────────────────────────────────────

class Test4AmbiguousInput(unittest.TestCase):
    """Supervisor should handle unusual/vague inputs without crashing."""

    def test_ambiguous_task_does_not_crash(self):
        with patch("agents.manager_agent._llm") as mock_llm:
            mock_llm.invoke.return_value = MagicMock(content="research")
            from agents.manager_agent import run_supervisor
            state = make_state(task="do the thing with the stuff")
            result = run_supervisor(state)
            self.assertIn(result["next"], ["research", "writer", "github", "FINISH"])

    def test_unexpected_llm_decision_defaults_to_finish(self):
        with patch("agents.manager_agent._llm") as mock_llm:
            mock_llm.invoke.return_value = MagicMock(content="dance")  # invalid
            from agents.manager_agent import run_supervisor
            state = make_state(task="do something weird")
            result = run_supervisor(state)
            self.assertEqual(result["next"], "FINISH")

    def test_very_long_task_string(self):
        with patch("agents.manager_agent._llm") as mock_llm:
            mock_llm.invoke.return_value = MagicMock(content="research")
            from agents.manager_agent import run_supervisor
            long_task = "Research " + "AI " * 500
            state = make_state(task=long_task)
            result = run_supervisor(state)
            self.assertIn(result["next"], ["research", "writer", "github", "FINISH"])

    def test_special_characters_in_task(self):
        with patch("agents.manager_agent._llm") as mock_llm:
            mock_llm.invoke.return_value = MagicMock(content="FINISH")
            from agents.manager_agent import run_supervisor
            state = make_state(task="!@#$%^&*() <script>alert('xss')</script>")
            result = run_supervisor(state)
            self.assertIn(result["next"], ["research", "writer", "github", "FINISH"])


# ─────────────────────────────────────────────────────────────────────────────
# Test 5 — GitHub Action Only
# ─────────────────────────────────────────────────────────────────────────────

class Test5GitHubActionOnly(unittest.TestCase):
    """GitHub agent handles create, update, delete, branch actions correctly."""

    def test_create_file(self):
        with patch("agents.github_agent._llm") as mock_llm, \
             patch("agents.github_agent.create_file") as mock_fn:
            mock_llm.invoke.return_value = MagicMock(
                content='{"action": "create_file", "path": "git_agent_output/new.md", "content": "hello", "commit_message": "Add new file"}'
            )
            mock_fn.return_value = "✅ File 'git_agent_output/new.md' created"
            from agents.github_agent import run_github_agent
            state = make_state(task="Create a new file called new.md with content hello")
            result = run_github_agent(state)
            self.assertIn("✅", result["github_result"])

    def test_create_branch(self):
        with patch("agents.github_agent._llm") as mock_llm, \
             patch("agents.github_agent.create_branch") as mock_fn:
            mock_llm.invoke.return_value = MagicMock(
                content='{"action": "create_branch", "branch_name": "feature-test", "source_branch": "main"}'
            )
            mock_fn.return_value = "✅ Branch 'feature-test' created from 'main'."
            from agents.github_agent import run_github_agent
            state = make_state(task="Create a branch called feature-test")
            result = run_github_agent(state)
            self.assertIn("✅", result["github_result"])

    def test_delete_file(self):
        with patch("agents.github_agent._llm") as mock_llm, \
             patch("agents.github_agent.delete_file") as mock_fn:
            mock_llm.invoke.return_value = MagicMock(
                content='{"action": "delete_file", "path": "git_agent_output/old.md", "commit_message": "Remove old file"}'
            )
            mock_fn.return_value = "✅ File 'git_agent_output/old.md' deleted"
            from agents.github_agent import run_github_agent
            state = make_state(task="Delete git_agent_output/old.md")
            result = run_github_agent(state)
            self.assertIn("✅", result["github_result"])

    def test_path_always_in_output_folder(self):
        """Paths must always be redirected to git_agent_output/."""
        from agents.github_agent import _enforce_output_folder
        self.assertEqual(_enforce_output_folder("report.md"), "git_agent_output/report.md")
        self.assertEqual(_enforce_output_folder("outputs/report.md"), "git_agent_output/report.md")
        self.assertEqual(_enforce_output_folder("git_agent_output/report.md"), "git_agent_output/report.md")


# ─────────────────────────────────────────────────────────────────────────────
# Test 6 — Empty / Garbage Input (Edge Case)
# ─────────────────────────────────────────────────────────────────────────────

class Test6EdgeCases(unittest.TestCase):
    """System should not crash on empty or bad inputs."""

    def test_empty_task_supervisor(self):
        with patch("agents.manager_agent._llm") as mock_llm:
            mock_llm.invoke.return_value = MagicMock(content="FINISH")
            from agents.manager_agent import run_supervisor
            state = make_state(task="")
            result = run_supervisor(state)
            self.assertIn(result["next"], ["research", "writer", "github", "FINISH"])

    def test_writer_rejects_empty_notes(self):
        from agents.writer_agent import run_writer_agent
        result = run_writer_agent("", "some topic")
        self.assertIn("Error", result)

    def test_writer_rejects_too_short_notes(self):
        from agents.writer_agent import run_writer_agent
        result = run_writer_agent("hi", "topic")
        self.assertIn("Error", result)

    def test_github_agent_handles_bad_json(self):
        with patch("agents.github_agent._llm") as mock_llm:
            mock_llm.invoke.return_value = MagicMock(content="not valid json at all!!")
            from agents.github_agent import run_github_agent
            state = make_state(task="Do something")
            result = run_github_agent(state)
            self.assertIn("❌", result["github_result"])

    def test_state_fields_always_present(self):
        """All required AgentState fields must always be present after supervisor."""
        with patch("agents.manager_agent._llm") as mock_llm:
            mock_llm.invoke.return_value = MagicMock(content="FINISH")
            from agents.manager_agent import run_supervisor
            state = make_state(task="")
            result = run_supervisor(state)
            for key in ["task", "research_notes", "final_report", "github_result", "next"]:
                self.assertIn(key, result)


# ─────────────────────────────────────────────────────────────────────────────
# Test 7 — Multi-step Explicit (Hardest)
# ─────────────────────────────────────────────────────────────────────────────

class Test7MultiStepExplicit(unittest.TestCase):
    """Full pipeline: research → writer → github, checking state at each step."""

    def test_full_pipeline_state_transitions(self):
        """Simulate the full graph flow and verify state at every step."""
        # Step 1: Supervisor → research
        with patch("agents.manager_agent._llm") as mock_llm:
            mock_llm.invoke.return_value = MagicMock(content="research")
            from agents.manager_agent import run_supervisor
            state = make_state(task="Research LangGraph and save report to GitHub")
            state = run_supervisor(state)
            self.assertEqual(state["next"], "research")

        # Step 2: Research node fills research_notes
        with patch("agents.dynamic_research_agent._agent") as mock_agent:
            mock_agent.invoke.return_value = {
                "messages": [MagicMock(content="## LangGraph\nLangGraph is a graph-based orchestration framework...")]
            }
            from graph.pipeline_graph import research_node
            state = research_node(state)
            self.assertGreater(len(state["research_notes"]), 0)

        # Step 3: Supervisor → writer
        with patch("agents.manager_agent._llm") as mock_llm:
            mock_llm.invoke.return_value = MagicMock(content="writer")
            from agents.manager_agent import run_supervisor
            state = run_supervisor(state)
            self.assertEqual(state["next"], "writer")

        # Step 4: Writer node fills final_report
        with patch("agents.writer_agent._llm") as mock_llm:
            mock_llm.invoke.return_value = MagicMock(
                content="## LangGraph Deep Dive\n\nLangGraph enables stateful multi-agent workflows.\n\n## Bottom Line\nUse LangGraph for complex agent orchestration."
            )
            from graph.pipeline_graph import writer_node
            state = writer_node(state)
            self.assertGreater(len(state["final_report"]), 0)

        # Step 5: Supervisor → github
        with patch("agents.manager_agent._llm") as mock_llm:
            mock_llm.invoke.return_value = MagicMock(content="github")
            from agents.manager_agent import run_supervisor
            state = run_supervisor(state)
            self.assertEqual(state["next"], "github")

        # Step 6: GitHub node saves the report
        with patch("agents.github_agent._llm") as mock_llm, \
             patch("agents.github_agent.create_or_update_file") as mock_save:
            mock_llm.invoke.return_value = MagicMock(
                content='{"action": "create_or_update_file", "path": "git_agent_output/langgraph_report.md", "content": "# LangGraph Report", "commit_message": "Add LangGraph report"}'
            )
            mock_save.return_value = "✅ File 'git_agent_output/langgraph_report.md' created"
            from graph.pipeline_graph import github_node
            state = github_node(state)
            self.assertIn("✅", state["github_result"])

        # Step 7: Supervisor → FINISH
        with patch("agents.manager_agent._llm") as mock_llm:
            mock_llm.invoke.return_value = MagicMock(content="FINISH")
            from agents.manager_agent import run_supervisor
            state = run_supervisor(state)
            self.assertEqual(state["next"], "FINISH")

    def test_pipeline_does_not_loop_infinitely(self):
        """Supervisor must eventually return FINISH."""
        with patch("agents.manager_agent._llm") as mock_llm:
            mock_llm.invoke.return_value = MagicMock(content="FINISH")
            from agents.manager_agent import run_supervisor
            state = make_state(
                task="Research AI and save to GitHub",
                research_notes="notes",
                final_report="report",
                github_result="saved"
            )
            result = run_supervisor(state)
            self.assertEqual(result["next"], "FINISH")


# ─────────────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  🧪 AI Agent Project — Full Test Suite (7 Tests)")
    print("="*60 + "\n")
    unittest.main(verbosity=2)
