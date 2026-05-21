"""
api/email_endpoint.py
Flask + FastAPI endpoint bridge for the production-grade Email Agent.

Routes:
  POST /api/email              — JSON task
  POST /api/email/send         — compose + send immediately
  POST /api/email/upload       — with attachment upload
  GET  /api/email/inbox        — fetch inbox
  GET  /api/email/modes        — list all modes

Flask:   from api.email_endpoint import email_bp; app.register_blueprint(email_bp)
FastAPI: from api.email_endpoint import router;   app.include_router(router)
"""
import json

# ── Flask ─────────────────────────────────────────────────────────────────────
try:
    from flask import Blueprint, request, jsonify
    from agents.email_agent import run_email_agent, _fetch_emails, _send_email

    email_bp = Blueprint("email", __name__)

    def _build_state(task, email_mode, email_context):
        return {
            "task":                 task,
            "email_mode":           email_mode,
            "email_context":        email_context,
            "email_result":         "",
            "research_notes":       "",
            "final_report":         "",
            "code_result":          "",
            "github_result":        "",
            "pdf_result":           "",
            "convo_result":         "",
            "conversation_history": [],
            "next":                 "",
            "pdf_mode":             "auto",
            "pdf_text":             "",
            "pdf_bytes":            b"",
            "pdf2_bytes":           b"",
        }

    @email_bp.route("/api/email", methods=["POST"])
    def email_endpoint():
        """
        JSON body:
        {
          "task":          "Compose a follow-up email to the investor",
          "email_mode":    "compose",       // optional, auto-inferred
          "email_context": {                // optional
            "to":             "name@email.com",
            "cc":             "other@email.com",
            "tone":           "formal",
            "original_email": "original email text for reply/rewrite/analyze",
            "message_id":     "<msg-id>",
            "auto_send":      false,
            "thread":         [{"from":"...","body":"...","date":"..."}],
            "recipients":     ["r1@x.com","r2@y.com"],
            "template":       "template text with {{placeholders}}"
          }
        }
        """
        body = request.get_json(force=True, silent=True) or {}
        state = _build_state(
            task=body.get("task", ""),
            email_mode=body.get("email_mode", "auto"),
            email_context=body.get("email_context", {}),
        )
        try:
            result_state = run_email_agent(state)
            return jsonify({"result": result_state["email_result"]})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @email_bp.route("/api/email/send", methods=["POST"])
    def email_send():
        """Quick send: { to, subject, body, cc?, bcc?, html_body? }"""
        body = request.get_json(force=True, silent=True) or {}
        result = _send_email(
            to=body.get("to",""),
            subject=body.get("subject",""),
            body=body.get("body",""),
            html_body=body.get("html_body",""),
            cc=body.get("cc",""),
            bcc=body.get("bcc",""),
        )
        return jsonify(result)

    @email_bp.route("/api/email/inbox", methods=["GET"])
    def email_inbox():
        """Fetch inbox. Query params: folder, limit"""
        folder = request.args.get("folder", "INBOX")
        limit  = int(request.args.get("limit", 10))
        emails = _fetch_emails(folder=folder, limit=limit)
        return jsonify({"folder": folder, "count": len(emails), "emails": emails})

    @email_bp.route("/api/email/upload", methods=["POST"])
    def email_upload():
        """Multipart: task, email_mode, file (attachment)"""
        import base64
        task       = request.form.get("task","")
        email_mode = request.form.get("email_mode","auto")
        ctx        = {}
        if "file" in request.files:
            f = request.files["file"]
            ctx["attachment"] = {
                "filename": f.filename,
                "data": base64.b64encode(f.read()).decode(),
                "content_type": f.content_type,
            }
        state = _build_state(task=task, email_mode=email_mode, email_context=ctx)
        try:
            result_state = run_email_agent(state)
            return jsonify({"result": result_state["email_result"]})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @email_bp.route("/api/email/modes", methods=["GET"])
    def email_modes():
        modes = {
            "Core Ops":      ["compose","reply","forward","send"],
            "AI Writing":    ["rewrite_tone","resize","fix_grammar","improve_clarity","translate","suggest_subject","from_bullets","match_style"],
            "Inbox":         ["read","search","digest"],
            "Analysis":      ["summarize","summarize_thread","extract_actions","extract_entities","analyze","classify"],
            "Smart":         ["smart_reply","auto_reply","follow_up"],
            "Templates":     ["template","mail_merge","drip","ab_test"],
            "Scheduling":    ["schedule","best_time"],
            "Security":      ["security_check","sensitive_data","gdpr"],
            "Integrations":  ["crm_log","meeting","unsubscribe"],
            "Bulk":          ["bulk"],
            "Output":        ["export","signature"],
        }
        return jsonify({"modes": modes, "total": sum(len(v) for v in modes.values())})

except ImportError:
    email_bp = None


# ── FastAPI ───────────────────────────────────────────────────────────────────
try:
    from fastapi import APIRouter, UploadFile, File, Form, Query
    from pydantic import BaseModel
    from typing import Optional, Dict, Any

    router = APIRouter()

    class EmailRequest(BaseModel):
        task:          str           = ""
        email_mode:    str           = "auto"
        email_context: Dict[str, Any] = {}

    class SendRequest(BaseModel):
        to:        str = ""
        subject:   str = ""
        body:      str = ""
        html_body: str = ""
        cc:        str = ""
        bcc:       str = ""

    def _build_state_fa(body: EmailRequest):
        return {
            "task":                 body.task,
            "email_mode":           body.email_mode,
            "email_context":        body.email_context,
            "email_result":         "",
            "research_notes":       "",
            "final_report":         "",
            "code_result":          "",
            "github_result":        "",
            "pdf_result":           "",
            "convo_result":         "",
            "conversation_history": [],
            "next":                 "",
            "pdf_mode":             "auto",
            "pdf_text":             "",
            "pdf_bytes":            b"",
            "pdf2_bytes":           b"",
        }

    @router.post("/api/email")
    async def email_endpoint_fa(body: EmailRequest):
        from agents.email_agent import run_email_agent
        state = _build_state_fa(body)
        try:
            result_state = run_email_agent(state)
            return {"result": result_state["email_result"]}
        except Exception as e:
            return {"error": str(e)}

    @router.post("/api/email/send")
    async def email_send_fa(body: SendRequest):
        from agents.email_agent import _send_email
        result = _send_email(to=body.to, subject=body.subject, body=body.body,
                             html_body=body.html_body, cc=body.cc, bcc=body.bcc)
        return result

    @router.get("/api/email/inbox")
    async def email_inbox_fa(folder: str = Query("INBOX"), limit: int = Query(10)):
        from agents.email_agent import _fetch_emails
        emails = _fetch_emails(folder=folder, limit=limit)
        return {"folder": folder, "count": len(emails), "emails": emails}

    @router.get("/api/email/modes")
    async def email_modes_fa():
        modes = {
            "Core Ops":      ["compose","reply","forward","send"],
            "AI Writing":    ["rewrite_tone","resize","fix_grammar","improve_clarity","translate","suggest_subject","from_bullets","match_style"],
            "Inbox":         ["read","search","digest"],
            "Analysis":      ["summarize","summarize_thread","extract_actions","extract_entities","analyze","classify"],
            "Smart":         ["smart_reply","auto_reply","follow_up"],
            "Templates":     ["template","mail_merge","drip","ab_test"],
            "Scheduling":    ["schedule","best_time"],
            "Security":      ["security_check","sensitive_data","gdpr"],
            "Integrations":  ["crm_log","meeting","unsubscribe"],
            "Bulk":          ["bulk"],
            "Output":        ["export","signature"],
        }
        return {"modes": modes, "total": sum(len(v) for v in modes.values())}

except ImportError:
    router = None
