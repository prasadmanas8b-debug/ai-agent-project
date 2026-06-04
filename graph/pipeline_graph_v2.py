"""
graph/pipeline_graph_v2.py — Production-grade LangGraph pipeline with:

  1. Infinite loop prevention (max iterations guard)
  2. Deadlock detection (same agent twice with no state change → FINISH)
  3. Graceful degradation (errors don't crash the graph)
  4. Observability hooks (tracing + metrics on every node)
  5. Structured logging throughout

BACKWARD COMPATIBLE: build_graph() signature unchanged.
All original agent imports preserved — no agents modified.

Usage:
    from graph.pipeline_graph_v2 import build_graph
    graph  = build_graph()
    result = graph.invoke(initial_state)
"""

from __future__ import annotations

import logging
import time
from typing import Any

from langgraph.graph import StateGraph, END

from graph.state_v2 import AgentState, record_agent_run, add_error, get_state_summary
from agents.manager_agent import run_supervisor
from agents.dynamic_research_agent import run_research_agent
from agents.writer_agent import run_writer_agent
from agents.coder_agent import run_coder_agent
from agents.github_agent import run_github_agent
from agents.pdf_agent import run_pdf_agent
from agents.email_agent import run_email_agent
from agents.convo_agent import run_convo_agent
from agents.database_agent import run_database_agent
from observability.tracer import tracer
from observability.metrics import metrics

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 10
VALID_AGENTS = frozenset({
    "research", "writer", "coder", "github",
    "pdf", "email", "convo", "database"
})


def _get_output_field(agent_name: str, state: AgentState) -> str:
    field_map = {
        "research": "research_notes", "writer": "final_report",
        "coder": "code_result", "github": "github_result",
        "pdf": "pdf_result", "email": "email_result",
        "convo": "convo_result", "database": "db_result",
        "supervisor": "next",
    }
    key = field_map.get(agent_name, "")
    val = state.get(key, "") if key else ""
    return str(val)[:200] if val else ""


def _run_with_observability(agent_name, func, state, *args):
    run_id = state.get("run_id", "unknown")
    start_ts = time.monotonic()
    logger.info("[pipeline] Starting agent: %s | run_id: %s", agent_name, run_id)

    try:
        if args:
            raw = func(*args)
            if isinstance(raw, str):
                if agent_name == "research":
                    result_state = {**state, "research_notes": raw}
                elif agent_name == "writer":
                    result_state = {**state, "final_report": raw}
                else:
                    result_state = state
            else:
                result_state = raw
        else:
            result_state = func(state)

        duration_ms = round((time.monotonic() - start_ts) * 1000, 2)

        error_key = f"{agent_name}_result"
        result_val = result_state.get(error_key, "") if hasattr(result_state, "get") else ""
        had_error = isinstance(result_val, str) and (
            result_val.startswith("❌") or "[ERROR]" in result_val
        )

        tracer.record_agent_success(
            run_id=run_id, agent=agent_name, start_ts=start_ts,
            output_preview=_get_output_field(agent_name, result_state),
        )
        metrics.record_success(agent_name, duration_ms=duration_ms)
        logger.info("[pipeline] Agent done: %s | %.0fms | error=%s", agent_name, duration_ms, had_error)
        return record_agent_run(result_state, agent_name, had_error=had_error)

    except Exception as exc:
        duration_ms = round((time.monotonic() - start_ts) * 1000, 2)
        error_msg = f"[{agent_name}] Unhandled exception: {type(exc).__name__}: {exc}"
        logger.error("[pipeline] Agent exception: %s — %s", agent_name, exc, exc_info=True)
        tracer.record_agent_failure(run_id=run_id, agent=agent_name, start_ts=start_ts, error=str(exc))
        metrics.record_failure(agent_name, error=str(exc), duration_ms=duration_ms)
        error_state = add_error(state, error_msg)
        return record_agent_run(
            {**error_state, f"{agent_name}_result": f"❌ {error_msg}"},
            agent_name, had_error=True,
        )


def supervisor_node(state: AgentState) -> AgentState:
    run_id = state.get("run_id", "unknown")
    iteration = state.get("iteration_count", 0)

    if iteration >= MAX_ITERATIONS:
        logger.warning("[pipeline] MAX_ITERATIONS (%d) reached — forcing FINISH", MAX_ITERATIONS)
        tracer.record_supervisor_decision(run_id, "FINISH (max iterations)")
        return {**state, "next": "FINISH"}

    agent_history = state.get("agent_history", [])
    if len(agent_history) >= 2:
        last_two = agent_history[-2:]
        if last_two[0] == last_two[1] and last_two[0] in VALID_AGENTS:
            if not state.get(f"{last_two[0]}_result"):
                logger.warning("[pipeline] Deadlock detected on '%s' — forcing FINISH", last_two[0])
                tracer.record_supervisor_decision(run_id, f"FINISH (deadlock: {last_two[0]})")
                return {**state, "next": "FINISH"}

    start_ts = time.monotonic()
    try:
        result = run_supervisor(state)
        duration_ms = round((time.monotonic() - start_ts) * 1000, 2)
        decision = result.get("next", "FINISH")
        logger.info("[pipeline] Supervisor → %s | iteration %d", decision, iteration)
        tracer.record_supervisor_decision(run_id, decision, duration_ms=duration_ms)
        metrics.record_success("supervisor", duration_ms=duration_ms)
        return result
    except Exception as exc:
        logger.error("[pipeline] Supervisor exception: %s — defaulting FINISH", exc, exc_info=True)
        metrics.record_failure("supervisor", error=str(exc))
        return {**state, "next": "FINISH"}


def research_node(state):
    return _run_with_observability("research", run_research_agent, state, state["task"])

def writer_node(state):
    return _run_with_observability("writer", run_writer_agent, state,
                                   state.get("research_notes", ""), state.get("task", ""))

def coder_node(state):
    return _run_with_observability("coder", run_coder_agent, state)

def github_node(state):
    return _run_with_observability("github", run_github_agent, state)

def pdf_node(state):
    return _run_with_observability("pdf", run_pdf_agent, state)

def email_node(state):
    return _run_with_observability("email", run_email_agent, state)

def convo_node(state):
    return _run_with_observability("convo", run_convo_agent, state)

def database_node(state):
    return _run_with_observability("database", run_database_agent, state)


def route_after_supervisor(state: AgentState) -> str:
    decision = state.get("next", "FINISH")
    if decision == "FINISH" or decision not in VALID_AGENTS:
        return END
    return decision


def build_graph():
    """
    Build and compile the production-grade LangGraph StateGraph.
    Drop-in replacement for the original build_graph() — same signature.
    """
    graph = StateGraph(AgentState)

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("research",   research_node)
    graph.add_node("writer",     writer_node)
    graph.add_node("coder",      coder_node)
    graph.add_node("github",     github_node)
    graph.add_node("pdf",        pdf_node)
    graph.add_node("email",      email_node)
    graph.add_node("convo",      convo_node)
    graph.add_node("database",   database_node)

    graph.set_entry_point("supervisor")

    graph.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "research": "research", "writer": "writer",
            "coder": "coder",       "github": "github",
            "pdf": "pdf",           "email": "email",
            "convo": "convo",       "database": "database",
            END: END,
        }
    )

    for agent in ["research", "writer", "coder", "github", "pdf", "email", "convo", "database"]:
        graph.add_edge(agent, "supervisor")

    return graph.compile()
