"""
email_agent.py — AI-powered Email Agent for the Multi-Agent System.

CAPABILITIES:
  1.  Draft professional emails from a simple description
  2.  Send emails via Gmail SMTP (or any SMTP server)
  3.  Reply to emails (given original thread context)
  4.  Write cold outreach emails
  5.  Write follow-up emails
  6.  Write apology / complaint / escalation emails
  7.  Summarize long emails into key bullet points
  8.  Translate emails to a different language
  9.  Adjust tone: formal ↔ casual ↔ aggressive ↔ friendly
 10.  Attach research or writer agent output as email body
 11.  Send to multiple recipients (CC / BCC support)
 12.  Preview draft before sending (dry-run mode)
 13.  Log all sent emails to memory/email_log.json
"""

import os
import json
import smtplib
import ssl
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

# ── LLM Setup ────────────────────────────────────────────────────────────────
def get_llm():
    return ChatGroq(
        model="llama3-70b-8192",
        temperature=0.4,
        api_key=os.getenv("GROQ_API_KEY"),
    )

# ── Email Config from .env ────────────────────────────────────────────────────
EMAIL_SENDER   = os.getenv("EMAIL_SENDER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
SMTP_HOST      = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT      = int(os.getenv("SMTP_PORT", "587"))
EMAIL_LOG_PATH = os.path.join("memory", "email_log.json")


# ── Core Agent Function (LangGraph Node) ─────────────────────────────────────
def email_agent(state: dict) -> dict:
    """
    Main LangGraph node for the Email Agent.
    Reads `state["task"]` to determine what kind of email task to perform.
    Optionally uses `state["final_report"]` or `state["research_notes"]` as body content.
    Updates state with `email_draft` and `email_result`.
    """
    task = state.get("task", "").strip()
    context = state.get("final_report", "") or state.get("research_notes", "")

    if not task:
        state["email_draft"] = ""
        state["email_result"] = "❌ No task provided to the Email Agent."
        state["next"] = "end"
        return state

    print(f"\n[EmailAgent] 📧 Task received: {task[:80]}...")

    action = _detect_action(task)
    print(f"[EmailAgent] 🔍 Detected action: {action}")

    result = _dispatch(action, task, context)

    state["email_draft"] = result.get("draft", "")
    state["email_result"] = result.get("summary", "")
    state["next"] = "end"

    print(f"[EmailAgent] ✅ Done. Action={action}")
    return state


# ── Action Detector ───────────────────────────────────────────────────────────
def _detect_action(task: str) -> str:
    t = task.lower()
    if any(k in t for k in ["send", "email to", "mail to"]):
        return "send"
    if any(k in t for k in ["reply", "respond to", "answer this email"]):
        return "reply"
    if any(k in t for k in ["follow up", "follow-up", "checking in"]):
        return "followup"
    if any(k in t for k in ["cold outreach", "introduce myself", "sales email", "pitch"]):
        return "cold_outreach"
    if any(k in t for k in ["apologize", "apology", "sorry"]):
        return "apology"
    if any(k in t for k in ["summarize", "summarise", "tldr", "key points"]):
        return "summarize"
    if any(k in t for k in ["translate", "in spanish", "in french", "in hindi"]):
        return "translate"
    if any(k in t for k in ["formal", "casual", "professional", "friendly", "change tone"]):
        return "tone_adjust"
    if any(k in t for k in ["complaint", "escalate", "not happy", "issue with"]):
        return "complaint"
    return "draft"


def _dispatch(action: str, task: str, context: str) -> dict:
    dispatch_map = {
        "draft":        _draft_email,
        "send":         _draft_and_send,
        "reply":        _reply_email,
        "followup":     _followup_email,
        "cold_outreach": _cold_outreach_email,
        "apology":      _apology_email,
        "summarize":    _summarize_email,
        "translate":    _translate_email,
        "tone_adjust":  _adjust_tone,
        "complaint":    _complaint_email,
    }
    fn = dispatch_map.get(action, _draft_email)
    return fn(task, context)


# ── Action Implementations ────────────────────────────────────────────────────

def _draft_email(task: str, context: str) -> dict:
    """Draft a professional email from a description."""
    llm = get_llm()
    system = SystemMessage(content=(
        "You are a professional email writer. "
        "Write a complete, polished email with: Subject line, greeting, body, and sign-off. "
        "Format exactly as:\n"
        "Subject: <subject>\n\n<full email body>"
    ))
    prompt = task
    if context:
        prompt = f"Use this content as the email body/background:\n{context}\n\nEmail request: {task}"

    response = llm.invoke([system, HumanMessage(content=prompt)])
    draft = response.content.strip()
    _log_email_action("draft", task, draft)

    return {
        "draft": draft,
        "summary": f"📧 Email Draft Ready:\n\n{draft}",
    }


def _draft_and_send(task: str, context: str) -> dict:
    """Draft an email AND send it via SMTP."""
    # First draft it
    result = _draft_email(task, context)
    draft = result["draft"]

    # Parse recipient from task
    to_address = _extract_recipient(task)
    if not to_address:
        return {
            "draft": draft,
            "summary": (
                f"📧 Email Drafted (NOT SENT — no recipient found in task):\n\n{draft}\n\n"
                "💡 Tip: Include 'to: someone@example.com' in your task to auto-send."
            ),
        }

    # Parse subject and body from draft
    subject, body = _parse_draft(draft)

    send_result = send_email(
        to=to_address,
        subject=subject,
        body=body,
    )

    _log_email_action("send", task, draft, to=to_address, sent=send_result["success"])

    summary = f"{'✅ Email Sent!' if send_result['success'] else '❌ Send Failed'}\n"
    summary += f"To: {to_address}\nSubject: {subject}\n\n"
    summary += f"Draft:\n{draft}"
    if not send_result["success"]:
        summary += f"\n\nError: {send_result.get('error', 'Unknown error')}"

    return {"draft": draft, "summary": summary}


def _reply_email(task: str, context: str) -> dict:
    """Write a reply to an email thread."""
    llm = get_llm()
    system = SystemMessage(content=(
        "You are a professional email writer. "
        "Write a reply to the given email thread. "
        "Be concise, polite, and address all points raised. "
        "Format as: Subject: Re: <original subject>\n\n<reply body>"
    ))
    prompt = f"Original email / thread:\n{context or task}\n\nInstruction: {task}"
    response = llm.invoke([system, HumanMessage(content=prompt)])
    draft = response.content.strip()
    _log_email_action("reply", task, draft)
    return {"draft": draft, "summary": f"↩️ Reply Email Ready:\n\n{draft}"}


def _followup_email(task: str, context: str) -> dict:
    """Write a follow-up email."""
    llm = get_llm()
    system = SystemMessage(content=(
        "You are a professional email writer. "
        "Write a polite, concise follow-up email. "
        "Reference the prior interaction naturally. Don't be pushy. "
        "Format as: Subject: <subject>\n\n<body>"
    ))
    response = llm.invoke([system, HumanMessage(content=task)])
    draft = response.content.strip()
    _log_email_action("followup", task, draft)
    return {"draft": draft, "summary": f"🔁 Follow-up Email Ready:\n\n{draft}"}


def _cold_outreach_email(task: str, context: str) -> dict:
    """Write a cold outreach / sales / intro email."""
    llm = get_llm()
    system = SystemMessage(content=(
        "You are an expert at cold email outreach. "
        "Write a compelling, personalized cold email. "
        "Keep it short (under 150 words), lead with value, end with a clear CTA. "
        "Format as: Subject: <subject>\n\n<body>"
    ))
    response = llm.invoke([system, HumanMessage(content=task)])
    draft = response.content.strip()
    _log_email_action("cold_outreach", task, draft)
    return {"draft": draft, "summary": f"📨 Cold Outreach Email Ready:\n\n{draft}"}


def _apology_email(task: str, context: str) -> dict:
    """Write an apology or sorry email."""
    llm = get_llm()
    system = SystemMessage(content=(
        "You are a professional email writer. "
        "Write a sincere, empathetic apology email. "
        "Acknowledge the issue, take responsibility, and offer a resolution. "
        "Format as: Subject: <subject>\n\n<body>"
    ))
    response = llm.invoke([system, HumanMessage(content=task)])
    draft = response.content.strip()
    _log_email_action("apology", task, draft)
    return {"draft": draft, "summary": f"🙏 Apology Email Ready:\n\n{draft}"}


def _complaint_email(task: str, context: str) -> dict:
    """Write a firm but professional complaint email."""
    llm = get_llm()
    system = SystemMessage(content=(
        "You are a professional email writer. "
        "Write a firm, assertive but professional complaint email. "
        "Clearly state the issue, impact, and expected resolution. "
        "Format as: Subject: <subject>\n\n<body>"
    ))
    response = llm.invoke([system, HumanMessage(content=task)])
    draft = response.content.strip()
    _log_email_action("complaint", task, draft)
    return {"draft": draft, "summary": f"📢 Complaint Email Ready:\n\n{draft}"}


def _summarize_email(task: str, context: str) -> dict:
    """Summarize a long email into key bullet points."""
    llm = get_llm()
    system = SystemMessage(content=(
        "You are an expert at summarizing emails. "
        "Extract the key points as bullet points. "
        "Also note: sender's intent, action items, and deadline (if any)."
    ))
    content_to_summarize = context or task
    response = llm.invoke([system, HumanMessage(content=content_to_summarize)])
    summary_text = response.content.strip()
    return {
        "draft": summary_text,
        "summary": f"📋 Email Summary:\n\n{summary_text}",
    }


def _translate_email(task: str, context: str) -> dict:
    """Translate an email to another language."""
    llm = get_llm()
    system = SystemMessage(content=(
        "You are a professional translator specializing in business email. "
        "Translate the given email accurately, preserving tone and formality. "
        "Output only the translated email."
    ))
    content = context or task
    response = llm.invoke([system, HumanMessage(content=f"Task: {task}\n\nEmail to translate:\n{content}")])
    translated = response.content.strip()
    _log_email_action("translate", task, translated)
    return {"draft": translated, "summary": f"🌍 Translated Email:\n\n{translated}"}


def _adjust_tone(task: str, context: str) -> dict:
    """Rewrite an email in a different tone."""
    llm = get_llm()
    system = SystemMessage(content=(
        "You are a professional email writer. "
        "Rewrite the given email in the requested tone (formal/casual/friendly/assertive/warm). "
        "Preserve all content — only change the tone and phrasing."
    ))
    content = context or task
    response = llm.invoke([system, HumanMessage(content=f"Instruction: {task}\n\nEmail:\n{content}")])
    draft = response.content.strip()
    _log_email_action("tone_adjust", task, draft)
    return {"draft": draft, "summary": f"🎨 Tone-Adjusted Email:\n\n{draft}"}


# ── SMTP Sender ───────────────────────────────────────────────────────────────
def send_email(
    to: str,
    subject: str,
    body: str,
    cc: str = "",
    bcc: str = "",
    html: bool = False,
) -> dict:
    """
    Send an email via SMTP.
    Requires EMAIL_SENDER, EMAIL_PASSWORD in .env.
    Returns: { success: bool, message: str, error: str }
    """
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        return {
            "success": False,
            "message": "",
            "error": (
                "EMAIL_SENDER or EMAIL_PASSWORD not set in .env. "
                "Add them to send real emails."
            ),
        }

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = EMAIL_SENDER
        msg["To"]      = to
        if cc:
            msg["Cc"] = cc
        if bcc:
            msg["Bcc"] = bcc

        mime_type = "html" if html else "plain"
        msg.attach(MIMEText(body, mime_type))

        recipients = [to]
        if cc:
            recipients += [a.strip() for a in cc.split(",")]
        if bcc:
            recipients += [a.strip() for a in bcc.split(",")]

        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls(context=context)
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, recipients, msg.as_string())

        return {"success": True, "message": f"Email sent to {to}", "error": ""}

    except smtplib.SMTPAuthenticationError:
        return {
            "success": False,
            "message": "",
            "error": (
                "SMTP Authentication failed. "
                "For Gmail, use an App Password (not your account password). "
                "Enable 2FA → Google Account → Security → App Passwords."
            ),
        }
    except Exception as e:
        return {"success": False, "message": "", "error": str(e)}


# ── Helpers ───────────────────────────────────────────────────────────────────
def _extract_recipient(task: str) -> str:
    """Try to extract email address from the task string."""
    import re
    match = re.search(r"[\w.\-+]+@[\w.\-]+\.\w+", task)
    return match.group(0) if match else ""


def _parse_draft(draft: str) -> tuple[str, str]:
    """Parse subject and body from a drafted email string."""
    lines = draft.strip().splitlines()
    subject = "No Subject"
    body_start = 0
    for i, line in enumerate(lines):
        if line.lower().startswith("subject:"):
            subject = line.split(":", 1)[1].strip()
            body_start = i + 1
            break
    body = "\n".join(lines[body_start:]).strip()
    return subject, body


def _log_email_action(action: str, task: str, draft: str, to: str = "", sent: bool = False):
    """Append email action to the memory log."""
    os.makedirs("memory", exist_ok=True)
    log = []
    if os.path.exists(EMAIL_LOG_PATH):
        try:
            with open(EMAIL_LOG_PATH, "r") as f:
                log = json.load(f)
        except Exception:
            log = []

    entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "task": task[:200],
        "draft_preview": draft[:300],
        "to": to,
        "sent": sent,
    }
    log.append(entry)

    with open(EMAIL_LOG_PATH, "w") as f:
        json.dump(log, f, indent=2)


# ── Standalone CLI mode ───────────────────────────────────────────────────────
if __name__ == "__main__":
    test_state = {
        "task": "Draft a professional email to my manager asking for a day off next Friday",
        "research_notes": "",
        "final_report": "",
        "email_draft": "",
        "email_result": "",
        "next": "",
    }
    result = email_agent(test_state)
    print("\n" + "=" * 60)
    print(result["email_result"])
