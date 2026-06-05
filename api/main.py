"""
api/main.py — FastAPI application entry point.

Routes:
  GET  /           → health check
  POST /api/agent  → generic agent task
  POST /api/email  → email agent endpoint
  POST /api/pdf    → pdf agent endpoint
  GET  /api/modes  → list all agent capabilities

Run with:
    uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
"""

from __future__ import annotations

import json
import base64
import traceback
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from graph.pipeline_graph import build_graph
from agents.email_agent import run_email_agent
from agents.pdf_agent import run_pdf_agent

# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Agent System API",
    description="Production-grade multi-agent AI — Research, Code, PDF, Email, GitHub, DB",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Build graph once at startup
_graph = None

def _get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def _empty_state(task: str) -> Dict[str, Any]:
    return {
        "task":                 task,
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


# ── Models ────────────────────────────────────────────────────────────────────

class AgentRequest(BaseModel):
    task: str
    email_context: Optional[Dict[str, Any]] = None
    db_context: Optional[Dict[str, Any]] = None


class EmailRequest(BaseModel):
    task: str
    email_mode: Optional[str] = "auto"
    email_context: Optional[Dict[str, Any]] = None


class PDFRequest(BaseModel):
    task: str
    pdf_mode: Optional[str] = "auto"
    pdf_text: Optional[str] = ""
    pdf_b64: Optional[str] = None
    pdf2_b64: Optional[str] = None


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def health_check():
    return {
        "status": "ok",
        "system": "AI Agent System v2.0",
        "agents": ["research", "writer", "coder", "github", "pdf", "email", "convo", "database"],
    }


@app.get("/api/modes")
def list_modes():
    return {
        "agents": {
            "research":  "Web search, find info, latest news, comparisons",
            "writer":    "Turn research into polished reports, blogs, summaries",
            "coder":     "Write Python code, scripts, algorithms, automation",
            "github":    "List/read/create/update/delete files on GitHub",
            "pdf":       "Summarize, extract, convert, OCR, merge, split PDFs",
            "email":     "Compose, send, read, analyze, reply to emails",
            "convo":     "General chat, greetings, system questions",
            "database":  "SQL queries, NL-to-SQL, table management, exports",
        }
    }


@app.post("/api/agent")
def run_agent(req: AgentRequest):
    """Run any task through the full agent pipeline."""
    try:
        state = _empty_state(req.task)
        if req.email_context:
            state["email_context"] = req.email_context
        if req.db_context:
            state["db_context"] = req.db_context

        result = _get_graph().invoke(state)

        return {
            "task":            result.get("task"),
            "research_notes":  result.get("research_notes", ""),
            "final_report":    result.get("final_report", ""),
            "code_result":     result.get("code_result", ""),
            "github_result":   result.get("github_result", ""),
            "pdf_result":      result.get("pdf_result", ""),
            "email_result":    result.get("email_result", ""),
            "convo_result":    result.get("convo_result", ""),
            "db_result":       result.get("db_result", ""),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Agent error: {exc}\n{traceback.format_exc()}")


@app.post("/api/email")
def run_email(req: EmailRequest):
    """Run the Email Agent directly."""
    try:
        state = _empty_state(req.task)
        state["email_mode"]    = req.email_mode or "auto"
        state["email_context"] = req.email_context or {}
        result = run_email_agent(state)
        return {"email_result": result.get("email_result", "")}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/pdf")
def run_pdf(req: PDFRequest):
    """Run the PDF Agent directly."""
    try:
        state = _empty_state(req.task)
        state["pdf_mode"]  = req.pdf_mode or "auto"
        state["pdf_text"]  = req.pdf_text or ""
        state["pdf_bytes"] = base64.b64decode(req.pdf_b64)  if req.pdf_b64  else b""
        state["pdf2_bytes"] = base64.b64decode(req.pdf2_b64) if req.pdf2_b64 else b""
        result = run_pdf_agent(state)
        return {"pdf_result": result.get("pdf_result", "")}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
