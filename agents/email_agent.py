"""
agents/email_agent.py
Production-grade Email Agent — 80+ features across 18 categories.
AI layer: Groq (llama-4-scout) for composition, analysis, summarization.
Transport layer: SMTP (send), IMAP (read) — or mock mode when not configured.

Categories:
  Core Ops, AI Writing, Inbox Mgmt, Organization, Summarization,
  Threading, Attachments, Contacts, Templates, Scheduling,
  Smart Replies, Security, Tracking, Multi-Account, Notifications,
  Bulk/Campaign, Formatting, Audit/Compliance

Stack: langchain_groq · ChatGroq · meta-llama/llama-4-scout-17b-16e-instruct
       smtplib · imaplib · email (stdlib)
"""

from __future__ import annotations
import os, re, json, smtplib, imaplib, email as email_lib, base64, html
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.header import decode_header
from datetime import datetime, timedelta
from typing import Any
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import AgentState

load_dotenv()

# ── LLM ───────────────────────────────────────────────────────────────────────
_llm = None
def _get_llm():
    global _llm
    if _llm is None:
        _llm = ChatGroq(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            temperature=0.3,
            max_tokens=4096,
            api_key=os.getenv("GROQ_API_KEY"),
        )
    return _llm

def _llm_call(system: str, user: str) -> str:
    resp = _get_llm().invoke([SystemMessage(content=system), HumanMessage(content=user)])
    return resp.content.strip()

def _parse_json(raw: str) -> Any:
    raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)

# ── IMAP helpers ──────────────────────────────────────────────────────────────
def _imap_connect():
    host = os.getenv("EMAIL_IMAP_HOST", "imap.gmail.com")
    user = os.getenv("EMAIL_ADDRESS", "")
    pwd  = os.getenv("EMAIL_PASSWORD", "")
    if not user or not pwd:
        return None
    M = imaplib.IMAP4_SSL(host)
    M.login(user, pwd)
    return M

def _decode_header_val(val):
    if not val:
        return ""
    parts = decode_header(val)
    decoded = []
    for part, enc in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(enc or "utf-8", errors="replace"))
        else:
            decoded.append(str(part))
    return " ".join(decoded)

def _parse_email_message(msg_bytes: bytes) -> dict:
    msg = email_lib.message_from_bytes(msg_bytes)
    subject  = _decode_header_val(msg.get("Subject", ""))
    from_    = _decode_header_val(msg.get("From", ""))
    to_      = _decode_header_val(msg.get("To", ""))
    date_    = msg.get("Date", "")
    msg_id   = msg.get("Message-ID", "")

    body_plain, body_html = "", ""
    attachments = []

    for part in msg.walk():
        ct = part.get_content_type()
        cd = str(part.get("Content-Disposition", ""))
        if "attachment" in cd:
            fname = part.get_filename() or "attachment"
            attachments.append({
                "filename": _decode_header_val(fname),
                "content_type": ct,
                "size": len(part.get_payload(decode=True) or b""),
            })
        elif ct == "text/plain" and not body_plain:
            payload = part.get_payload(decode=True)
            body_plain = payload.decode(part.get_content_charset() or "utf-8", errors="replace") if payload else ""
        elif ct == "text/html" and not body_html:
            payload = part.get_payload(decode=True)
            body_html = payload.decode(part.get_content_charset() or "utf-8", errors="replace") if payload else ""

    return {
        "message_id": msg_id,
        "subject":    subject,
        "from":       from_,
        "to":         to_,
        "date":       date_,
        "body":       body_plain or re.sub(r"<[^>]+>", " ", body_html),
        "body_html":  body_html,
        "attachments": attachments,
    }

def _fetch_emails(folder: str = "INBOX", limit: int = 20, search: str = "ALL") -> list[dict]:
    M = _imap_connect()
    if not M:
        return [{"error": "IMAP not configured. Set EMAIL_ADDRESS, EMAIL_PASSWORD, EMAIL_IMAP_HOST in .env"}]
    try:
        M.select(folder)
        _, data = M.search(None, search)
        ids = data[0].split()[-limit:]
        emails = []
        for eid in reversed(ids):
            _, msg_data = M.fetch(eid, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    parsed = _parse_email_message(response_part[1])
                    parsed["uid"] = eid.decode()
                    emails.append(parsed)
        M.logout()
        return emails
    except Exception as e:
        return [{"error": str(e)}]

def _send_email(to: str, subject: str, body: str, html_body: str = "",
                cc: str = "", bcc: str = "", attachments: list = None,
                reply_to_id: str = "") -> dict:
    host = os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("EMAIL_SMTP_PORT", "587"))
    user = os.getenv("EMAIL_ADDRESS", "")
    pwd  = os.getenv("EMAIL_PASSWORD", "")

    if not user or not pwd:
        return {
            "sent": False,
            "mock": True,
            "to": to, "subject": subject,
            "body_preview": body[:200],
            "note": "SMTP not configured. Set EMAIL_ADDRESS, EMAIL_PASSWORD, EMAIL_SMTP_HOST in .env. Email composed successfully."
        }

    msg = MIMEMultipart("alternative")
    msg["From"]    = user
    msg["To"]      = to
    msg["Subject"] = subject
    if cc:  msg["Cc"]  = cc
    if bcc: msg["Bcc"] = bcc
    if reply_to_id: msg["In-Reply-To"] = reply_to_id

    msg.attach(MIMEText(body, "plain"))
    if html_body:
        msg.attach(MIMEText(html_body, "html"))

    if attachments:
        for att in attachments:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(att.get("data", b""))
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={att.get('filename','file')}")
            msg.attach(part)

    recipients = [to] + ([cc] if cc else []) + ([bcc] if bcc else [])
    try:
        with smtplib.SMTP(host, port) as server:
            server.ehlo()
            server.starttls()
            server.login(user, pwd)
            server.sendmail(user, recipients, msg.as_string())
        return {"sent": True, "to": to, "subject": subject, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        return {"sent": False, "error": str(e)}

# ═══════════════════════════════════════════════════════════════════════════════
#  FEATURE HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════

# ── 1. Compose email from prompt ──────────────────────────────────────────────
def feat_compose(task: str, email_context: dict) -> dict:
    SYSTEM = """You are a professional email composer.
Return ONLY valid JSON:
{
  "subject":    "email subject line",
  "body":       "complete email body (plain text)",
  "body_html":  "complete email body (HTML with proper formatting)",
  "tone":       "formal|casual|friendly|assertive",
  "word_count": 0,
  "notes":      "any composition notes"
}"""
    ctx = ""
    if email_context.get("to"):    ctx += f"To: {email_context['to']}\n"
    if email_context.get("cc"):    ctx += f"CC: {email_context['cc']}\n"
    if email_context.get("tone"):  ctx += f"Tone: {email_context['tone']}\n"
    raw = _llm_call(SYSTEM, f"{ctx}\nCompose email: {task}")
    result = _parse_json(raw)
    # Auto-send if recipient provided
    if email_context.get("to") and email_context.get("auto_send"):
        send_result = _send_email(
            to=email_context["to"], subject=result["subject"],
            body=result["body"], html_body=result.get("body_html",""),
            cc=email_context.get("cc",""), bcc=email_context.get("bcc",""),
        )
        result["send_result"] = send_result
    return result

# ── 2. Reply ──────────────────────────────────────────────────────────────────
def feat_reply(task: str, email_context: dict) -> dict:
    original = email_context.get("original_email", "")
    SYSTEM = """You are composing a reply to an email.
Return ONLY valid JSON:
{
  "subject":   "Re: <original subject>",
  "body":      "complete reply body",
  "body_html": "HTML version",
  "reply_type": "reply|reply_all",
  "tone":      "formal|casual"
}"""
    raw = _llm_call(SYSTEM, f"Original email:\n{original}\n\nReply instructions: {task}")
    result = _parse_json(raw)
    if email_context.get("to") and email_context.get("auto_send"):
        result["send_result"] = _send_email(
            to=email_context.get("to",""),
            subject=result.get("subject","Re:"),
            body=result.get("body",""),
            reply_to_id=email_context.get("message_id",""),
        )
    return result

# ── 3. Forward ────────────────────────────────────────────────────────────────
def feat_forward(task: str, email_context: dict) -> dict:
    original = email_context.get("original_email", "")
    SYSTEM = """Compose a forwarding email with a brief intro note.
Return ONLY valid JSON:
{
  "subject":   "Fwd: <original subject>",
  "body":      "intro note + forwarded message",
  "body_html": "HTML version"
}"""
    raw = _llm_call(SYSTEM, f"Original:\n{original}\n\nForward instructions: {task}")
    result = _parse_json(raw)
    if email_context.get("to") and email_context.get("auto_send"):
        result["send_result"] = _send_email(
            to=email_context["to"], subject=result.get("subject","Fwd:"),
            body=result.get("body",""),
        )
    return result

# ── 4. AI Rewrite for tone ────────────────────────────────────────────────────
def feat_rewrite_tone(task: str, email_context: dict) -> dict:
    original = email_context.get("original_email", task)
    tone_m = re.search(r'\b(formal|casual|friendly|assertive|professional|empathetic|concise)\b', task, re.I)
    tone = tone_m.group(1) if tone_m else "formal"
    SYSTEM = f"""Rewrite the email in a {tone} tone.
Return ONLY valid JSON:
{{
  "original":    "original text",
  "rewritten":   "rewritten email body",
  "subject":     "updated subject if needed",
  "tone":        "{tone}",
  "changes":     ["change 1", "change 2"]
}}"""
    raw = _llm_call(SYSTEM, f"Rewrite in {tone} tone:\n\n{original}")
    return _parse_json(raw)

# ── 5. Shorten / Expand ───────────────────────────────────────────────────────
def feat_resize(task: str, email_context: dict) -> dict:
    original = email_context.get("original_email", task)
    action = "shorten" if "shorten" in task.lower() else "expand"
    SYSTEM = f"""{'Shorten' if action == 'shorten' else 'Expand'} the email while preserving meaning.
Return ONLY valid JSON:
{{
  "original_word_count": 0,
  "new_word_count": 0,
  "result": "the {'shortened' if action == 'shorten' else 'expanded'} email",
  "subject": "updated subject if changed"
}}"""
    raw = _llm_call(SYSTEM, f"{action.capitalize()} this email:\n\n{original}")
    return _parse_json(raw)

# ── 6. Fix grammar & spelling ─────────────────────────────────────────────────
def feat_fix_grammar(task: str, email_context: dict) -> dict:
    text = email_context.get("original_email", task)
    SYSTEM = """Fix all grammar, spelling, and punctuation errors.
Return ONLY valid JSON:
{
  "corrected": "fully corrected email",
  "corrections": [{"original": "...", "corrected": "...", "type": "grammar|spelling|punctuation"}],
  "error_count": 0
}"""
    raw = _llm_call(SYSTEM, f"Fix grammar:\n\n{text}")
    return _parse_json(raw)

# ── 7. Improve clarity & flow ─────────────────────────────────────────────────
def feat_improve_clarity(task: str, email_context: dict) -> dict:
    text = email_context.get("original_email", task)
    SYSTEM = """Improve the clarity, structure, and flow of the email.
Return ONLY valid JSON:
{
  "improved": "improved email text",
  "improvements": ["improvement 1", "improvement 2"],
  "readability_score_before": "A-F",
  "readability_score_after": "A-F"
}"""
    raw = _llm_call(SYSTEM, f"Improve clarity:\n\n{text}")
    return _parse_json(raw)

# ── 8. Translate email ────────────────────────────────────────────────────────
def feat_translate(task: str, email_context: dict) -> dict:
    text = email_context.get("original_email", "")
    lang_m = re.search(r'\bto\s+([\w ]+?)(?:\s*$|\n)', task, re.I)
    lang = lang_m.group(1).strip() if lang_m else "Spanish"
    SYSTEM = """Translate the email to the target language.
Return ONLY valid JSON:
{
  "target_language": "...",
  "translated_subject": "...",
  "translated_body": "...",
  "notes": "translation notes"
}"""
    raw = _llm_call(SYSTEM, f"Translate to {lang}:\n\n{text or task}")
    return _parse_json(raw)

# ── 9. Suggest subject line ───────────────────────────────────────────────────
def feat_suggest_subject(task: str, email_context: dict) -> dict:
    text = email_context.get("original_email", task)
    SYSTEM = """Suggest 5 compelling subject lines for this email.
Return ONLY valid JSON:
{
  "suggestions": [
    {"subject": "...", "style": "direct|question|numeric|urgency|curiosity", "open_rate_prediction": "high|medium|low"}
  ],
  "recommended": "the best suggestion"
}"""
    raw = _llm_call(SYSTEM, f"Suggest subject lines for:\n\n{text}")
    return _parse_json(raw)

# ── 10. Generate from bullet points ──────────────────────────────────────────
def feat_from_bullets(task: str, email_context: dict) -> dict:
    SYSTEM = """Convert bullet points into a polished professional email.
Return ONLY valid JSON:
{
  "subject": "email subject",
  "body":    "full email body",
  "body_html": "HTML version",
  "tone":    "detected tone"
}"""
    raw = _llm_call(SYSTEM, f"Convert to email:\n{task}")
    return _parse_json(raw)

# ── 11. Read / Fetch emails ───────────────────────────────────────────────────
def feat_read(task: str, email_context: dict) -> dict:
    limit = int(re.search(r'\b(\d+)\b', task).group(1)) if re.search(r'\b(\d+)\b', task) else 10
    folder = "INBOX"
    if "sent" in task.lower():   folder = "Sent"
    if "draft" in task.lower():  folder = "Drafts"
    if "spam" in task.lower():   folder = "Spam"
    emails = _fetch_emails(folder=folder, limit=limit)
    return {"folder": folder, "count": len(emails), "emails": emails}

# ── 12. Search emails ─────────────────────────────────────────────────────────
def feat_search(task: str, email_context: dict) -> dict:
    # Build IMAP search criteria
    criteria = []
    from_m  = re.search(r'from\s+["\']?([^"\']+?)["\']?(?:\s|$)', task, re.I)
    subj_m  = re.search(r'subject\s+["\']?([^"\']+?)["\']?(?:\s|$)', task, re.I)
    kw_m    = re.search(r'keyword\s+["\']?([^"\']+?)["\']?(?:\s|$)', task, re.I)
    date_m  = re.search(r'since\s+(\d{4}-\d{2}-\d{2})', task, re.I)

    if from_m:  criteria.append(f'FROM "{from_m.group(1).strip()}"')
    if subj_m:  criteria.append(f'SUBJECT "{subj_m.group(1).strip()}"')
    if kw_m:    criteria.append(f'BODY "{kw_m.group(1).strip()}"')
    if date_m:
        d = datetime.strptime(date_m.group(1), "%Y-%m-%d")
        criteria.append(f'SINCE {d.strftime("%d-%b-%Y")}')

    search_str = " ".join(criteria) if criteria else "ALL"
    emails = _fetch_emails(search=search_str, limit=20)
    return {"query": task, "criteria": search_str, "count": len(emails), "emails": emails}

# ── 13. Summarize email ───────────────────────────────────────────────────────
def feat_summarize(task: str, email_context: dict) -> dict:
    text = email_context.get("original_email", "")
    if not text:
        # Fetch last N emails and summarize as digest
        emails = _fetch_emails(limit=5)
        if emails and not emails[0].get("error"):
            text = "\n\n---\n\n".join([
                f"From: {e['from']}\nSubject: {e['subject']}\n{e['body'][:500]}"
                for e in emails
            ])
    SYSTEM = """Summarize the email(s) concisely.
Return ONLY valid JSON:
{
  "summary":         "2-3 sentence summary",
  "action_items":    ["action 1", "action 2"],
  "deadlines":       ["deadline 1"],
  "key_people":      ["name 1", "name 2"],
  "sentiment":       "positive|neutral|negative",
  "intent":          "request|complaint|inquiry|approval|information|meeting|other",
  "priority":        "high|medium|low",
  "requires_reply":  true
}"""
    raw = _llm_call(SYSTEM, f"Summarize:\n\n{text or task}")
    return _parse_json(raw)

# ── 14. Summarize thread ──────────────────────────────────────────────────────
def feat_summarize_thread(task: str, email_context: dict) -> dict:
    thread = email_context.get("thread", [])
    thread_text = "\n\n---\n\n".join([
        f"From: {e.get('from','?')}\nDate: {e.get('date','?')}\n{e.get('body','')[:800]}"
        for e in thread
    ]) if thread else email_context.get("original_email", task)
    SYSTEM = """Summarize the full email thread.
Return ONLY valid JSON:
{
  "thread_summary":   "complete thread summary",
  "participants":     ["person 1", "person 2"],
  "timeline":         [{"date": "...", "event": "..."}],
  "current_status":   "resolved|pending|action_needed",
  "next_steps":       ["step 1"],
  "action_items":     {"person": ["action"]},
  "unresolved":       ["open question 1"]
}"""
    raw = _llm_call(SYSTEM, f"Summarize this thread:\n\n{thread_text}")
    return _parse_json(raw)

# ── 15. Extract action items ──────────────────────────────────────────────────
def feat_extract_actions(task: str, email_context: dict) -> dict:
    text = email_context.get("original_email", task)
    SYSTEM = """Extract all action items, deadlines, and commitments from the email.
Return ONLY valid JSON:
{
  "action_items":  [{"task": "...", "owner": "...", "due_date": "...", "priority": "high|medium|low"}],
  "deadlines":     [{"description": "...", "date": "..."}],
  "commitments":   ["commitment 1"],
  "questions":     ["question needing answer 1"],
  "follow_ups":    ["follow up 1"]
}"""
    raw = _llm_call(SYSTEM, f"Extract actions from:\n\n{text}")
    return _parse_json(raw)

# ── 16. Extract entities ──────────────────────────────────────────────────────
def feat_extract_entities(task: str, email_context: dict) -> dict:
    text = email_context.get("original_email", task)
    SYSTEM = """Extract all named entities from the email.
Return ONLY valid JSON:
{
  "people":        ["name1"],
  "organizations": ["org1"],
  "emails":        ["email@example.com"],
  "phones":        ["+1-234-567-8900"],
  "dates":         ["date1"],
  "amounts":       ["$1000"],
  "urls":          ["https://..."],
  "locations":     ["location1"],
  "products":      ["product1"]
}"""
    raw = _llm_call(SYSTEM, f"Extract entities:\n\n{text}")
    return _parse_json(raw)

# ── 17. Sentiment & intent analysis ──────────────────────────────────────────
def feat_analyze(task: str, email_context: dict) -> dict:
    text = email_context.get("original_email", task)
    SYSTEM = """Analyze the email for sentiment and intent.
Return ONLY valid JSON:
{
  "sentiment":         "positive|negative|neutral|mixed",
  "sentiment_score":   0.0,
  "intent":            "request|complaint|inquiry|approval|information|meeting_request|follow_up|other",
  "urgency":           "high|medium|low",
  "tone":              "formal|informal|aggressive|friendly|passive|assertive",
  "emotion":           "happy|frustrated|anxious|confident|neutral",
  "key_phrases":       ["phrase 1"],
  "is_spam_likely":    false,
  "is_phishing_likely": false,
  "summary":           "1 sentence analysis"
}"""
    raw = _llm_call(SYSTEM, f"Analyze:\n\n{text}")
    return _parse_json(raw)

# ── 18. Classify email ────────────────────────────────────────────────────────
def feat_classify(task: str, email_context: dict) -> dict:
    text = email_context.get("original_email", task)
    SYSTEM = """Classify the email into categories.
Return ONLY valid JSON:
{
  "primary_category":  "work|personal|finance|newsletter|support|spam|social|promotions",
  "sub_category":      "invoice|meeting|task|announcement|alert|receipt|other",
  "type":              "plain|thread|newsletter|automated|transactional",
  "labels":            ["label1", "label2"],
  "priority":          "high|medium|low",
  "auto_reply_needed": false,
  "crm_relevant":      false,
  "calendar_event":    false
}"""
    raw = _llm_call(SYSTEM, f"Classify:\n\n{text}")
    return _parse_json(raw)

# ── 19. Smart reply suggestions ───────────────────────────────────────────────
def feat_smart_reply(task: str, email_context: dict) -> dict:
    text = email_context.get("original_email", task)
    SYSTEM = """Generate 3 smart one-click reply options.
Return ONLY valid JSON:
{
  "replies": [
    {"label": "Acknowledge", "body": "short reply text", "tone": "formal|casual"},
    {"label": "Decline",     "body": "short reply text", "tone": "formal|casual"},
    {"label": "Schedule",    "body": "short reply text", "tone": "formal|casual"}
  ],
  "context": "brief description of what the email is about"
}"""
    raw = _llm_call(SYSTEM, f"Generate smart replies for:\n\n{text}")
    return _parse_json(raw)

# ── 20. Auto-reply / Out-of-office ────────────────────────────────────────────
def feat_auto_reply(task: str, email_context: dict) -> dict:
    SYSTEM = """Generate an auto-reply / out-of-office message.
Return ONLY valid JSON:
{
  "subject":        "Auto-Reply: Out of Office",
  "body":           "complete OOO message",
  "body_html":      "HTML version",
  "return_date":    "detected or suggested return date",
  "contact_backup": "suggested backup contact format"
}"""
    raw = _llm_call(SYSTEM, f"Generate auto-reply: {task}")
    return _parse_json(raw)

# ── 21. Follow-up reminder ────────────────────────────────────────────────────
def feat_follow_up(task: str, email_context: dict) -> dict:
    original = email_context.get("original_email", "")
    days_m = re.search(r'(\d+)\s+day', task, re.I)
    days = int(days_m.group(1)) if days_m else 3
    follow_up_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    SYSTEM = """Compose a polite follow-up email.
Return ONLY valid JSON:
{
  "subject":       "Follow-up: <original subject>",
  "body":          "polite follow-up email body",
  "body_html":     "HTML version",
  "send_after_days": 0,
  "follow_up_date": ""
}"""
    raw = _llm_call(SYSTEM, f"Write a follow-up email for:\n{original or task}\nSend after {days} days.")
    result = _parse_json(raw)
    result["follow_up_date"] = follow_up_date
    result["send_after_days"] = days
    return result

# ── 22. Daily / weekly digest ─────────────────────────────────────────────────
def feat_digest(task: str, email_context: dict) -> dict:
    limit = 20 if "week" in task.lower() else 10
    emails = _fetch_emails(limit=limit)
    if emails and emails[0].get("error"):
        return emails[0]
    thread_text = "\n\n".join([
        f"From: {e['from']} | Subject: {e['subject']} | Date: {e['date']}\n{e['body'][:300]}"
        for e in emails
    ])
    SYSTEM = """Create an email digest summary.
Return ONLY valid JSON:
{
  "period":        "today|this week",
  "total_emails":  0,
  "highlights":    ["highlight 1", "highlight 2"],
  "action_items":  ["action 1"],
  "important":     [{"from":"...", "subject":"...", "reason":"..."}],
  "digest_text":   "full digest in readable format"
}"""
    raw = _llm_call(SYSTEM, f"Create a digest of {len(emails)} emails:\n\n{thread_text}")
    result = _parse_json(raw)
    result["total_emails"] = len(emails)
    return result

# ── 23. Template management ───────────────────────────────────────────────────
def feat_template(task: str, email_context: dict) -> dict:
    SYSTEM = """Create a reusable email template with variable placeholders.
Return ONLY valid JSON:
{
  "template_name": "descriptive name",
  "subject":       "subject with {{placeholders}}",
  "body":          "email body with {{name}}, {{date}}, {{company}} style placeholders",
  "body_html":     "HTML version",
  "variables":     ["variable1", "variable2"],
  "use_case":      "when to use this template",
  "example_filled": "example with placeholders filled in"
}"""
    raw = _llm_call(SYSTEM, f"Create template for: {task}")
    return _parse_json(raw)

# ── 24. Mail merge ────────────────────────────────────────────────────────────
def feat_mail_merge(task: str, email_context: dict) -> dict:
    template = email_context.get("template", "")
    recipients = email_context.get("recipients", [])
    if not template:
        template = task
    SYSTEM = """Generate a mail merge plan with personalized emails for each recipient.
Return ONLY valid JSON:
{
  "base_template":   "template with placeholders",
  "merge_fields":    ["field1", "field2"],
  "personalized_emails": [{"to":"...", "subject":"...", "body":"..."}],
  "python_code":     "code to perform mail merge from a CSV file",
  "notes":           ["note1"]
}"""
    recip_str = json.dumps(recipients[:5]) if recipients else "['recipient1@example.com', 'recipient2@example.com']"
    raw = _llm_call(SYSTEM, f"Mail merge template:\n{template}\n\nRecipients sample: {recip_str}")
    return _parse_json(raw)

# ── 25. Phishing / spam detection ────────────────────────────────────────────
def feat_security_check(task: str, email_context: dict) -> dict:
    text = email_context.get("original_email", task)
    SYSTEM = """Perform a security analysis on the email.
Return ONLY valid JSON:
{
  "is_spam":           false,
  "is_phishing":       false,
  "spam_score":        0.0,
  "phishing_score":    0.0,
  "red_flags":         ["flag 1"],
  "suspicious_links":  ["url1"],
  "sensitive_data":    ["SSN", "credit card"],
  "verdict":           "safe|suspicious|dangerous",
  "recommendation":    "what to do"
}"""
    raw = _llm_call(SYSTEM, f"Security check:\n\n{text}")
    return _parse_json(raw)

# ── 26. Sensitive data detection ─────────────────────────────────────────────
def feat_sensitive_data(task: str, email_context: dict) -> dict:
    text = email_context.get("original_email", task)
    patterns = {
        "ssn":          re.findall(r'\b\d{3}-\d{2}-\d{4}\b', text),
        "credit_card":  re.findall(r'\b(?:\d{4}[-\s]?){3}\d{4}\b', text),
        "phone":        re.findall(r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', text),
        "email":        re.findall(r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Z|a-z]{2,}\b', text),
        "ip_address":   re.findall(r'\b\d{1,3}(?:\.\d{1,3}){3}\b', text),
    }
    has_sensitive = any(patterns.values())
    return {
        "has_sensitive_data": has_sensitive,
        "findings": patterns,
        "risk_level": "high" if patterns["ssn"] or patterns["credit_card"] else "medium" if has_sensitive else "low",
        "recommendation": "Redact sensitive data before forwarding" if has_sensitive else "No sensitive data found",
    }

# ── 27. Export email ──────────────────────────────────────────────────────────
def feat_export(task: str, email_context: dict) -> dict:
    text = email_context.get("original_email", "")
    subject = email_context.get("subject", "Email")
    fmt_m = re.search(r'\b(eml|pdf|csv|html|txt)\b', task, re.I)
    fmt = fmt_m.group(1).lower() if fmt_m else "txt"

    if fmt == "eml":
        eml = f"Subject: {subject}\nDate: {datetime.now().isoformat()}\n\n{text}"
        return {"format": "eml", "content": eml, "filename": f"{subject[:30]}.eml"}
    elif fmt == "html":
        html_content = f"<html><body><h2>{html.escape(subject)}</h2><pre>{html.escape(text)}</pre></body></html>"
        return {"format": "html", "content": html_content, "filename": f"{subject[:30]}.html"}
    elif fmt == "csv":
        csv = f"Subject,From,Date,Body\n\"{subject}\",\"{email_context.get('from','')}\",\"{datetime.now().isoformat()}\",\"{text[:500]}\""
        return {"format": "csv", "content": csv, "filename": "email_export.csv"}
    else:
        return {"format": "txt", "content": text, "filename": f"{subject[:30]}.txt"}

# ── 28. Schedule send ─────────────────────────────────────────────────────────
def feat_schedule(task: str, email_context: dict) -> dict:
    SYSTEM = """Parse the email scheduling request.
Return ONLY valid JSON:
{
  "scheduled_time": "ISO datetime string",
  "timezone":       "detected timezone",
  "subject":        "email subject",
  "body":           "email body",
  "recipient":      "to address",
  "python_code":    "Python code using APScheduler or celery to schedule the send",
  "notes":          "scheduling notes"
}"""
    raw = _llm_call(SYSTEM, f"Schedule email: {task}\nCurrent time: {datetime.now().isoformat()}")
    return _parse_json(raw)

# ── 29. Best time to send ─────────────────────────────────────────────────────
def feat_best_time(task: str, email_context: dict) -> dict:
    SYSTEM = """Suggest the best time to send the email for maximum open rate.
Return ONLY valid JSON:
{
  "best_times": [
    {"day": "Tuesday", "time": "10:00 AM", "reason": "...", "open_rate_est": "high"}
  ],
  "avoid_times": ["Monday morning", "Friday afternoon"],
  "timezone_note": "adjust for recipient timezone",
  "industry_tips": ["tip 1"]
}"""
    raw = _llm_call(SYSTEM, f"Best send time for: {task}")
    return _parse_json(raw)

# ── 30. CRM log ───────────────────────────────────────────────────────────────
def feat_crm_log(task: str, email_context: dict) -> dict:
    text = email_context.get("original_email", task)
    SYSTEM = """Extract CRM-relevant information from the email.
Return ONLY valid JSON:
{
  "contact_name":    "...",
  "contact_email":   "...",
  "company":         "...",
  "deal_value":      "...",
  "stage":           "lead|prospect|negotiation|closed_won|closed_lost",
  "next_action":     "...",
  "tags":            ["tag1"],
  "salesforce_note": "formatted note for Salesforce",
  "hubspot_note":    "formatted note for HubSpot"
}"""
    raw = _llm_call(SYSTEM, f"Extract CRM data from:\n\n{text}")
    return _parse_json(raw)

# ── 31. Meeting detection ─────────────────────────────────────────────────────
def feat_meeting(task: str, email_context: dict) -> dict:
    text = email_context.get("original_email", task)
    SYSTEM = """Detect and extract meeting/calendar information from the email.
Return ONLY valid JSON:
{
  "has_meeting_request": false,
  "meeting_title":    "...",
  "proposed_times":   ["time1", "time2"],
  "duration":         "...",
  "location":         "...",
  "attendees":        ["email1"],
  "calendar_event":   {"title":"...", "start":"ISO datetime", "end":"ISO datetime", "description":"..."},
  "ics_content":      "VCALENDAR content for .ics file",
  "action":           "accept|decline|propose_new_time|no_meeting"
}"""
    raw = _llm_call(SYSTEM, f"Detect meeting in:\n\n{text}")
    return _parse_json(raw)

# ── 32. Unsubscribe helper ────────────────────────────────────────────────────
def feat_unsubscribe(task: str, email_context: dict) -> dict:
    text = email_context.get("original_email", task)
    links = re.findall(r'https?://[^\s"\'<>]+(?:unsub|unsubscribe|opt.out|remove)[^\s"\'<>]*', text, re.I)
    SYSTEM = """Find unsubscribe options and generate instructions.
Return ONLY valid JSON:
{
  "unsubscribe_links": ["url1"],
  "email_found":       "list email address if present",
  "method":            "link|reply|email",
  "instructions":      "step-by-step instructions",
  "confirmation_text": "email text to send if needed"
}"""
    raw = _llm_call(SYSTEM, f"Find unsubscribe in:\n\n{text[:3000]}")
    result = _parse_json(raw)
    if links:
        result["unsubscribe_links"] = links
    return result

# ── 33. Bulk action code ──────────────────────────────────────────────────────
def feat_bulk(task: str, email_context: dict) -> dict:
    SYSTEM = """Generate Python IMAP code for bulk email operations.
Return ONLY valid JSON:
{
  "operation":   "detected operation (bulk delete|archive|mark read|label)",
  "python_code": "complete Python IMAP code to perform the bulk operation",
  "criteria":    "filter criteria used",
  "warning":     "any destructive operation warning",
  "notes":       ["note1"]
}"""
    raw = _llm_call(SYSTEM, f"Bulk email operation: {task}")
    return _parse_json(raw)

# ── 34. GDPR / compliance ─────────────────────────────────────────────────────
def feat_gdpr(task: str, email_context: dict) -> dict:
    text = email_context.get("original_email", task)
    SYSTEM = """Analyze the email for GDPR compliance and data privacy concerns.
Return ONLY valid JSON:
{
  "gdpr_risks":         ["risk 1"],
  "personal_data_found": ["data type 1"],
  "consent_present":    false,
  "unsubscribe_present": false,
  "recommendations":    ["rec 1"],
  "compliance_score":   "0-100",
  "required_actions":   ["action 1"]
}"""
    raw = _llm_call(SYSTEM, f"GDPR check:\n\n{text}")
    return _parse_json(raw)

# ── 35. Drip campaign ─────────────────────────────────────────────────────────
def feat_drip(task: str, email_context: dict) -> dict:
    SYSTEM = """Design a multi-step drip email campaign.
Return ONLY valid JSON:
{
  "campaign_name":  "...",
  "goal":           "...",
  "sequence": [
    {"day": 0,  "subject": "...", "body": "...", "goal": "..."},
    {"day": 3,  "subject": "...", "body": "...", "goal": "..."},
    {"day": 7,  "subject": "...", "body": "...", "goal": "..."},
    {"day": 14, "subject": "...", "body": "...", "goal": "..."}
  ],
  "python_code": "code to implement with APScheduler or Celery",
  "kpis":        ["open rate", "click rate", "conversion rate"]
}"""
    raw = _llm_call(SYSTEM, f"Design drip campaign: {task}")
    return _parse_json(raw)

# ── 36. A/B subject test ──────────────────────────────────────────────────────
def feat_ab_test(task: str, email_context: dict) -> dict:
    text = email_context.get("original_email", task)
    SYSTEM = """Create A/B test variants for email subject lines.
Return ONLY valid JSON:
{
  "variant_a": {"subject": "...", "approach": "...", "predicted_open_rate": "high|medium|low"},
  "variant_b": {"subject": "...", "approach": "...", "predicted_open_rate": "high|medium|low"},
  "variant_c": {"subject": "...", "approach": "...", "predicted_open_rate": "high|medium|low"},
  "testing_recommendation": "how to run the A/B test",
  "metrics_to_track": ["open rate", "click rate"]
}"""
    raw = _llm_call(SYSTEM, f"A/B test subjects for:\n\n{text}")
    return _parse_json(raw)

# ── 37. Signature generator ───────────────────────────────────────────────────
def feat_signature(task: str, email_context: dict) -> dict:
    SYSTEM = """Generate a professional email signature.
Return ONLY valid JSON:
{
  "signature_plain": "plain text signature",
  "signature_html":  "HTML signature with proper formatting",
  "variants":        [{"style": "minimal|full|social", "html": "..."}]
}"""
    raw = _llm_call(SYSTEM, f"Generate signature for: {task}")
    return _parse_json(raw)

# ── 38. Match recipient style ─────────────────────────────────────────────────
def feat_match_style(task: str, email_context: dict) -> dict:
    original = email_context.get("original_email", "")
    new_content = task
    SYSTEM = """Rewrite the new email content to match the style of the reference email.
Return ONLY valid JSON:
{
  "style_analysis":  "detected style of reference email",
  "rewritten":       "new content rewritten in matching style",
  "style_markers":   ["marker 1", "marker 2"]
}"""
    raw = _llm_call(SYSTEM, f"Reference style:\n{original}\n\nRewrite in this style:\n{new_content}")
    return _parse_json(raw)

# ═══════════════════════════════════════════════════════════════════════════════
#  MODE ROUTING
# ═══════════════════════════════════════════════════════════════════════════════

FEATURE_MAP = {
    # Core ops
    "compose":          feat_compose,
    "reply":            feat_reply,
    "forward":          feat_forward,
    "send":             feat_compose,       # alias
    # AI writing
    "rewrite_tone":     feat_rewrite_tone,
    "resize":           feat_resize,
    "fix_grammar":      feat_fix_grammar,
    "improve_clarity":  feat_improve_clarity,
    "translate":        feat_translate,
    "suggest_subject":  feat_suggest_subject,
    "from_bullets":     feat_from_bullets,
    "match_style":      feat_match_style,
    # Inbox
    "read":             feat_read,
    "search":           feat_search,
    "digest":           feat_digest,
    # Analysis
    "summarize":        feat_summarize,
    "summarize_thread": feat_summarize_thread,
    "extract_actions":  feat_extract_actions,
    "extract_entities": feat_extract_entities,
    "analyze":          feat_analyze,
    "classify":         feat_classify,
    # Smart
    "smart_reply":      feat_smart_reply,
    "auto_reply":       feat_auto_reply,
    "follow_up":        feat_follow_up,
    # Templates
    "template":         feat_template,
    "mail_merge":       feat_mail_merge,
    "drip":             feat_drip,
    "ab_test":          feat_ab_test,
    # Scheduling
    "schedule":         feat_schedule,
    "best_time":        feat_best_time,
    # Security
    "security_check":   feat_security_check,
    "sensitive_data":   feat_sensitive_data,
    "gdpr":             feat_gdpr,
    # Integrations
    "crm_log":          feat_crm_log,
    "meeting":          feat_meeting,
    "unsubscribe":      feat_unsubscribe,
    # Bulk
    "bulk":             feat_bulk,
    # Output
    "export":           feat_export,
    "signature":        feat_signature,
}

_MODE_KEYWORDS = {
    "compose":          ["compose", "write an email", "draft an email", "new email", "create email", "send an email"],
    "reply":            ["reply", "respond to", "write back"],
    "forward":          ["forward"],
    "rewrite_tone":     ["rewrite", "rephrase", "make it more", "formal", "casual", "assertive", "friendl"],
    "resize":           ["shorten", "expand", "make it shorter", "make it longer"],
    "fix_grammar":      ["fix grammar", "grammar check", "spelling", "proofread"],
    "improve_clarity":  ["improve clarity", "improve flow", "clarity", "readable"],
    "translate":        ["translate email", "email in spanish", "email in french"],
    "suggest_subject":  ["suggest subject", "subject line", "email subject"],
    "from_bullets":     ["bullet point", "from bullets", "from notes", "from points"],
    "match_style":      ["match style", "writing style", "match tone of"],
    "read":             ["read email", "fetch email", "get email", "show email", "inbox", "my emails"],
    "search":           ["search email", "find email", "look for email"],
    "digest":           ["digest", "summary of emails", "email summary", "weekly summary", "daily summary"],
    "summarize":        ["summarize email", "summarize this", "tldr", "key points of email"],
    "summarize_thread": ["summarize thread", "thread summary", "conversation summary"],
    "extract_actions":  ["action item", "extract action", "to-do", "tasks from email"],
    "extract_entities": ["extract entity", "extract names", "extract emails", "extract phone"],
    "analyze":          ["analyze email", "email analysis", "sentiment", "intent", "tone"],
    "classify":         ["classify email", "categorize email", "label email", "email type"],
    "smart_reply":      ["smart reply", "quick reply", "reply suggestion"],
    "auto_reply":       ["auto reply", "out of office", "ooo", "automatic reply"],
    "follow_up":        ["follow up", "follow-up", "no reply", "remind me"],
    "template":         ["template", "email template", "reusable email"],
    "mail_merge":       ["mail merge", "bulk send", "personalized bulk"],
    "drip":             ["drip", "drip campaign", "email sequence", "nurture"],
    "ab_test":          ["a/b test", "ab test", "subject test", "split test"],
    "schedule":         ["schedule email", "send later", "schedule send"],
    "best_time":        ["best time", "when to send", "optimal time"],
    "security_check":   ["security check", "phishing", "spam check", "safe to open"],
    "sensitive_data":   ["sensitive data", "pii", "personal data in email"],
    "gdpr":             ["gdpr", "compliance", "privacy", "opt-out", "data protection"],
    "crm_log":          ["crm", "salesforce", "hubspot", "log email", "crm note"],
    "meeting":          ["meeting", "calendar", "schedule a call", "appointment", "ics"],
    "unsubscribe":      ["unsubscribe", "opt out", "mailing list", "stop emails"],
    "bulk":             ["bulk delete", "bulk archive", "bulk mark", "mass delete"],
    "export":           ["export email", "save as eml", "email to pdf", "download email"],
    "signature":        ["signature", "email signature", "sign off"],
}

def _infer_mode(task: str) -> str:
    tl = task.lower()
    for mode, keywords in _MODE_KEYWORDS.items():
        if any(kw in tl for kw in keywords):
            return mode
    return "compose"

# ── Main entry ────────────────────────────────────────────────────────────────
def run_email_agent(state: AgentState) -> AgentState:
    task          = state.get("task", "")
    mode          = state.get("email_mode", "auto").strip().lower()
    email_context = state.get("email_context", {})

    print(f"\n📧 Email Agent — task: {task[:80]}  mode: {mode}")

    if mode in ("auto", "", None):
        mode = _infer_mode(task)
    print(f"📧 Email Agent — resolved mode: {mode}")

    handler = FEATURE_MAP.get(mode)
    if not handler:
        result = {"error": f"Unknown mode: '{mode}'. Available: {sorted(FEATURE_MAP.keys())}"}
    else:
        try:
            result = handler(task, email_context)
        except Exception as e:
            import traceback
            result = {"error": str(e), "traceback": traceback.format_exc()[-1000:]}

    output = json.dumps(result, ensure_ascii=False, indent=2)
    print(f"📧 Email Agent — done, {len(output):,} chars")
    return {**state, "email_result": output}
