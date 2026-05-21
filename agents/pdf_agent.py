"""
agents/pdf_agent.py
PDF Agent — 8-feature AI toolkit powered by Groq (same stack as all other agents).

Features (set via state["pdf_mode"] or auto-inferred from task):
  create      Generate PDF content plan + ReportLab Python code
  summarize   Extract title, summary, key points, sentiment, topics
  qa          Answer questions about a PDF
  translate   Translate PDF content to a target language
  extract     Pull tables, lists, key-values, named entities
  reformat    Restructure layout + new ReportLab code
  merge_plan  Multi-document merge strategy + pypdf code
  metadata    Detect + suggest metadata + SEO score + setter code

Stack: langchain_groq · ChatGroq · meta-llama/llama-4-scout-17b-16e-instruct
       (same model / pattern as writer_agent.py and dynamic_research_agent.py)

Dependencies:
  pymupdf    pip install pymupdf
  requests   pip install requests   (already in requirements)
"""
import os
import re
import urllib.request
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import AgentState

load_dotenv()

# ── Lazy LLM init — same pattern as every other agent ────────────────────────
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


# ── System prompts — one per feature ─────────────────────────────────────────
SYSTEM_PROMPTS = {
    "create": """You are a PDF content generator.
Return ONLY valid JSON (no markdown fences):
{
  "plan":         "full structured content plan with title and all sections",
  "python_code":  "complete runnable ReportLab code that saves to output.pdf — must include headers, footers, page numbers, styled headings, body paragraphs, bullet points, tables if relevant, proper margins",
  "preview_text": "first 3 paragraphs of the document content"
}""",

    "summarize": """You are a PDF summarization expert.
Return ONLY valid JSON (no markdown fences):
{
  "title":         "inferred document title",
  "summary":       "2-3 paragraph executive summary",
  "key_points":    ["up to 8 bullet points"],
  "topics":        ["topic1", "topic2"],
  "word_count":    integer,
  "reading_time":  "X min read",
  "sentiment":     "positive|neutral|negative",
  "document_type": "report|article|legal|technical|other"
}""",

    "qa": """You are a PDF Q&A assistant.
Answer thoroughly and accurately, citing specific sections when possible.
If the answer is not found in the provided text, say so clearly.
Return plain text — no JSON.""",

    "translate": """You are a PDF translation expert.
Return ONLY valid JSON (no markdown fences):
{
  "target_language":    "...",
  "translated_content": "full translated text preserving original structure",
  "notes":              "translation notes or cultural adaptations made"
}""",

    "extract": """You are a data extraction specialist for PDFs.
Return ONLY valid JSON (no markdown fences):
{
  "tables":     [{"title": "...", "headers": [...], "rows": [[...]]}],
  "key_values": {"key": "value"},
  "lists":      [{"title": "...", "items": [...]}],
  "entities":   {"dates": [...], "names": [...], "numbers": [...], "emails": [...]}
}""",

    "reformat": """You are a PDF reformatting assistant.
Return ONLY valid JSON (no markdown fences):
{
  "original_analysis":  "brief analysis of the original document structure",
  "suggested_structure": "description of the improved structure",
  "python_code":        "complete ReportLab code for the reformatted version",
  "changes_made":       ["change 1", "change 2"]
}""",

    "merge_plan": """You are a PDF merge strategist.
Return ONLY valid JSON (no markdown fences):
{
  "merge_strategy":  "description of how to merge the documents",
  "document_order":  ["doc 1 purpose", "doc 2 purpose"],
  "python_code":     "complete pypdf Python code to perform the merge",
  "recommendations": ["tip 1", "tip 2"]
}""",

    "metadata": """You are a PDF metadata analyst.
Return ONLY valid JSON (no markdown fences):
{
  "detected_metadata":  {"title": "", "author": "", "subject": "", "keywords": [], "created": "", "modified": ""},
  "suggested_metadata": {"title": "", "author": "", "subject": "", "keywords": []},
  "python_code":        "complete pypdf code to set the suggested metadata",
  "seo_score":          "1-10 score with a one-sentence explanation"
}""",
}

# ── Mode inference (backwards-compat when pdf_mode not provided) ──────────────
_MODE_KEYWORDS = {
    "create":     ["create", "generate", "make", "build", "write a pdf", "new pdf"],
    "summarize":  ["summarize", "summary", "overview", "brief", "key points"],
    "qa":         ["question", "ask", "what is", "who is", "how does", "answer"],
    "translate":  ["translate", "translation", "to spanish", "to french", "to hindi", "to language"],
    "extract":    ["extract", "table", "tables", "data", "entities", "key-value"],
    "reformat":   ["reformat", "restructure", "restyle", "layout", "redesign"],
    "merge_plan": ["merge", "combine", "join", "concatenate", "multiple pdf"],
    "metadata":   ["metadata", "author", "title", "keywords", "seo"],
}

def _infer_mode(task: str) -> str:
    tl = task.lower()
    for mode, keywords in _MODE_KEYWORDS.items():
        if any(kw in tl for kw in keywords):
            return mode
    return "summarize"


# ── PDF loading utilities ─────────────────────────────────────────────────────
def _extract_text_from_bytes(pdf_bytes: bytes) -> str:
    try:
        import fitz  # PyMuPDF
        doc   = fitz.open(stream=pdf_bytes, filetype="pdf")
        pages = []
        for i, page in enumerate(doc, 1):
            text = page.get_text("text").strip()
            if text:
                pages.append(f"[Page {i}]\n{text}")
        doc.close()
        return "\n\n".join(pages) or "No extractable text found in PDF."
    except ImportError:
        return "ERROR: PyMuPDF not installed. Run: pip install pymupdf"
    except Exception as e:
        return f"ERROR extracting PDF text: {e}"


def _load_pdf_url(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def _load_pdf_path(path: str) -> bytes:
    if not os.path.exists(path):
        raise FileNotFoundError(f"PDF not found at path: {path!r}")
    with open(path, "rb") as f:
        return f.read()


def _detect_pdf_source(task: str):
    url_m = re.search(r"https?://\S+\.pdf", task, re.IGNORECASE)
    if url_m:
        return "url", url_m.group(0).rstrip(".,)")
    path_m = re.search(r"([/~][\w/._-]+\.pdf|[\w._-]+\.pdf)", task, re.IGNORECASE)
    if path_m:
        raw = path_m.group(0)
        if not os.path.isabs(raw):
            for prefix in ("", "uploads/", "git_agent_output/"):
                if os.path.exists(prefix + raw):
                    return "path", prefix + raw
        return "path", raw
    return "none", ""


# ── User message builder ──────────────────────────────────────────────────────
def _build_user_message(mode: str, task: str, pdf_text: str) -> str:
    p = pdf_text[:12000]
    if len(pdf_text) > 12000:
        p += "\n\n[Document truncated to fit context window.]"
    if mode == "create":     return task
    if mode == "summarize":  return f"Summarize this PDF:\n\n{p}"
    if mode == "qa":         return f"PDF Content:\n{p}\n\nQuestion: {task}"
    if mode == "translate":
        lang = re.search(r"to ([\w ]+)", task, re.IGNORECASE)
        return f"Translate to {lang.group(1).strip() if lang else task}:\n\n{p}"
    if mode == "extract":    return f"Extract all structured data from this PDF:\n\n{p}"
    if mode == "reformat":   return f"Reformat this PDF.\nInstructions: {task}\n\nContent:\n{p}"
    if mode == "merge_plan": return f"Plan this PDF merge: {task}"
    if mode == "metadata":   return f"Analyze metadata.\nContent sample:\n{p[:2000]}\n\nUser notes: {task}"
    return task


# ── Main pipeline entry point ─────────────────────────────────────────────────
def run_pdf_agent(state: AgentState) -> AgentState:
    """
    PDF Agent — entry point for the LangGraph pipeline.

    Reads:  state["task"], state["pdf_mode"] (optional), state["pdf_text"] (optional)
    Writes: state["pdf_result"]
    """
    task     = state.get("task", "")
    mode     = state.get("pdf_mode", "auto").strip().lower()
    pdf_text = state.get("pdf_text", "")

    print(f"\n📄 PDF Agent -- task: {task[:80]}  mode: {mode}")

    # Resolve mode
    if mode in ("auto", "", None):
        mode = _infer_mode(task)
    print(f"📄 PDF Agent -- resolved mode: {mode}")

    # Load PDF if needed and not already provided
    if mode not in ("create", "merge_plan") and not pdf_text:
        src_type, src_val = _detect_pdf_source(task)
        if src_type == "none":
            msg = (
                "⚠️  PDF Agent: No PDF source found.\n"
                "Provide a local path or URL in your task, or pass state[\'pdf_text\'].\n"
                "Examples:\n"
                "  summarize PDF at uploads/report.pdf\n"
                "  extract text from https://example.com/doc.pdf"
            )
            return {**state, "pdf_result": msg}
        try:
            pdf_bytes = _load_pdf_url(src_val) if src_type == "url" else _load_pdf_path(src_val)
            print(f"📄 PDF Agent -- extracting text from {src_type}: {src_val}")
            pdf_text = _extract_text_from_bytes(pdf_bytes)
            if pdf_text.startswith("ERROR"):
                return {**state, "pdf_result": pdf_text}
            print(f"📄 PDF Agent -- extracted {len(pdf_text):,} chars")
        except (RuntimeError, FileNotFoundError) as e:
            return {**state, "pdf_result": f"❌ PDF Agent: {e}"}

    # Call LLM
    user_msg = _build_user_message(mode, task, pdf_text)
    print(f"📄 PDF Agent -- calling Groq (mode={mode})...")
    try:
        resp   = _get_llm().invoke([
            SystemMessage(content=SYSTEM_PROMPTS[mode]),
            HumanMessage(content=user_msg),
        ])
        result = resp.content.strip()
        # Strip accidental markdown fences
        result = re.sub(r"^```(?:json)?\n?", "", result, flags=re.MULTILINE)
        result = re.sub(r"```$", "", result.strip()).strip()
    except Exception as e:
        return {**state, "pdf_result": f"❌ PDF Agent LLM error: {e}"}

    print(f"📄 PDF Agent -- done ({len(result)} chars)")
    return {**state, "pdf_result": result}


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    mode_arg = sys.argv[1] if len(sys.argv) > 1 else "summarize"
    src_arg  = sys.argv[2] if len(sys.argv) > 2 else input("PDF path or URL: ").strip()
    out = run_pdf_agent({
        "task": f"{mode_arg} PDF at {src_arg}", "pdf_mode": mode_arg,
        "pdf_text": "", "research_notes": "", "final_report": "",
        "code_result": "", "github_result": "", "pdf_result": "",
        "convo_result": "", "conversation_history": [], "next": "",
    })
    print("\n" + "="*60)
    print(out["pdf_result"])
