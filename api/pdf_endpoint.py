"""
api/pdf_endpoint.py
Flask endpoint that bridges the React frontend to the Python PDF Agent.

Mount this in your main Flask/FastAPI app:
  POST /api/pdf  { task, pdf_mode, pdf_text }
  -> { result: str }

Usage with Flask:
  from api.pdf_endpoint import pdf_bp
  app.register_blueprint(pdf_bp)

Usage with FastAPI:
  from api.pdf_endpoint import router
  app.include_router(router)
"""
import json

# ── Flask version ─────────────────────────────────────────────────
try:
    from flask import Blueprint, request, jsonify
    from agents.pdf_agent import run_pdf_agent

    pdf_bp = Blueprint("pdf", __name__)

    @pdf_bp.route("/api/pdf", methods=["POST"])
    def pdf_endpoint():
        body = request.get_json(force=True, silent=True) or {}
        state = {
            "task":                 body.get("task", ""),
            "pdf_mode":             body.get("pdf_mode", "auto"),
            "pdf_text":             body.get("pdf_text", ""),
            "research_notes":       "",
            "final_report":         "",
            "code_result":          "",
            "github_result":        "",
            "pdf_result":           "",
            "convo_result":         "",
            "conversation_history": [],
            "next":                 "",
        }
        try:
            result_state = run_pdf_agent(state)
            return jsonify({"result": result_state["pdf_result"]})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

except ImportError:
    pdf_bp = None  # Flask not installed


# ── FastAPI version ───────────────────────────────────────────────
try:
    from fastapi import APIRouter
    from pydantic import BaseModel

    router = APIRouter()

    class PDFRequest(BaseModel):
        task:     str  = ""
        pdf_mode: str  = "auto"
        pdf_text: str  = ""

    @router.post("/api/pdf")
    async def pdf_endpoint_fastapi(body: PDFRequest):
        from agents.pdf_agent import run_pdf_agent
        state = {
            "task":                 body.task,
            "pdf_mode":             body.pdf_mode,
            "pdf_text":             body.pdf_text,
            "research_notes":       "",
            "final_report":         "",
            "code_result":          "",
            "github_result":        "",
            "pdf_result":           "",
            "convo_result":         "",
            "conversation_history": [],
            "next":                 "",
        }
        try:
            result_state = run_pdf_agent(state)
            return {"result": result_state["pdf_result"]}
        except Exception as e:
            return {"error": str(e)}, 500

except ImportError:
    router = None  # FastAPI not installed
