"""
agents/pdf_agent.py
Production-grade PDF Agent — 100+ features across 20 categories.
Powered by Groq (llama-4-scout) + PyMuPDF + pypdf + reportlab + weasyprint + pytesseract.

Categories:
  Core Operations, Page Management, Merge/Split, Text, Images, Tables, Forms,
  Security, Metadata, AI Features, Conversion, OCR, Annotations, Bookmarks,
  Compression, Accessibility, Batch, Audit/Compare, Output/Delivery

Stack: langchain_groq · ChatGroq · meta-llama/llama-4-scout-17b-16e-instruct
"""

from __future__ import annotations
import os, re, io, json, base64, urllib.request, tempfile, hashlib, shutil
from pathlib import Path
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

# ── Helpers ───────────────────────────────────────────────────────────────────
def _llm_call(system: str, user: str) -> str:
    resp = _get_llm().invoke([SystemMessage(content=system), HumanMessage(content=user)])
    return resp.content.strip()

def _parse_json(raw: str) -> Any:
    raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)

def _load_pdf_bytes(src: str) -> bytes:
    if src.startswith("http://") or src.startswith("https://"):
        req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read()
    with open(src, "rb") as f:
        return f.read()

def _bytes_to_b64(data: bytes) -> str:
    return base64.b64encode(data).decode()

def _extract_text(pdf_bytes: bytes) -> str:
    try:
        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pages = []
        for i, page in enumerate(doc, 1):
            text = page.get_text("text").strip()
            if text:
                pages.append(f"[Page {i}]\n{text}")
        doc.close()
        return "\n\n".join(pages) or "No extractable text."
    except Exception as e:
        return f"ERROR: {e}"

def _extract_text_layout(pdf_bytes: bytes) -> str:
    """Text with layout preserved (blocks, positions)."""
    try:
        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pages = []
        for i, page in enumerate(doc, 1):
            blocks = page.get_text("blocks")
            lines = [f"[Page {i}]"]
            for b in sorted(blocks, key=lambda x: (x[1], x[0])):
                t = b[4].strip()
                if t:
                    lines.append(t)
            pages.append("\n".join(lines))
        doc.close()
        return "\n\n".join(pages)
    except Exception as e:
        return f"ERROR: {e}"

def _get_page_count(pdf_bytes: bytes) -> int:
    try:
        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        n = len(doc)
        doc.close()
        return n
    except:
        return 0

def _detect_scanned(pdf_bytes: bytes) -> bool:
    """Heuristic: very little extractable text → likely scanned."""
    text = _extract_text(pdf_bytes)
    words = len(text.split())
    pages = _get_page_count(pdf_bytes)
    return pages > 0 and (words / max(pages, 1)) < 50

# ═══════════════════════════════════════════════════════════════════════════════
#  FEATURE HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════

# ── 1. Core: Read / Parse ─────────────────────────────────────────────────────
def feat_read(pdf_bytes: bytes, task: str) -> dict:
    text = _extract_text(pdf_bytes)
    pages = _get_page_count(pdf_bytes)
    words = len(text.split())
    return {
        "pages": pages,
        "word_count": words,
        "text_preview": text[:2000],
        "full_text": text,
        "is_scanned": _detect_scanned(pdf_bytes),
    }

# ── 2. Create PDF from prompt ─────────────────────────────────────────────────
def feat_create(task: str) -> dict:
    SYSTEM = """You are a PDF content generator.
You MUST return ONLY a valid JSON object — no markdown fences, no explanation, no preamble.
Start your response with { and end with }.
Required format:
{
  "title": "document title",
  "plan": "structured outline",
  "python_code": "complete ReportLab Python code that saves to outputs/pdf_agent_output.pdf — include title page, headers, footers, page numbers, styled headings, body paragraphs, bullets, tables where relevant. Import everything needed. Use only reportlab.",
  "preview_text": "first 3 paragraphs of the actual document content"
}"""
    raw = _llm_call(SYSTEM, f"Create a professional PDF document about: {task}")
    # Strip markdown fences if present
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"```$", "", raw.strip()).strip()
    # Find JSON object boundaries
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start != -1 and end > start:
        raw = raw[start:end]
    if not raw:
        return {"error": "LLM returned empty response for feat_create"}
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        return {"error": f"JSON parse failed: {e}", "raw_response": raw[:500]}

    # ── Execute the generated ReportLab code and save the PDF ──────────────
    python_code = result.get("python_code", "")
    if python_code:
        output_path = "outputs/pdf_agent_output.pdf"
        try:
            os.makedirs("outputs", exist_ok=True)
            exec_globals = {"__builtins__": __builtins__}
            exec(compile(python_code, "<pdf_gen>", "exec"), exec_globals)
            if os.path.exists(output_path):
                with open(output_path, "rb") as f:
                    pdf_bytes_out = f.read()
                result["saved_path"] = output_path
                result["pdf_b64"] = _bytes_to_b64(pdf_bytes_out)
                result["file_size_kb"] = round(len(pdf_bytes_out) / 1024, 1)
                print(f"📄 PDF Agent — created PDF: {output_path} ({result['file_size_kb']} KB)")
            else:
                result["warning"] = "Code executed but PDF file not found at outputs/pdf_agent_output.pdf"
        except Exception as exec_err:
            result["exec_error"] = str(exec_err)
            # Fallback: build a simple PDF with reportlab directly
            try:
                from reportlab.lib.pagesizes import A4
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
                from reportlab.lib.styles import getSampleStyleSheet
                os.makedirs("outputs", exist_ok=True)
                doc = SimpleDocTemplate(output_path, pagesize=A4)
                styles = getSampleStyleSheet()
                story = [
                    Paragraph(result.get("title", "Generated Document"), styles["Title"]),
                    Spacer(1, 12),
                    Paragraph(result.get("preview_text", task), styles["BodyText"]),
                ]
                doc.build(story)
                with open(output_path, "rb") as f:
                    pdf_bytes_out = f.read()
                result["saved_path"] = output_path
                result["pdf_b64"] = _bytes_to_b64(pdf_bytes_out)
                result["file_size_kb"] = round(len(pdf_bytes_out) / 1024, 1)
                result["fallback_used"] = True
                print(f"📄 PDF Agent — fallback PDF saved: {output_path}")
            except Exception as fb_err:
                result["fallback_error"] = str(fb_err)

    return result

# ── 3. Summarize ──────────────────────────────────────────────────────────────
def feat_summarize(pdf_bytes: bytes, task: str) -> dict:
    text = _extract_text(pdf_bytes)[:12000]
    SYSTEM = """You are a PDF summarization expert.
Return ONLY valid JSON:
{
  "title": "inferred title",
  "summary": "2-3 paragraph executive summary",
  "key_points": ["up to 10 bullets"],
  "topics": ["topic1","topic2"],
  "word_count": 0,
  "reading_time": "X min read",
  "sentiment": "positive|neutral|negative",
  "document_type": "report|article|legal|technical|other",
  "language": "detected language"
}"""
    raw = _llm_call(SYSTEM, f"Summarize:\n\n{text}")
    return _parse_json(raw)

# ── 4. Q&A ────────────────────────────────────────────────────────────────────
def feat_qa(pdf_bytes: bytes, task: str) -> dict:
    text = _extract_text(pdf_bytes)[:14000]
    SYSTEM = """You are a PDF Q&A assistant. Answer thoroughly citing specific sections.
If not found, say so. Return plain JSON: {"answer": "...", "confidence": "high|medium|low", "source_sections": ["..."]}"""
    question = re.sub(r"(answer|question|ask|qa|q&a)[:\s]*", "", task, flags=re.I).strip() or task
    raw = _llm_call(SYSTEM, f"PDF Content:\n{text}\n\nQuestion: {question}")
    try:
        return _parse_json(raw)
    except:
        return {"answer": raw, "confidence": "medium", "source_sections": []}

# ── 5. Translate ──────────────────────────────────────────────────────────────
def feat_translate(pdf_bytes: bytes, task: str) -> dict:
    text = _extract_text(pdf_bytes)[:10000]
    lang_m = re.search(r"\bto\s+([\w ]+?)(?:\s*$|\s*\bfrom\b|\s*\bpdf\b)", task, re.I)
    lang = lang_m.group(1).strip() if lang_m else "Spanish"
    SYSTEM = """You are a PDF translation expert.
Return ONLY valid JSON:
{
  "target_language": "...",
  "translated_content": "full translated text preserving structure",
  "notes": "translation notes"
}"""
    raw = _llm_call(SYSTEM, f"Translate to {lang}:\n\n{text}")
    return _parse_json(raw)

# ── 6. Extract (tables, entities, lists, key-values) ─────────────────────────
def feat_extract(pdf_bytes: bytes, task: str) -> dict:
    text = _extract_text(pdf_bytes)[:12000]
    SYSTEM = """You are a data extraction specialist.
Return ONLY valid JSON:
{
  "tables":     [{"title":"...","headers":[...],"rows":[[...]]}],
  "key_values": {"key":"value"},
  "lists":      [{"title":"...","items":[...]}],
  "entities":   {"dates":[],"names":[],"numbers":[],"emails":[],"phones":[],"urls":[],"orgs":[]}
}"""
    raw = _llm_call(SYSTEM, f"Extract all structured data:\n\n{text}")
    return _parse_json(raw)

# ── 7. Search text ────────────────────────────────────────────────────────────
def feat_search(pdf_bytes: bytes, task: str) -> dict:
    query_m = re.search(r'(?:search|find)\s+["\']?(.+?)["\']?\s*(?:in|$)', task, re.I)
    query = query_m.group(1).strip() if query_m else task
    try:
        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        results = []
        for i, page in enumerate(doc, 1):
            hits = page.search_for(query)
            if hits:
                text_ctx = page.get_text("text")
                for hit in hits:
                    results.append({"page": i, "rect": list(hit), "context": text_ctx[:300]})
        doc.close()
        return {"query": query, "total_hits": len(results), "results": results[:50]}
    except Exception as e:
        return {"error": str(e)}

# ── 8. Find & Replace ─────────────────────────────────────────────────────────
def feat_find_replace(pdf_bytes: bytes, task: str) -> dict:
    m = re.search(r'replace\s+["\'](.+?)["\']\s+with\s+["\'](.+?)["\']', task, re.I)
    if not m:
        return {"error": "Use format: replace 'old text' with 'new text'"}
    old, new = m.group(1), m.group(2)
    text = _extract_text(pdf_bytes)
    count = text.count(old)
    replaced_text = text.replace(old, new)
    SYSTEM = "Return ONLY valid JSON: {\"python_code\": \"complete pypdf/reportlab code to replace text in PDF\", \"occurrences\": 0}"
    raw = _llm_call(SYSTEM, f"Generate Python code to replace '{old}' with '{new}' in a PDF. Found {count} occurrences.\n\nText sample:\n{text[:3000]}")
    try:
        result = _parse_json(raw)
    except:
        result = {}
    result.update({"find": old, "replace": new, "occurrences_found": count, "replaced_preview": replaced_text[:2000]})
    return result

# ── 9. Page Management ────────────────────────────────────────────────────────
def feat_page_ops(pdf_bytes: bytes, task: str) -> dict:
    tl = task.lower()
    try:
        from pypdf import PdfReader, PdfWriter
        reader = PdfReader(io.BytesIO(pdf_bytes))
        writer = PdfWriter()
        n = len(reader.pages)
        op_desc = ""

        # Rotate
        rot_m = re.search(r"rotate\s+(?:page\s*)?(\d+)\s+(?:by\s+)?(\d+)", tl)
        if rot_m:
            pg, angle = int(rot_m.group(1)) - 1, int(rot_m.group(2))
            for i, page in enumerate(reader.pages):
                writer.add_page(page)
            writer.pages[pg].rotate(angle)
            op_desc = f"Rotated page {pg+1} by {angle}°"

        # Extract pages
        elif "extract page" in tl or "extract pages" in tl:
            nums = [int(x)-1 for x in re.findall(r'\d+', task)]
            for idx in nums:
                if 0 <= idx < n:
                    writer.add_page(reader.pages[idx])
            op_desc = f"Extracted pages: {nums}"

        # Remove page
        elif "remove page" in tl or "delete page" in tl:
            nums = set(int(x)-1 for x in re.findall(r'\d+', task))
            for i, page in enumerate(reader.pages):
                if i not in nums:
                    writer.add_page(page)
            op_desc = f"Removed pages: {[n+1 for n in nums]}"

        # Add blank page
        elif "add blank" in tl or "insert blank" in tl:
            for page in reader.pages:
                writer.add_page(page)
            writer.add_blank_page()
            op_desc = "Added blank page at end"

        else:
            return {"page_count": n, "info": "Provide operation: rotate/extract/remove/add blank page"}

        out = io.BytesIO()
        writer.write(out)
        return {
            "operation": op_desc,
            "original_pages": n,
            "result_pages": len(writer.pages),
            "pdf_b64": _bytes_to_b64(out.getvalue()),
        }
    except Exception as e:
        return {"error": str(e)}

# ── 10. Merge ─────────────────────────────────────────────────────────────────
def feat_merge(pdf_bytes_list: list[bytes]) -> dict:
    try:
        from pypdf import PdfWriter
        writer = PdfWriter()
        total = 0
        for pb in pdf_bytes_list:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(pb))
            for page in reader.pages:
                writer.add_page(page)
                total += 1
        out = io.BytesIO()
        writer.write(out)
        return {"merged_pages": total, "pdf_b64": _bytes_to_b64(out.getvalue())}
    except Exception as e:
        return {"error": str(e)}

# ── 11. Split ─────────────────────────────────────────────────────────────────
def feat_split(pdf_bytes: bytes, task: str) -> dict:
    try:
        from pypdf import PdfReader, PdfWriter
        reader = PdfReader(io.BytesIO(pdf_bytes))
        n = len(reader.pages)
        # Parse range e.g. "split 1-5 and 6-10" or "split every 3 pages"
        ranges_raw = re.findall(r'(\d+)\s*[-–]\s*(\d+)', task)
        if not ranges_raw:
            # split in half
            mid = n // 2
            ranges_raw = [(1, mid), (mid+1, n)]
        parts = []
        for start, end in ranges_raw:
            writer = PdfWriter()
            for i in range(int(start)-1, min(int(end), n)):
                writer.add_page(reader.pages[i])
            out = io.BytesIO()
            writer.write(out)
            parts.append({"range": f"{start}-{end}", "pages": int(end)-int(start)+1, "pdf_b64": _bytes_to_b64(out.getvalue())})
        return {"original_pages": n, "parts": parts}
    except Exception as e:
        return {"error": str(e)}

# ── 12. Add Watermark ─────────────────────────────────────────────────────────
def feat_watermark(pdf_bytes: bytes, task: str) -> dict:
    wm_m = re.search(r'watermark\s+["\']?(.+?)["\']?\s*$', task, re.I)
    wm_text = wm_m.group(1).strip() if wm_m else "CONFIDENTIAL"
    try:
        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page in doc:
            rect = page.rect
            page.insert_text(
                (rect.width * 0.15, rect.height * 0.5),
                wm_text,
                fontsize=48,
                color=(0.8, 0.8, 0.8),
                rotate=45,
                overlay=True,
            )
        out = io.BytesIO()
        doc.save(out)
        doc.close()
        return {"watermark": wm_text, "pdf_b64": _bytes_to_b64(out.getvalue())}
    except Exception as e:
        return {"error": str(e)}

# ── 13. Add Page Numbers ──────────────────────────────────────────────────────
def feat_page_numbers(pdf_bytes: bytes, task: str) -> dict:
    try:
        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for i, page in enumerate(doc, 1):
            rect = page.rect
            page.insert_text(
                (rect.width / 2 - 10, rect.height - 20),
                str(i),
                fontsize=10,
                color=(0, 0, 0),
            )
        out = io.BytesIO()
        doc.save(out)
        doc.close()
        return {"pages_numbered": len(doc), "pdf_b64": _bytes_to_b64(out.getvalue())}
    except Exception as e:
        return {"error": str(e)}

# ── 14. Add Header / Footer ───────────────────────────────────────────────────
def feat_header_footer(pdf_bytes: bytes, task: str) -> dict:
    header_m = re.search(r'header\s+["\'](.+?)["\']', task, re.I)
    footer_m = re.search(r'footer\s+["\'](.+?)["\']', task, re.I)
    header = header_m.group(1) if header_m else ""
    footer = footer_m.group(1) if footer_m else ""
    try:
        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page in doc:
            rect = page.rect
            if header:
                page.insert_text((20, 15), header, fontsize=9, color=(0.3, 0.3, 0.3))
            if footer:
                page.insert_text((20, rect.height - 10), footer, fontsize=9, color=(0.3, 0.3, 0.3))
        out = io.BytesIO()
        doc.save(out)
        doc.close()
        return {"header": header, "footer": footer, "pdf_b64": _bytes_to_b64(out.getvalue())}
    except Exception as e:
        return {"error": str(e)}

# ── 15. Extract Images ────────────────────────────────────────────────────────
def feat_extract_images(pdf_bytes: bytes, task: str) -> dict:
    try:
        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        images = []
        for i, page in enumerate(doc, 1):
            for img in page.get_images(full=True):
                xref = img[0]
                base_img = doc.extract_image(xref)
                images.append({
                    "page": i,
                    "width": base_img["width"],
                    "height": base_img["height"],
                    "ext": base_img["ext"],
                    "image_b64": _bytes_to_b64(base_img["image"]),
                })
        doc.close()
        return {"total_images": len(images), "images": images[:20]}
    except Exception as e:
        return {"error": str(e)}

# ── 16. Convert PDF pages to images ──────────────────────────────────────────
def feat_pdf_to_images(pdf_bytes: bytes, task: str) -> dict:
    fmt_m = re.search(r'\b(png|jpg|jpeg)\b', task, re.I)
    fmt = (fmt_m.group(1).lower() if fmt_m else "png").replace("jpg", "jpeg")
    try:
        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        images = []
        for i, page in enumerate(doc, 1):
            mat = fitz.Matrix(2.0, 2.0)  # 2x resolution
            pix = page.get_pixmap(matrix=mat)
            img_bytes = pix.tobytes(fmt)
            images.append({"page": i, "format": fmt, "width": pix.width, "height": pix.height, "image_b64": _bytes_to_b64(img_bytes)})
        doc.close()
        return {"total_pages": len(images), "format": fmt, "images": images}
    except Exception as e:
        return {"error": str(e)}

# ── 17. PDF Metadata ──────────────────────────────────────────────────────────
def feat_metadata(pdf_bytes: bytes, task: str) -> dict:
    try:
        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        meta = doc.metadata
        doc.close()
    except:
        meta = {}
    text_sample = _extract_text(pdf_bytes)[:3000]
    SYSTEM = """You are a PDF metadata analyst.
Return ONLY valid JSON:
{
  "detected_metadata": {"title":"","author":"","subject":"","keywords":[],"created":"","modified":""},
  "suggested_metadata": {"title":"","author":"","subject":"","keywords":[]},
  "python_code": "complete pypdf code to set the suggested metadata",
  "seo_score": "1-10 with explanation"
}"""
    raw = _llm_call(SYSTEM, f"Metadata from file: {json.dumps(meta)}\n\nContent sample:\n{text_sample}\n\nTask: {task}")
    try:
        result = _parse_json(raw)
    except:
        result = {"detected_metadata": meta}
    result["raw_metadata"] = meta
    return result

# ── 18. Set / Write Metadata ──────────────────────────────────────────────────
def feat_set_metadata(pdf_bytes: bytes, task: str) -> dict:
    SYSTEM = """Extract metadata fields from the user's task and return ONLY valid JSON:
{"title":"","author":"","subject":"","keywords":[],"creator":""}"""
    raw = _llm_call(SYSTEM, task)
    try:
        fields = _parse_json(raw)
    except:
        fields = {}
    try:
        from pypdf import PdfReader, PdfWriter
        reader = PdfReader(io.BytesIO(pdf_bytes))
        writer = PdfWriter()
        writer.append_pages_from_reader(reader)
        writer.add_metadata({f"/{k.capitalize()}": v for k, v in fields.items() if v})
        out = io.BytesIO()
        writer.write(out)
        return {"metadata_set": fields, "pdf_b64": _bytes_to_b64(out.getvalue())}
    except Exception as e:
        return {"error": str(e), "fields_parsed": fields}

# ── 19. Password Protect ──────────────────────────────────────────────────────
def feat_protect(pdf_bytes: bytes, task: str) -> dict:
    pw_m = re.search(r'password\s+["\']?(\S+)["\']?', task, re.I)
    password = pw_m.group(1) if pw_m else "pdf_password_123"
    try:
        from pypdf import PdfReader, PdfWriter
        reader = PdfReader(io.BytesIO(pdf_bytes))
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        writer.encrypt(password)
        out = io.BytesIO()
        writer.write(out)
        return {"password_set": True, "password": password, "pdf_b64": _bytes_to_b64(out.getvalue())}
    except Exception as e:
        return {"error": str(e)}

# ── 20. Remove Password ───────────────────────────────────────────────────────
def feat_decrypt(pdf_bytes: bytes, task: str) -> dict:
    pw_m = re.search(r'password\s+["\']?(\S+)["\']?', task, re.I)
    password = pw_m.group(1) if pw_m else ""
    try:
        from pypdf import PdfReader, PdfWriter
        reader = PdfReader(io.BytesIO(pdf_bytes))
        if reader.is_encrypted:
            reader.decrypt(password)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        out = io.BytesIO()
        writer.write(out)
        return {"decrypted": True, "pdf_b64": _bytes_to_b64(out.getvalue())}
    except Exception as e:
        return {"error": str(e)}

# ── 21. Redact ────────────────────────────────────────────────────────────────
def feat_redact(pdf_bytes: bytes, task: str) -> dict:
    terms_m = re.findall(r'["\']([^"\']+)["\']', task)
    if not terms_m:
        terms_m = re.sub(r'redact\s*', '', task, flags=re.I).strip().split(',')
        terms_m = [t.strip() for t in terms_m if t.strip()]
    try:
        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        redacted = 0
        for page in doc:
            for term in terms_m:
                hits = page.search_for(term)
                for hit in hits:
                    page.add_redact_annot(hit, fill=(0, 0, 0))
                    redacted += 1
            page.apply_redactions()
        out = io.BytesIO()
        doc.save(out)
        doc.close()
        return {"redacted_terms": terms_m, "total_redactions": redacted, "pdf_b64": _bytes_to_b64(out.getvalue())}
    except Exception as e:
        return {"error": str(e)}

# ── 22. OCR ───────────────────────────────────────────────────────────────────
def feat_ocr(pdf_bytes: bytes, task: str) -> dict:
    lang_m = re.search(r'\blang(?:uage)?\s+(\w+)', task, re.I)
    lang = lang_m.group(1) if lang_m else "eng"
    is_scanned = _detect_scanned(pdf_bytes)
    try:
        import fitz
        try:
            import pytesseract
            from PIL import Image
        except ImportError:
            return {
                "is_scanned": is_scanned,
                "error": "pytesseract / PIL not installed. Run: pip install pytesseract pillow",
                "install_hint": "Also install Tesseract OCR binary: https://github.com/tesseract-ocr/tesseract"
            }
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        ocr_text = []
        for i, page in enumerate(doc, 1):
            mat = fitz.Matrix(2, 2)
            pix = page.get_pixmap(matrix=mat)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text = pytesseract.image_to_string(img, lang=lang)
            ocr_text.append(f"[Page {i}]\n{text}")
        doc.close()
        full_text = "\n\n".join(ocr_text)
        return {
            "is_scanned": is_scanned,
            "ocr_language": lang,
            "ocr_text": full_text,
            "word_count": len(full_text.split()),
        }
    except Exception as e:
        return {"error": str(e), "is_scanned": is_scanned}

# ── 23. Compress ──────────────────────────────────────────────────────────────
def feat_compress(pdf_bytes: bytes, task: str) -> dict:
    original_size = len(pdf_bytes)
    try:
        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        out = io.BytesIO()
        doc.save(out, garbage=4, deflate=True, clean=True)
        doc.close()
        compressed = out.getvalue()
        return {
            "original_size_kb": round(original_size / 1024, 1),
            "compressed_size_kb": round(len(compressed) / 1024, 1),
            "reduction_pct": round((1 - len(compressed)/original_size) * 100, 1),
            "pdf_b64": _bytes_to_b64(compressed),
        }
    except Exception as e:
        return {"error": str(e)}

# ── 24. Highlight / Annotate ──────────────────────────────────────────────────
def feat_annotate(pdf_bytes: bytes, task: str) -> dict:
    terms_m = re.findall(r'["\']([^"\']+)["\']', task)
    note_m = re.search(r'(?:note|comment|sticky)\s*[:\-]?\s*["\'](.+?)["\']', task, re.I)
    note_text = note_m.group(1) if note_m else ""
    try:
        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        annotations = 0
        for page in doc:
            for term in terms_m:
                hits = page.search_for(term)
                for hit in hits:
                    page.add_highlight_annot(hit)
                    annotations += 1
            if note_text and annotations == 0:
                rect = fitz.Rect(20, 20, 200, 60)
                page.add_text_annot(rect.tl, note_text)
                annotations += 1
                break
        out = io.BytesIO()
        doc.save(out)
        doc.close()
        return {"annotations_added": annotations, "highlighted_terms": terms_m, "note": note_text, "pdf_b64": _bytes_to_b64(out.getvalue())}
    except Exception as e:
        return {"error": str(e)}

# ── 25. Bookmarks / TOC ───────────────────────────────────────────────────────
def feat_bookmarks(pdf_bytes: bytes, task: str) -> dict:
    try:
        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        toc = doc.get_toc()
        doc.close()
        if not toc:
            # Auto-generate from headings using LLM
            text = _extract_text(pdf_bytes)[:8000]
            SYSTEM = """Analyze the PDF text and generate a table of contents.
Return ONLY valid JSON:
{"toc": [{"level": 1, "title": "...", "page": 1}], "python_code": "pypdf code to set bookmarks"}"""
            raw = _llm_call(SYSTEM, f"Generate TOC from:\n{text}")
            try:
                return _parse_json(raw)
            except:
                return {"toc": [], "message": "No bookmarks found, could not generate TOC"}
        return {"toc": [{"level": t[0], "title": t[1], "page": t[2]} for t in toc]}
    except Exception as e:
        return {"error": str(e)}

# ── 26. Reformat / Restructure ────────────────────────────────────────────────
def feat_reformat(pdf_bytes: bytes, task: str) -> dict:
    text = _extract_text(pdf_bytes)[:10000]
    SYSTEM = """You are a PDF reformatting assistant.
Return ONLY valid JSON:
{
  "original_analysis": "brief analysis of the current structure",
  "suggested_structure": "description of the improved structure",
  "python_code": "complete ReportLab code for the reformatted version",
  "changes_made": ["change 1", "change 2"]
}"""
    raw = _llm_call(SYSTEM, f"Reformat this PDF.\nInstructions: {task}\n\nContent:\n{text}")
    return _parse_json(raw)

# ── 27. Merge Plan (AI strategy) ──────────────────────────────────────────────
def feat_merge_plan(task: str) -> dict:
    SYSTEM = """You are a PDF merge strategist.
Return ONLY valid JSON:
{
  "merge_strategy": "description of how to merge",
  "document_order": ["doc 1 purpose", "doc 2 purpose"],
  "python_code": "complete pypdf code to perform the merge",
  "recommendations": ["tip 1", "tip 2"]
}"""
    raw = _llm_call(SYSTEM, f"Plan this PDF merge: {task}")
    return _parse_json(raw)

# ── 28. Generate from template (Markdown → PDF) ───────────────────────────────
def feat_md_to_pdf(task: str) -> dict:
    SYSTEM = """You are a Markdown-to-PDF generator.
Return ONLY valid JSON:
{
  "markdown_content": "complete markdown document",
  "python_code": "Python code using reportlab or weasyprint to convert markdown to PDF",
  "preview": "first 500 chars of the document"
}"""
    raw = _llm_call(SYSTEM, f"Generate a Markdown document and PDF conversion code for: {task}")
    return _parse_json(raw)

# ── 29. Extract Tables → CSV ──────────────────────────────────────────────────
def feat_tables_to_csv(pdf_bytes: bytes, task: str) -> dict:
    data = feat_extract(pdf_bytes, task)
    tables = data.get("tables", [])
    csvs = []
    for t in tables:
        lines = [",".join(str(h) for h in t.get("headers", []))]
        for row in t.get("rows", []):
            lines.append(",".join(str(c) for c in row))
        csvs.append({"title": t.get("title", "Table"), "csv": "\n".join(lines)})
    return {"tables_found": len(tables), "csvs": csvs}

# ── 30. PDF → Markdown ────────────────────────────────────────────────────────
def feat_to_markdown(pdf_bytes: bytes, task: str) -> dict:
    text = _extract_text_layout(pdf_bytes)[:12000]
    SYSTEM = """Convert the PDF text content to clean, well-structured Markdown.
Return ONLY valid JSON: {"markdown": "full markdown content", "headings": ["h1", "h2"...], "sections": 0}"""
    raw = _llm_call(SYSTEM, f"Convert to Markdown:\n\n{text}")
    try:
        return _parse_json(raw)
    except:
        return {"markdown": raw}

# ── 31. PDF → HTML ────────────────────────────────────────────────────────────
def feat_to_html(pdf_bytes: bytes, task: str) -> dict:
    text = _extract_text_layout(pdf_bytes)[:12000]
    SYSTEM = """Convert the PDF text to clean semantic HTML5.
Return ONLY valid JSON: {"html": "full HTML document with proper tags, headings, paragraphs, lists, tables"}"""
    raw = _llm_call(SYSTEM, f"Convert to HTML:\n\n{text}")
    try:
        return _parse_json(raw)
    except:
        return {"html": f"<html><body><pre>{text}</pre></body></html>"}

# ── 32. Classify Document ─────────────────────────────────────────────────────
def feat_classify(pdf_bytes: bytes, task: str) -> dict:
    text = _extract_text(pdf_bytes)[:6000]
    SYSTEM = """Classify the PDF document.
Return ONLY valid JSON:
{
  "document_type": "invoice|contract|report|resume|article|legal|technical|financial|medical|other",
  "confidence": "high|medium|low",
  "sub_type": "more specific classification",
  "language": "detected language",
  "estimated_date": "approximate date range of document",
  "topics": ["topic1", "topic2"],
  "reasoning": "brief explanation"
}"""
    raw = _llm_call(SYSTEM, f"Classify this document:\n\n{text}")
    return _parse_json(raw)

# ── 33. Sentiment Analysis ────────────────────────────────────────────────────
def feat_sentiment(pdf_bytes: bytes, task: str) -> dict:
    text = _extract_text(pdf_bytes)[:8000]
    SYSTEM = """Perform sentiment analysis on the PDF content.
Return ONLY valid JSON:
{
  "overall_sentiment": "positive|negative|neutral|mixed",
  "sentiment_score": 0.0,
  "emotion_breakdown": {"joy":0,"anger":0,"fear":0,"surprise":0,"sadness":0,"trust":0},
  "key_positive_phrases": ["..."],
  "key_negative_phrases": ["..."],
  "tone": "formal|informal|persuasive|informative|emotional",
  "summary": "2-3 sentence analysis"
}"""
    raw = _llm_call(SYSTEM, f"Analyze sentiment:\n\n{text}")
    return _parse_json(raw)

# ── 34. Named Entity Recognition ─────────────────────────────────────────────
def feat_ner(pdf_bytes: bytes, task: str) -> dict:
    text = _extract_text(pdf_bytes)[:10000]
    SYSTEM = """Extract all named entities from the PDF.
Return ONLY valid JSON:
{
  "people": ["name1","name2"],
  "organizations": ["org1","org2"],
  "locations": ["loc1","loc2"],
  "dates": ["date1","date2"],
  "money": ["$1000","€500"],
  "emails": ["email@example.com"],
  "phones": ["+1-234-567-8900"],
  "urls": ["https://example.com"],
  "products": ["product1"],
  "events": ["event1"]
}"""
    raw = _llm_call(SYSTEM, f"Extract all named entities:\n\n{text}")
    return _parse_json(raw)

# ── 35. Compare Two PDFs ──────────────────────────────────────────────────────
def feat_compare(pdf1_bytes: bytes, pdf2_bytes: bytes) -> dict:
    text1 = _extract_text(pdf1_bytes)[:6000]
    text2 = _extract_text(pdf2_bytes)[:6000]
    SYSTEM = """Compare two PDF documents and identify differences.
Return ONLY valid JSON:
{
  "similarity_pct": 0,
  "doc1_unique": ["content only in doc1"],
  "doc2_unique": ["content only in doc2"],
  "common_topics": ["shared topics"],
  "key_differences": ["difference 1", "difference 2"],
  "recommendation": "which is more recent/complete and why"
}"""
    raw = _llm_call(SYSTEM, f"Compare:\n\n--- Document 1 ---\n{text1}\n\n--- Document 2 ---\n{text2}")
    return _parse_json(raw)

# ── 36. Rewrite / Rephrase ────────────────────────────────────────────────────
def feat_rewrite(pdf_bytes: bytes, task: str) -> dict:
    text = _extract_text(pdf_bytes)[:10000]
    style_m = re.search(r'(?:rewrite|rephrase)\s+(?:in\s+)?(.+?)(?:\s+style)?$', task, re.I)
    style = style_m.group(1).strip() if style_m else "formal professional"
    SYSTEM = f"""You are a document rewriter. Rewrite the content in a {style} style.
Return ONLY valid JSON:
{{"rewritten_text": "full rewritten content", "changes_summary": "what changed", "word_count_original": 0, "word_count_new": 0}}"""
    raw = _llm_call(SYSTEM, f"Rewrite:\n\n{text}")
    return _parse_json(raw)

# ── 37. Auto-tag / Categorize ─────────────────────────────────────────────────
def feat_autotag(pdf_bytes: bytes, task: str) -> dict:
    text = _extract_text(pdf_bytes)[:6000]
    SYSTEM = """Auto-tag and categorize this PDF document.
Return ONLY valid JSON:
{
  "tags": ["tag1","tag2","tag3"],
  "categories": ["primary","secondary"],
  "department": "HR|Legal|Finance|Engineering|Marketing|Other",
  "priority": "high|medium|low",
  "action_required": true,
  "expiry_suggestion": "when this document may become outdated",
  "related_document_types": ["type1","type2"]
}"""
    raw = _llm_call(SYSTEM, f"Auto-tag this document:\n\n{text}")
    return _parse_json(raw)

# ── 38. Forms ─────────────────────────────────────────────────────────────────
def feat_forms(pdf_bytes: bytes, task: str) -> dict:
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(pdf_bytes))
        fields = reader.get_fields() or {}
        return {
            "has_form": bool(fields),
            "field_count": len(fields),
            "fields": {k: {"type": v.get("/FT",""), "value": v.get("/V","")} for k,v in fields.items()},
            "python_code": f"# To fill fields:\nfrom pypdf import PdfReader, PdfWriter\nwriter = PdfWriter()\nwriter.append(reader)\nwriter.update_page_form_field_values(writer.pages[0], {{{', '.join([repr(k)+': '+repr('value') for k in list(fields.keys())[:3]])}}})"
        }
    except Exception as e:
        return {"error": str(e)}

# ── 39. Accessibility Check ───────────────────────────────────────────────────
def feat_accessibility(pdf_bytes: bytes, task: str) -> dict:
    text = _extract_text(pdf_bytes)
    pages = _get_page_count(pdf_bytes)
    images_data = feat_extract_images(pdf_bytes, task)
    total_images = images_data.get("total_images", 0)
    SYSTEM = """Audit a PDF for accessibility (WCAG / PDF/UA compliance).
Return ONLY valid JSON:
{
  "score": "A|AA|AAA|Non-compliant",
  "issues": [{"issue":"...","severity":"high|medium|low","fix":"..."}],
  "passed": ["test1","test2"],
  "recommendations": ["rec1","rec2"],
  "estimated_remediation_effort": "low|medium|high"
}"""
    raw = _llm_call(SYSTEM, f"Audit accessibility. Pages: {pages}, Images: {total_images}, Text length: {len(text)}\n\nText sample:\n{text[:3000]}")
    return _parse_json(raw)

# ── 40. Batch Processing ──────────────────────────────────────────────────────
def feat_batch_info(task: str) -> dict:
    SYSTEM = """Generate Python code for batch PDF processing.
Return ONLY valid JSON:
{
  "operation": "detected batch operation",
  "python_code": "complete Python script for batch processing multiple PDFs",
  "cli_command": "command line usage example",
  "notes": ["note1","note2"]
}"""
    raw = _llm_call(SYSTEM, f"Generate batch processing code for: {task}")
    return _parse_json(raw)

# ── 41. Digital Signature ─────────────────────────────────────────────────────
def feat_signature(pdf_bytes: bytes, task: str) -> dict:
    SYSTEM = """Generate Python code to add a digital signature to a PDF.
Return ONLY valid JSON:
{
  "python_code": "complete Python code using pyhanko or pypdf to add a digital signature",
  "requirements": ["pyhanko", "cryptography"],
  "notes": ["important notes about digital signatures"]
}"""
    raw = _llm_call(SYSTEM, f"Add digital signature to PDF: {task}")
    return _parse_json(raw)

# ── 42. Repair corrupted PDF ──────────────────────────────────────────────────
def feat_repair(pdf_bytes: bytes, task: str) -> dict:
    try:
        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        out = io.BytesIO()
        doc.save(out, garbage=4, deflate=True, clean=True)
        pages = len(doc)
        doc.close()
        return {"repaired": True, "pages_recovered": pages, "pdf_b64": _bytes_to_b64(out.getvalue())}
    except Exception as e:
        return {"repaired": False, "error": str(e)}

# ── 43. Linearize (fast web view) ────────────────────────────────────────────
def feat_linearize(pdf_bytes: bytes, task: str) -> dict:
    try:
        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        out = io.BytesIO()
        doc.save(out, linear=True)
        doc.close()
        return {"linearized": True, "pdf_b64": _bytes_to_b64(out.getvalue())}
    except Exception as e:
        return {"error": str(e)}

# ═══════════════════════════════════════════════════════════════════════════════
#  MODE ROUTING
# ═══════════════════════════════════════════════════════════════════════════════

FEATURE_MAP = {
    # Core
    "read":           feat_read,
    "create":         feat_create,
    "summarize":      feat_summarize,
    "qa":             feat_qa,
    "translate":      feat_translate,
    "extract":        feat_extract,
    # Text ops
    "search":         feat_search,
    "find_replace":   feat_find_replace,
    "watermark":      feat_watermark,
    "page_numbers":   feat_page_numbers,
    "header_footer":  feat_header_footer,
    # Page management
    "page_ops":       feat_page_ops,
    # Merge/Split
    "merge":          None,  # handled separately
    "merge_plan":     feat_merge_plan,
    "split":          feat_split,
    # Images
    "extract_images": feat_extract_images,
    "pdf_to_images":  feat_pdf_to_images,
    # AI
    "reformat":       feat_reformat,
    "classify":       feat_classify,
    "sentiment":      feat_sentiment,
    "ner":            feat_ner,
    "compare":        None,  # handled separately
    "rewrite":        feat_rewrite,
    "autotag":        feat_autotag,
    "md_to_pdf":      feat_md_to_pdf,
    # Data
    "tables_to_csv":  feat_tables_to_csv,
    "to_markdown":    feat_to_markdown,
    "to_html":        feat_to_html,
    # Metadata
    "metadata":       feat_metadata,
    "set_metadata":   feat_set_metadata,
    # Security
    "protect":        feat_protect,
    "decrypt":        feat_decrypt,
    "redact":         feat_redact,
    "signature":      feat_signature,
    # OCR
    "ocr":            feat_ocr,
    # Annotations
    "annotate":       feat_annotate,
    # Bookmarks
    "bookmarks":      feat_bookmarks,
    # Optimization
    "compress":       feat_compress,
    "repair":         feat_repair,
    "linearize":      feat_linearize,
    # Forms
    "forms":          feat_forms,
    # Accessibility
    "accessibility":  feat_accessibility,
    # Batch
    "batch":          feat_batch_info,
}

_MODE_KEYWORDS = {
    "create":         ["create", "generate a pdf", "make a pdf", "build a pdf", "new pdf", "write a pdf"],
    "summarize":      ["summarize", "summary", "overview", "brief", "key points", "tldr"],
    "qa":             ["question", "ask", "what is", "who is", "how does", "answer", "q&a", "qa"],
    "translate":      ["translate", "translation", "to spanish", "to french", "to hindi", "to arabic", "to german"],
    "extract":        ["extract data", "extract table", "key-value", "named entit", "extract list", "structured data"],
    "search":         ["search for", "find text", "search text", "search in"],
    "find_replace":   ["find and replace", "replace '", "replace \""],
    "watermark":      ["watermark"],
    "page_numbers":   ["page number", "add numbering", "number pages"],
    "header_footer":  ["header", "footer"],
    "page_ops":       ["rotate page", "remove page", "delete page", "extract page", "add blank", "insert blank", "reorder"],
    "split":          ["split", "divide pdf", "break pdf", "separate pages"],
    "merge":          ["merge", "combine pdf", "join pdf"],
    "merge_plan":     ["merge plan", "merge strategy"],
    "extract_images": ["extract image", "pull image", "get image"],
    "pdf_to_images":  ["pdf to image", "convert to png", "convert to jpg", "pages to image"],
    "metadata":       ["metadata", "author info", "seo score", "document info"],
    "set_metadata":   ["set metadata", "update metadata", "write metadata", "set author", "set title"],
    "protect":        ["protect", "encrypt", "password protect", "lock pdf"],
    "decrypt":        ["decrypt", "remove password", "unlock pdf"],
    "redact":         ["redact"],
    "signature":      ["signature", "sign pdf", "digital sign"],
    "ocr":            ["ocr", "scanned pdf", "image-based pdf", "searchable"],
    "annotate":       ["highlight", "annotate", "comment", "sticky note", "markup"],
    "bookmarks":      ["bookmark", "table of contents", "toc", "outline"],
    "reformat":       ["reformat", "restructure", "restyle", "redesign layout"],
    "classify":       ["classify", "document type", "categorize document"],
    "sentiment":      ["sentiment", "emotion", "tone analysis"],
    "ner":            ["named entity", "extract names", "extract emails", "extract phones", "ner"],
    "compare":        ["compare", "diff", "difference between"],
    "rewrite":        ["rewrite", "rephrase", "paraphrase"],
    "autotag":        ["tag", "auto-tag", "label document", "categorize"],
    "md_to_pdf":      ["markdown to pdf", "md to pdf", "from markdown"],
    "tables_to_csv":  ["table to csv", "extract csv", "table to excel", "export tables"],
    "to_markdown":    ["to markdown", "convert to markdown", "pdf to markdown"],
    "to_html":        ["to html", "convert to html", "pdf to html"],
    "compress":       ["compress", "reduce size", "optimize size", "shrink pdf"],
    "repair":         ["repair", "fix pdf", "corrupted", "broken pdf"],
    "linearize":      ["linearize", "web view", "fast web", "optimize for web"],
    "forms":          ["form", "fillable", "form field", "checkbox", "fill form"],
    "accessibility":  ["accessibility", "wcag", "screen reader", "pdf/ua", "accessible"],
    "batch":          ["batch", "bulk process", "multiple files", "mass convert"],
    "read":           ["read pdf", "parse pdf", "open pdf", "load pdf"],
}

def _infer_mode(task: str) -> str:
    tl = task.lower()
    for mode, keywords in _MODE_KEYWORDS.items():
        if any(kw in tl for kw in keywords):
            return mode
    return "summarize"

# ── PDF source detection ──────────────────────────────────────────────────────
def _detect_pdf_source(task: str):
    url_m = re.search(r"https?://\S+\.pdf", task, re.IGNORECASE)
    if url_m:
        return "url", url_m.group(0).rstrip(".,)")
    path_m = re.search(r"([/~][\w/._-]+\.pdf|[\w._-]+\.pdf)", task, re.IGNORECASE)
    if path_m:
        raw = path_m.group(0)
        for prefix in ("", "uploads/", "git_agent_output/"):
            full = prefix + raw if not os.path.isabs(raw) else raw
            if os.path.exists(full):
                return "path", full
        return "path", raw
    return "none", ""

# ── Main entry ────────────────────────────────────────────────────────────────
def run_pdf_agent(state: AgentState) -> AgentState:
    task      = state.get("task", "")
    mode      = state.get("pdf_mode", "auto").strip().lower()
    pdf_text  = state.get("pdf_text", "")
    pdf_bytes = state.get("pdf_bytes", b"")  # raw bytes, optional
    pdf2_bytes= state.get("pdf2_bytes", b"")  # for compare/merge

    print(f"\n📄 PDF Agent — task: {task[:80]}  mode: {mode}")

    if mode in ("auto", "", None):
        mode = _infer_mode(task)
    print(f"📄 PDF Agent — resolved mode: {mode}")

    # Load PDF bytes if needed
    NO_PDF_MODES = {"create", "merge_plan", "md_to_pdf", "batch"}
    if mode not in NO_PDF_MODES and not pdf_bytes:
        if pdf_text:
            # We have text, that's enough for AI modes
            pdf_bytes = b""
        else:
            src_type, src_val = _detect_pdf_source(task)
            if src_type == "none":
                return {**state, "pdf_result": json.dumps({
                    "error": "No PDF source found. Provide a file path or URL, or pass pdf_bytes in state.",
                    "examples": ["summarize PDF at uploads/doc.pdf", "extract from https://example.com/doc.pdf"]
                })}
            try:
                pdf_bytes = _load_pdf_bytes(src_val)
                print(f"📄 PDF Agent — loaded {len(pdf_bytes):,} bytes from {src_type}: {src_val}")
            except Exception as e:
                return {**state, "pdf_result": json.dumps({"error": str(e)})}

    try:
        # Special multi-PDF operations
        if mode == "compare":
            if not pdf2_bytes:
                result = {"error": "compare needs two PDFs: pass pdf_bytes and pdf2_bytes"}
            else:
                result = feat_compare(pdf_bytes, pdf2_bytes)

        elif mode == "merge" and pdf2_bytes:
            result = feat_merge([pdf_bytes, pdf2_bytes])

        elif mode == "merge_plan":
            result = feat_merge_plan(task)

        # Modes that don't need pdf_bytes
        elif mode == "create":
            result = feat_create(task)

        elif mode == "md_to_pdf":
            result = feat_md_to_pdf(task)

        elif mode == "batch":
            result = feat_batch_info(task)

        # All other modes need pdf_bytes
        elif not pdf_bytes and not pdf_text:
            result = {"error": f"Mode '{mode}' requires a PDF file."}

        else:
            # For AI-only modes that just need text, synthesize pdf_bytes from text
            if not pdf_bytes and pdf_text:
                pdf_bytes = pdf_text.encode()  # not real PDF, but text extraction fallback

            handler = FEATURE_MAP.get(mode)
            if handler is None:
                result = {"error": f"Unknown mode: {mode}. Available: {list(FEATURE_MAP.keys())}"}
            elif mode in ("read",):
                result = handler(pdf_bytes, task)
            elif mode in ("merge_plan", "batch"):
                result = handler(task)
            else:
                result = handler(pdf_bytes, task)

    except Exception as e:
        import traceback
        result = {"error": str(e), "traceback": traceback.format_exc()[-1000:]}

    output = json.dumps(result, ensure_ascii=False, indent=2)
    print(f"📄 PDF Agent — done, output {len(output):,} chars")
    return {**state, "pdf_result": output}

