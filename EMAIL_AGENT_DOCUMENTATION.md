# Email Agent — Complete Documentation

Production-grade Email Agent with 38 feature handlers across 11 categories.
AI layer: **Groq (llama-4-scout-17b)** · Transport: **SMTP + IMAP (stdlib)**

---

## 📦 Setup

### 1. Install dependencies
No new pip packages required beyond the existing `requirements.txt`.
The agent uses Python stdlib (`smtplib`, `imaplib`, `email`) for transport.

### 2. Configure .env
```env
# Required for send / read features
EMAIL_ADDRESS=you@gmail.com
EMAIL_PASSWORD=your_app_password        # Gmail: use App Password, not your main password
EMAIL_SMTP_HOST=smtp.gmail.com          # Gmail default
EMAIL_SMTP_PORT=587                     # TLS port
EMAIL_IMAP_HOST=imap.gmail.com          # Gmail default

# Existing (already set)
GROQ_API_KEY=your_groq_key
```

> **Gmail users:** Enable 2FA → generate an App Password at https://myaccount.google.com/apppasswords

> **AI features work without SMTP/IMAP** — compose, rewrite, analyze, summarize, templates, etc. all run 100% via the LLM. Only `read` and `send` need credentials.

---

## 🗂️ Feature Reference — 38 Handlers

### Core Ops
| Mode | Description | Needs Original |
|------|-------------|----------------|
| `compose` | Compose a new email from a prompt. Returns subject, body, HTML body, tone. | No |
| `reply` | Reply to an email. Pass original in `email_context.original_email`. | Yes |
| `forward` | Forward with an intro note. | Yes |
| `send` | Alias for compose with `auto_send: true`. | No |

### AI Writing
| Mode | Description |
|------|-------------|
| `rewrite_tone` | Rewrite for formal / casual / assertive / friendly / empathetic / concise |
| `resize` | Shorten or expand the email |
| `fix_grammar` | Fix all grammar, spelling, and punctuation errors |
| `improve_clarity` | Improve structure, flow, and readability score |
| `translate` | Translate to any language |
| `suggest_subject` | Generate 5 subject line suggestions with open-rate predictions |
| `from_bullets` | Convert bullet points into a full email |
| `match_style` | Rewrite new content to match the recipient's writing style |

### Inbox Management
| Mode | Description |
|------|-------------|
| `read` | Fetch emails from INBOX / Sent / Drafts / Spam (requires IMAP) |
| `search` | Search by sender, subject, keyword, date (IMAP SEARCH) |
| `digest` | AI-powered digest of recent emails — highlights + action items |

### Analysis
| Mode | Description |
|------|-------------|
| `summarize` | Summary + action items + deadlines + priority + sentiment |
| `summarize_thread` | Full thread summary — participants, timeline, open questions |
| `extract_actions` | Extract tasks, deadlines, commitments, follow-ups |
| `extract_entities` | People, orgs, emails, phones, dates, amounts, URLs |
| `analyze` | Sentiment, intent, urgency, tone, emotion detection |
| `classify` | Category (work/personal/finance), type, labels, priority |

### Smart Features
| Mode | Description |
|------|-------------|
| `smart_reply` | 3 one-click reply options (Acknowledge / Decline / Schedule) |
| `auto_reply` | Generate out-of-office / auto-reply message |
| `follow_up` | Write a follow-up email for N days after no reply |

### Templates & Campaigns
| Mode | Description |
|------|-------------|
| `template` | Create reusable template with `{{name}}`, `{{date}}` placeholders |
| `mail_merge` | Personalized bulk email — returns Python code + CSV guide |
| `drip` | Design a 4-step drip campaign sequence with Python code |
| `ab_test` | 3 A/B subject line variants with predicted open rates |

### Scheduling
| Mode | Description |
|------|-------------|
| `schedule` | Parse scheduling request → ISO datetime + Python APScheduler code |
| `best_time` | Predict best day/time to send for maximum open rate |

### Security
| Mode | Description |
|------|-------------|
| `security_check` | Detect phishing, spam, suspicious links — verdict + score |
| `sensitive_data` | Find SSNs, credit cards, phone numbers, IPs via regex |
| `gdpr` | GDPR compliance audit — risks, consent, score, required actions |

### Integrations
| Mode | Description |
|------|-------------|
| `crm_log` | Extract Salesforce/HubSpot CRM fields — contact, deal stage, tags |
| `meeting` | Detect meeting request → calendar event + `.ics` file content |
| `unsubscribe` | Find unsubscribe links + generate opt-out instructions |

### Bulk
| Mode | Description |
|------|-------------|
| `bulk` | Generate Python IMAP code for bulk delete / archive / mark read |

### Output
| Mode | Description |
|------|-------------|
| `export` | Export email as `.eml`, `.txt`, `.html`, or `.csv` |
| `signature` | Generate professional email signature (plain + HTML variants) |

---

## 📡 API Reference

### `POST /api/email`
```json
{
  "task":          "Compose a follow-up email to the investor",
  "email_mode":    "compose",
  "email_context": {
    "to":             "investor@vc.com",
    "cc":             "team@startup.com",
    "tone":           "formal",
    "original_email": "original email text for reply/rewrite ops",
    "message_id":     "<msg-id-for-threading>",
    "auto_send":      false,
    "thread":         [{"from":"...","body":"...","date":"..."}],
    "recipients":     ["r1@x.com", "r2@y.com"],
    "template":       "template text with {{placeholders}}"
  }
}
```

**Response:**
```json
{ "result": "{ ...JSON result... }" }
```

### `POST /api/email/send`
```json
{ "to": "name@email.com", "subject": "...", "body": "...", "html_body": "...", "cc": "", "bcc": "" }
```

### `GET /api/email/inbox`
```
GET /api/email/inbox?folder=INBOX&limit=10
```

### `POST /api/email/upload`
Multipart: `task`, `email_mode`, `file` (attachment).

### `GET /api/email/modes`
Returns all 38 modes organized by category.

---

## 🏗️ Architecture

```
state["task"]           → _infer_mode()  → handler(task, email_context)
state["email_mode"]     ↗                              ↓
state["email_context"]                    state["email_result"]  (JSON string)
```

### Mode inference (auto)
The agent reads the task string and matches against keyword lists per mode.
Examples:
- `"compose a follow-up email"` → `compose`
- `"check this email for phishing"` → `security_check`
- `"translate this email to French"` → `translate`
- `"summarize the thread"` → `summarize_thread`
- `"generate drip campaign"` → `drip`

### Transport layer
- **Send:** `smtplib.SMTP` with TLS (`starttls`) on port 587
- **Read:** `imaplib.IMAP4_SSL` — supports all standard IMAP folders + search
- **Mock mode:** If `EMAIL_ADDRESS` / `EMAIL_PASSWORD` are not set, all send/read operations return mock responses — AI composition still works fully

---

## 🔌 Integration with Pipeline

The Email Agent is wired into the LangGraph pipeline:

```
supervisor → email → supervisor → FINISH
```

**Supervisor routing rules (email-relevant):**
```
task mentions email/inbox/compose email/send email/reply/forward/mail → email
task mentions draft/subject line/phishing/unsubscribe/mail merge/drip → email
```

### Python usage
```python
from agents.email_agent import run_email_agent

state = run_email_agent({
    "task":          "Compose a follow-up email to the investor about Q1 results",
    "email_mode":    "compose",
    "email_context": {"to": "investor@vc.com", "tone": "formal"},
    # ... other required state fields ...
})

import json
result = json.loads(state["email_result"])
print(result["subject"])
print(result["body"])
```

### Auto-send
```python
state = run_email_agent({
    "task":          "Write a meeting confirmation email",
    "email_mode":    "compose",
    "email_context": {
        "to":        "client@company.com",
        "tone":      "formal",
        "auto_send": True,          # ← sends via SMTP immediately
    },
    ...
})
```

---

## 📋 Response Schemas

### `compose` / `reply` / `forward`
```json
{
  "subject":     "Email subject",
  "body":        "Plain text body",
  "body_html":   "<html>...</html>",
  "tone":        "formal",
  "word_count":  120,
  "notes":       "...",
  "send_result": { "sent": true, "to": "...", "timestamp": "..." }
}
```

### `summarize`
```json
{
  "summary":        "Executive summary",
  "action_items":   ["action 1"],
  "deadlines":      ["deadline 1"],
  "key_people":     ["Alice"],
  "sentiment":      "positive",
  "intent":         "request",
  "priority":       "high",
  "requires_reply": true
}
```

### `analyze`
```json
{
  "sentiment":          "positive",
  "sentiment_score":    0.8,
  "intent":             "meeting_request",
  "urgency":            "high",
  "tone":               "formal",
  "emotion":            "confident",
  "key_phrases":        ["phrase 1"],
  "is_spam_likely":     false,
  "is_phishing_likely": false,
  "summary":            "one sentence analysis"
}
```

### `security_check`
```json
{
  "is_spam":           false,
  "is_phishing":       false,
  "spam_score":        0.1,
  "phishing_score":    0.05,
  "red_flags":         [],
  "suspicious_links":  [],
  "sensitive_data":    [],
  "verdict":           "safe",
  "recommendation":    "Safe to open"
}
```

### `drip`
```json
{
  "campaign_name": "SaaS Onboarding",
  "goal": "Activate new users",
  "sequence": [
    { "day": 0,  "subject": "Welcome!", "body": "...", "goal": "First impression" },
    { "day": 3,  "subject": "Quick tip", "body": "...", "goal": "Feature discovery" },
    { "day": 7,  "subject": "Check-in",  "body": "...", "goal": "Engagement" },
    { "day": 14, "subject": "Upgrade",   "body": "...", "goal": "Conversion" }
  ],
  "python_code": "...",
  "kpis": ["open rate", "click rate", "conversion rate"]
}
```

### `read` / `search`
```json
{
  "folder":  "INBOX",
  "count":   10,
  "emails":  [
    {
      "uid":         "123",
      "message_id":  "<msg-id>",
      "subject":     "...",
      "from":        "sender@email.com",
      "to":          "you@email.com",
      "date":        "Mon, 21 May 2026 10:00:00 +0530",
      "body":        "plain text body",
      "attachments": [{"filename":"doc.pdf","content_type":"application/pdf","size":12345}]
    }
  ]
}
```

---

## 🗂️ Files Added / Modified

| File | Status | Description |
|------|--------|-------------|
| `agents/email_agent.py` | ✅ New | 38 feature handlers, SMTP/IMAP transport, LLM AI layer |
| `api/email_endpoint.py` | ✅ New | Flask + FastAPI routes: `/api/email`, `/api/email/send`, `/api/email/inbox`, `/api/email/upload`, `/api/email/modes` |
| `frontend/EmailAgent.jsx` | ✅ New | Full React UI — 11 categories, tone picker, original email paste, smart result panels |
| `graph/state.py` | ✅ Updated | Added `email_result`, `email_mode`, `email_context` fields |
| `graph/pipeline_graph.py` | ✅ Updated | Added `email` node wired into the graph |
| `agents/manager_agent.py` | ✅ Updated | Supervisor now routes email tasks → `email` agent |
| `main.py` | ✅ Updated | Email examples, email_context init, email result output handler |
| `EMAIL_AGENT_DOCUMENTATION.md` | ✅ New | This file |

---

## ⚙️ .env Reference

```env
# Email Agent
EMAIL_ADDRESS=you@gmail.com
EMAIL_PASSWORD=xxxx xxxx xxxx xxxx    # App Password for Gmail
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_IMAP_HOST=imap.gmail.com

# Other providers
# Outlook: smtp.office365.com / imap-mail.outlook.com
# Yahoo:   smtp.mail.yahoo.com  / imap.mail.yahoo.com
# Custom:  your SMTP/IMAP host
```

---

*Stack: LangChain · ChatGroq · meta-llama/llama-4-scout-17b-16e-instruct · smtplib · imaplib · email (stdlib)*
