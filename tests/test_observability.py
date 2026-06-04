"""
tests/test_observability.py — Tests for the observability layer.

Tests:
  - Structured logging output
  - Metrics accumulation and reporting
  - Trace recording and file persistence

Run:
    pytest tests/test_observability.py -v
"""

import json
import os
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from implementation.observability.metrics import MetricsCollector
from implementation.observability.tracer import ExecutionTracer, new_run_id
from implementation.observability.logger import AgentLogger, get_agent_logger


class TestMetricsCollector(unittest.TestCase):

    def setUp(self):
        self.metrics = MetricsCollector()

    def test_initial_state(self):
        report = self.metrics.report()
        self.assertEqual(report["runs"]["total"], 0)
        self.assertEqual(report["runs"]["successful"], 0)
        self.assertEqual(report["runs"]["failed"], 0)
        self.assertEqual(report["agents"], {})

    def test_record_success(self):
        self.metrics.record_success("research", duration_ms=4200.0)
        report = self.metrics.report()
        self.assertIn("research", report["agents"])
        self.assertEqual(report["agents"]["research"]["success_count"], 1)
        self.assertEqual(report["agents"]["research"]["total_calls"], 1)

    def test_record_failure(self):
        self.metrics.record_failure("github", error="timeout")
        report = self.metrics.report()
        self.assertEqual(report["agents"]["github"]["failure_count"], 1)
        self.assertEqual(report["agents"]["github"]["last_error"], "timeout")

    def test_success_rate_calculation(self):
        self.metrics.record_success("coder", duration_ms=2000.0)
        self.metrics.record_success("coder", duration_ms=3000.0)
        self.metrics.record_failure("coder", error="oops")
        report = self.metrics.report()
        # 2 successes, 1 failure = 66.67%
        rate = report["agents"]["coder"]["success_rate_pct"]
        self.assertAlmostEqual(rate, 66.67, places=1)

    def test_latency_stats(self):
        durations = [100.0, 200.0, 300.0, 400.0, 500.0]
        for d in durations:
            self.metrics.record_success("writer", duration_ms=d)
        report = self.metrics.report()
        stats = report["agents"]["writer"]["latency_ms"]
        self.assertEqual(stats["min"], 100.0)
        self.assertEqual(stats["max"], 500.0)
        self.assertAlmostEqual(stats["avg"], 300.0, places=1)

    def test_tool_call_tracking(self):
        self.metrics.record_tool_call("research", "web_search", success=True, duration_ms=1200.0)
        self.metrics.record_tool_call("research", "web_search", success=True, duration_ms=800.0)
        self.metrics.record_tool_call("research", "web_search", success=False, duration_ms=500.0)
        report = self.metrics.report()
        tool_data = report["agents"]["research"]["tools"]["web_search"]
        self.assertEqual(tool_data["calls"], 3)
        self.assertEqual(tool_data["failures"], 1)

    def test_llm_call_tracking(self):
        self.metrics.record_llm_call("supervisor", estimated_tokens=1500)
        self.metrics.record_llm_call("supervisor", estimated_tokens=2000)
        report = self.metrics.report()
        self.assertEqual(report["agents"]["supervisor"]["llm_calls"], 2)
        self.assertEqual(report["agents"]["supervisor"]["estimated_tokens"], 3500)

    def test_circuit_breaker_tracking(self):
        self.metrics.record_circuit_breaker_open("groq")
        self.metrics.record_circuit_breaker_open("groq")
        report = self.metrics.report()
        self.assertEqual(report["circuit_breakers"]["groq"], 2)

    def test_run_level_tracking(self):
        self.metrics.record_run_start()
        self.metrics.record_run_start()
        self.metrics.record_run_success()
        self.metrics.record_run_failure()
        report = self.metrics.report()
        self.assertEqual(report["runs"]["total"], 2)
        self.assertEqual(report["runs"]["successful"], 1)
        self.assertEqual(report["runs"]["failed"], 1)

    def test_save_to_file(self):
        self.metrics.record_success("research", duration_ms=1000.0)
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            path = f.name
        try:
            self.metrics.save_to_file(path)
            with open(path) as f:
                data = json.load(f)
            self.assertIn("agents", data)
            self.assertIn("research", data["agents"])
        finally:
            os.unlink(path)

    def test_reset(self):
        self.metrics.record_success("research")
        self.metrics.record_failure("github", error="err")
        self.metrics.reset()
        report = self.metrics.report()
        self.assertEqual(report["agents"], {})
        self.assertEqual(report["runs"]["total"], 0)

    def test_thread_safety(self):
        """Concurrent writes should not corrupt data."""
        import threading

        def record_many():
            for _ in range(100):
                self.metrics.record_success("research", duration_ms=10.0)

        threads = [threading.Thread(target=record_many) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        report = self.metrics.report()
        self.assertEqual(report["agents"]["research"]["success_count"], 500)


class TestExecutionTracer(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tracer = ExecutionTracer(traces_dir=self.tmpdir)

    def test_start_and_finish_run(self):
        run_id = new_run_id()
        self.tracer.start_run(run_id, task="Test task")
        trace = self.tracer.finish_run(run_id, status="success")
        self.assertIsNotNone(trace)
        self.assertEqual(trace["run_id"], run_id)
        self.assertEqual(trace["status"], "success")
        self.assertEqual(trace["task"], "Test task")

    def test_trace_file_created(self):
        run_id = new_run_id()
        self.tracer.start_run(run_id, task="File creation test")
        self.tracer.finish_run(run_id)
        trace_file = os.path.join(self.tmpdir, f"run_{run_id}.json")
        self.assertTrue(os.path.exists(trace_file))
        with open(trace_file) as f:
            data = json.load(f)
        self.assertEqual(data["run_id"], run_id)

    def test_record_supervisor_decision(self):
        run_id = new_run_id()
        self.tracer.start_run(run_id, task="Routing test")
        self.tracer.record_supervisor_decision(run_id, "research", duration_ms=350.0)
        trace = self.tracer.finish_run(run_id)
        self.assertEqual(len(trace["steps"]), 1)
        self.assertEqual(trace["steps"][0]["agent"], "supervisor")
        self.assertEqual(trace["steps"][0]["decision"], "research")

    def test_record_agent_success(self):
        run_id = new_run_id()
        self.tracer.start_run(run_id, task="Agent success test")
        start_ts = self.tracer.record_agent_start(run_id, "research")
        time.sleep(0.01)
        self.tracer.record_agent_success(
            run_id=run_id, agent="research",
            start_ts=start_ts, output_preview="## Overview\nQuantum..."
        )
        trace = self.tracer.finish_run(run_id)
        step = trace["steps"][0]
        self.assertEqual(step["agent"], "research")
        self.assertEqual(step["status"], "success")
        self.assertGreater(step["duration_ms"], 0)

    def test_record_agent_failure(self):
        run_id = new_run_id()
        self.tracer.start_run(run_id, task="Failure test")
        start_ts = self.tracer.record_agent_start(run_id, "github")
        self.tracer.record_agent_failure(
            run_id=run_id, agent="github",
            start_ts=start_ts, error="Connection refused"
        )
        trace = self.tracer.finish_run(run_id, status="failure")
        step = trace["steps"][0]
        self.assertEqual(step["status"], "failure")
        self.assertIn("Connection refused", step["error"])

    def test_duration_calculated(self):
        run_id = new_run_id()
        self.tracer.start_run(run_id, task="Duration test")
        time.sleep(0.05)
        trace = self.tracer.finish_run(run_id)
        self.assertGreater(trace["total_duration_ms"], 40)  # at least 40ms

    def test_load_trace_from_disk(self):
        run_id = new_run_id()
        self.tracer.start_run(run_id, task="Persistence test")
        self.tracer.finish_run(run_id)
        loaded = self.tracer.load_trace(run_id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["run_id"], run_id)

    def test_unknown_run_id_returns_none(self):
        result = self.tracer.finish_run("nonexistent_id_xyz")
        self.assertIsNone(result)

    def test_multi_step_trace(self):
        run_id = new_run_id()
        self.tracer.start_run(run_id, task="Research and write report")

        self.tracer.record_supervisor_decision(run_id, "research")
        ts = self.tracer.record_agent_start(run_id, "research")
        self.tracer.record_agent_success(run_id, "research", ts)

        self.tracer.record_supervisor_decision(run_id, "writer")
        ts = self.tracer.record_agent_start(run_id, "writer")
        self.tracer.record_agent_success(run_id, "writer", ts)

        self.tracer.record_supervisor_decision(run_id, "FINISH")
        trace = self.tracer.finish_run(run_id, status="success")

        self.assertEqual(trace["step_count"], 5)  # sup→research→sup→writer→sup
        self.assertIn("research", trace["agents_used"])
        self.assertIn("writer", trace["agents_used"])


class TestAgentLogger(unittest.TestCase):

    def test_logger_created(self):
        log = get_agent_logger("test_agent")
        self.assertIsInstance(log, AgentLogger)
        self.assertEqual(log.agent_name, "test_agent")

    def test_same_name_returns_same_instance(self):
        log1 = get_agent_logger("shared_agent")
        log2 = get_agent_logger("shared_agent")
        self.assertIs(log1, log2)

    def test_agent_start_returns_timestamp(self):
        log = AgentLogger("timing_test")
        start = log.agent_start("Test task")
        self.assertIsInstance(start, float)

    def test_agent_success_returns_duration(self):
        log = AgentLogger("duration_test")
        log.agent_start("Test task")
        time.sleep(0.01)
        duration = log.agent_success(output_len=500)
        self.assertGreater(duration, 5.0)  # at least 5ms

    def test_bind_run_propagates(self):
        log = AgentLogger("run_bind_test")
        log.bind_run("abc123")
        self.assertEqual(log._run_id, "abc123")

    def test_score_output_confidence_empty(self):
        log = AgentLogger("confidence_test")
        self.assertEqual(log.score_output_confidence(""), 0.0)

    def test_score_output_confidence_error_response(self):
        log = AgentLogger("confidence_test2")
        score = log.score_output_confidence("I cannot help with that request.")
        self.assertLess(score, 0.5)

    def test_score_output_confidence_good_output(self):
        log = AgentLogger("confidence_test3")
        good_output = "## Overview\n" + "Detail text. " * 50 + "\n## Conclusion\nDone."
        score = log.score_output_confidence(good_output)
        self.assertGreater(score, 0.7)


class TestNewRunId(unittest.TestCase):

    def test_run_id_unique(self):
        ids = {new_run_id() for _ in range(100)}
        self.assertEqual(len(ids), 100)

    def test_run_id_length(self):
        run_id = new_run_id()
        self.assertEqual(len(run_id), 12)

    def test_run_id_hex(self):
        run_id = new_run_id()
        int(run_id, 16)  # should not raise — valid hex


if __name__ == "__main__":
    unittest.main(verbosity=2)
