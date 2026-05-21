"""
agents/pdf_agent.py
PDF Agent — reads a PDF (from local path or URL) and extracts / summarizes its content.
Supports:
  - Local file: "summarize PDF at /path/to/file.pdf"
  - URL:        "extract text from https://example.com/report.pdf"
  - Uploaded:   looks in uploads/ folder by default

Dependencies (add to requirements.txt):
  pymupdf          -> pip install pymupdf
  requests         -> already in requirements.txt
"""
import os
import re
import io
import tempfile
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

_llm = None

def _get_llm():
    global _llm
    if _llm is None:
        _llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            api_key=os.getenv("GROQ_API_KEY"),
        )
    return _llm

# ─────────────────────────────────────────────────────────────────────────────
#  PDF TEXT EXTRACTION
# ─────────────────────────────────────────────────────────────────────────────

def _extract_text_from_bytes(pdf_bytes: bytes) -> str:
    """Extract all text from PDF bytes using PyMuPDF (fitz)."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pages_text = []
        for page_num, page in enumerate(doc, start=1):
            text = page.get_text("text").strip()
            if text:
                pages_text.append(f"[Page {page_num}]\n{text}")
        doc.close()
        return "\n\n".join(pages_text) if pages_text else "No extractable text found in PDF."
    except ImportError:
        return "ERROR: PyMuPDF (fitz) not installed. Run: pip install pymupdf"
    except Exception as e:
        return f"ERROR extracting PDF text: {e}"


def _load_pdf_from_url(url: str) -> bytes:
    """Download PDF from a URL and return bytes."""
    import urllib.request
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read()
    except Exception as e:
        raise RuntimeError(f"Failed to download PDF from URL '{url}': {e}")


def _load_pdf_from_path(path: str) -> bytes:
    """Load PDF from local filesystem and return bytes."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"PDF file not found at path: '{path}'")
    with open(path, "rb") as f:
        return f.read()


def _detect_pdf_source(task: str) -> tuple[str, str]:
    """
    Parse the task string to find a PDF path or URL.
    Returns (source_type, source_value) where source_type is 'url' or 'path'.
    """
    # Check for URL
    url_match = re.search(r'https?://\S+\.pdf', task, re.IGNORECASE)
    if url_match:
        return "url", url_match.group(0).rstrip(".,)")

    # Check for absolute or relative file path
    path_match = re.search(r'([/~][\w/._-]+\.pdf|[\w._-]+\.pdf)', task, re.IGNORECASE)
    if path_match:
        raw_path = path_match.group(0)
        # Try uploads/ folder as default location
        if not os.path.isabs(raw_path):
            candidates = [
                raw_path,
                os.path.join("uploads", raw_path),
                os.path.join("git_agent_output", raw_path),
            ]
            for c in candidates:
                if os.path.exists(c):
                    return "path", c
            return "path", raw_path  # return as-is; error handled later
        return "path", raw_path

    return "none", ""


# ─────────────────────────────────────────────────────────────────────────────
#  LLM SUMMARIZER
# ─────────────────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """
You are an expert document analyst. You are given extracted text from a PDF document.

Your task: produce a clean, structured summary of the document.

STRUCTURE:
## Document Overview
A 2-3 sentence description of what this document is about.

## Key Points
Bullet points of the most important information, facts, or arguments.

## Details
Any important sections, findings, data, tables, or quotes worth noting.

## Bottom Line
One tight paragraph summarizing the most critical takeaway.

RULES:
- Be factual. Use only what is in the document.
- Do NOT invent information.
- If the document has numbers, dates, or names, include them.
- Keep it clear and professional.
"""

def _summarize_text(raw_text: str, task: str) -> str:
    """Use LLM to produce a structured summary of the extracted text."""
    # Limit to first 12000 chars to stay within token limits
    truncated = raw_text[:12000]
    if len(raw_text) > 12000:
        truncated += "\n\n[Note: Document was truncated to fit context window. Full text has more content.]"

    messages = [
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=(
            f"Task: {task}\n\n"
            f"Extracted PDF Text:\n{truncated}\n\n"
            f"Write the structured summary now."
        )),
    ]
    response = _get_llm().invoke(messages)
    return response.content


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def run_pdf_agent(state: dict) -> dict:
    """
    PDF Agent entry point for the LangGraph pipeline.

    Reads a PDF from a URL or local path mentioned in state['task'],
    extracts text, and summarizes it via LLM.

    Updates state['pdf_result'] with the summary.
    """
    task = state.get("task", "")
    print(f"\n📄 PDF Agent -- task: {task[:120]}")

    # 1. Detect source
    source_type, source_value = _detect_pdf_source(task)

    if source_type == "none":
        msg = (
            "⚠️ PDF Agent: No PDF path or URL found in the task.\n"
            "Please specify a PDF file path or URL in your request.\n"
            "Examples:\n"
            "  - 'summarize PDF at uploads/report.pdf'\n"
            "  - 'extract text from https://example.com/doc.pdf'"
        )
        print(msg)
        return {**state, "pdf_result": msg}

    # 2. Load PDF bytes
    try:
        if source_type == "url":
            print(f"📄 PDF Agent -- downloading from URL: {source_value}")
            pdf_bytes = _load_pdf_from_url(source_value)
        else:
            print(f"📄 PDF Agent -- reading local file: {source_value}")
            pdf_bytes = _load_pdf_from_path(source_value)
    except (RuntimeError, FileNotFoundError) as e:
        msg = f"❌ PDF Agent: {e}"
        print(msg)
        return {**state, "pdf_result": msg}

    # 3. Extract text
    print("📄 PDF Agent -- extracting text...")
    raw_text = _extract_text_from_bytes(pdf_bytes)

    if raw_text.startswith("ERROR"):
        return {**state, "pdf_result": raw_text}

    char_count = len(raw_text)
    print(f"📄 PDF Agent -- extracted {char_count} characters from PDF")

    # 4. Summarize
    print("📄 PDF Agent -- summarizing with LLM...")
    summary = _summarize_text(raw_text, task)

    result = (
        f"📄 **PDF Processed:** `{source_value}`\n"
        f"📏 **Extracted:** {char_count:,} characters\n\n"
        f"{summary}"
    )
    print(f"📄 PDF Agent -- done. Summary length: {len(summary)} chars")
    return {**state, "pdf_result": result}


# ─────────────────────────────────────────────────────────────────────────────
#  STANDALONE TEST
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        pdf_path_or_url = sys.argv[1]
    else:
        pdf_path_or_url = input("Enter PDF path or URL: ").strip()

    test_state = {
        "task":           f"summarize PDF at {pdf_path_or_url}",
        "research_notes": "",
        "final_report":   "",
        "code_result":    "",
        "github_result":  "",
        "pdf_result":     "",
        "next":           "",
    }
    result = run_pdf_agent(test_state)
    print("\n" + "=" * 60)
    print(result["pdf_result"])
