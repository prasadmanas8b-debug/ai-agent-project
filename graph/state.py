"""
graph/state.py  --  Shared whiteboard passed between all agents.
"""
from typing import TypedDict, List, Dict, Any

class AgentState(TypedDict):
    task: str
    # Original user input. Set once, never changed.

    research_notes: str
    # Written by Research Agent -- raw web research text.

    final_report: str
    # Written by Writer Agent -- polished markdown report.

    code_result: str
    # Written by Coder Agent -- save confirmation + line count.

    github_result: str
    # Written by GitHub Agent -- result of file/branch operations.

    pdf_result: str
    # Written by PDF Agent -- JSON string with result data.

    email_result: str
    # Written by Email Agent -- JSON string with result data.

    convo_result: str
    # Written by Convo Agent -- latest conversational reply.

    conversation_history: List[Dict[str, str]]
    # Maintained by Convo Agent -- list of {role: str, content: str} dicts.
    # role is "user" or "assistant".

    next: str
    # Written by Supervisor each loop.
    # Values: "research"|"writer"|"coder"|"github"|"pdf"|"email"|"convo"|"FINISH"

    # ── PDF Agent fields ──────────────────────────────────────────────────────

    pdf_mode: str
    # Controls which PDF feature to invoke. Defaults to "auto".
    # Options: read|create|summarize|qa|translate|extract|search|find_replace|
    #   watermark|page_numbers|header_footer|page_ops|split|merge|merge_plan|
    #   extract_images|pdf_to_images|classify|sentiment|ner|compare|autotag|
    #   reformat|md_to_pdf|tables_to_csv|to_markdown|to_html|metadata|set_metadata|
    #   protect|decrypt|redact|signature|ocr|annotate|bookmarks|compress|repair|
    #   linearize|forms|accessibility|batch|rewrite

    pdf_text: str
    # Optional pre-extracted text for the PDF agent. Skips file loading if provided.

    pdf_bytes: bytes
    # Optional: raw bytes of the primary PDF file.

    pdf2_bytes: bytes
    # Optional: raw bytes of a second PDF file (for compare / merge).

    # ── Email Agent fields ────────────────────────────────────────────────────

    email_mode: str
    # Controls which Email feature to invoke. Defaults to "auto".
    # Options: compose|reply|forward|send|rewrite_tone|resize|fix_grammar|
    #   improve_clarity|translate|suggest_subject|from_bullets|match_style|
    #   read|search|digest|summarize|summarize_thread|extract_actions|
    #   extract_entities|analyze|classify|smart_reply|auto_reply|follow_up|
    #   template|mail_merge|drip|ab_test|schedule|best_time|security_check|
    #   sensitive_data|gdpr|crm_log|meeting|unsubscribe|bulk|export|signature

    email_context: Dict[str, Any]
    # Optional context dict for the email agent. Supported keys:
    #   to:             str  — recipient email address
    #   cc:             str  — CC address
    #   bcc:            str  — BCC address
    #   tone:           str  — formal|casual|friendly|assertive|empathetic|concise
    #   original_email: str  — original email text (for reply/analyze/rewrite)
    #   message_id:     str  — Message-ID header (for threading)
    #   auto_send:      bool — if True, sends immediately via SMTP after composing
    #   thread:         list — list of {from, body, date} dicts for thread summary
    #   recipients:     list — list of email addresses (for mail merge)
    #   template:       str  — template text with {{placeholders}}
    #   subject:        str  — email subject (for export / set operations)
    #   attachment:     dict — {filename, data (base64), content_type}
