"""
agents/pdf_agent.py
PDF Agent — full 8-feature AI toolkit for the LangGraph pipeline.

Features routed via state["pdf_mode"]:
  create      — Generate PDF content + ReportLab Python code from a prompt
  summarize   — Extract key insights, sentiment, topics from a PDF
  qa          — Answer questions about a PDF
  translate   — Translate PDF content to a target language
  extract     — Pull tables, lists, entities, key-values from a PDF
  reformat    — Restructure / restyle a PDF with new Python code
  merge_plan  — Plan a multi-document PDF merge with pypdf code
  metadata    — Detect + suggest PDF metadata, generate setter code

If state["pdf_mode"] is absent or "auto", the agent infers the mode from
the task string (legacy behaviour — fully backwards-compatible).

Dependencies:
  pymupdf    pip install pymupdf
  requests   pip install requests
"""
import os
import re
import json
import urllib.request
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

_llm = None

def _get_llm(temperature: float = 0.3):
    """Lazy-init the LLM. Temperature is configurable per feature."""
    global _llm
    if _llm is None:
        _llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=temperature,
            api_key=os.getenv("GROQ_API_KEY"),
        )
    return _llm


# ─────────────────────────────────────────────────────────────────
#  SYSTEM PROMPTS  (one per feature)
# ─────────────────────────────────────────────────────────────────
SYSTEM_PROMPTS = {
    "create": """You are a PDF content generator. The user will describe what PDF they want.
Respond with JSON (no markdown fences):
{
  "plan":         "full structured content plan with title and sections",
  "python_code":  "complete runnable ReportLab code that saves to output.pdf",
  "preview_text": "first 3 paragraphs of the document content"
}
The python_code must include: headers, footers, page numbers, styled headings,
body paragraphs, bullet points, tables if needed, and proper margins.
Return ONLY the JSON.""",

    "summarize": """You are a PDF summarization expert.
Return JSON (no markdown fences):
{
  "title":         "inferred document title",
  "summary":       "2-3 paragraph executive summary",
  "key_points":    ["up to 8 bullet points"],
  "topics":        ["topic1", "topic2"],
  "word_count":    integer,
  "reading_time":  "X min read",
  "sentiment":     "positive|neutral|negative",
  "document_type": "report|article|legal|technical|etc"
}
Return ONLY valid JSON.""",

    "qa": """You are a PDF Q&A assistant. Answer thoroughly, citing specific sections.
If the answer is not in the text, say so clearly.""",

    "translate": """You are a PDF translation expert.
Return JSON (no markdown fences):
{
  "target_language":    "...",
  "translated_content": "full translated text preserving structure",
  "notes":              "translation notes or cultural adaptations"
}
Return ONLY valid JSON.""",

    "extract": """You are a data extraction specialist for PDFs.
Return JSON (no markdown fences):
{
  "tables":     [{"title":"...","headers":[...],"rows":[[...]]}],
  "key_values": {"key": "value"},
  "lists":      [{"title":"...","items":[...]}],
  "entities":   {"dates":[...],"names":[...],"numbers":[...],"emails":[...]}
}
Return ONLY valid JSON.""",

    "reformat": """You are a PDF reformatting assistant.
Return JSON (no markdown fences):
{
  "original_analysis":  "brief analysis of original structure",
  "suggested_structure":"description of improved structure",
  "python_code":        "complete ReportLab code for reformatted version",
  "changes_made":       ["change 1","change 2"]
}
Return ONLY valid JSON.""",

    "merge_plan": """You are a PDF merge strategist.
Return JSON (no markdown fences):
{
  "merge_strategy":  "description of how to merge",
  "document_order":  ["doc 1 purpose","doc 2 purpose"],
  "python_code":     "complete pypdf Python code to merge the PDFs",
  "recommendations": ["tip 1","tip 2"]
}
Return ONLY valid JSON.""",

    "metadata": """You are a PDF metadata analyst.
Return JSON (no markdown fences):
{
  "detected_metadata":  {"title":"...","author":"...","subject":"...","keywords":[...],"created":"...","modified":"..."},
  "suggested_metadata": {"title":"...","author":"...","subject":"...","keywords":[...]},
  "python_code":        "complete pypdf code to set the suggested metadata",
  "seo_score":          "1-10 score with one-sentence explanation"
}
Return ONLY valid JSON.""",
}

# ─────────────────────────────────────────────────────────────────
#  PDF LOADING UTILITIES
# ─────────────────────────────────────────────────────────────────
def _extract_text_from_bytes(pdf_bytes: bytes) -> str:
    try:
        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pages = []
        for i, page in enumerate(doc, 1):
            text = page.get_text("text").strip()
            if text:
                pages.append(f"[Page {i}]\n{text}")
        doc.close()
        return "\n\n".join(pages) or "No extractable text found in PDF."
    except ImportError:
        return "ERROR: PyMuPDF (fitz) not installed. Run: pip install pymupdf"
    except Exception as e:
        return f"ERROR extracting PDF text: {e}"


def _load_pdf_url(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def _load_pdf_path(path: str) -> bytes:
    if not os.path.exists(path):
        raise FileNotFoundError(f"PDF not found: {path!r}")
    with open(path, "rb") as f:
        return f.read()


def _detect_pdf_source(task: str) -> tuple:
    url_m = re.search(r"https?://\S+\.pdf", task, re.IGNORECASE)
    if url_m:
        return "url", url_m.group(0).rstrip(".,)")
    path_m = re.search(r"([/~][\w/._-]+\.pdf|[\w._-]+\.pdf)", task, re.IGNORECASE)
    if path_m:
        raw = path_m.group(0)
        if not os.path.isabs(raw):
            for prefix in ("", "uploads/", "git_agent_output/"):
                candidate = prefix + raw
                if os.path.exists(candidate):
                    return "path", candidate
        return "path", raw
    return "none", ""


# ─────────────────────────────────────────────────────────────────
#  MODE INFERENCE  (for backwards-compat when pdf_mode not set)
# ─────────────────────────────────────────────────────────────────
_MODE_KEYWORDS = {
    "summarize":  ["summarize","summary","overview","brief","key points"],
    "qa":         ["question","ask","what is","who is","how does","answer","q&a"],
    "translate":  ["translate","translation","in spanish","in french","in hindi","to language"],
    "extract":    ["extract","table","tables","data","entities","key-value","structured"],
    "reformat":   ["reformat","restructure","restyle","layout","redesign"],
    "merge_plan": ["merge","combine","join","concatenate","multiple pdf"],
    "metadata":   ["metadata","author","title","keywords","seo"],
    "create":     ["create","generate","make","build","write a pdf","new pdf"],
}

def _infer_mode(task: str) -> str:
    tl = task.lower()
    for mode, keywords in _MODE_KEYWORDS.items():
        if any(kw in tl for kw in keywords):
            return mode
    return "summarize"  # sensible default


# ─────────────────────────────────────────────────────────────────
#  PER-FEATURE USER MESSAGE BUILDERS
# ─────────────────────────────────────────────────────────────────
def _build_user_message(mode: str, task: str, pdf_text: str) -> str:
    t = task
    p = pdf_text[:12000] if pdf_text else ""
    if len(pdf_text) > 12000:
        p += "\n\n[Document truncated to fit context window.]"

    if mode == "create":
        return t
    if mode == "summarize":
        return f"Summarize this PDF:\n\n{p}"
    if mode == "qa":
        return f"PDF Content:\n{p}\n\nQuestion: {t}"
    if mode == "translate":
        lang = re.search(r"to ([\w ]+)", t, re.IGNORECASE)
        lang_str = lang.group(1).strip() if lang else t
        return f"Translate the following PDF content to {lang_str}:\n\n{p}"
    if mode == "extract":
        return f"Extract all structured data from this PDF:\n\n{p}"
    if mode == "reformat":
        return f"Reformat this PDF per these instructions: {t}\n\nOriginal content:\n{p}"
    if mode == "merge_plan":
        return f"Help me plan merging PDFs. Details: {t}"
    if mode == "metadata":
        return f"Analyze metadata for this PDF:\n\nContent sample:\n{p[:2000]}\n\nUser notes: {t}"
    return t


# ─────────────────────────────────────────────────────────────────
#  MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────
def run_pdf_agent(state: dict) -> dict:
    """
    PDF Agent entry point for the LangGraph pipeline.

    State keys read:
      state["task"]        — user instruction
      state["pdf_mode"]    — optional: create|summarize|qa|translate|extract|
                              reformat|merge_plan|metadata  (auto-inferred if absent)
      state["pdf_text"]    — optional: pre-extracted PDF text (e.g. from frontend)

    State key written:
      state["pdf_result"]  — JSON string or plain text result
    """
    task     = state.get("task", "")
    mode     = state.get("pdf_mode", "auto").strip().lower()
    pdf_text = state.get("pdf_text", "")

    print(f"\n📄 PDF Agent -- task: {task[:100]}  mode: {mode}")

    # ── Resolve mode ─────────────────────────────────────────────
    if mode in ("auto", "", None):
        mode = _infer_mode(task)
    print(f"📄 PDF Agent -- resolved mode: {mode}")

    # ── Load PDF if mode needs it and no pre-extracted text ──────
    if mode not in ("create", "merge_plan") and not pdf_text:
        source_type, source_value = _detect_pdf_source(task)
        if source_type == "none":
            msg = (
                "⚠️ PDF Agent: No PDF source found.\n"
                "Provide a path or URL, or set state['pdf_text'] with extracted text.\n"
                "Example tasks:\n"
                "  summarize PDF at uploads/report.pdf\n"
                "  extract text from https://example.com/doc.pdf"
            )
            print(msg)
            return {**state, "pdf_result": msg}
        try:
            if source_type == "url":
                print(f"📄 PDF Agent -- downloading: {source_value}")
                pdf_bytes = _load_pdf_url(source_value)
            else:
                print(f"📄 PDF Agent -- reading: {source_value}")
                pdf_bytes = _load_pdf_path(source_value)
            print("📄 PDF Agent -- extracting text...")
            pdf_text = _extract_text_from_bytes(pdf_bytes)
            if pdf_text.startswith("ERROR"):
                return {**state, "pdf_result": pdf_text}
            print(f"📄 PDF Agent -- extracted {len(pdf_text):,} chars")
        except (RuntimeError, FileNotFoundError) as e:
            return {**state, "pdf_result": f"❌ PDF Agent: {e}"}

    # ── Build prompt & call LLM ───────────────────────────────────
    system_prompt = SYSTEM_PROMPTS.get(mode, SYSTEM_PROMPTS["summarize"])
    user_msg      = _build_user_message(mode, task, pdf_text)
    temp          = 0.7 if mode == "create" else 0.3

    print(f"📄 PDF Agent -- calling LLM (mode={mode}, temp={temp})...")
    try:
        llm      = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=temp,
            api_key=os.getenv("GROQ_API_KEY"),
        )
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_msg),
        ])
        result_text = response.content.strip()
        # Strip accidental markdown fences
        result_text = re.sub(r"^```(?:json)?\n?", "", result_text, flags=re.MULTILINE)
        result_text = re.sub(r"```$", "", result_text.strip()).strip()
    except Exception as e:
        return {**state, "pdf_result": f"❌ PDF Agent LLM error: {e}"}

    print(f"📄 PDF Agent -- done ({len(result_text)} chars)")
    return {**state, "pdf_result": result_text}


# ─────────────────────────────────────────────────────────────────
#  STANDALONE TEST
# ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    mode_arg = sys.argv[1] if len(sys.argv) > 1 else "summarize"
    src_arg  = sys.argv[2] if len(sys.argv) > 2 else input("PDF path or URL: ").strip()

    test_state = {
        "task":           f"{mode_arg} PDF at {src_arg}",
        "pdf_mode":       mode_arg,
        "pdf_text":       "",
        "research_notes": "",
        "final_report":   "",
        "code_result":    "",
        "github_result":  "",
        "pdf_result":     "",
        "convo_result":   "",
        "conversation_history": [],
        "next":           "",
    }
    out = run_pdf_agent(test_state)
    print("\n" + "=" * 60)
    print(out["pdf_result"])
