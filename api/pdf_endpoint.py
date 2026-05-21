"""
api/pdf_endpoint.py
Flask + FastAPI endpoint bridge for the production-grade PDF Agent.

Supports:
  POST /api/pdf          — JSON body task
  POST /api/pdf/upload   — multipart file upload + task

Flask usage:
  from api.pdf_endpoint import pdf_bp
  app.register_blueprint(pdf_bp)

FastAPI usage:
  from api.pdf_endpoint import router
  app.include_router(router)
"""
import json
import base64

# ── Flask ─────────────────────────────────────────────────────────────────────
try:
    from flask import Blueprint, request, jsonify
    from agents.pdf_agent import run_pdf_agent

    pdf_bp = Blueprint("pdf", __name__)

    def _build_state(task, pdf_mode, pdf_text, pdf_bytes=b"", pdf2_bytes=b""):
        return {
            "task":                 task,
            "pdf_mode":             pdf_mode,
            "pdf_text":             pdf_text,
            "pdf_bytes":            pdf_bytes,
            "pdf2_bytes":           pdf2_bytes,
            "research_notes":       "",
            "final_report":         "",
            "code_result":          "",
            "github_result":        "",
            "pdf_result":           "",
            "convo_result":         "",
            "conversation_history": [],
            "next":                 "",
        }

    @pdf_bp.route("/api/pdf", methods=["POST"])
    def pdf_endpoint():
        """JSON body: { task, pdf_mode?, pdf_text?, pdf_b64?, pdf2_b64? }"""
        body = request.get_json(force=True, silent=True) or {}
        pdf_bytes  = base64.b64decode(body["pdf_b64"])  if body.get("pdf_b64")  else b""
        pdf2_bytes = base64.b64decode(body["pdf2_b64"]) if body.get("pdf2_b64") else b""
        state = _build_state(
            task=body.get("task", ""),
            pdf_mode=body.get("pdf_mode", "auto"),
            pdf_text=body.get("pdf_text", ""),
            pdf_bytes=pdf_bytes,
            pdf2_bytes=pdf2_bytes,
        )
        try:
            result_state = run_pdf_agent(state)
            return jsonify({"result": result_state["pdf_result"]})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @pdf_bp.route("/api/pdf/upload", methods=["POST"])
    def pdf_upload_endpoint():
        """Multipart: file=<pdf>, file2=<pdf2>, task=<str>, pdf_mode=<str>"""
        task     = request.form.get("task", "")
        pdf_mode = request.form.get("pdf_mode", "auto")
        pdf_bytes  = request.files["file"].read()  if "file"  in request.files else b""
        pdf2_bytes = request.files["file2"].read() if "file2" in request.files else b""
        state = _build_state(task=task, pdf_mode=pdf_mode, pdf_text="",
                             pdf_bytes=pdf_bytes, pdf2_bytes=pdf2_bytes)
        try:
            result_state = run_pdf_agent(state)
            return jsonify({"result": result_state["pdf_result"]})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @pdf_bp.route("/api/pdf/modes", methods=["GET"])
    def pdf_modes():
        """List all available PDF agent modes."""
        modes = {
            "Core": ["read","create","summarize","qa","translate","extract"],
            "Text": ["search","find_replace","watermark","page_numbers","header_footer"],
            "Pages": ["page_ops","split","merge","merge_plan"],
            "Images": ["extract_images","pdf_to_images"],
            "AI": ["reformat","classify","sentiment","ner","compare","rewrite","autotag","md_to_pdf"],
            "Data": ["tables_to_csv","to_markdown","to_html"],
            "Metadata": ["metadata","set_metadata"],
            "Security": ["protect","decrypt","redact","signature"],
            "OCR": ["ocr"],
            "Annotations": ["annotate","bookmarks"],
            "Optimization": ["compress","repair","linearize"],
            "Forms": ["forms"],
            "Accessibility": ["accessibility"],
            "Batch": ["batch"],
        }
        return jsonify({"modes": modes, "total": sum(len(v) for v in modes.values())})

except ImportError:
    pdf_bp = None


# ── FastAPI ───────────────────────────────────────────────────────────────────
try:
    from fastapi import APIRouter, UploadFile, File, Form
    from pydantic import BaseModel
    from typing import Optional

    router = APIRouter()

    class PDFRequest(BaseModel):
        task:      str = ""
        pdf_mode:  str = "auto"
        pdf_text:  str = ""
        pdf_b64:   str = ""   # base64-encoded PDF bytes
        pdf2_b64:  str = ""   # second PDF for compare/merge

    def _build_state_fa(body: PDFRequest):
        from agents.pdf_agent import run_pdf_agent as _run
        pdf_bytes  = base64.b64decode(body.pdf_b64)  if body.pdf_b64  else b""
        pdf2_bytes = base64.b64decode(body.pdf2_b64) if body.pdf2_b64 else b""
        return {
            "task":                 body.task,
            "pdf_mode":             body.pdf_mode,
            "pdf_text":             body.pdf_text,
            "pdf_bytes":            pdf_bytes,
            "pdf2_bytes":           pdf2_bytes,
            "research_notes":       "",
            "final_report":         "",
            "code_result":          "",
            "github_result":        "",
            "pdf_result":           "",
            "convo_result":         "",
            "conversation_history": [],
            "next":                 "",
        }

    @router.post("/api/pdf")
    async def pdf_endpoint_fastapi(body: PDFRequest):
        from agents.pdf_agent import run_pdf_agent
        state = _build_state_fa(body)
        try:
            result_state = run_pdf_agent(state)
            return {"result": result_state["pdf_result"]}
        except Exception as e:
            return {"error": str(e)}

    @router.post("/api/pdf/upload")
    async def pdf_upload_fastapi(
        task:      str        = Form(""),
        pdf_mode:  str        = Form("auto"),
        file:      UploadFile = File(None),
        file2:     UploadFile = File(None),
    ):
        from agents.pdf_agent import run_pdf_agent
        pdf_bytes  = await file.read()  if file  else b""
        pdf2_bytes = await file2.read() if file2 else b""
        state = {
            "task": task, "pdf_mode": pdf_mode, "pdf_text": "",
            "pdf_bytes": pdf_bytes, "pdf2_bytes": pdf2_bytes,
            "research_notes": "", "final_report": "", "code_result": "",
            "github_result": "", "pdf_result": "", "convo_result": "",
            "conversation_history": [], "next": "",
        }
        try:
            result_state = run_pdf_agent(state)
            return {"result": result_state["pdf_result"]}
        except Exception as e:
            return {"error": str(e)}

    @router.get("/api/pdf/modes")
    async def pdf_modes_fastapi():
        modes = {
            "Core": ["read","create","summarize","qa","translate","extract"],
            "Text": ["search","find_replace","watermark","page_numbers","header_footer"],
            "Pages": ["page_ops","split","merge","merge_plan"],
            "Images": ["extract_images","pdf_to_images"],
            "AI": ["reformat","classify","sentiment","ner","compare","rewrite","autotag","md_to_pdf"],
            "Data": ["tables_to_csv","to_markdown","to_html"],
            "Metadata": ["metadata","set_metadata"],
            "Security": ["protect","decrypt","redact","signature"],
            "OCR": ["ocr"],
            "Annotations": ["annotate","bookmarks"],
            "Optimization": ["compress","repair","linearize"],
            "Forms": ["forms"],
            "Accessibility": ["accessibility"],
            "Batch": ["batch"],
        }
        return {"modes": modes, "total": sum(len(v) for v in modes.values())}

except ImportError:
    router = None
